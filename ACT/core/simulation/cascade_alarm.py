from typing import Dict, Any, List
from datetime import datetime
from enum import Enum
from .exception_handler import AlarmCascadeError, ExceptionHandler


class AlarmLevel(Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class Severity(Enum):
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CascadeAlarmEngine:
    """级联告警传播引擎"""

    MAX_PROPAGATION_DEPTH = 3

    ALARM_PROPAGATION_TREE = {
        'L1_device_alarm': {
            'level': AlarmLevel.L1,
            'trigger': 'device_anomaly',
            'propagation': ['L2_link_alarm', 'L2_regional_alarm']
        },
        'L2_link_alarm': {
            'level': AlarmLevel.L2,
            'trigger': 'device_chain_failure',
            'propagation': ['L3_system_alarm']
        },
        'L3_system_alarm': {
            'level': AlarmLevel.L3,
            'trigger': 'multiple_region_failure',
            'propagation': []
        }
    }

    DEVICE_CHAINS = {
        'VHF-001': ['VHF-001', 'ILS-001', 'DME-001'],
        'VHF-002': ['VHF-002', 'ILS-002', 'DME-002'],
        'VHF-003': ['VHF-003', 'VOR-001', 'DME-001'],
        'ILS-001': ['ILS-001', 'DME-001'],
        'ILS-002': ['ILS-002', 'DME-002'],
        'VOR-001': ['VOR-001', 'DME-001'],
        'VOR-002': ['VOR-002', 'DME-002'],
    }

    REGION_DEVICES = {
        'runway_A': ['ILS-001', 'DME-001', 'VOR-001'],
        'runway_B': ['ILS-002', 'DME-002', 'VOR-002'],
        'tower': ['VHF-001', 'VHF-002', 'VHF-003'],
        'navigation_station': ['HF-001', 'HF-002', 'HF-003'],
    }

    def __init__(self):
        self.alarm_history: List[Dict[str, Any]] = []
        self.active_alarms: Dict[str, Dict[str, Any]] = {}
        self.exception_handler = ExceptionHandler()
        self.propagation_depth: Dict[str, int] = {}

    def trigger_device_alarm(self, device_id: str, alarm_type: str, trigger_value: Any) -> Dict[str, Any]:
        """
        触发设备级告警（L1）
        异常处理策略：级联告警死循环时设置传播深度上限（≤3层）
        :param device_id: 设备ID
        :param alarm_type: 告警类型
        :param trigger_value: 触发值
        :return: 告警对象
        """
        alarm = self._create_alarm(
            device_id=device_id,
            level=AlarmLevel.L1,
            severity=Severity.WARN,
            message=f'{device_id} {alarm_type} detected',
            trigger_value=trigger_value,
            alarm_type='device_alarm'
        )

        self.propagation_depth[alarm['alarm_id']] = 1

        if self.should_propagate_to_link_level(device_id, alarm_type):
            self.trigger_link_alarm(device_id, alarm)

        return alarm

    def trigger_link_alarm(self, source_device: str, source_alarm: Dict[str, Any]) -> Dict[str, Any]:
        """
        触发链路级告警（L2）
        异常处理策略：检查传播深度上限，防止级联告警死循环
        :param source_device: 源设备ID
        :param source_alarm: 源告警对象
        :return: 链路告警对象
        """
        source_depth = self.propagation_depth.get(source_alarm['alarm_id'], 0)
        
        if source_depth >= self.MAX_PROPAGATION_DEPTH:
            cascade_error = AlarmCascadeError(
                code='MAX_DEPTH_REACHED',
                message=f'告警传播深度达到上限: {source_depth} >= {self.MAX_PROPAGATION_DEPTH}'
            )
            self.exception_handler.log_error('cascade_error', cascade_error)
            self.exception_handler.handle_cascade_error(cascade_error)
            return {}

        link_devices = self.get_device_chain(source_device)
        
        if not link_devices:
            return {}

        link_health = self.calculate_link_health(link_devices)

        if link_health < 0.7:
            link_alarm = self._create_alarm(
                device_id=f'LINK-{source_device}',
                level=AlarmLevel.L2,
                severity=Severity.ERROR,
                message=f'Link degradation due to {source_device} failure',
                affected_devices=link_devices,
                propagation_source=source_alarm['alarm_id'],
                alarm_type='link_alarm',
                link_health=link_health
            )

            self.propagation_depth[link_alarm['alarm_id']] = source_depth + 1

            if self.should_propagate_to_system_level(link_alarm):
                self.trigger_system_alarm(link_alarm)

            return link_alarm

        return {}

    def trigger_system_alarm(self, source_link_alarm: Dict[str, Any]) -> Dict[str, Any]:
        """
        触发系统级告警（L3）
        异常处理策略：检查传播深度上限，防止级联告警死循环
        :param source_link_alarm: 源链路告警对象
        :return: 系统告警对象
        """
        source_depth = self.propagation_depth.get(source_link_alarm['alarm_id'], 0)
        
        if source_depth >= self.MAX_PROPAGATION_DEPTH:
            cascade_error = AlarmCascadeError(
                code='MAX_DEPTH_REACHED',
                message=f'告警传播深度达到上限: {source_depth} >= {self.MAX_PROPAGATION_DEPTH}'
            )
            self.exception_handler.log_error('cascade_error', cascade_error)
            self.exception_handler.handle_cascade_error(cascade_error)
            return {}

        affected_regions = self.get_alarm_affected_regions(source_link_alarm)

        system_alarm = self._create_alarm(
            alarm_id=f'SYS-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            level=AlarmLevel.L3,
            severity=Severity.CRITICAL,
            message=f'System-wide alert: Multiple region failure',
            affected_regions=affected_regions,
            propagation_source=source_link_alarm['alarm_id'],
            alarm_type='system_alarm',
            recommended_action='Emergency maintenance required'
        )

        self.propagation_depth[system_alarm['alarm_id']] = source_depth + 1

        return system_alarm

    def _create_alarm(self, **kwargs) -> Dict[str, Any]:
        """创建告警对象"""
        alarm = {
            'alarm_id': kwargs.get('alarm_id', f'ALM-{datetime.now().strftime("%Y%m%d%H%M%S")}'),
            'level': kwargs['level'].value,
            'type': kwargs.get('alarm_type', 'device_alarm'),
            'device_id': kwargs.get('device_id', ''),
            'trigger_time': datetime.now().isoformat(),
            'severity': kwargs['severity'].value,
            'message': kwargs['message'],
            'trigger_value': kwargs.get('trigger_value'),
            'affected_devices': kwargs.get('affected_devices', []),
            'affected_regions': kwargs.get('affected_regions', []),
            'propagation_source': kwargs.get('propagation_source'),
            'link_health': kwargs.get('link_health'),
            'recommended_action': kwargs.get('recommended_action')
        }

        self.alarm_history.append(alarm)
        self.active_alarms[alarm['alarm_id']] = alarm

        return alarm

    def should_propagate_to_link_level(self, device_id: str, alarm_type: str) -> bool:
        """检查是否应传播到链路级"""
        critical_types = ['overheat', 'signal_loss', 'power_fluctuation']
        return alarm_type in critical_types and device_id in self.DEVICE_CHAINS

    def should_propagate_to_system_level(self, link_alarm: Dict[str, Any]) -> bool:
        """检查是否应传播到系统级"""
        affected_devices = link_alarm.get('affected_devices', [])
        return len(affected_devices) >= 3

    def get_device_chain(self, device_id: str) -> List[str]:
        """获取设备链路"""
        return self.DEVICE_CHAINS.get(device_id, [])

    def calculate_link_health(self, link_devices: List[str]) -> float:
        """计算链路健康度"""
        if not link_devices:
            return 1.0

        faulty_count = 0
        for device_id in link_devices:
            for alarm in self.alarm_history:
                if alarm['device_id'] == device_id and alarm['level'] == AlarmLevel.L1.value:
                    faulty_count += 1
                    break

        return 1.0 - (faulty_count / len(link_devices)) * 0.5

    def get_alarm_affected_regions(self, alarm: Dict[str, Any]) -> List[str]:
        """获取告警影响区域"""
        affected_regions = []
        affected_devices = alarm.get('affected_devices', [])

        for region_id, devices in self.REGION_DEVICES.items():
            for device_id in affected_devices:
                if device_id in devices and region_id not in affected_regions:
                    affected_regions.append(region_id)

        return affected_regions

    def get_alarm_propagation_chain(self, source_alarm_id: str) -> List[Dict[str, Any]]:
        """获取告警传播链"""
        chain = []
        current_alarm_id = source_alarm_id

        while current_alarm_id:
            alarm = self.active_alarms.get(current_alarm_id)
            if not alarm:
                break

            chain.append(alarm)
            current_alarm_id = None

            for next_alarm in self.alarm_history:
                if next_alarm.get('propagation_source') == alarm['alarm_id']:
                    current_alarm_id = next_alarm['alarm_id']
                    break

        return chain

    def get_alarm_correlation_matrix(self) -> Dict[str, float]:
        """获取告警关联矩阵"""
        l1_count = sum(1 for a in self.alarm_history if a['level'] == AlarmLevel.L1.value)
        l2_count = sum(1 for a in self.alarm_history if a['level'] == AlarmLevel.L2.value)
        l3_count = sum(1 for a in self.alarm_history if a['level'] == AlarmLevel.L3.value)

        l1_l2_correlation = l2_count / max(l1_count, 1) if l1_count > 0 else 0.0
        l2_l3_correlation = l3_count / max(l2_count, 1) if l2_count > 0 else 0.0

        return {
            'L1_L2_correlation': round(l1_l2_correlation, 2),
            'L2_L3_correlation': round(l2_l3_correlation, 2),
            'cascade_delay_seconds': 300,
            'total_alarms': len(self.alarm_history),
            'L1_count': l1_count,
            'L2_count': l2_count,
            'L3_count': l3_count
        }

    def clear_alarm(self, alarm_id: str):
        """清除告警"""
        if alarm_id in self.active_alarms:
            del self.active_alarms[alarm_id]

    def get_active_alarms(self) -> List[Dict[str, Any]]:
        """获取所有活动告警"""
        return list(self.active_alarms.values())
