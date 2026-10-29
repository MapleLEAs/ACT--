from enum import Enum
from datetime import datetime
from typing import Dict


class EventType(Enum):
    """事件类型枚举"""
    NORMAL_FLUCTUATION = "normal_fluctuation"
    WEATHER_CHANGE = "weather_change"
    DEVICE_FAILURE = "device_failure"
    DEVICE_RECOVERY = "device_recovery"
    LOAD_SPIKE = "load_spike"
    CASCADE_ALARM = "cascade_alarm"
    REGIONAL_FAULT = "regional_fault"


class Event:
    """事件对象"""
    def __init__(self, type: EventType, payload: Dict):
        self.type = type
        self.payload = payload
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            'type': self.type.value,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat()
        }