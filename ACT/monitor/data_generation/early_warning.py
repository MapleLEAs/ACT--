from typing import Dict, List


class EarlyWarningModel:
    """
    预警模型：提前发出预警信号
    """

    def __init__(self):
        self.warning_thresholds = {
            'temperature_rising': 0.05,
            'health_declining': 0.7,
            'signal_weakening': -80
        }

    def check_early_warning(self, prediction: Dict, current_state: Dict) -> Dict:
        """
        检查是否需要提前预警
        """
        warnings = []

        if prediction.get('trend_slope', 0) > self.warning_thresholds['temperature_rising']:
            warnings.append({
                'type': 'TEMPERATURE_RISING',
                'severity': 'WARN',
                'message': '温度上升趋势明显，建议72小时内巡检',
                'predicted_time': '24小时后'
            })

        if current_state.get('health', 1.0) < self.warning_thresholds['health_declining']:
            warnings.append({
                'type': 'HEALTH_DECLINING',
                'severity': 'ERROR',
                'message': '设备健康度下降明显，建议48小时内维护',
                'predicted_time': '12小时后'
            })

        if current_state.get('signal_strength', -60) < self.warning_thresholds['signal_weakening']:
            warnings.append({
                'type': 'SIGNAL_WEAKENING',
                'severity': 'WARN',
                'message': '信号强度下降，建议检查通信链路',
                'predicted_time': '6小时后'
            })

        return {
            'has_warning': len(warnings) > 0,
            'warnings': warnings,
            'recommended_action': self._generate_action_recommendation(warnings)
        }

    def _generate_action_recommendation(self, warnings: List[Dict]) -> str:
        """生成行动建议"""
        if not warnings:
            return "设备状态正常，无需特殊关注"

        severities = [w['severity'] for w in warnings]
        if 'ERROR' in severities:
            return "建议立即安排维护人员检查"
        elif 'WARN' in severities:
            return "建议安排巡检计划"
        else:
            return "建议持续监控"