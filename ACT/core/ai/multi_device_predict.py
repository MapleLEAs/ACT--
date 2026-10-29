from typing import Dict, Any
from .inference import InferenceEngine
import logging

logger = logging.getLogger(__name__)

def multi_device_predict(devices: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    多设备联合预测模型 (Multi-device Joint Prediction)
    处理不同设备类型之间的耦合影响，例如 VHF 通信故障导致 ILS 信号干扰。
    
    Args:
        devices: 设备数据字典 {'VHF': {...}, 'ILS': {...}}
    
    Returns:
        results: 联合预测结果
    """
    results = {}
    engine = InferenceEngine.get_instance()
    
    # 1. 预测 VHF (通信设备)
    vhf_input = devices.get("VHF")
    if vhf_input:
        device_id = vhf_input.get("device_id", "VHF-001")
        metrics = {
            'device_temperature': vhf_input.get('temperature', 20.0),
            'signal_strength': vhf_input.get('signal_strength', 80.0),
            'power_voltage': vhf_input.get('power_voltage', 220.0)
        }
        
        # 使用 InferenceEngine 里的 HybridPredictor
        vhf_result = engine.infer(device_id, "VHF", metrics, enable_prediction=True)
        results["VHF"] = {
            "device_id": device_id,
            "temp": vhf_result.predictions.get('device_temperature', metrics['device_temperature']),
            "signal": vhf_result.predictions.get('signal_strength', metrics['signal_strength']),
            "health": 1.0 - (abs(vhf_result.anomaly_score) if vhf_result.anomaly_score < 0 else 0),
            "alarm_status": "ALARM" if vhf_result.is_anomaly else "NORMAL"
        }
    
    # 2. VHF 影响 ILS (导航设备)
    ils_input = devices.get("ILS")
    if ils_input:
        device_id = ils_input.get("device_id", "ILS-001")
        
        metrics = {
            'device_temperature': ils_input.get('temperature', 20.0),
            'signal_power': ils_input.get('signal_power', 90.0),
            'power_voltage': ils_input.get('power_voltage', 220.0),
            'interference': ils_input.get('interference', 0.0)
        }
        
        # 计算 VHF 信号损失对 ILS 的影响
        if "VHF" in results:
            vhf_signal = results["VHF"].get("signal", 80.0)
            signal_loss = max(0.0, (80.0 - vhf_signal) / 100.0)
            # 更新 ILS 输入参数 (耦合影响: VHF 信号变弱，增加干扰)
            metrics["interference"] += signal_loss * 0.3
            
        ils_result = engine.infer(device_id, "ILS", metrics, enable_prediction=True)
        results["ILS"] = {
            "device_id": device_id,
            "temp": ils_result.predictions.get('device_temperature', metrics['device_temperature']),
            "signal": ils_result.predictions.get('signal_power', metrics['signal_power']),
            "health": 1.0 - (abs(ils_result.anomaly_score) if ils_result.anomaly_score < 0 else 0),
            "alarm_status": "ALARM" if ils_result.is_anomaly else "NORMAL"
        }
        
    # 3. 系统健康度评估
    results["system_health"] = calculate_system_health(results)
    
    return results

def calculate_system_health(results: Dict[str, Any]) -> float:
    """计算系统整体健康度"""
    weights = {
        "VHF": 0.4,  # 通信设备权重较高
        "ILS": 0.3,  # 导航设备权重
        "VOR": 0.15,
        "DME": 0.15
    }
    
    total_health = 0.0
    weight_sum = 0.0
    
    for device_type, weight in weights.items():
        if device_type in results:
            total_health += results[device_type].get("health", 1.0) * weight
            weight_sum += weight
            
    if weight_sum > 0:
        return round(total_health / weight_sum, 3)
    return 1.0
