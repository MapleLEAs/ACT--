from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import deque


class RealtimeDataLayer:
    """
    L1 实时数据层：实时设备状态推送
    """

    def __init__(self):
        self.realtime_cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = 60

    def push_realtime_status(self, device_id: str, current_status: Dict[str, Any]):
        """
        推送实时状态
        :param device_id: 设备ID
        :param current_status: 当前状态
        """
        self.realtime_cache[device_id] = {
            'layer': 'L1',
            'type': 'realtime_update',
            'device_id': device_id,
            'timestamp': datetime.now().isoformat(),
            'status': current_status,
            'ttl': self.ttl_seconds
        }

    def get_realtime_status(self, device_id: str) -> Dict[str, Any]:
        """
        获取实时状态
        :param device_id: 设备ID
        :return: 实时状态
        """
        return self.realtime_cache.get(device_id, {})

    def get_all_realtime_status(self) -> Dict[str, Any]:
        """获取所有设备实时状态"""
        return self.realtime_cache.copy()

    def cleanup_expired(self):
        """清理过期数据"""
        now = datetime.now()
        expired_keys = []
        
        for device_id, data in self.realtime_cache.items():
            timestamp = datetime.fromisoformat(data['timestamp'])
            if (now - timestamp).total_seconds() > self.ttl_seconds:
                expired_keys.append(device_id)
        
        for key in expired_keys:
            del self.realtime_cache[key]


class TimeSeriesDataLayer:
    """
    L2 时序数据层：历史数据持久化
    """

    def __init__(self):
        self.time_series_store: Dict[str, deque] = {}
        self.retention_days = 90
        self.max_points_per_device = 90 * 24 * 12

    def store_time_series_data(self, device_id: str, data_points: List[Dict[str, Any]]):
        """
        存储时序数据
        :param device_id: 设备ID
        :param data_points: 数据点列表
        """
        if device_id not in self.time_series_store:
            self.time_series_store[device_id] = deque(maxlen=self.max_points_per_device)
        
        for point in data_points:
            self.time_series_store[device_id].append({
                'layer': 'L2',
                'device_id': device_id,
                **point,
                'storage_policy': 'compressed'
            })

    def get_time_series_data(self, device_id: str, start_time: datetime = None,
                              end_time: datetime = None) -> List[Dict[str, Any]]:
        """
        获取时序数据
        :param device_id: 设备ID
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return: 数据点列表
        """
        if device_id not in self.time_series_store:
            return []
        
        data = list(self.time_series_store[device_id])
        
        if start_time:
            data = [d for d in data if d.get('timestamp') and datetime.fromisoformat(d['timestamp']) >= start_time]
        
        if end_time:
            data = [d for d in data if d.get('timestamp') and datetime.fromisoformat(d['timestamp']) <= end_time]
        
        return data

    def get_device_data_summary(self, device_id: str) -> Dict[str, Any]:
        """
        获取设备数据摘要
        :param device_id: 设备ID
        :return: 摘要信息
        """
        if device_id not in self.time_series_store:
            return {'device_id': device_id, 'data_points': 0}
        
        points = list(self.time_series_store[device_id])
        if not points:
            return {'device_id': device_id, 'data_points': 0}
        
        return {
            'device_id': device_id,
            'data_points': len(points),
            'retention_days': self.retention_days,
            'first_timestamp': points[0].get('timestamp'),
            'last_timestamp': points[-1].get('timestamp')
        }


