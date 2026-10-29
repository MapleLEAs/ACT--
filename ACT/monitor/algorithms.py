import numpy as np
from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from functools import lru_cache


class SlidingWindow:
    """
    优化后的滑动窗口算法实现
    支持更大的时间窗口和更高效的数据处理
    """

    def __init__(self, window_size: int):
        """
        初始化滑动窗口

        Args:
            window_size (int): 窗口大小
        """
        self.window_size = window_size
        self.data = deque(maxlen=window_size)
        self._cached_stats = {}
        self._cache_valid = False

    def add(self, value: float) -> None:
        """
        添加数据到滑动窗口

        Args:
            value (float): 要添加的数据值
        """
        self.data.append(value)
        self._cache_valid = False

    def add_batch(self, values: List[float]) -> None:
        """
        批量添加数据到滑动窗口

        Args:
            values (list): 要添加的数据值列表
        """
        for value in values:
            self.data.append(value)
        self._cache_valid = False

    def get_average(self) -> Optional[float]:
        """
        计算滑动窗口内数据的平均值

        Returns:
            float: 滑动窗口内数据的平均值
        """
        if not self.data:
            return None
        return sum(self.data) / len(self.data)

    def get_std(self) -> Optional[float]:
        """
        计算滑动窗口内数据的标准差

        Returns:
            float: 滑动窗口内数据的标准差
        """
        if len(self.data) < 2:
            return None
        return float(np.std(list(self.data)))

    def get_variance(self) -> Optional[float]:
        """
        计算滑动窗口内数据的方差

        Returns:
            float: 滑动窗口内数据的方差
        """
        if len(self.data) < 2:
            return None
        return float(np.var(list(self.data)))

    def get_min(self) -> Optional[float]:
        """
        获取滑动窗口内的最小值

        Returns:
            float: 滑动窗口内的最小值
        """
        if not self.data:
            return None
        return min(self.data)

    def get_max(self) -> Optional[float]:
        """
        获取滑动窗口内的最大值

        Returns:
            float: 滑动窗口内的最大值
        """
        if not self.data:
            return None
        return max(self.data)

    def get_percentile(self, percentile: float) -> Optional[float]:
        """
        计算滑动窗口内数据的百分位数

        Args:
            percentile (float): 百分位数 (0-100)

        Returns:
            float: 对应的百分位数值
        """
        if not self.data:
            return None
        return float(np.percentile(list(self.data), percentile))

    def get_median(self) -> Optional[float]:
        """
        获取滑动窗口内数据的中位数

        Returns:
            float: 滑动窗口内数据的中位数
        """
        return self.get_percentile(50)

    def get_range(self) -> Optional[float]:
        """
        获取滑动窗口内数据的范围（最大值-最小值）

        Returns:
            float: 滑动窗口内数据的范围
        """
        if not self.data:
            return None
        return max(self.data) - min(self.data)

    def is_full(self) -> bool:
        """
        检查滑动窗口是否已满

        Returns:
            bool: 滑动窗口是否已满
        """
        return len(self.data) == self.window_size

    def get_fill_rate(self) -> float:
        """
        获取窗口填充率

        Returns:
            float: 窗口填充率 (0-1)
        """
        return len(self.data) / self.window_size if self.window_size > 0 else 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取滑动窗口的完整统计信息

        Returns:
            dict: 包含各项统计指标的字典
        """
        if not self.data:
            return {
                'count': 0,
                'average': None,
                'std': None,
                'min': None,
                'max': None,
                'median': None,
                'range': None,
                'variance': None,
                'fill_rate': 0,
                'is_full': False
            }

        data_list = list(self.data)
        return {
            'count': len(data_list),
            'average': self.get_average(),
            'std': self.get_std(),
            'min': min(data_list),
            'max': max(data_list),
            'median': self.get_median(),
            'range': max(data_list) - min(data_list),
            'variance': self.get_variance(),
            'fill_rate': self.get_fill_rate(),
            'is_full': self.is_full()
        }

    def clear(self) -> None:
        """
        清空滑动窗口
        """
        self.data.clear()
        self._cache_valid = False

    def get_data(self) -> List[float]:
        """
        获取当前窗口内的所有数据

        Returns:
            list: 窗口内的数据列表
        """
        return list(self.data)

    def get_weighted_average(self, weights: Optional[List[float]] = None) -> Optional[float]:
        """
        计算滑动窗口内数据的加权平均值

        Args:
            weights (list): 权重列表，如果为None则使用等权重

        Returns:
            float: 加权平均值
        """
        if not self.data:
            return None

        data_list = list(self.data)
        if weights is None:
            return sum(data_list) / len(data_list)

        if len(weights) != len(data_list):
            return None

        weighted_sum = sum(d * w for d, w in zip(data_list, weights))
        weight_sum = sum(weights)

        return weighted_sum / weight_sum if weight_sum != 0 else None


class OptimizedSlidingWindow(SlidingWindow):
    """
    进一步优化的滑动窗口算法
    使用增量计算提高大数据量场景的性能
    """

    def __init__(self, window_size: int):
        super().__init__(window_size)
        self._sum = 0.0
        self._sum_sq = 0.0
        self._enable_incremental = True

    def add(self, value: float) -> None:
        if len(self.data) == self.window_size:
            old_value = self.data[0]
            self._sum -= old_value
            self._sum_sq -= old_value ** 2

        self.data.append(value)
        self._sum += value
        self._sum_sq += value ** 2

    def add_batch(self, values: List[float]) -> None:
        for value in values:
            self.add(value)

    def get_average(self) -> Optional[float]:
        if not self.data:
            return None
        return self._sum / len(self.data)

    def get_std(self) -> Optional[float]:
        if len(self.data) < 2:
            return None
        mean = self._sum / len(self.data)
        variance = (self._sum_sq / len(self.data)) - (mean ** 2)
        return float(np.sqrt(max(0, variance)))

    def get_variance(self) -> Optional[float]:
        if len(self.data) < 2:
            return None
        mean = self._sum / len(self.data)
        variance = (self._sum_sq / len(self.data)) - (mean ** 2)
        return float(max(0, variance))

    def clear(self) -> None:
        super().clear()
        self._sum = 0.0
        self._sum_sq = 0.0


class TrendCalculator:
    """
    趋势计算算法实现
    """

    def __init__(self, window_size: int = 10):
        """
        初始化趋势计算器

        Args:
            window_size (int): 计算趋势的窗口大小
        """
        self.window_size = window_size
        self.sliding_window = SlidingWindow(window_size)
        self.historical_values = deque(maxlen=1000)

    def calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """
        计算趋势

        Args:
            values (list): 数据值列表

        Returns:
            dict: 包含趋势信息的字典
        """
        if len(values) < 2:
            return {
                'trend_score': 0,
                'trend_direction': 'stable',
                'slope': 0,
                'r_squared': 0,
                'correlation': 0
            }

        x = np.arange(len(values))
        y = np.array(values)

        if len(values) == 2:
            slope = (y[1] - y[0]) / (x[1] - x[0])
            r_squared = 1.0 if y[0] != y[1] else 1.0
            correlation = 1.0 if (y[1] - y[0]) > 0 else (-1.0 if (y[1] - y[0]) < 0 else 0)
        else:
            coeffs = np.polyfit(x, y, 1)
            slope = coeffs[0]

            y_pred = np.polyval(coeffs, x)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            correlation = np.corrcoef(x, y)[0, 1] if len(values) > 2 else 0

        trend_score = abs(slope) * 100 * (1 + r_squared)

        if abs(slope) < 0.01:
            trend_direction = 'stable'
        elif slope > 0:
            trend_direction = 'increasing'
        else:
            trend_direction = 'decreasing'

        return {
            'trend_score': float(trend_score),
            'trend_direction': trend_direction,
            'slope': float(slope),
            'r_squared': float(r_squared),
            'correlation': float(correlation) if not np.isnan(correlation) else 0
        }

    def calculate_moving_average(self, values: List[float], window_size: int) -> List[float]:
        """
        计算移动平均值

        Args:
            values (list): 数据值列表
            window_size (int): 窗口大小

        Returns:
            list: 移动平均值列表
        """
        if len(values) < window_size:
            return []

        result = []
        window = deque(maxlen=window_size)

        for value in values:
            window.append(value)
            if len(window) == window_size:
                result.append(sum(window) / window_size)

        return result

    def calculate_exponential_moving_average(self, values: List[float], alpha: float = 0.3) -> List[float]:
        """
        计算指数移动平均值

        Args:
            values (list): 数据值列表
            alpha (float): 平滑系数 (0-1)

        Returns:
            list: 指数移动平均值列表
        """
        if not values:
            return []

        result = [values[0]]
        for value in values[1:]:
            ema = alpha * value + (1 - alpha) * result[-1]
            result.append(ema)

        return result

    def calculate_weighted_moving_average(self, values: List[float], window_size: int) -> List[float]:
        """
        计算加权移动平均值

        Args:
            values (list): 数据值列表
            window_size (int): 窗口大小

        Returns:
            list: 加权移动平均值列表
        """
        if len(values) < window_size:
            return []

        result = []
        weights = np.arange(1, window_size + 1)
        weights = weights / weights.sum()

        for i in range(len(values) - window_size + 1):
            window = values[i:i + window_size]
            wma = sum(w * wt for w, wt in zip(window, weights))
            result.append(wma)

        return result

    def detect_anomaly(self, value: float, mean: float, std: float, threshold: float = 3) -> Dict[str, Any]:
        """
        检测异常值

        Args:
            value (float): 当前值
            mean (float): 平均值
            std (float): 标准差
            threshold (float): 异常检测阈值

        Returns:
            dict: 异常检测结果
        """
        if std == 0:
            return {
                'is_anomaly': False,
                'anomaly_score': 0,
                'z_score': 0
            }

        z_score = abs(value - mean) / std
        is_anomaly = z_score > threshold

        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': float(z_score),
            'z_score': float(z_score)
        }

    def detect_change_point(self, values: List[float], window_size: int = 5) -> List[int]:
        """
        检测变化点

        Args:
            values (list): 数据值列表
            window_size (int): 检测窗口大小

        Returns:
            list: 变化点索引列表
        """
        if len(values) < 2 * window_size:
            return []

        change_points = []
        for i in range(window_size, len(values) - window_size):
            left_window = values[i - window_size:i]
            right_window = values[i:i + window_size]

            left_mean = sum(left_window) / len(left_window)
            right_mean = sum(right_window) / len(right_window)

            if abs(right_mean - left_mean) > 2 * np.std(values):
                change_points.append(i)

        return change_points

    def predict_next_values(self, values: List[float], horizon: int = 5) -> List[float]:
        """
        基于当前趋势预测未来值

        Args:
            values (list): 数据值列表
            horizon (int): 预测步数

        Returns:
            list: 预测值列表
        """
        if len(values) < 2:
            return [values[0]] * horizon if values else [0] * horizon

        trend = self.calculate_trend(values)
        slope = trend['slope']
        last_value = values[-1]

        predictions = []
        for i in range(1, horizon + 1):
            predicted = last_value + slope * i
            predictions.append(predicted)

        return predictions


class PredictionModel:
    """
    预测模型实现
    支持环境数据集成和多种预测算法
    """

    def __init__(self):
        """
        初始化预测模型
        """
        self.trend_calculator = TrendCalculator()
        self.models_cache = {}

    def predict(self, historical_data: List[float], horizon: int = 5) -> List[float]:
        """
        基于历史数据预测未来值

        Args:
            historical_data (list): 历史数据
            horizon (int): 预测时间跨度

        Returns:
            list: 预测值列表
        """
        if len(historical_data) < 2:
            return [historical_data[-1]] * horizon if historical_data else [0] * horizon

        window_size = min(5, len(historical_data))
        predictions = []

        for i in range(horizon):
            if len(historical_data) >= window_size:
                avg = sum(historical_data[-window_size:]) / window_size
            else:
                avg = sum(historical_data) / len(historical_data)

            predictions.append(avg)
            historical_data.append(avg)

        return predictions

    def predict_with_trend(self, historical_data: List[float], horizon: int = 5) -> Dict[str, Any]:
        """
        使用趋势分析进行预测

        Args:
            historical_data (list): 历史数据
            horizon (int): 预测时间跨度

        Returns:
            dict: 包含预测值和趋势信息的字典
        """
        if len(historical_data) < 2:
            return {
                'predictions': [historical_data[-1]] * horizon if historical_data else [0] * horizon,
                'trend': {'slope': 0, 'direction': 'stable'},
                'confidence': 0.5
            }

        trend = self.trend_calculator.calculate_trend(historical_data)
        slope = trend['slope']
        last_value = historical_data[-1]

        predictions = []
        for i in range(1, horizon + 1):
            predicted = last_value + slope * i
            predictions.append(predicted)

        confidence = self.calculate_confidence(historical_data)

        return {
            'predictions': predictions,
            'trend': {
                'slope': trend['slope'],
                'direction': trend['trend_direction'],
                'score': trend['trend_score']
            },
            'confidence': confidence
        }

    def predict_with_environmental_factors(
        self,
        historical_data: List[float],
        environmental_data: List[Dict[str, float]],
        horizon: int = 5
    ) -> Dict[str, Any]:
        """
        结合环境因素进行预测

        Args:
            historical_data (list): 历史数据
            environmental_data (list): 环境数据列表，每项包含温度、湿度等
            horizon (int): 预测时间跨度

        Returns:
            dict: 包含预测值和环境因素影响的字典
        """
        if len(historical_data) < 2:
            return {
                'predictions': [historical_data[-1]] * horizon if historical_data else [0] * horizon,
                'environmental_impact': {},
                'confidence': 0.5
            }

        base_predictions = self.predict_with_trend(historical_data, horizon)

        if not environmental_data:
            return {
                **base_predictions,
                'environmental_impact': {},
                'raw_predictions': base_predictions['predictions']
            }

        impact_analysis = self._analyze_environmental_impact(historical_data, environmental_data)

        adjusted_predictions = []
        for i, pred in enumerate(base_predictions['predictions']):
            impact = impact_analysis.get('total_impact', 0)
            adjusted_pred = pred + impact
            adjusted_predictions.append(adjusted_pred)

        return {
            'predictions': adjusted_predictions,
            'raw_predictions': base_predictions['predictions'],
            'trend': base_predictions['trend'],
            'confidence': base_predictions['confidence'] * impact_analysis.get('reliability', 0.5),
            'environmental_impact': {
                'temperature_impact': impact_analysis.get('temperature_coefficient', 0) * impact_analysis.get('avg_temperature', 0),
                'humidity_impact': impact_analysis.get('humidity_coefficient', 0) * impact_analysis.get('avg_humidity', 0),
                'total_impact': impact_analysis.get('total_impact', 0),
                'reliability': impact_analysis.get('reliability', 0)
            }
        }

    def _analyze_environmental_impact(
        self,
        historical_data: List[float],
        environmental_data: List[Dict[str, float]]
    ) -> Dict[str, float]:
        """
        分析环境因素对设备状态的影响

        Args:
            historical_data (list): 历史设备数据
            environmental_data (list): 环境数据

        Returns:
            dict: 环境因素影响分析结果
        """
        if len(historical_data) != len(environmental_data) or len(historical_data) < 3:
            return {
                'temperature_coefficient': 0,
                'humidity_coefficient': 0,
                'total_impact': 0,
                'reliability': 0
            }

        temp_values = [e.get('ambient_temperature', 0) for e in environmental_data]
        humidity_values = [e.get('humidity', 0) for e in environmental_data]

        device_std = np.std(historical_data)
        if device_std == 0:
            device_std = 1

        temp_coef = np.corrcoef(historical_data, temp_values)[0, 1] if len(set(temp_values)) > 1 else 0
        humidity_coef = np.corrcoef(historical_data, humidity_values)[0, 1] if len(set(humidity_values)) > 1 else 0

        temp_coef = 0 if np.isnan(temp_coef) else temp_coef
        humidity_coef = 0 if np.isnan(humidity_coef) else humidity_coef

        avg_temp = np.mean(temp_values)
        avg_humidity = np.mean(humidity_values)

        temp_impact = temp_coef * avg_temp * 0.01
        humidity_impact = humidity_coef * avg_humidity * 0.001

        reliability = min(abs(temp_coef) + abs(humidity_coef), 1.0)

        return {
            'temperature_coefficient': float(temp_coef),
            'humidity_coefficient': float(humidity_coef),
            'avg_temperature': float(avg_temp),
            'avg_humidity': float(avg_humidity),
            'total_impact': float(temp_impact + humidity_impact),
            'reliability': float(reliability)
        }

    def calculate_confidence(self, historical_data: List[float]) -> float:
        """
        计算预测置信度

        Args:
            historical_data (list): 历史数据

        Returns:
            float: 置信度值
        """
        if len(historical_data) < 3:
            return 0.5

        std = np.std(historical_data)
        if std == 0:
            return 1.0

        stability_score = 1 / (1 + std)
        data_amount_score = min(len(historical_data) / 100, 1.0)

        confidence = (stability_score + data_amount_score) / 2
        return float(confidence)

    def auto_tune_parameters(self, historical_data: List[float]) -> Dict[str, Any]:
        """
        根据历史数据自动调优模型参数

        Args:
            historical_data (list): 历史数据

        Returns:
            dict: 调优后的参数
        """
        if len(historical_data) < 10:
            return {
                'window_size': 5,
                'alpha': 0.3,
                'threshold': 3
            }

        trend = self.trend_calculator.calculate_trend(historical_data)

        volatility = np.std(historical_data) / (np.mean(historical_data) + 0.001)

        if volatility < 0.05:
            window_size = min(10, len(historical_data))
            alpha = 0.5
            threshold = 2.5
        elif volatility < 0.2:
            window_size = min(7, len(historical_data))
            alpha = 0.3
            threshold = 3.0
        else:
            window_size = min(5, len(historical_data))
            alpha = 0.2
            threshold = 3.5

        return {
            'window_size': window_size,
            'alpha': alpha,
            'threshold': threshold,
            'volatility': float(volatility),
            'trend_direction': trend['trend_direction']
        }


class ThresholdComparator:
    """
    阈值对比逻辑实现
    """

    def __init__(self):
        self.default_severity_levels = {
            'INFO': 0,
            'WARN': 1,
            'ERROR': 2,
            'CRITICAL': 3
        }

    def compare(self, value: float, threshold: float, operator: str) -> bool:
        """
        比较值与阈值

        Args:
            value (float): 要比较的值
            threshold (float): 阈值
            operator (str): 比较操作符

        Returns:
            bool: 比较结果
        """
        if operator == '<':
            return value < threshold
        elif operator == '>':
            return value > threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '==':
            return value == threshold
        elif operator == '!=':
            return value != threshold
        elif operator == 'abs>':
            return abs(value) > threshold
        else:
            return False

    def compare_multiple(self, value: float, conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        多个条件比较

        Args:
            value (float): 要比较的值
            conditions (list): 条件列表，每个条件包含threshold、operator和severity

        Returns:
            dict: 包含最严重级别和触发条件的字典
        """
        triggered_conditions = []
        max_severity = 'INFO'
        severity_order = ['INFO', 'WARN', 'ERROR', 'CRITICAL']

        for condition in conditions:
            threshold = condition.get('threshold')
            operator = condition.get('operator')
            severity = condition.get('severity', 'INFO')

            if threshold is None or operator is None:
                continue

            if self.compare(value, threshold, operator):
                triggered_conditions.append(condition)
                if severity_order.index(severity) > severity_order.index(max_severity):
                    max_severity = severity

        return {
            'is_triggered': len(triggered_conditions) > 0,
            'max_severity': max_severity,
            'triggered_conditions': triggered_conditions
        }

    def determine_severity(self, value: float, threshold: float, operator: str, severity_levels: Optional[Dict[str, int]] = None) -> str:
        """
        根据值与阈值的关系确定严重程度

        Args:
            value (float): 要比较的值
            threshold (float): 阈值
            operator (str): 比较操作符
            severity_levels (dict): 严重程度级别定义

        Returns:
            str: 严重程度
        """
        levels = severity_levels or self.default_severity_levels

        if not self.compare(value, threshold, operator):
            return 'INFO'

        if operator in ['>', '>=', 'abs>']:
            ratio = value / threshold if threshold != 0 else float('inf')
        elif operator in ['<', '<=']:
            ratio = threshold / value if value != 0 else float('inf')
        else:
            return 'WARN'

        if ratio >= 2:
            return 'CRITICAL'
        elif ratio >= 1.5:
            return 'ERROR'
        else:
            return 'WARN'

    def calculate_deviation(self, value: float, threshold: float, operator: str) -> Dict[str, Any]:
        """
        计算值与阈值的偏差

        Args:
            value (float): 要比较的值
            threshold (float): 阈值
            operator (str): 比较操作符

        Returns:
            dict: 包含偏差信息的字典
        """
        if threshold == 0:
            return {
                'deviation': None,
                'deviation_ratio': None,
                'is_exceeded': False
            }

        if operator in ['>', '>=']:
            deviation = value - threshold
            deviation_ratio = deviation / threshold
        elif operator in ['<', '<=']:
            deviation = threshold - value
            deviation_ratio = deviation / threshold
        elif operator == 'abs>':
            deviation = abs(value) - threshold
            deviation_ratio = deviation / threshold
        else:
            deviation = value - threshold
            deviation_ratio = deviation / threshold

        is_exceeded = self.compare(value, threshold, operator)

        return {
            'deviation': float(deviation),
            'deviation_ratio': float(deviation_ratio),
            'is_exceeded': is_exceeded
        }


