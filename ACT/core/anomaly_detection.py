"""
AI 异常检测服务模块
使用 Isolation Forest 算法进行多指标异常检测
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AnomalyDetectionService:
    """
    异常检测服务
    使用 Isolation Forest 算法检测设备状态异常
    """
    
    _models = {}  # 缓存训练好的模型
    
    @staticmethod
    def train_model(device_type, data):
        """
        训练异常检测模型
        :param device_type: 设备类型
        :param data: 训练数据，格式为 [[metric1, metric2, ...], ...]
        """
        if not data or len(data) < 10:
            logger.warning(f"训练数据不足，设备类型: {device_type}")
            return None
        
        try:
            # 标准化数据
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(data)
            
            # 训练 Isolation Forest
            model = IsolationForest(
                n_estimators=100,
                contamination=0.05,  # 预期异常比例
                random_state=42,
                n_jobs=-1
            )
            model.fit(scaled_data)
            
            # 保存模型和 scaler
            AnomalyDetectionService._models[device_type] = {
                'model': model,
                'scaler': scaler,
                'feature_count': len(data[0])
            }
            
            logger.info(f"异常检测模型训练完成，设备类型: {device_type}, 样本数: {len(data)}")
            return model
            
        except Exception as e:
            logger.error(f"训练异常检测模型失败: {str(e)}")
            return None
    
    @staticmethod
    def detect_anomaly(device_type, features):
        """
        检测异常
        :param device_type: 设备类型
        :param features: 特征向量，格式为 [metric1, metric2, ...]
        :return: (is_anomaly, anomaly_score)
                 is_anomaly: True 表示异常，False 表示正常
                 anomaly_score: 异常分数，越接近 -1 越异常
        """
        if device_type not in AnomalyDetectionService._models:
            logger.warning(f"未找到设备类型 {device_type} 的模型")
            return False, 0.0
        
        model_info = AnomalyDetectionService._models[device_type]
        model = model_info['model']
        scaler = model_info['scaler']
        
        try:
            # 标准化特征
            features_array = np.array(features).reshape(1, -1)
            scaled_features = scaler.transform(features_array)
            
            # 预测
            prediction = model.predict(scaled_features)
            anomaly_score = model.decision_function(scaled_features)[0]
            
            # prediction == -1 表示异常
            is_anomaly = prediction[0] == -1
            
            return is_anomaly, anomaly_score
            
        except Exception as e:
            logger.error(f"异常检测失败: {str(e)}")
            return False, 0.0
    
    @staticmethod
    def get_device_features(device_type, status_log):
        """
        从设备状态日志中提取特征向量
        :param device_type: 设备类型
        :param status_log: DeviceStatusLog 实例
        :return: 特征向量列表
        """
        features = []
        
        # VHF 设备特征
        if device_type == 'VHF':
            if status_log.signal_strength is not None:
                features.append(float(status_log.signal_strength))
            if status_log.power_voltage is not None:
                features.append(float(status_log.power_voltage))
            if status_log.device_temperature is not None:
                features.append(float(status_log.device_temperature))
            if status_log.bit_error_rate is not None:
                features.append(float(status_log.bit_error_rate))
        
        # ILS 设备特征
        elif device_type == 'ILS':
            if status_log.signal_power is not None:
                features.append(float(status_log.signal_power))
            if status_log.loc_guidance_deviation is not None:
                features.append(float(status_log.loc_guidance_deviation))
            if status_log.gs_guidance_deviation is not None:
                features.append(float(status_log.gs_guidance_deviation))
            if status_log.antenna_swr is not None:
                features.append(float(status_log.antenna_swr))
            if status_log.power_voltage is not None:
                features.append(float(status_log.power_voltage))
            if status_log.device_temperature is not None:
                features.append(float(status_log.device_temperature))
        
        # 通用特征
        else:
            if status_log.power_voltage is not None:
                features.append(float(status_log.power_voltage))
            if status_log.device_temperature is not None:
                features.append(float(status_log.device_temperature))
        
        return features
    
    @staticmethod
    def batch_detect(device_type, status_logs):
        """
        批量检测异常
        :param device_type: 设备类型
        :param status_logs: DeviceStatusLog 实例列表
        :return: 检测结果列表 [(status_log, is_anomaly, score), ...]
        """
        results = []
        
        for log in status_logs:
            features = AnomalyDetectionService.get_device_features(device_type, log)
            if features:
                is_anomaly, score = AnomalyDetectionService.detect_anomaly(device_type, features)
                results.append((log, is_anomaly, score))
        
        return results
    
    @staticmethod
    def warm_up_models():
        """
        预热所有设备类型的模型
        从历史数据训练模型
        """
        from monitor.models import Device, DeviceStatusLog
        
        device_types = Device.objects.values_list('device_type', flat=True).distinct()
        
        for device_type in device_types:
            # 获取该类型设备的最近状态日志
            logs = DeviceStatusLog.objects.filter(
                device__device_type=device_type
            ).order_by('-collect_time')[:500]
            
            # 提取特征
            features_list = []
            for log in logs:
                features = AnomalyDetectionService.get_device_features(device_type, log)
                if features:
                    features_list.append(features)
            
            # 训练模型
            if features_list:
                AnomalyDetectionService.train_model(device_type, features_list)
