import random
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def get_coupling_strength(device_id: str, neighbor_id: str) -> float:
    """
    获取设备耦合强度 (Coupling Strength)
    """
    # 设备耦合矩阵（基于真实空管逻辑）
    # 真实场景中，这部分应从知识图谱或Neo4j图数据库读取
    coupling_matrix = {
        ('VHF-001', 'VHF-002'): 0.15,  # 信号干扰耦合
        ('VHF-001', 'ILS-001'): 0.10,  # 通信影响导航
        ('ILS-001', 'DME-001'): 0.20,  # 导航耦合
        ('VOR-001', 'DME-001'): 0.25,  # 定位耦合
    }
    
    key = (device_id, neighbor_id)
    reverse_key = (neighbor_id, device_id)
    
    return coupling_matrix.get(key, coupling_matrix.get(reverse_key, 0.05))

def log_fault_propagation(source: str, target: str, probability: float):
    """记录故障传播事件"""
    logger.info(f"Fault Propagation Event: {source} -> {target} (Prob: {probability:.2f})")

def fault_propagation(devices: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    故障传播预测模型 (Fault Propagation Model)
    计算级联故障和区域性能下降
    
    Args:
        devices: 设备列表 [{'id': 'VHF-001', 'status': 'NORMAL', 'neighbors': ['VHF-002']}]
    
    Returns:
        new_faults: 新故障状态字典 {'VHF-002': 'DEGRADED'}
    """
    new_faults = {}
    
    device_map = {d['id']: d for d in devices}
    
    for d in devices:
        # 检查是否处于故障或报警状态
        if d.get("status") in ["FAULT", "ALARM", "CRITICAL"]:
            
            # 获取邻居设备
            neighbors = d.get("neighbors", [])
            for neighbor_id in neighbors:
                
                # 计算传播概率
                coupling_strength = get_coupling_strength(d["id"], neighbor_id)
                propagation_prob = 0.3 * coupling_strength
                
                # 判断是否发生故障传播
                if random.random() < propagation_prob:
                    neighbor = device_map.get(neighbor_id)
                    
                    if neighbor and neighbor.get("status") == "NORMAL":
                        new_faults[neighbor_id] = "DEGRADED"
                        log_fault_propagation(
                            source=d["id"],
                            target=neighbor_id,
                            probability=propagation_prob
                        )
                        
    return new_faults
