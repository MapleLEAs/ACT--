"""
Event Schema - 统一事件定义
所有系统事件遵循统一的 Schema
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import json


class EventType(Enum):
    DEVICE_STATUS_RECEIVED = "DeviceStatusReceived"
    ALARM_TRIGGERED = "AlarmTriggered"
    ALARM_CLEARED = "AlarmCleared"
    ALARM_ACKNOWLEDGED = "AlarmAcknowledged"
    PREDICTION_GENERATED = "PredictionGenerated"
    DEVICE_OFFLINE = "DeviceOffline"
    DEVICE_ONLINE = "DeviceOnline"
    RULE_EVALUATED = "RuleEvaluated"
    ANOMALY_DETECTED = "AnomalyDetected"


class EventPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class BaseEvent:
    event_id: str
    event_type: EventType
    timestamp: datetime
    source: str
    priority: EventPriority = EventPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "priority": self.priority.value,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        data = data.copy()
        data['event_type'] = EventType(data['event_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['priority'] = EventPriority(data['priority'])
        return cls(**data)


@dataclass
class DeviceStatusEvent(BaseEvent):
    device_id: str = ""
    device_type: str = ""
    online_status: bool = True
    device_status: str = "normal"
    alarm_flag: bool = False
    metrics: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.event_type = EventType.DEVICE_STATUS_RECEIVED
        self.source = f"device:{self.device_id}"
        self.metadata = {
            "device_type": self.device_type,
            "online_status": self.online_status,
            "device_status": self.device_status,
            "alarm_flag": self.alarm_flag,
            "metrics": self.metrics
        }


@dataclass
class AlarmTriggeredEvent(BaseEvent):
    alarm_id: str = ""
    device_id: str = ""
    rule_id: Optional[int] = None
    metric: str = ""
    value: float = 0.0
    threshold: float = 0.0
    severity: str = "WARN"
    message: str = ""

    def __post_init__(self):
        self.event_type = EventType.ALARM_TRIGGERED
        self.source = f"alarm:{self.alarm_id}"
        self.metadata = {
            "device_id": self.device_id,
            "rule_id": self.rule_id,
            "metric": self.metric,
            "value": self.value,
            "threshold": self.threshold,
            "severity": self.severity,
            "message": self.message
        }


@dataclass
class AlarmClearedEvent(BaseEvent):
    alarm_id: str = ""
    device_id: str = ""
    rule_id: Optional[int] = None
    clear_type: str = "AUTO"
    recover_value: Optional[float] = None
    message: str = ""

    def __post_init__(self):
        self.event_type = EventType.ALARM_CLEARED
        self.source = f"alarm:{self.alarm_id}"
        self.metadata = {
            "device_id": self.device_id,
            "rule_id": self.rule_id,
            "clear_type": self.clear_type,
            "recover_value": self.recover_value,
            "message": self.message
        }


@dataclass
class AlarmAcknowledgedEvent(BaseEvent):
    alarm_id: str = ""
    device_id: str = ""
    acknowledged_by: str = ""
    message: str = ""

    def __post_init__(self):
        self.event_type = EventType.ALARMACKNOWLEDGED
        self.source = f"alarm:{self.alarm_id}"
        self.metadata = {
            "device_id": self.device_id,
            "acknowledged_by": self.acknowledged_by,
            "message": self.message
        }


@dataclass
class PredictionGeneratedEvent(BaseEvent):
    device_id: str = ""
    metric: str = ""
    predicted_value: float = 0.0
    confidence_score: float = 0.0
    prediction_horizon: int = 60
    is_anomaly: bool = False
    severity: str = ""

    def __post_init__(self):
        self.event_type = EventType.PREDICTION_GENERATED
        self.source = f"device:{self.device_id}"
        self.metadata = {
            "metric": self.metric,
            "predicted_value": self.predicted_value,
            "confidence_score": self.confidence_score,
            "prediction_horizon": self.prediction_horizon,
            "is_anomaly": self.is_anomaly,
            "severity": self.severity
        }


@dataclass
class DeviceOfflineEvent(BaseEvent):
    device_id: str = ""
    device_type: str = ""
    last_seen: Optional[datetime] = None
    offline_duration: int = 0

    def __post_init__(self):
        self.event_type = EventType.DEVICE_OFFLINE
        self.source = f"device:{self.device_id}"
        self.priority = EventPriority.HIGH
        self.metadata = {
            "device_type": self.device_type,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "offline_duration": self.offline_duration
        }


@dataclass
class AnomalyDetectedEvent(BaseEvent):
    device_id: str = ""
    device_type: str = ""
    anomaly_score: float = 0.0
    features: Dict[str, float] = field(default_factory=dict)
    severity: str = "WARN"

    def __post_init__(self):
        self.event_type = EventType.ANOMALY_DETECTED
        self.source = f"device:{self.device_id}"
        self.metadata = {
            "device_type": self.device_type,
            "anomaly_score": self.anomaly_score,
            "features": self.features,
            "severity": self.severity
        }


class EventBus:
    """
    事件总线 - 统一事件分发中心
    支持同步和异步（未来扩展）分发
    """
    _subscribers: Dict[EventType, List[Callable]] = {}
    _all_subscribers: List[Callable] = []
    _is_async = False # 可以通过配置开启异步

    @classmethod
    def subscribe(cls, event_type: EventType, handler: Callable):
        """订阅特定类型事件"""
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        if handler not in cls._subscribers[event_type]:
            cls._subscribers[event_type].append(handler)

    @classmethod
    def subscribe_all(cls, handler: Callable):
        """订阅所有事件"""
        if handler not in cls._all_subscribers:
            cls._all_subscribers.append(handler)

    @classmethod
    def publish(cls, event: BaseEvent):
        """发布事件"""
        event_dict = event.to_dict()
        
        # 1. 分发给特定类型订阅者
        if event.event_type in cls._subscribers:
            for handler in cls._subscribers[event.event_type]:
                cls._execute_handler(handler, event_dict)

        # 2. 分发给全局订阅者
        for handler in cls._all_subscribers:
            cls._execute_handler(handler, event_dict)

    @classmethod
    def _execute_handler(cls, handler: Callable, event_data: Dict[str, Any]):
        try:
            # 如果是异步模式，这里可以推送到任务队列（如 Celery 或 ThreadPool）
            handler(event_data)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"事件处理失败 [{handler.__name__}]: {e}")
