from typing import Dict, Any, List
from datetime import datetime
import numpy as np
from .exception_handler import DataQualityError, ExceptionHandler


class DataQualityEngine:
    """数据质量检测引擎"""

    REQUIRED_FIELDS = ['device_id', 'timestamp', 'temperature', 'status']
    QUALITY_THRESHOLD = 60.0

    def __init__(self):
        self.quality_reports: List[Dict[str, Any]] = []
        self.exception_handler = ExceptionHandler()

    def validate_data_quality(self, data_stream: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        四维数据质量检测
        异常处理策略：数据质量评分过低时阻断数据入库，触发人工审核流程
        :param data_stream: 数据流
        :return: 质量报告
        """
        quality_report = {
            'completeness': self.check_completeness(data_stream),
            'consistency': self.check_consistency(data_stream),
            'timeliness': self.check_timeliness(data_stream),
            'accuracy': self.check_accuracy(data_stream)
        }

        quality_report['overall_score'] = self._calculate_overall_score(quality_report)

        overall_score = quality_report['overall_score']
        is_blocked = overall_score < self.QUALITY_THRESHOLD

        if is_blocked:
            quality_error = DataQualityError(
                code='QUALITY_TOO_LOW',
                message=f'数据质量评分过低: {overall_score} < {self.QUALITY_THRESHOLD}',
                details={
                    'overall_score': overall_score,
                    'threshold': self.QUALITY_THRESHOLD,
                    'action': 'blocked'
                }
            )
            self.exception_handler.log_error('data_quality', quality_error)
            self.exception_handler.handle_data_quality(quality_error)

        report_entry = {
            'quality_report_id': f'QR-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            'generation_time': datetime.now().isoformat(),
            'status': 'blocked' if is_blocked else 'passed',
            **quality_report
        }

        self.quality_reports.append(report_entry)

        return report_entry

    def check_completeness(self, data_stream: List[Dict[str, Any]]) -> Dict[str, Any]:
        """完整性检测：缺失值检测"""
        missing_fields = []
        
        for data_point in data_stream:
            for field in self.REQUIRED_FIELDS:
                if field not in data_point or data_point[field] is None:
                    missing_fields.append({
                        'device_id': data_point.get('device_id'),
                        'field': field,
                        'type': 'missing_value'
                    })
        
        score = 100 - (len(missing_fields) / max(len(data_stream) * len(self.REQUIRED_FIELDS), 1)) * 100
        
        return {
            'score': round(score, 2),
            'issues': missing_fields[:10]
        }

    def check_consistency(self, data_stream: List[Dict[str, Any]]) -> Dict[str, Any]:
        """一致性检测：数据格式和类型检查"""
        consistency_issues = []
        
        valid_statuses = ['NORMAL', 'DEGRADED', 'FAULT', 'OFFLINE']
        
        for data_point in data_stream:
            status = data_point.get('status')
            if status and status not in valid_statuses:
                consistency_issues.append({
                    'device_id': data_point.get('device_id'),
                    'field': 'status',
                    'value': status,
                    'type': 'invalid_status'
                })
            
            temperature = data_point.get('temperature')
            if temperature is not None:
                if not isinstance(temperature, (int, float)):
                    consistency_issues.append({
                        'device_id': data_point.get('device_id'),
                        'field': 'temperature',
                        'type': 'type_mismatch'
                    })
        
        score = 100 - (len(consistency_issues) / max(len(data_stream), 1)) * 5
        
        return {
            'score': round(score, 2),
            'issues': consistency_issues[:10]
        }

    def check_timeliness(self, data_stream: List[Dict[str, Any]]) -> Dict[str, Any]:
        """时效性检测：时间断点检测"""
        gaps = []
        
        sorted_data = sorted(data_stream, key=lambda x: x.get('timestamp', ''))
        
        for i in range(1, len(sorted_data)):
            prev_time = datetime.fromisoformat(sorted_data[i-1]['timestamp'])
            curr_time = datetime.fromisoformat(sorted_data[i]['timestamp'])
            gap_duration = (curr_time - prev_time).total_seconds() / 60
            
            if gap_duration > 10:
                gaps.append({
                    'start_time': prev_time.isoformat(),
                    'end_time': curr_time.isoformat(),
                    'gap_minutes': round(gap_duration, 2),
                    'type': 'time_gap'
                })
        
        score = 100 - len(gaps) * 5
        
        return {
            'score': round(score, 2),
            'issues': gaps[:10]
        }

    def check_accuracy(self, data_stream: List[Dict[str, Any]]) -> Dict[str, Any]:
        """准确性检测：异常值检测"""
        anomalies = []
        
        for i, data_point in enumerate(data_stream):
            temperature = data_point.get('temperature')
            if temperature is not None:
                if temperature < -20 or temperature > 100:
                    anomalies.append({
                        'device_id': data_point.get('device_id'),
                        'timestamp': data_point.get('timestamp'),
                        'value': temperature,
                        'type': 'physical_anomaly'
                    })
                
                if i > 0:
                    prev_temp = data_stream[i-1].get('temperature')
                    if prev_temp is not None:
                        change_rate = abs(temperature - prev_temp) / 5
                        if change_rate > 2.0:
                            anomalies.append({
                                'device_id': data_point.get('device_id'),
                                'timestamp': data_point.get('timestamp'),
                                'change_rate': round(change_rate, 2),
                                'type': 'change_rate_anomaly'
                            })
        
        score = 100 - len(anomalies) * 2
        
        return {
            'score': round(score, 2),
            'issues': anomalies[:10]
        }

    def _calculate_overall_score(self, quality_report: Dict[str, Any]) -> float:
        """计算总体质量分数"""
        weights = {
            'completeness': 0.3,
            'consistency': 0.2,
            'timeliness': 0.25,
            'accuracy': 0.25
        }
        
        total = 0.0
        for key, weight in weights.items():
            total += quality_report[key]['score'] * weight
        
        return round(total, 2)

    def get_quality_report(self, report_id: str = None) -> Dict[str, Any]:
        """
        获取质量报告
        :param report_id: 报告ID，None表示最新报告
        :return: 质量报告
        """
        if not self.quality_reports:
            return {}
        
        if report_id:
            for report in self.quality_reports:
                if report.get('quality_report_id') == report_id:
                    return report
            return {}
        
        return self.quality_reports[-1]

    def get_recent_reports(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近的质量报告
        :param count: 报告数量
        :return: 报告列表
        """
        return self.quality_reports[-count:]