class InsightDataLayer:
    """
    L3 洞察数据层：AI分析、预测、告警聚合
    """

    def __init__(self):
        self.insights_store: Dict[str, List[Dict[str, Any]]] = {}

    def generate_insights(self, device_id: str, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成洞察数据
        :param device_id: 设备ID
        :param historical_data: 历史数据
        :return: 洞察结果
        """
        anomalies = self._detect_anomalies(historical_data)
        prediction = self._predict_future_state(historical_data)
        alarm_correlation = self._correlate_alarms(historical_data)

        insight = {
            'layer': 'L3',
            'device_id': device_id,
            'timestamp': datetime.now().isoformat(),
            'insights': {
                'anomaly_detection': anomalies,
                'prediction': prediction,
                'alarm_correlation': alarm_correlation
            }
        }

        if device_id not in self.insights_store:
            self.insights_store[device_id] = []
        self.insights_store[device_id].append(insight)

        return insight

    def get_insights(self, device_id: str) -> List[Dict[str, Any]]:
        """
        获取设备洞察数据
        :param device_id: 设备ID
        :return: 洞察列表
        """
        return self.insights_store.get(device_id, [])

    def _detect_anomalies(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检测异常"""
        if not historical_data:
            return {'anomalies': [], 'score': 100.0}
        
        values = [d.get('value', 0) for d in historical_data if d.get('value') is not None]
        if len(values) < 3:
            return {'anomalies': [], 'score': 100.0}
        
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        
        anomalies = []
        for d in historical_data:
            value = d.get('value')
            if value is not None and std > 0:
                z_score = abs(value - mean) / std
                if z_score > 3:
                    anomalies.append({
                        'timestamp': d.get('timestamp'),
                        'value': value,
                        'z_score': round(z_score, 2),
                        'type': 'outlier'
                    })
        
        return {
            'anomalies': anomalies,
            'score': round(100 - len(anomalies) * 10, 2)
        }

    def _predict_future_state(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """预测未来状态"""
        if not historical_data:
            return {'predicted_value': None, 'confidence': 0.0}
        
        values = [d.get('value', 0) for d in historical_data if d.get('value') is not None]
        if len(values) < 3:
            return {'predicted_value': None, 'confidence': 0.0}
        
        recent = values[-24:]
        predicted_value = sum(recent) / len(recent)
        confidence = min(0.95, len(recent) / 24)
        
        return {
            'predicted_value': round(predicted_value, 2),
            'prediction_time': (datetime.now() + timedelta(hours=24)).isoformat(),
            'confidence': round(confidence, 2)
        }

    def _correlate_alarms(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """告警关联分析"""
        alarm_count = sum(1 for d in historical_data if d.get('alarm') is True)
        return {
            'total_alarms': alarm_count,
            'alarm_rate': round(alarm_count / max(len(historical_data), 1), 4)
        }


class DataLayerManager:
    """数据分层架构管理器"""

    def __init__(self):
        self.l1 = RealtimeDataLayer()
        self.l2 = TimeSeriesDataLayer()
        self.l3 = InsightDataLayer()

    def ingest_data(self, device_id: str, data: Dict[str, Any]):
        """
        数据入口：将数据写入三层架构
        :param device_id: 设备ID
        :param data: 数据
        """
        self.l1.push_realtime_status(device_id, data)
        
        self.l2.store_time_series_data(device_id, [{
            'timestamp': datetime.now().isoformat(),
            **data
        }])
        
        historical_data = self.l2.get_time_series_data(device_id)
        self.l3.generate_insights(device_id, historical_data)

    def get_data_layer(self, layer: str):
        """
        获取指定数据层
        :param layer: 层名称（L1/L2/L3）
        :return: 数据层实例
        """
        if layer == 'L1':
            return self.l1
        elif layer == 'L2':
            return self.l2
        elif layer == 'L3':
            return self.l3
        return None

    def get_data_flow_summary(self) -> Dict[str, Any]:
        """获取数据流转摘要"""
        return {
            'layers': {
                'L1': {
                    'name': '实时层',
                    'description': 'WebSocket推送，TTL 60秒',
                    'device_count': len(self.l1.get_all_realtime_status())
                },
                'L2': {
                    'name': '时序层',
                    'description': '数据库持久化，保留90天',
                    'device_count': len(self.l2.time_series_store)
                },
                'L3': {
                    'name': '洞察层',
                    'description': 'AI分析、预测、告警聚合',
                    'device_count': len(self.l3.insights_store)
                }
            }
        }
