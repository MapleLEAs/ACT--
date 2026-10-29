from typing import Dict, Any, List
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
from .exception_handler import PredictionConfidenceError, ExceptionHandler


class TrendBasedPredictor:
    """趋势预测引擎"""

    MIN_SAMPLES = 12

    def __init__(self, historical_data: List[Dict[str, Any]] = None):
        self.historical_data = historical_data or []
        self.exception_handler = ExceptionHandler()

    def decompose_time_series(self) -> Dict[str, Any]:
        """
        时间序列分解：趋势 + 季节性 + 残差
        :return: 分解结果
        """
        if len(self.historical_data) < 12:
            return {
                'trend': [],
                'seasonal': [],
                'residual': [],
                'trend_direction': 'stable'
            }

        values = np.array([d.get('value', 0) for d in self.historical_data])
        timestamps = [d.get('timestamp') for d in self.historical_data]

        trend = self._moving_average(values, window=12)
        seasonal = self._extract_seasonal_component(values, trend)
        residual = values - trend - seasonal

        trend_direction = 'rising' if trend[-1] > trend[0] else 'falling' if trend[-1] < trend[0] else 'stable'

        return {
            'trend': trend.tolist(),
            'seasonal': seasonal.tolist(),
            'residual': residual.tolist(),
            'trend_direction': trend_direction,
            'trend_slope': round((trend[-1] - trend[0]) / max(len(trend) - 1, 1), 4),
            'seasonal_pattern': 'daily_cycle',
            'residual_std': round(np.std(residual), 4)
        }

    def predict_with_uncertainty(self, components: Dict[str, Any], horizon_hours: int = 24) -> Dict[str, Any]:
        """
        基于趋势的预测（带不确定性区间）
        异常处理策略：预测置信度不足时返回预测结果，但标记"样本不足"
        :param components: 时间序列分解组件
        :param horizon_hours: 预测时间范围（小时）
        :return: 预测结果
        """
        trend = np.array(components.get('trend', []))
        seasonal = np.array(components.get('seasonal', []))
        residual = np.array(components.get('residual', []))

        has_insufficient_samples = len(self.historical_data) < self.MIN_SAMPLES

        if len(trend) == 0:
            if has_insufficient_samples:
                confidence_error = PredictionConfidenceError(
                    code='INSUFFICIENT_SAMPLES',
                    message=f'历史样本不足: {len(self.historical_data)} < {self.MIN_SAMPLES}'
                )
                self.exception_handler.log_error('prediction_confidence', confidence_error)
                self.exception_handler.handle_prediction_confidence(confidence_error)
            
            return {
                'predicted_value': None,
                'confidence_interval': None,
                'trend_direction': 'stable',
                'anomaly_probability': 0.0,
                'confidence_warning': 'insufficient_samples' if has_insufficient_samples else None
            }

        trend_forecast = self._extrapolate_trend(trend, horizon_hours)
        seasonal_forecast = self._repeat_seasonal_pattern(seasonal, horizon_hours)

        predicted_value = trend_forecast + seasonal_forecast

        std_residual = np.std(residual) if len(residual) > 0 else 1.0
        confidence_interval = {
            'lower': round(predicted_value - 2 * std_residual, 2),
            'upper': round(predicted_value + 2 * std_residual, 2),
            'confidence': 0.95
        }

        anomaly_prob = self.calculate_anomaly_probability(predicted_value)

        result = {
            'predicted_value': round(predicted_value, 2),
            'prediction_time': (datetime.now() + timedelta(hours=horizon_hours)).isoformat(),
            'horizon_hours': horizon_hours,
            'confidence_interval': confidence_interval,
            'trend_direction': components.get('trend_direction', 'stable'),
            'anomaly_probability': round(anomaly_prob, 4),
            'threshold_breach_probability': round(self._calculate_breach_probability(predicted_value, std_residual), 4)
        }

        if has_insufficient_samples:
            confidence_error = PredictionConfidenceError(
                code='INSUFFICIENT_SAMPLES',
                message=f'历史样本不足: {len(self.historical_data)} < {self.MIN_SAMPLES}'
            )
            self.exception_handler.log_error('prediction_confidence', confidence_error)
            self.exception_handler.handle_prediction_confidence(confidence_error)
            result['confidence_warning'] = 'insufficient_samples'

        return result

    def calculate_anomaly_probability(self, predicted_value: float) -> float:
        """
        异常偏离概率计算
        :param predicted_value: 预测值
        :return: 异常概率
        """
        if not self.historical_data:
            return 0.0

        historical_values = [d.get('value', 0) for d in self.historical_data]
        historical_mean = np.mean(historical_values)
        historical_std = np.std(historical_values)

        if historical_std == 0:
            return 0.0

        deviation = abs(predicted_value - historical_mean) / historical_std
        anomaly_prob = 1 - norm.cdf(deviation)

        return anomaly_prob

    def _calculate_breach_probability(self, predicted_value: float, std_residual: float) -> float:
        """
        计算阈值突破概率
        :param predicted_value: 预测值
        :param std_residual: 残差标准差
        :return: 突破概率
        """
        threshold = 85.0
        if predicted_value >= threshold:
            return 1.0
        
        z_score = (threshold - predicted_value) / std_residual
        return 1 - norm.cdf(z_score)

    def _moving_average(self, data: np.ndarray, window: int) -> np.ndarray:
        """计算移动平均"""
        weights = np.repeat(1.0, window) / window
        return np.convolve(data, weights, 'same')

    def _extract_seasonal_component(self, data: np.ndarray, trend: np.ndarray) -> np.ndarray:
        """提取季节性分量"""
        detrended = data - trend
        seasonal = np.zeros_like(data)
        
        period = 24
        for i in range(period):
            indices = np.arange(i, len(data), period)
            if len(indices) > 0:
                seasonal[indices] = np.mean(detrended[indices])
        
        return seasonal

    def _extrapolate_trend(self, trend: np.ndarray, horizon_hours: int) -> float:
        """趋势外推"""
        if len(trend) < 2:
            return trend[-1] if len(trend) > 0 else 0.0
        
        slope = (trend[-1] - trend[0]) / (len(trend) - 1)
        return trend[-1] + slope * horizon_hours

    def _repeat_seasonal_pattern(self, seasonal: np.ndarray, horizon_hours: int) -> float:
        """重复季节性模式"""
        if len(seasonal) == 0:
            return 0.0
        
        period = 24
        if len(seasonal) >= period:
            return np.mean(seasonal[-period:])
        return np.mean(seasonal)

    def get_prediction_output(self, device_id: str, metric: str) -> Dict[str, Any]:
        """
        获取预测输出格式
        :param device_id: 设备ID
        :param metric: 指标名称
        :return: 预测输出
        """
        components = self.decompose_time_series()
        prediction = self.predict_with_uncertainty(components)

        return {
            'prediction_id': f'PRED-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            'device_id': device_id,
            'metric': metric,
            'trend_analysis': {
                'trend_direction': components.get('trend_direction', 'stable'),
                'trend_slope': components.get('trend_slope', 0),
                'seasonal_pattern': components.get('seasonal_pattern', 'unknown'),
                'residual_std': components.get('residual_std', 0)
            },
            'prediction_result': prediction
        }
