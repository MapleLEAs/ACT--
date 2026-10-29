"""
Trend Predictor - 趋势预测器
基于滑动窗口的短期趋势预测
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


class TrendPredictor:
    """
    趋势预测器
    支持多种预测算法：线性回归、指数平滑、移动平均
    """

    def __init__(self, horizon: int = 5):
        self.horizon = horizon
        self._buffers: Dict[str, deque] = {}
        self._window_size = 60

    def push(self, device_id: str, value: float, timestamp: datetime = None):
        """添加数据点"""
        if device_id not in self._buffers:
            self._buffers[device_id] = deque(maxlen=self._window_size)
        self._buffers[device_id].append({
            'value': value,
            'timestamp': timestamp or datetime.now()
        })

    def predict_linear(self, device_id: str, n_future: int = None) -> Optional[float]:
        """线性回归预测"""
        if device_id not in self._buffers or len(self._buffers[device_id]) < 10:
            return None

        n_future = n_future or self.horizon
        values = [v['value'] for v in self._buffers[device_id]]
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)

        future_x = len(values) + n_future
        predicted = np.polyval(coeffs, future_x)
        return float(predicted)

    def predict_moving_average(self, device_id: str, period: int = 5) -> Optional[float]:
        """移动平均预测"""
        if device_id not in self._buffers or len(self._buffers[device_id]) < period:
            return None

        values = list(self._buffers[device_id])[-period:]
        return float(np.mean([v['value'] for v in values]))

    def predict_exponential_smoothing(
        self,
        device_id: str,
        alpha: float = 0.3
    ) -> Optional[float]:
        """指数平滑预测"""
        if device_id not in self._buffers or len(self._buffers[device_id]) < 2:
            return None

        values = [v['value'] for v in self._buffers[device_id]]
        ema = values[0]
        for v in values[1:]:
            ema = alpha * v + (1 - alpha) * ema
        return ema

    def get_trend(self, device_id: str) -> Tuple[str, float]:
        """
        获取趋势方向
        :return: (趋势方向: 'up'/'down'/'stable', 斜率)
        """
        if device_id not in self._buffers or len(self._buffers[device_id]) < 10:
            return 'stable', 0.0

        values = [v['value'] for v in self._buffers[device_id]]
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)

        threshold = 0.1 * np.mean(np.abs(values))
        if abs(slope) < threshold:
            return 'stable', float(slope)
        elif slope > 0:
            return 'up', float(slope)
        else:
            return 'down', float(slope)

    def predict_all(self, device_id: str) -> Dict[str, Optional[float]]:
        """获取所有预测方法的结果"""
        return {
            'linear': self.predict_linear(device_id),
            'moving_average': self.predict_moving_average(device_id),
            'exponential_smoothing': self.predict_exponential_smoothing(device_id),
            'trend': self.get_trend(device_id)[0],
            'slope': self.get_trend(device_id)[1],
        }


class SeasonalPredictor:
    """
    季节性预测器
    适用于有周期性规律的数据
    """

    def __init__(self, period: int = 24):
        self.period = period
        self._history: Dict[str, List[float]] = {}

    def add_seasonal_data(self, device_id: str, value: float):
        """添加季节性数据"""
        if device_id not in self._history:
            self._history[device_id] = []
        self._history[device_id].append(value)

        max_history = self.period * 10
        if len(self._history[device_id]) > max_history:
            self._history[device_id] = self._history[device_id][-max_history:]

    def predict_seasonal(self, device_id: str) -> Optional[float]:
        """基于季节性模式预测"""
        if device_id not in self._history or len(self._history[device_id]) < self.period:
            return None

        history = self._history[device_id]
        season_values = history[-self.period:]
        return float(np.mean(season_values))

    def get_seasonal_strength(self, device_id: str) -> float:
        """计算季节性强度"""
        if device_id not in self._history or len(self._history[device_id]) < self.period * 2:
            return 0.0

        history = self._history[device_id]
        n_seasons = len(history) // self.period

        seasonal_means = []
        for i in range(n_seasons):
            start = i * self.period
            end = start + self.period
            seasonal_means.append(np.mean(history[start:end]))

        overall_mean = np.mean(history)
        variance_between = np.var(seasonal_means)
        variance_total = np.var(history)

        if variance_total == 0:
            return 0.0

        return float(variance_between / variance_total)
