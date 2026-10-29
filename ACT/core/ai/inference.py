"""
Inference Engine - 推理引擎
在线推理服务，统一调度异常检测和预测
"""
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
from dataclasses import dataclass

from .detector import AnomalyDetector, StreamingAnomalyDetector
from .hybrid_model import HybridPredictor
from .features import FeatureExtractor
from .trainer import ModelTrainer

logger = logging.getLogger(__name__)


@dataclass
class InferenceResult:
    device_id: str
    device_type: str
    timestamp: datetime
    is_anomaly: bool
    anomaly_score: float
    predictions: Dict[str, float]
    features: Dict[str, float]
    severity: str = "NORMAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            'device_type': self.device_type,
            'timestamp': self.timestamp.isoformat(),
            'is_anomaly': self.is_anomaly,
            'anomaly_score': self.anomaly_score,
            'predictions': self.predictions,
            'features': self.features,
            'severity': self.severity
        }


class InferenceEngine:
    """
    推理引擎
    统一调度 AI 模型，提供在线推理服务
    """

    _initialized = False

    def __init__(self):
        self.feature_extractors: Dict[str, FeatureExtractor] = {}
        self.predictors: Dict[str, HybridPredictor] = {}
        self.streaming_detectors: Dict[str, StreamingAnomalyDetector] = {}
        from collections import deque
        self._history_buffers: Dict[str, Dict[str, deque]] = {}

    @classmethod
    def initialize(cls):
        """初始化推理引擎，加载所有预训练模型"""
        if cls._initialized:
            return

        logger.info("初始化推理引擎...")

        results = ModelTrainer.batch_train_all_types()
        for device_type, success in results.items():
            if success:
                logger.info(f"  ✓ {device_type} 异常检测模型已加载")
            else:
                logger.warning(f"  ✗ {device_type} 模型加载失败")

        cls._initialized = True
        logger.info("推理引擎初始化完成")

    @classmethod
    def get_instance(cls) -> 'InferenceEngine':
        """获取推理引擎单例"""
        if not hasattr(cls, '_instance'):
            cls._instance = InferenceEngine()
            cls.initialize()
        return cls._instance

    def infer(
        self,
        device_id: str,
        device_type: str,
        metrics: Dict[str, float],
        enable_prediction: bool = True
    ) -> InferenceResult:
        """
        执行推理
        :param device_id: 设备ID
        :param device_type: 设备类型
        :param metrics: 当前指标值
        :param enable_prediction: 是否启用预测
        :return: 推理结果
        """
        timestamp = datetime.now()

        is_anomaly = False
        anomaly_score = 0.0
        severity = "NORMAL"

        if AnomalyDetector.has_model(device_type):
            X = self._build_feature_vector(device_id, device_type, metrics)
            if X is not None:
                is_anomaly, anomaly_score, _ = AnomalyDetector.detect(device_type, X)
                severity = self._score_to_severity(anomaly_score)

        predictions = {}
        if enable_prediction:
            predictions = self._predict(device_id, metrics)

        features = self._extract_current_features(device_id, device_type, metrics)

        return InferenceResult(
            device_id=device_id,
            device_type=device_type,
            timestamp=timestamp,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            predictions=predictions,
            features=features,
            severity=severity
        )

    def infer_batch(
        self,
        device_id: str,
        device_type: str,
        history_metrics: List[Dict[str, float]]
    ) -> List[InferenceResult]:
        """批量推理"""
        results = []
        for metrics in history_metrics:
            result = self.infer(device_id, device_type, metrics)
            results.append(result)
        return results

    def _build_feature_vector(
        self,
        device_id: str,
        device_type: str,
        current_metrics: Dict[str, float]
    ) -> Optional[Any]:
        """构建特征向量"""
        if device_type not in self.feature_extractors:
            self.feature_extractors[device_type] = FeatureExtractor()

        extractor = self.feature_extractors[device_type]
        extractor.add_sample(device_id, current_metrics)

        metric_names = list(current_metrics.keys())
        vector = extractor.get_feature_vector(device_id, metric_names)

        if not vector:
            return None

        import numpy as np
        return np.array(vector)

    def _predict(
        self,
        device_id: str,
        current_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """执行预测"""
        if device_id not in self.predictors:
            self.predictors[device_id] = HybridPredictor()
            self._history_buffers[device_id] = {}

        predictor = self.predictors[device_id]
        history_buffers = self._history_buffers[device_id]
        predictions = {}
        
        # 简单模拟环境状态
        env_state = {
            'temperature': current_metrics.get('device_temperature', 20.0),
            'load': 0.5
        }

        for metric, value in current_metrics.items():
            if metric not in history_buffers:
                from collections import deque
                history_buffers[metric] = deque(maxlen=60)
                
            history_list = list(history_buffers[metric])
            
            # 使用混合预测模型
            pred_result = predictor.predict(
                device_id=device_id,
                current_value=value,
                historical_data=history_list,
                env_state=env_state
            )
            
            # 存入历史数据
            history_buffers[metric].append(value)
            
            if pred_result and 'prediction' in pred_result:
                predictions[metric] = pred_result['prediction']

        return predictions

    def _extract_current_features(
        self,
        device_id: str,
        device_type: str,
        current_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """提取当前特征"""
        if device_type not in self.feature_extractors:
            return current_metrics

        extractor = self.feature_extractors[device_type]
        metric_names = list(current_metrics.keys())

        features = extractor.extract_all_features(device_id, metric_names[0] if metric_names else 'signal_strength')
        return features if features else current_metrics

    @staticmethod
    def _score_to_severity(score: float) -> str:
        """将异常分数转换为严重程度"""
        if score > -0.1:
            return "NORMAL"
        elif score > -0.3:
            return "WARN"
        elif score > -0.5:
            return "ERROR"
        else:
            return "CRITICAL"

    def save_predictions(
        self,
        result: InferenceResult,
        save_to_db: bool = True
    ):
        """保存预测结果"""
        if not save_to_db:
            return

        try:
            from monitor.models import PredictionResult
            from monitor.models import Device

            device = Device.objects.filter(device_id=result.device_id).first()
            if not device:
                return

            for metric, predicted_value in result.predictions.items():
                PredictionResult.objects.create(
                    device=device,
                    metric=metric,
                    predicted_value=predicted_value,
                    prediction_time=result.timestamp,
                    prediction_horizon=5,
                    confidence_score=max(0, min(1, 1 + result.anomaly_score)),
                    is_above_threshold=result.is_anomaly,
                    severity=result.severity if result.is_anomaly else None,
                    status='PREDICTED'
                )

            logger.debug(f"预测结果已保存: {result.device_id}")

        except Exception as e:
            logger.error(f"保存预测结果失败: {e}")
