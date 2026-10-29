"""
Feature Extractor - 特征提取器
从设备状态时序数据中提取特征
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    特征提取器
    支持滑动窗口、统计特征、时序特征提取
    """

    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self._feature_buffers: Dict[str, deque] = {}

    def register_device(self, device_id: str):
        """注册设备，初始化特征缓冲区"""
        if device_id not in self._feature_buffers:
            self._feature_buffers[device_id] = deque(maxlen=self.window_size)

    def add_sample(self, device_id: str, metrics: Dict[str, float], timestamp: datetime = None):
        """添加一个样本到设备的特征缓冲区"""
        self.register_device(device_id)
        sample = {
            'timestamp': timestamp or datetime.now(),
            'metrics': metrics
        }
        self._feature_buffers[device_id].append(sample)

    def extract_statistical_features(self, device_id: str, metric_name: str) -> Dict[str, float]:
        """
        提取统计特征
        :return: {
            'mean': 平均值,
            'std': 标准差,
            'min': 最小值,
            'max': 最大值,
            'range': 极差,
            'median': 中位数,
            'q25': 25分位数,
            'q75': 75分位数,
            'iqr': 四分位距
        }
        """
        if device_id not in self._feature_buffers:
            return {}

        values = []
        for sample in self._feature_buffers[device_id]:
            if metric_name in sample['metrics']:
                values.append(sample['metrics'][metric_name])

        if len(values) < 5:
            return {}

        values = np.array(values)
        return {
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'range': float(np.max(values) - np.min(values)),
            'median': float(np.median(values)),
            'q25': float(np.percentile(values, 25)),
            'q75': float(np.percentile(values, 75)),
            'iqr': float(np.percentile(values, 75) - np.percentile(values, 25)),
        }

    def extract_temporal_features(self, device_id: str, metric_name: str) -> Dict[str, float]:
        """
        提取时序特征
        :return: {
            'trend': 趋势（上升/下降）,
            'change_rate': 变化率,
            'volatility': 波动率,
            'seasonality': 季节性强度
        }
        """
        if device_id not in self._feature_buffers or len(self._feature_buffers[device_id]) < 10:
            return {}

        samples = list(self._feature_buffers[device_id])
        timestamps = [s['timestamp'] for s in samples]
        values = [s['metrics'].get(metric_name) for s in samples if metric_name in s['metrics']]

        if len(values) < 10:
            return {}

        values = np.array(values)
        times = np.arange(len(values))

        trend, _ = self._linear_fit(times, values)
        change_rate = float(np.mean(np.diff(values)))
        volatility = float(np.std(values))

        return {
            'trend': float(trend),
            'change_rate': change_rate,
            'volatility': volatility,
        }

    def extract_gradient_features(self, device_id: str, metric_name: str) -> Dict[str, float]:
        """
        提取梯度特征
        :return: {
            'gradient_mean': 平均梯度,
            'gradient_max': 最大梯度,
            'gradient_std': 梯度标准差,
            'positive_ratio': 正梯度比例
        }
        """
        if device_id not in self._feature_buffers or len(self._feature_buffers[device_id]) < 3:
            return {}

        values = []
        for sample in self._feature_buffers[device_id]:
            if metric_name in sample['metrics']:
                values.append(sample['metrics'][metric_name])

        if len(values) < 3:
            return {}

        gradients = np.diff(values)
        return {
            'gradient_mean': float(np.mean(gradients)),
            'gradient_max': float(np.max(gradients)),
            'gradient_std': float(np.std(gradients)),
            'positive_ratio': float(np.sum(gradients > 0) / len(gradients)),
        }

    def extract_all_features(self, device_id: str, metric_name: str) -> Dict[str, float]:
        """提取所有类型特征"""
        features = {}
        features.update(self.extract_statistical_features(device_id, metric_name))
        features.update(self.extract_temporal_features(device_id, metric_name))
        features.update(self.extract_gradient_features(device_id, metric_name))
        return features

    def get_feature_vector(self, device_id: str, metric_names: List[str]) -> List[float]:
        """
        获取特征向量（用于模型输入）
        :param metric_names: 要提取特征的指标名称列表
        :return: 特征值向量
        """
        vector = []
        for metric in metric_names:
            features = self.extract_all_features(device_id, metric)
            if features:
                vector.extend([
                    features.get('mean', 0),
                    features.get('std', 0),
                    features.get('trend', 0),
                    features.get('volatility', 0),
                    features.get('gradient_mean', 0),
                ])
            else:
                vector.extend([0, 0, 0, 0, 0])
        return vector

    @staticmethod
    def _linear_fit(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
        """线性拟合，返回斜率和截距"""
        if len(x) < 2:
            return 0, 0
        try:
            coeffs = np.polyfit(x, y, 1)
            return coeffs[0], coeffs[1]
        except:
            return 0, 0


class SlidingWindowFeatureExtractor:
    """
    滑动窗口特征提取器
    用于实时流数据处理
    """

    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.windows: Dict[str, deque] = {}

    def push(self, device_id: str, value: float, timestamp: datetime = None):
        """推入新数据点"""
        if device_id not in self.windows:
            self.windows[device_id] = deque(maxlen=self.window_size)
        self.windows[device_id].append({
            'value': value,
            'timestamp': timestamp or datetime.now()
        })

    def get_moving_average(self, device_id: str, period: int = 5) -> Optional[float]:
        """获取移动平均"""
        if device_id not in self.windows or len(self.windows[device_id]) < period:
            return None
        values = list(self.windows[device_id])[-period:]
        return np.mean([v['value'] for v in values])

    def get_exponential_moving_average(self, device_id: str, alpha: float = 0.3) -> Optional[float]:
        """获取指数移动平均"""
        if device_id not in self.windows or len(self.windows[device_id]) < 2:
            return None
        values = [v['value'] for v in self.windows[device_id]]
        ema = values[0]
        for v in values[1:]:
            ema = alpha * v + (1 - alpha) * ema
        return ema

    def get_bollinger_bands(self, device_id: str, period: int = 20, num_std: float = 2.0) -> Optional[Dict[str, float]]:
        """获取布林带"""
        if device_id not in self.windows or len(self.windows[device_id]) < period:
            return None
        values = np.array([v['value'] for v in list(self.windows[device_id])[-period:]])
        mean = np.mean(values)
        std = np.std(values)
        return {
            'upper': float(mean + num_std * std),
            'middle': float(mean),
            'lower': float(mean - num_std * std),
        }


class CrossMetricFeatureExtractor:
    """
    跨指标特征提取器
    提取多指标组合特征
    """

    @staticmethod
    def compute_correlation(metric_a: List[float], metric_b: List[float]) -> float:
        """计算两个指标的相关性"""
        if len(metric_a) != len(metric_b) or len(metric_a) < 2:
            return 0.0
        try:
            return float(np.corrcoef(metric_a, metric_b)[0, 1])
        except:
            return 0.0

    @staticmethod
    def compute_ratio(metric_a: List[float], metric_b: List[float]) -> List[float]:
        """计算两个指标的比率"""
        if len(metric_a) != len(metric_b):
            return []
        result = []
        for a, b in zip(metric_a, metric_b):
            if b != 0:
                result.append(a / b)
            else:
                result.append(0)
        return result

    @staticmethod
    def compute_difference(metric_a: List[float], metric_b: List[float]) -> List[float]:
        """计算两个指标的差值"""
        if len(metric_a) != len(metric_b):
            return []
        return [a - b for a, b in zip(metric_a, metric_b)]
