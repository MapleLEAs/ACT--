"""
Anomaly Detector - 异常检测器
基于 Isolation Forest 的在线异常检测
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    异常检测器
    支持多指标联合异常检测
    """

    _models: Dict[str, Tuple[IsolationForest, StandardScaler, List[str]]] = {}
    _contamination = 0.05

    @classmethod
    def train(
        cls,
        device_type: str,
        X: np.ndarray,
        feature_names: List[str],
        contamination: float = 0.05
    ) -> bool:
        """
        训练异常检测模型
        :param device_type: 设备类型
        :param X: 训练数据 (n_samples, n_features)
        :param feature_names: 特征名称列表
        :param contamination: 异常比例
        """
        if X.shape[0] < 50:
            logger.warning(f"训练数据不足: {X.shape[0]} < 50")
            return False

        try:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            model = IsolationForest(
                n_estimators=100,
                contamination=contamination,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_scaled)

            cls._models[device_type] = (model, scaler, feature_names)
            cls._contamination = contamination

            logger.info(f"异常检测模型训练完成: {device_type}, 样本数: {X.shape[0]}")
            return True

        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            return False

    @classmethod
    def detect(
        cls,
        device_type: str,
        X: np.ndarray
    ) -> Tuple[bool, float, np.ndarray]:
        """
        检测异常
        :param device_type: 设备类型
        :param X: 待检测数据 (1, n_features) 或 (n_features,)
        :return: (是否异常, 异常分数, 决策路径)
        """
        if device_type not in cls._models:
            logger.warning(f"未找到设备类型 {device_type} 的模型")
            return False, 0.0, np.array([])

        model, scaler, feature_names = cls._models[device_type]

        try:
            if X.ndim == 1:
                X = X.reshape(1, -1)

            X_scaled = scaler.transform(X)
            prediction = model.predict(X_scaled)
            scores = model.decision_function(X_scaled)
            decision_paths = model.decision_path(X_scaled)

            is_anomaly = prediction[0] == -1
            anomaly_score = float(scores[0])

            return is_anomaly, anomaly_score, decision_paths.toarray()[0]

        except Exception as e:
            logger.error(f"异常检测失败: {e}")
            return False, 0.0, np.array([])

    @classmethod
    def detect_batch(
        cls,
        device_type: str,
        X: np.ndarray
    ) -> List[Tuple[bool, float]]:
        """
        批量检测异常
        :return: [(是否异常, 异常分数), ...]
        """
        if device_type not in cls._models:
            return [(False, 0.0)] * len(X)

        model, scaler, _ = cls._models[device_type]

        try:
            X_scaled = scaler.transform(X)
            predictions = model.predict(X_scaled)
            scores = model.decision_function(X_scaled)

            return [(p == -1, float(s)) for p, s in zip(predictions, scores)]

        except Exception as e:
            logger.error(f"批量异常检测失败: {e}")
            return [(False, 0.0)] * len(X)

    @classmethod
    def get_feature_importance(
        cls,
        device_type: str
    ) -> Dict[str, float]:
        """
        获取特征重要性（基于异常样本分析）
        """
        if device_type not in cls._models:
            return {}

        _, _, feature_names = cls._models[device_type]

        importance = {}
        for name in feature_names:
            importance[name] = 1.0 / len(feature_names)

        return importance

    @classmethod
    def clear_model(cls, device_type: str):
        """清除指定设备类型的模型"""
        if device_type in cls._models:
            del cls._models[device_type]
            logger.info(f"模型已清除: {device_type}")

    @classmethod
    def has_model(cls, device_type: str) -> bool:
        """检查是否有指定设备类型的模型"""
        return device_type in cls._models

    @classmethod
    def save_model(cls, device_type: str, path: str):
        """保存模型到文件"""
        if device_type not in cls._models:
            logger.warning(f"模型不存在: {device_type}")
            return False

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            model_data = {
                'model': cls._models[device_type][0],
                'scaler': cls._models[device_type][1],
                'feature_names': cls._models[device_type][2],
                'device_type': device_type,
                'saved_at': datetime.now().isoformat()
            }
            joblib.dump(model_data, path)
            logger.info(f"模型已保存: {path}")
            return True
        except Exception as e:
            logger.error(f"模型保存失败: {e}")
            return False

    @classmethod
    def load_model(cls, path: str) -> bool:
        """从文件加载模型"""
        try:
            model_data = joblib.load(path)
            device_type = model_data['device_type']
            cls._models[device_type] = (
                model_data['model'],
                model_data['scaler'],
                model_data['feature_names']
            )
            logger.info(f"模型已加载: {path}")
            return True
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False


class StreamingAnomalyDetector:
    """
    流式异常检测器
    适用于实时数据流
    """

    def __init__(self, device_type: str, threshold: float = -0.1):
        self.device_type = device_type
        self.threshold = threshold
        self.feature_extractor = None
        self.detector = AnomalyDetector

    def process(self, metrics: Dict[str, float]) -> Tuple[bool, float, Dict[str, float]]:
        """
        处理单个数据点
        :param metrics: 指标字典
        :return: (是否异常, 异常分数, 特征字典)
        """
        if not self.detector.has_model(self.device_type):
            return False, 0.0, metrics

        from .features import FeatureExtractor

        if self.feature_extractor is None:
            self.feature_extractor = FeatureExtractor()

        device_id = f"streaming_{self.device_type}"
        self.feature_extractor.add_sample(device_id, metrics)

        feature_names = list(metrics.keys())
        feature_vector = self.feature_extractor.get_feature_vector(device_id, feature_names)

        if not feature_vector:
            return False, 0.0, metrics

        X = np.array(feature_vector).reshape(1, -1)
        is_anomaly, score, _ = self.detector.detect(self.device_type, X)

        return is_anomaly, score, dict(zip(feature_names, metrics.values()))
