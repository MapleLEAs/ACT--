"""
Model Trainer - 模型训练器
负责从历史数据训练 AI 模型
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    模型训练器
    从历史状态日志中提取数据并训练模型
    """

    @staticmethod
    def prepare_training_data(
        device_type: str,
        metric_names: List[str],
        start_time: datetime = None,
        end_time: datetime = None,
        min_samples: int = 100
    ) -> Tuple[np.ndarray, List[str]]:
        """
        准备训练数据
        :param device_type: 设备类型
        :param metric_names: 要训练的指标名称
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param min_samples: 最小样本数
        :return: (特征矩阵, 特征名称列表)
        """
        from monitor.models import DeviceStatusLog

        query = DeviceStatusLog.objects.filter(
            device__device_type=device_type
        )

        if start_time:
            query = query.filter(collect_time__gte=start_time)
        if end_time:
            query = query.filter(collect_time__lte=end_time)

        query = query.order_by('-collect_time')[:1000]
        logs = list(query)

        if len(logs) < min_samples:
            logger.warning(f"训练数据不足: {len(logs)} < {min_samples}")
            return np.array([]), []

        samples = []
        for log in logs:
            features = ModelTrainer._extract_features(log, metric_names)
            if features:
                samples.append(features)

        if not samples:
            return np.array([]), []

        feature_names = ModelTrainer._build_feature_names(metric_names)
        return np.array(samples), feature_names

    @staticmethod
    def _extract_features(log, metric_names: List[str]) -> List[float]:
        """从状态日志中提取特征"""
        features = []
        for metric in metric_names:
            value = getattr(log, metric, None)
            if value is not None:
                try:
                    features.append(float(value))
                except (ValueError, TypeError):
                    pass
        return features

    @staticmethod
    def _build_feature_names(metric_names: List[str]) -> List[str]:
        """构建特征名称列表"""
        return metric_names

    @classmethod
    def train_anomaly_model(
        cls,
        device_type: str,
        metric_names: List[str] = None,
        contamination: float = 0.05
    ) -> bool:
        """
        训练异常检测模型
        """
        from .detector import AnomalyDetector

        if metric_names is None:
            metric_names = cls._get_default_metrics(device_type)

        X, feature_names = cls.prepare_training_data(
            device_type,
            metric_names,
            min_samples=100
        )

        if X.shape[0] == 0:
            logger.error(f"无法准备训练数据: {device_type}")
            return False

        return AnomalyDetector.train(
            device_type,
            X,
            feature_names,
            contamination
        )

    @staticmethod
    def _get_default_metrics(device_type: str) -> List[str]:
        """获取设备类型的默认指标"""
        default_metrics = {
            'VHF': ['signal_strength', 'power_voltage', 'device_temperature', 'bit_error_rate'],
            'ILS': ['signal_power', 'loc_guidance_deviation', 'gs_guidance_deviation', 'antenna_swr', 'power_voltage'],
            'VOR': ['signal_strength', 'power_voltage', 'device_temperature'],
            'DME': ['signal_strength', 'power_voltage', 'device_temperature'],
            'HF': ['signal_strength', 'power_voltage', 'device_temperature'],
        }
        return default_metrics.get(device_type, ['power_voltage', 'device_temperature'])

    @classmethod
    def batch_train_all_types(cls):
        """批量训练所有设备类型"""
        from monitor.models import Device

        device_types = Device.objects.values_list('device_type', flat=True).distinct()
        results = {}

        for device_type in device_types:
            success = cls.train_anomaly_model(device_type)
            results[device_type] = success

        return results

    @classmethod
    def incremental_train(
        cls,
        device_type: str,
        new_samples: List[Dict[str, float]],
        batch_size: int = 100
    ):
        """
        增量训练
        用新样本更新模型
        """
        from .detector import AnomalyDetector

        if not AnomalyDetector.has_model(device_type):
            logger.warning(f"设备类型 {device_type} 没有预训练模型")
            return False

        X = np.array(new_samples)
        if X.shape[1] == 0:
            return False

        model, scaler, feature_names = AnomalyDetector._models[device_type]

        X_scaled = scaler.transform(X)
        model.fit(X_scaled)

        logger.info(f"增量训练完成: {device_type}, 新增 {len(new_samples)} 样本")
        return True

    @classmethod
    def train_hybrid_predictor(cls, device_type: str, metric_name: str, horizon: int = 5) -> bool:
        """
        训练特定设备类型和指标的混合预测模型残差部分
        """
        from monitor.models import DeviceStatusLog
        from .hybrid_model import HybridPredictor
        from .inference import InferenceEngine

        logger.info(f"开始训练混合预测模型: {device_type} - {metric_name}")
        
        # 1. 获取按时间排序的日志
        query = DeviceStatusLog.objects.filter(
            device__device_type=device_type
        ).order_by('device_id', 'collect_time')[:5000]
        
        logs = list(query)
        if len(logs) < 50:
            logger.warning(f"训练数据不足 ({len(logs)} < 50)")
            return False
            
        # 2. 按 device_id 分组
        from collections import defaultdict
        device_logs = defaultdict(list)
        for log in logs:
            val = getattr(log, metric_name, None)
            if val is not None:
                device_logs[log.device_id].append({
                    'value': float(val),
                    'temperature': float(log.device_temperature) if getattr(log, 'device_temperature', None) else 20.0,
                    'time': log.collect_time
                })
                
        # 3. 构造训练样本
        training_samples = []
        for d_id, d_logs in device_logs.items():
            if len(d_logs) < horizon + 5:
                continue
                
            # 滑动窗口构造样本
            for i in range(5, len(d_logs) - horizon):
                hist_data = [x['value'] for x in d_logs[i-5:i]]
                current_val = d_logs[i]['value']
                env = {'temperature': d_logs[i]['temperature'], 'load': 0.5}
                actual_future = d_logs[i + horizon]['value']
                
                training_samples.append({
                    'current_value': current_val,
                    'historical_data': hist_data,
                    'env_state': env,
                    'actual_future_value': actual_future
                })
                
        if not training_samples:
            logger.warning(f"构造出的训练样本不足")
            return False
            
        # 4. 训练模型
        engine = InferenceEngine.get_instance()
        # 对于所有属于该类型的 device_id，我们使用相同的训练好的模型，或者在引擎中为该类型存储一个基础模型。
        # 这里为了简化，我们直接取其中一个设备的预测器进行训练，实际生产中可以共享权重。
        sample_device_id = list(device_logs.keys())[0]
        
        if sample_device_id not in engine.predictors:
            from .hybrid_model import HybridPredictor
            engine.predictors[sample_device_id] = HybridPredictor()
            
        predictor = engine.predictors[sample_device_id]
        predictor.train_residual(training_samples)
        
        # 将训练好的模型复制给同类型的其他设备 (简化处理)
        for d_id in device_logs.keys():
            if d_id != sample_device_id:
                engine.predictors[d_id] = predictor
                
        logger.info(f"混合预测模型训练完成，样本数: {len(training_samples)}")
        return True
