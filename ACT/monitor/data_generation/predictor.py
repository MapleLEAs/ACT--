import numpy as np
from scipy import stats
from typing import Dict, List


class PredictionModel:
    """
    预测模型：基于历史数据预测未来状态
    """

    def __init__(self):
        self.historical_window = 12

    def predict(self, historical_data: List[Dict]) -> Dict:
        """
        预测未来24小时状态
        """
        if len(historical_data) < self.historical_window:
            return {'status': 'insufficient_data'}

        temps = [d['temperature'] for d in historical_data]
        trend = np.polyfit(range(len(temps)), temps, 1)[0]

        std_dev = np.std(temps)

        predicted_temp = temps[-1] + trend * 24

        confidence_interval = {
            'lower': predicted_temp - 2 * std_dev,
            'upper': predicted_temp + 2 * std_dev,
            'confidence_level': 0.95
        }

        return {
            'predicted_temperature': round(predicted_temp, 2),
            'trend': 'rising' if trend > 0 else 'stable',
            'trend_slope': round(trend, 4),
            'confidence_interval': confidence_interval,
            'std_deviation': round(std_dev, 2)
        }