class ExponentialSmoothingModel:
    """
    指数平滑预测模型
    实现简单指数平滑(SES)和Holt's双指数平滑
    支持趋势数据的预测
    """

    def __init__(self, alpha: float = 0.3, beta: float = 0.1):
        """
        初始化指数平滑模型

        Args:
            alpha (float): 水平平滑系数 (0-1)
            beta (float): 趋势平滑系数 (0-1)
        """
        self.alpha = alpha
        self.beta = beta
        self.level = None
        self.trend = None
        self.is_fitted = False

    def simple_exponential_smoothing(self, data: List[float], horizon: int = 5) -> Dict[str, Any]:
        """
        简单指数平滑 (Simple Exponential Smoothing)
        适用于没有明显趋势的数据

        Args:
            data (list): 历史数据
            horizon (int): 预测步数

        Returns:
            dict: 预测结果
        """
        if len(data) < 2:
            return {
                'predictions': [data[-1]] * horizon if data else [0] * horizon,
                'smoothed_value': data[-1] if data else 0,
                'method': 'ses'
            }

        alpha = self.alpha
        n = len(data)

        smoothed = [data[0]]
        for i in range(1, n):
            s = alpha * data[i] + (1 - alpha) * smoothed[-1]
            smoothed.append(s)

        self.level = smoothed[-1]
        self.is_fitted = True
        
        # 计算最近的变化趋势，使预测更有变化
        if len(data) >= 5:
            recent_data = data[-5:]
            trend_slope = (recent_data[-1] - recent_data[0]) / 4
        else:
            trend_slope = 0
        
        # 生成带有轻微趋势的预测值
        predictions = []
        for h in range(1, horizon + 1):
            pred = self.level + trend_slope * h * 0.3  # 添加轻微趋势
            predictions.append(pred)

        return {
            'predictions': predictions,
            'smoothed_value': float(self.level),
            'method': 'ses',
            'alpha': alpha
        }

    def holt_double_exponential_smoothing(self, data: List[float], horizon: int = 5) -> Dict[str, Any]:
        """
        Holt's 双指数平滑
        适用于有明显趋势的数据

        Args:
            data (list): 历史数据
            horizon (int): 预测步数

        Returns:
            dict: 预测结果
        """
        if len(data) < 3:
            return self.simple_exponential_smoothing(data, horizon)

        alpha = self.alpha
        beta = self.beta
        n = len(data)

        level = [data[0]]
        trend = [data[1] - data[0]]

        for i in range(1, n):
            l = alpha * data[i] + (1 - alpha) * (level[-1] + trend[-1])
            t = beta * (l - level[-1]) + (1 - beta) * trend[-1]
            level.append(l)
            trend.append(t)

        self.level = level[-1]
        self.trend = trend[-1]
        self.is_fitted = True

        predictions = []
        for h in range(1, horizon + 1):
            pred = self.level + h * self.trend
            predictions.append(pred)

        return {
            'predictions': predictions,
            'level': float(self.level),
            'trend': float(self.trend),
            'method': 'holt',
            'alpha': alpha,
            'beta': beta
        }

    def predict(self, data: List[float], horizon: int = 5, method: str = 'auto') -> Dict[str, Any]:
        """
        预测接口，自动选择最佳方法

        Args:
            data (list): 历史数据
            horizon (int): 预测步数
            method (str): 'ses', 'holt', 或 'auto'

        Returns:
            dict: 预测结果
        """
        if len(data) < 3:
            method = 'ses'
        elif method == 'auto':
            trend = TrendCalculator()
            trend_result = trend.calculate_trend(data)
            # 使用更宽松的阈值，更倾向于使用Holt双指数平滑来捕捉趋势
            # 只有当数据非常平稳（标准差很小）时才使用SES
            data_std = np.std(data) if len(data) >= 2 else 0
            data_mean = np.mean(data) if len(data) >= 1 else 1
            coefficient_of_variation = data_std / data_mean if data_mean != 0 else 0
            
            # 如果数据非常稳定（变异系数 < 5%），使用SES；否则使用Holt
            if coefficient_of_variation < 0.05 and abs(trend_result['slope']) < 0.001:
                method = 'ses'
            else:
                method = 'holt'

        if method == 'ses':
            return self.simple_exponential_smoothing(data, horizon)
        else:
            return self.holt_double_exponential_smoothing(data, horizon)

    def model_fusion(self, data: List[float], horizon: int = 5, weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        模型融合预测
        结合移动平均、线性回归和指数平滑的优势

        Args:
            data (list): 历史数据
            horizon (int): 预测步数
            weights (dict): 各模型权重

        Returns:
            dict: 融合后的预测结果
        """
        if weights is None:
            weights = {'ma': 0.3, 'lr': 0.3, 'ses': 0.4}

        ma_predictions = self._moving_average_prediction(data, horizon)
        lr_predictions = self._linear_regression_prediction(data, horizon)
        ses_result = self.simple_exponential_smoothing(data, horizon)
        ses_predictions = ses_result['predictions']

        fused_predictions = []
        for i in range(horizon):
            fused = (
                weights.get('ma', 0.33) * ma_predictions[i] +
                weights.get('lr', 0.33) * lr_predictions[i] +
                weights.get('ses', 0.34) * ses_predictions[i]
            )
            fused_predictions.append(fused)

        return {
            'predictions': fused_predictions,
            'component_predictions': {
                'moving_average': ma_predictions,
                'linear_regression': lr_predictions,
                'exponential_smoothing': ses_predictions
            },
            'weights': weights,
            'method': 'fusion'
        }

    def _moving_average_prediction(self, data: List[float], horizon: int) -> List[float]:
        """移动平均预测"""
        window_size = min(5, len(data))
        ma_value = sum(data[-window_size:]) / window_size
        return [ma_value] * horizon

    def _linear_regression_prediction(self, data: List[float], horizon: int) -> List[float]:
        """线性回归预测"""
        n = len(data)
        x = np.arange(n)
        y = np.array(data)
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs

        predictions = []
        for i in range(1, horizon + 1):
            predictions.append(intercept + slope * (n + i - 1))
        return predictions


class IQRAnomalyDetector:
    """
    基于IQR（四分位距）的异常值检测算法
    提供更准确的异常值识别
    """

    def __init__(self, k: float = 1.5):
        """
        初始化IQR异常检测器

        Args:
            k (float): IQR倍数阈值，默认1.5
        """
        self.k = k
        self.q1 = None
        self.q3 = None
        self.iqr = None
        self.lower_bound = None
        self.upper_bound = None

    def fit(self, data: List[float]) -> 'IQRAnomalyDetector':
        """
        从数据中学习IQR参数

        Args:
            data (list): 历史数据

        Returns:
            self
        """
        if len(data) < 4:
            self.q1 = np.min(data)
            self.q3 = np.max(data)
        else:
            sorted_data = np.sort(data)
            self.q1 = float(np.percentile(sorted_data, 25))
            self.q3 = float(np.percentile(sorted_data, 75))

        self.iqr = self.q3 - self.q1
        self.lower_bound = self.q1 - self.k * self.iqr
        self.upper_bound = self.q3 + self.k * self.iqr

        return self

    def detect(self, value: float) -> Dict[str, Any]:
        """
        检测单个值是否为异常值

        Args:
            value (float): 待检测的值

        Returns:
            dict: 异常检测结果
        """
        if self.iqr is None:
            return {
                'is_anomaly': False,
                'anomaly_score': 0,
                'reason': 'not_fitted'
            }

        z_score = 0
        if value < self.lower_bound:
            distance = self.lower_bound - value
            z_score = distance / self.iqr if self.iqr != 0 else 0
            reason = 'below_lower_bound'
        elif value > self.upper_bound:
            distance = value - self.upper_bound
            z_score = distance / self.iqr if self.iqr != 0 else 0
            reason = 'above_upper_bound'
        else:
            reason = 'normal'

        return {
            'is_anomaly': z_score > self.k,
            'anomaly_score': float(z_score),
            'reason': reason,
            'bounds': {
                'lower': float(self.lower_bound),
                'upper': float(self.upper_bound)
            }
        }

    def detect_batch(self, data: List[float]) -> List[Dict[str, Any]]:
        """
        批量检测异常值

        Args:
            data (list): 待检测的数据列表

        Returns:
            list: 每个值的异常检测结果
        """
        self.fit(data)
        return [self.detect(v) for v in data]

    def get_adaptive_threshold(self, data: List[float], confidence_level: float = 0.95) -> Dict[str, float]:
        """
        根据历史数据动态调整异常检测阈值

        Args:
            data (list): 历史数据
            confidence_level (float): 置信水平

        Returns:
            dict: 自适应阈值
        """
        self.fit(data)

        sorted_data = np.sort(data)
        n = len(sorted_data)

        lower_idx = int(n * (1 - confidence_level) / 2)
        upper_idx = int(n * (1 + confidence_level) / 2)

        adaptive_lower = sorted_data[max(0, lower_idx)]
        adaptive_upper = sorted_data[min(n - 1, upper_idx)]

        return {
            'lower_threshold': float(adaptive_lower),
            'upper_threshold': float(adaptive_upper),
            'q1': float(self.q1),
            'q3': float(self.q3),
            'iqr': float(self.iqr),
            'confidence_level': confidence_level
        }


class MissingDataHandler:
    """
    缺失数据处理模块
    提供多种插值策略处理缺失数据
    """

    def __init__(self):
        self.method = 'linear'

    def linear_interpolate(self, data: List[float], timestamps: Optional[List[datetime]] = None) -> List[float]:
        """
        线性插值

        Args:
            data (list): 包含缺失值的数据，缺失值用None表示
            timestamps (list): 对应的时间戳

        Returns:
            list: 插值后的数据
        """
        result = data.copy()
        n = len(result)

        i = 0
        while i < n:
            if result[i] is None:
                start = i
                while i < n and result[i] is None:
                    i += 1
                end = i

                if start > 0 and end < n:
                    start_val = result[start - 1]
                    end_val = result[end]
                    for j in range(start, end):
                        ratio = (j - start + 1) / (end - start + 1)
                        result[j] = start_val + ratio * (end_val - start_val)
                elif start > 0:
                    for j in range(start, end):
                        result[j] = result[start - 1]
                elif end < n:
                    for j in range(start, end):
                        result[j] = result[end]

            i += 1

        return result

    def polynomial_interpolate(self, data: List[float], degree: int = 2) -> List[float]:
        """
        多项式插值

        Args:
            data (list): 包含缺失值的数据
            degree (int): 多项式阶数

        Returns:
            list: 插值后的数据
        """
        result = data.copy()
        n = len(result)

        valid_indices = [i for i, v in enumerate(result) if v is not None]

        if len(valid_indices) < degree + 1:
            return self.linear_interpolate(data)

        for i in range(n):
            if result[i] is None:
                left_indices = [idx for idx in valid_indices if idx < i]
                right_indices = [idx for idx in valid_indices if idx > i]

                if left_indices and right_indices:
                    start_idx = left_indices[-1]
                    end_idx = right_indices[0]
                    window_size = end_idx - start_idx + 1

                    if window_size >= degree + 1:
                        window_indices = valid_indices[valid_indices.index(start_idx):valid_indices.index(end_idx) + 1]
                        x = np.array([idx - start_idx for idx in window_indices])
                        y = np.array([result[idx] for idx in window_indices])
                        coeffs = np.polyfit(x, y, min(degree, len(x) - 1))
                        result[i] = float(np.polyval(coeffs, i - start_idx))
                    else:
                        start_val = result[start_idx]
                        end_val = result[end_idx]
                        ratio = (i - start_idx) / (end_idx - start_idx)
                        result[i] = start_val + ratio * (end_val - start_val)

        return result

    def knn_interpolate(self, data: List[float], k: int = 3) -> List[float]:
        """
        K近邻插值

        Args:
            data (list): 包含缺失值的数据
            k (int): K近邻数量

        Returns:
            list: 插值后的数据
        """
        result = data.copy()
        n = len(result)

        for i in range(n):
            if result[i] is None:
                left_vals = []
                right_vals = []

                for j in range(i - 1, -1, -1):
                    if result[j] is not None:
                        left_vals.append((i - j, result[j]))
                    if len(left_vals) >= k:
                        break

                for j in range(i + 1, n):
                    if result[j] is not None:
                        right_vals.append((j - i, result[j]))
                    if len(right_vals) >= k:
                        break

                neighbors = left_vals + right_vals
                neighbors.sort(key=lambda x: x[0])

                if neighbors:
                    k_neighbors = neighbors[:k]
                    weights = [1 / (dist + 0.001) for dist, val in k_neighbors]
                    total_weight = sum(weights)
                    result[i] = sum(val * w for (dist, val), w in zip(k_neighbors, weights)) / total_weight

        return result

    def handle_missing(self, data: List[float], method: str = 'linear', **kwargs) -> Dict[str, Any]:
        """
        统一处理接口

        Args:
            data (list): 包含缺失值的数据
            method (str): 插值方法，'linear', 'polynomial', 'knn'
            **kwargs: 其他参数

        Returns:
            dict: 处理结果
        """
        missing_count = sum(1 for v in data if v is None)

        if missing_count == 0:
            return {
                'data': data,
                'method': 'none',
                'missing_count': 0,
                'data_quality_score': 1.0
            }

        if method == 'linear':
            processed = self.linear_interpolate(data)
        elif method == 'polynomial':
            degree = kwargs.get('degree', 2)
            processed = self.polynomial_interpolate(data, degree)
        elif method == 'knn':
            k = kwargs.get('k', 3)
            processed = self.knn_interpolate(data, k)
        else:
            processed = self.linear_interpolate(data)

        data_quality = 1.0 - (missing_count / len(data))

        return {
            'data': processed,
            'method': method,
            'missing_count': missing_count,
            'data_quality_score': float(data_quality)
        }


class AdaptiveWindowSizer:
    """
    动态窗口大小调整算法
    根据数据波动程度自动调整滑动窗口大小
    """

    def __init__(self, min_window: int = 5, max_window: int = 50):
        """
        初始化自适应窗口调整器

        Args:
            min_window (int): 最小窗口大小
            max_window (int): 最大窗口大小
        """
        self.min_window = min_window
        self.max_window = max_window

    def calculate_volatility(self, data: List[float]) -> Dict[str, float]:
        """
        计算数据波动性指标

        Args:
            data (list): 历史数据

        Returns:
            dict: 波动性指标
        """
        if len(data) < 3:
            return {
                'volatility': 0.5,
                'cv': 0.5,
                'range_ratio': 0.5
            }

        data_array = np.array(data)
        mean = np.mean(data_array)
        std = np.std(data_array)

        cv = std / abs(mean) if mean != 0 else std
        data_range = np.max(data_array) - np.min(data_array)
        range_ratio = data_range / (abs(mean) + 0.001)

        volatility = min(cv * range_ratio, 1.0)

        return {
            'volatility': float(volatility),
            'cv': float(cv),
            'range_ratio': float(range_ratio),
            'std': float(std),
            'mean': float(mean)
        }

    def calculate_optimal_window(self, data: List[float]) -> int:
        """
        计算最优窗口大小

        Args:
            data (list): 历史数据

        Returns:
            int: 最优窗口大小
        """
        volatility = self.calculate_volatility(data)
        vol = volatility['volatility']

        if vol < 0.1:
            optimal = int(self.max_window * 0.9)
        elif vol < 0.3:
            optimal = int(self.max_window * 0.6)
        elif vol < 0.5:
            optimal = int(self.max_window * 0.4)
        else:
            optimal = int(self.max_window * 0.2)

        optimal = max(self.min_window, min(self.max_window, optimal))

        autocorr_lag = self._calculate_autocorrelation_lag(data)
        if autocorr_lag > optimal:
            optimal = min(autocorr_lag, self.max_window)

        return optimal

    def _calculate_autocorrelation_lag(self, data: List[float]) -> int:
        """
        计算自相关时间滞后期

        Args:
            data (list): 历史数据

        Returns:
            int: 滞后期
        """
        if len(data) < 4:
            return self.min_window

        data_array = np.array(data)
        mean = np.mean(data_array)
        var = np.var(data_array)

        if var == 0:
            return self.min_window

        n = len(data)
        for lag in range(1, min(n // 2, self.max_window)):
            covariance = np.mean((data_array[:-lag] - mean) * (data_array[lag:] - mean))
            autocorr = covariance / var
            if abs(autocorr) < 0.3:
                return lag

        return self.min_window

    def adapt_window(self, data: List[float]) -> Dict[str, Any]:
        """
        自适应窗口调整接口

        Args:
            data (list): 历史数据

        Returns:
            dict: 调整结果
        """
        optimal_window = self.calculate_optimal_window(data)
        volatility = self.calculate_volatility(data)

        return {
            'optimal_window': optimal_window,
            'min_window': self.min_window,
            'max_window': self.max_window,
            'volatility': volatility,
            'recommended_for': 'stable' if volatility['volatility'] < 0.3 else 'volatile'
        }


class MultiVariablePredictor:
    """
    多变量预测模型
    支持关联指标分析和交叉设备学习
    """

    def __init__(self):
        self.related_metrics_cache = {}
        self.cross_device_models = {}

    def analyze_related_metrics(
        self,
        target_data: List[float],
        related_data: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """
        分析关联指标对目标指标的影响

        Args:
            target_data (list): 目标指标数据
            related_data (dict): 关联指标数据，格式为 {指标名: [数据]}

        Returns:
            dict: 关联分析结果
        """
        if len(target_data) < 3:
            return {
                'correlations': {},
                'influential_metrics': [],
                'impact_scores': {}
            }

        correlations = {}
        impact_scores = {}

        target_array = np.array(target_data)

        for metric_name, metric_data in related_data.items():
            if len(metric_data) != len(target_data):
                continue

            metric_array = np.array(metric_data)

            if len(set(metric_array)) < 2:
                correlations[metric_name] = 0
                impact_scores[metric_name] = 0
                continue

            corr = np.corrcoef(target_array, metric_array)[0, 1]
            if np.isnan(corr):
                corr = 0

            correlations[metric_name] = float(corr)

            impact = abs(corr) * np.std(metric_array) / (np.std(target_array) + 0.001)
            impact_scores[metric_name] = float(min(impact, 1.0))

        influential = sorted(impact_scores.items(), key=lambda x: x[1], reverse=True)
        influential_metrics = [m[0] for m in influential if m[1] > 0.1][:5]

        return {
            'correlations': correlations,
            'influential_metrics': influential_metrics,
            'impact_scores': impact_scores,
            'analysis_sample_size': len(target_data)
        }

    def predict_with_related_metrics(
        self,
        target_data: List[float],
        related_data: Dict[str, List[float]],
        horizon: int = 5
    ) -> Dict[str, Any]:
        """
        使用关联指标进行预测

        Args:
            target_data (list): 目标指标历史数据
            related_data (dict): 关联指标数据
            horizon (int): 预测步数

        Returns:
            dict: 预测结果
        """
        analysis = self.analyze_related_metrics(target_data, related_data)

        prediction_model = PredictionModel()
        base_prediction = prediction_model.predict_with_trend(target_data, horizon)

        if not analysis['influential_metrics']:
            return {
                **base_prediction,
                'method': 'base_no_related',
                'related_metrics_contribution': 0
            }

        adjustment = 0
        for metric in analysis['influential_metrics']:
            if metric in related_data and len(related_data[metric]) > 0:
                recent_avg = np.mean(related_data[metric][-5:])
                metric_impact = analysis['impact_scores'][metric]
                corr = analysis['correlations'][metric]

                recent_target_avg = np.mean(target_data[-5:]) if len(target_data) >= 5 else np.mean(target_data)
                trend_direction = 1 if base_prediction['trend']['slope'] > 0 else -1

                adjustment += corr * metric_impact * (recent_avg - np.mean(related_data[metric])) * 0.01 * trend_direction

        adjusted_predictions = [p + adjustment for p in base_prediction['predictions']]

        return {
            'predictions': adjusted_predictions,
            'raw_predictions': base_prediction['predictions'],
            'trend': base_prediction['trend'],
            'confidence': base_prediction['confidence'] * (1 - abs(adjustment) / 100),
            'method': 'multi_variable',
            'related_metrics_contribution': float(adjustment),
            'influential_metrics': analysis['influential_metrics']
        }

    def learn_from_device_type(
        self,
        device_type: str,
        device_data: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """
        从同类设备学习预测模式

        Args:
            device_type (str): 设备类型
            device_data (dict): 设备数据，格式为 {device_id: [数据]}

        Returns:
            dict: 学习结果
        """
        if device_type not in self.cross_device_models:
            self.cross_device_models[device_type] = {
                'sample_count': 0,
                'avg_baseline': {},
                'typical_patterns': {}
            }

        model = self.cross_device_models[device_type]

        for metric, values in device_data.items():
            if len(values) < 3:
                continue

            if metric not in model['avg_baseline']:
                model['avg_baseline'][metric] = []

            model['avg_baseline'][metric].extend(values)

        model['sample_count'] += 1

        for metric in model['avg_baseline']:
            if model['avg_baseline'][metric]:
                model['typical_patterns'][metric] = {
                    'mean': float(np.mean(model['avg_baseline'][metric])),
                    'std': float(np.std(model['avg_baseline'][metric])),
                    'trend': TrendCalculator().calculate_trend(model['avg_baseline'][metric])
                }

        return {
            'device_type': device_type,
            'sample_count': model['sample_count'],
            'typical_patterns': model['typical_patterns'],
            'learning_status': 'updated'
        }


class RiskAssessmentEngine:
    """
    多维度风险评估引擎
    综合考虑预测值、趋势、置信度等因素进行风险评估
    """

    def __init__(self):
        self.severity_levels = {
            'INFO': 0,
            'WARN': 1,
            'ERROR': 2,
            'CRITICAL': 3
        }

    def assess_risk(
        self,
        prediction: float,
        current_value: float,
        threshold: float,
        trend: Dict[str, Any],
        confidence: float,
        environmental_factors: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        多维度风险评估

        Args:
            prediction (float): 预测值
            current_value (float): 当前值
            threshold (float): 阈值
            trend (dict): 趋势分析结果
            confidence (float): 置信度
            environmental_factors (dict): 环境因素影响

        Returns:
            dict: 风险评估结果
        """
        prediction_risk = self._evaluate_prediction_risk(prediction, threshold)
        trend_risk = self._evaluate_trend_risk(trend, threshold)
        confidence_risk = self._evaluate_confidence_risk(confidence)

        env_risk = 0
        if environmental_factors:
            env_risk = self._evaluate_environmental_risk(environmental_factors)

        deviation_ratio = abs(prediction - threshold) / abs(threshold) if threshold != 0 else 0

        time_to_threshold = self._estimate_time_to_threshold(
            current_value, trend['slope'], threshold
        )

        combined_risk = (
            prediction_risk * 0.4 +
            trend_risk * 0.3 +
            confidence_risk * 0.2 +
            env_risk * 0.1
        )

        severity = self._determine_overall_severity(
            combined_risk, deviation_ratio, time_to_threshold
        )

        priority = self._calculate_priority(severity, time_to_threshold)

        return {
            'risk_score': float(combined_risk),
            'severity': severity,
            'priority': priority,
            'components': {
                'prediction_risk': float(prediction_risk),
                'trend_risk': float(trend_risk),
                'confidence_risk': float(confidence_risk),
                'environmental_risk': float(env_risk)
            },
            'prediction': float(prediction),
            'threshold': float(threshold),
            'deviation_ratio': float(deviation_ratio),
            'time_to_threshold': time_to_threshold,
            'warning_level': self._get_warning_level(severity, time_to_threshold)
        }

    def _evaluate_prediction_risk(self, prediction: float, threshold: float) -> float:
        """评估预测值风险"""
        if threshold == 0:
            return 0.5

        deviation = abs(prediction - threshold) / abs(threshold)

        if deviation < 0.1:
            return deviation * 2
        elif deviation < 0.3:
            return 0.2 + (deviation - 0.1) * 2
        elif deviation < 0.5:
            return 0.6 + (deviation - 0.3) * 1.5
        else:
            return min(0.9 + (deviation - 0.5) * 0.2, 1.0)

    def _evaluate_trend_risk(self, trend: Dict[str, Any], threshold: float) -> float:
        """评估趋势风险"""
        slope = abs(trend.get('slope', 0))
        direction = trend.get('trend_direction', 'stable')

        if direction == 'stable':
            return 0.1

        risk = min(slope * 10, 0.8)

        if direction == 'increasing' and threshold > 0:
            risk = min(risk * 1.5, 1.0)
        elif direction == 'decreasing' and threshold < 0:
            risk = min(risk * 1.5, 1.0)

        return risk

    def _evaluate_confidence_risk(self, confidence: float) -> float:
        """评估置信度风险"""
        return 1.0 - confidence

    def _evaluate_environmental_risk(self, env_factors: Dict[str, float]) -> float:
        """评估环境因素风险"""
        risk = 0.0

        if 'temperature' in env_factors:
            temp = env_factors['temperature']
            if temp > 35 or temp < 10:
                risk += 0.3
            elif temp > 30 or temp < 15:
                risk += 0.15

        if 'humidity' in env_factors:
            humidity = env_factors['humidity']
            if humidity > 85 or humidity < 30:
                risk += 0.3
            elif humidity > 75 or humidity < 40:
                risk += 0.15

        return min(risk, 1.0)

    def _estimate_time_to_threshold(self, current: float, slope: float, threshold: float) -> Optional[float]:
        """估计到达阈值的时间（步数）"""
        if slope == 0:
            return None

        if (slope > 0 and current >= threshold) or (slope < 0 and current <= threshold):
            return 0

        if (slope > 0 and threshold < current) or (slope < 0 and threshold > current):
            return None

        distance = abs(threshold - current)
        steps = distance / abs(slope)

        return float(steps)

    def _determine_overall_severity(self, risk_score: float, deviation: float, time_to_threshold: Optional[float]) -> str:
        """确定整体严重程度"""
        if risk_score > 0.8 or deviation > 0.8:
            return 'CRITICAL'
        elif risk_score > 0.6 or deviation > 0.5:
            if time_to_threshold and time_to_threshold < 5:
                return 'CRITICAL'
            return 'ERROR'
        elif risk_score > 0.4 or deviation > 0.3:
            return 'WARN'
        else:
            return 'INFO'

    def _calculate_priority(self, severity: str, time_to_threshold: Optional[float]) -> int:
        """计算预警优先级"""
        base_priority = self.severity_levels.get(severity, 0) * 10

        if time_to_threshold is not None:
            if time_to_threshold < 3:
                base_priority += 5
            elif time_to_threshold < 10:
                base_priority += 2

        return base_priority

    def _get_warning_level(self, severity: str, time_to_threshold: Optional[float]) -> str:
        """获取预警级别"""
        if severity == 'CRITICAL' or (time_to_threshold and time_to_threshold < 3):
            return 'IMMEDIATE'
        elif severity == 'ERROR' or (time_to_threshold and time_to_threshold < 5):
            return 'URGENT'
        elif severity == 'WARN':
            return 'NORMAL'
        else:
            return 'LOW'

    def batch_assess_risk(
        self,
        predictions: List[float],
        current_value: float,
        threshold: float,
        trend: Dict[str, Any],
        confidence: float,
        environmental_factors: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量风险评估

        Args:
            predictions (list): 预测值列表
            current_value (float): 当前值
            threshold (float): 阈值
            trend (dict): 趋势分析结果
            confidence (float): 置信度
            environmental_factors (dict): 环境因素

        Returns:
            list: 每个预测点的风险评估结果
        """
        results = []
        for i, pred in enumerate(predictions):
            assessment = self.assess_risk(pred, current_value, threshold, trend, confidence, environmental_factors)
            assessment['horizon_step'] = i + 1
            results.append(assessment)

        return results


class PredictionCache:
    """
    预测结果缓存
    使用内存缓存存储近期预测结果，避免重复计算
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        """
        初始化预测缓存

        Args:
            max_size (int): 最大缓存条目数
            ttl_seconds (int): 缓存过期时间（秒）
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache = {}
        self._timestamps = {}

    def _generate_key(self, device_id: str, metric: str, horizon: int, method: str) -> str:
        """
        生成缓存键

        Args:
            device_id (str): 设备ID
            metric (str): 指标名称
            horizon (int): 预测步数
            method (str): 预测方法

        Returns:
            str: 缓存键
        """
        return f"{device_id}:{metric}:{horizon}:{method}"

    def _is_expired(self, key: str) -> bool:
        """
        检查缓存是否过期

        Args:
            key (str): 缓存键

        Returns:
            bool: 是否过期
        """
        if key not in self._timestamps:
            return True

        elapsed = (datetime.now() - self._timestamps[key]).total_seconds()
        return elapsed > self.ttl_seconds

    def get(self, device_id: str, metric: str, horizon: int, method: str = 'default') -> Optional[Dict[str, Any]]:
        """
        获取缓存的预测结果

        Args:
            device_id (str): 设备ID
            metric (str): 指标名称
            horizon (int): 预测步数
            method (str): 预测方法

        Returns:
            dict: 缓存的预测结果，如果不存在或已过期返回None
        """
        key = self._generate_key(device_id, metric, horizon, method)

        if key not in self._cache or self._is_expired(key):
            return None

        return self._cache[key]

    def set(self, device_id: str, metric: str, horizon: int, method: str, result: Dict[str, Any]) -> None:
        """
        缓存预测结果

        Args:
            device_id (str): 设备ID
            metric (str): 指标名称
            horizon (int): 预测步数
            method (str): 预测方法
            result (dict): 预测结果
        """
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]

        key = self._generate_key(device_id, metric, horizon, method)
        self._cache[key] = result
        self._timestamps[key] = datetime.now()

    def invalidate(self, device_id: Optional[str] = None, metric: Optional[str] = None) -> int:
        """
        使缓存失效

        Args:
            device_id (str): 设备ID，如果为None则删除所有设备的相关缓存
            metric (str): 指标名称，如果为None则删除该设备所有指标的缓存

        Returns:
            int: 删除的缓存条目数
        """
        if device_id is None:
            count = len(self._cache)
            self._cache.clear()
            self._timestamps.clear()
            return count

        keys_to_delete = []
        for key in self._cache.keys():
            parts = key.split(':')
            if len(parts) >= 2:
                key_device_id = parts[0]
                key_metric = parts[1] if len(parts) > 1 else None

                if key_device_id == device_id:
                    if metric is None or key_metric == metric:
                        keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._cache[key]
            del self._timestamps[key]

        return len(keys_to_delete)

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            dict: 缓存统计信息
        """
        total_entries = len(self._cache)
        expired_entries = sum(1 for key in self._cache.keys() if self._is_expired(key))

        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'valid_entries': total_entries - expired_entries,
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds,
            'utilization': total_entries / self.max_size if self.max_size > 0 else 0
        }


class BatchPredictionProcessor:
    """
    批量预测处理器
    同时处理多个设备的多个指标，减少数据库查询次数
    """

    def __init__(self, use_cache: bool = True, cache_ttl: int = 300):
        """
        初始化批量预测处理器

        Args:
            use_cache (bool): 是否使用缓存
            cache_ttl (int): 缓存过期时间（秒）
        """
        self.use_cache = use_cache
        self.cache = PredictionCache(max_size=1000, ttl_seconds=cache_ttl) if use_cache else None
        self.prediction_model = PredictionModel()
        self.exponential_smoothing_model = ExponentialSmoothingModel()

    def process_batch_predictions(
        self,
        device_data: List[Dict[str, Any]],
        horizon: int = 5,
        methods: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        批量处理多个设备的预测

        Args:
            device_data (list): 设备数据列表，格式为 [{
                'device_id': 'xxx',
                'metric': 'signal_strength',
                'values': [1.0, 2.0, 3.0, ...],
                'environmental_data': [{'ambient_temperature': 25.0, 'humidity': 60.0}, ...] (可选)
            }]
            horizon (int): 预测步数
            methods (list): 预测方法列表，可用值: 'trend', 'exponential_smoothing', 'fusion'

        Returns:
            dict: 批量预测结果
        """
        if methods is None:
            methods = ['trend', 'exponential_smoothing']

        results = []
        cache_hits = 0
        cache_misses = 0

        for device in device_data:
            device_id = device.get('device_id')
            metric = device.get('metric')
            values = device.get('values', [])
            environmental_data = device.get('environmental_data', [])

            if not device_id or not metric or not values:
                continue

            device_results = {
                'device_id': device_id,
                'metric': metric,
                'predictions': {}
            }

            for method in methods:
                if self.use_cache and self.cache:
                    cached = self.cache.get(device_id, metric, horizon, method)
                    if cached:
                        device_results['predictions'][method] = cached
                        device_results['predictions'][method]['from_cache'] = True
                        cache_hits += 1
                        continue
                    cache_misses += 1

                if method == 'trend':
                    prediction = self.prediction_model.predict_with_trend(values, horizon)
                    if environmental_data:
                        prediction = self.prediction_model.predict_with_environmental_factors(
                            values, environmental_data, horizon
                        )
                elif method == 'exponential_smoothing':
                    prediction = self.exponential_smoothing_model.predict(values, horizon, method='auto')
                elif method == 'fusion':
                    prediction = self.exponential_smoothing_model.model_fusion(values, horizon)
                else:
                    prediction = self.prediction_model.predict_with_trend(values, horizon)

                prediction['from_cache'] = False
                device_results['predictions'][method] = prediction

                if self.use_cache and self.cache:
                    self.cache.set(device_id, metric, horizon, method, prediction)

            results.append(device_results)

        return {
            'results': results,
            'summary': {
                'total_devices': len(results),
                'methods_used': methods,
                'cache_hits': cache_hits,
                'cache_misses': cache_misses,
                'cache_hit_rate': cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }

    def incremental_prediction(
        self,
        device_id: str,
        metric: str,
        new_value: float,
        historical_values: List[float],
        horizon: int = 5
    ) -> Dict[str, Any]:
        """
        增量预测 - 只对数据发生变化的设备重新预测

        Args:
            device_id (str): 设备ID
            metric (str): 指标名称
            new_value (float): 新数据点
            historical_values (list): 历史数据（不包括新值）
            horizon (int): 预测步数

        Returns:
            dict: 增量预测结果
        """
        updated_values = historical_values + [new_value]

        if self.use_cache and self.cache:
            self.cache.invalidate(device_id, metric)

        prediction = self.prediction_model.predict_with_trend(updated_values, horizon)

        if self.use_cache and self.cache:
            self.cache.set(device_id, metric, horizon, 'trend', prediction)

        return {
            'device_id': device_id,
            'metric': metric,
            'new_value': new_value,
            'prediction': prediction,
            'incremental': True,
            'cache_invalidated': True
        }

    def get_batch_predictions_by_device(
        self,
        device_id: str,
        metrics: List[str],
        historical_data: Dict[str, List[float]],
        horizon: int = 5
    ) -> Dict[str, Any]:
        """
        获取指定设备的所有指标预测

        Args:
            device_id (str): 设备ID
            metrics (list): 指标列表
            historical_data (dict): 历史数据，格式为 {metric: [values]}
            horizon (int): 预测步数

        Returns:
            dict: 预测结果
        """
        device_data = []
        for metric in metrics:
            if metric in historical_data and historical_data[metric]:
                device_data.append({
                    'device_id': device_id,
                    'metric': metric,
                    'values': historical_data[metric]
                })

        batch_result = self.process_batch_predictions(device_data, horizon)

        return {
            'device_id': device_id,
            'predictions': batch_result['results'],
            'summary': batch_result['summary']
        }

    def clear_cache(self, device_id: Optional[str] = None, metric: Optional[str] = None) -> int:
        """
        清除缓存

        Args:
            device_id (str): 设备ID
            metric (str): 指标名称

        Returns:
            int: 清除的缓存条目数
        """
        if not self.cache:
            return 0
        return self.cache.invalidate(device_id, metric)

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计

        Returns:
            dict: 缓存统计信息
        """
        if not self.cache:
            return {'cache_enabled': False}
        return {
            'cache_enabled': True,
            **self.cache.get_cache_stats()
        }
