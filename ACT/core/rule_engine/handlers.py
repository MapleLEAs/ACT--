"""
Event Handlers - 事件处理器
负责处理各类系统事件
"""
import logging
from typing import Dict, Any, Callable
from datetime import datetime
from django.core.cache import cache

from .events import (
    EventBus,
    EventType,
    BaseEvent,
    DeviceStatusEvent,
    AlarmTriggeredEvent,
    AlarmClearedEvent,
    PredictionGeneratedEvent,
    AnomalyDetectedEvent,
)

logger = logging.getLogger(__name__)


class EventHandlerRegistry:
    """
    事件处理器注册表
    管理所有事件处理器
    """

    _handlers: Dict[EventType, list] = {}

    @classmethod
    def register(cls, event_type: EventType):
        """装饰器：注册事件处理器"""
        def decorator(handler: Callable):
            if event_type not in cls._handlers:
                cls._handlers[event_type] = []
            if handler not in cls._handlers[event_type]:
                cls._handlers[event_type].append(handler)
            return handler
        return decorator

    @classmethod
    def handle_event(cls, event_data: Dict[str, Any]):
        """分发事件到对应处理器"""
        try:
            event_type_str = event_data.get('event_type')
            if not event_type_str:
                return
                
            event_type = EventType(event_type_str)
            if event_type in cls._handlers:
                for handler in cls._handlers[event_type]:
                    try:
                        handler(event_data)
                    except Exception as e:
                        logger.error(f"事件处理失败 [{handler.__name__}]: {e}")
        except Exception as e:
            logger.error(f"事件分发失败: {e}")


class AlarmEventHandler:
    """
    告警事件处理器
    处理告警触发、清除、确认等事件
    """

    @staticmethod
    @EventHandlerRegistry.register(EventType.ALARM_TRIGGERED)
    def on_alarm_triggered(event_data: Dict[str, Any]):
        """处理告警触发事件"""
        alarm_id = event_data.get('metadata', {}).get('alarm_id')
        device_id = event_data.get('metadata', {}).get('device_id')
        severity = event_data.get('metadata', {}).get('severity', 'WARN')

        logger.info(f"告警触发事件: {alarm_id} 设备: {device_id} 严重性: {severity}")

        cache.set(f"alarm:active:{device_id}", True, timeout=3600)

    @staticmethod
    @EventHandlerRegistry.register(EventType.ALARM_CLEARED)
    def on_alarm_cleared(event_data: Dict[str, Any]):
        """处理告警清除事件"""
        alarm_id = event_data.get('metadata', {}).get('alarm_id')
        device_id = event_data.get('metadata', {}).get('device_id')
        clear_type = event_data.get('metadata', {}).get('clear_type', 'AUTO')

        logger.info(f"告警清除事件: {alarm_id} 设备: {device_id} 类型: {clear_type}")

        cache.delete(f"alarm:active:{device_id}")


class WebSocketEventHandler:
    """
    WebSocket 事件处理器
    将事件推送到前端
    """

    @staticmethod
    @EventHandlerRegistry.register(EventType.ALARM_TRIGGERED)
    def broadcast_alarm(event_data: Dict[str, Any]):
        """广播告警到 WebSocket"""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                # 统一发送到 notifications 全局组
                async_to_sync(channel_layer.group_send)(
                    "notifications",
                    {
                        "type": "alarm_message",
                        "event": event_data
                    }
                )
                logger.debug(f"告警已广播: {event_data.get('event_id')}")
        except Exception as e:
            logger.warning(f"WebSocket 广播失败: {e}")

    @staticmethod
    @EventHandlerRegistry.register(EventType.DEVICE_STATUS_RECEIVED)
    def broadcast_status(event_data: Dict[str, Any]):
        """广播设备状态到 WebSocket"""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                # 同时也发送到 notifications 全局组，方便仪表盘更新
                async_to_sync(channel_layer.group_send)(
                    "notifications",
                    {
                        "type": "status_message",
                        "event": event_data
                    }
                )
        except Exception as e:
            logger.warning(f"状态广播失败: {e}")

    @staticmethod
    @EventHandlerRegistry.register(EventType.ANOMALY_DETECTED)
    def broadcast_anomaly(event_data: Dict[str, Any]):
        """广播异常检测结果到 WebSocket"""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    "notifications",
                    {
                        "type": "anomaly_message",
                        "event": event_data
                    }
                )
        except Exception as e:
            logger.warning(f"异常广播失败: {e}")


class NGsiLdEventHandler:
    """
    NGSI-LD 事件处理器
    将事件转换为 NGSI-LD 格式并发布
    """

    @staticmethod
    @EventHandlerRegistry.register(EventType.ALARM_TRIGGERED)
    def publish_alarm_to_ngsi_ld(event_data: Dict[str, Any]):
        """发布告警到 NGSI-LD"""
        try:
            from core.ngsi_exchange import NGSIExchangeService

            alarm_id = event_data.get('metadata', {}).get('alarm_id')
            if alarm_id:
                ngsi_entity = NGSIExchangeService.get_entity_by_urn(f"urn:ngsi-ld:Alarm:{alarm_id}")
                if ngsi_entity:
                    cache.set(f"ngsi:alarm:{alarm_id}", ngsi_entity, timeout=300)
                    logger.debug(f"NGSI-LD 告警缓存: {alarm_id}")
        except Exception as e:
            logger.warning(f"NGSI-LD 发布失败: {e}")

    @staticmethod
    @EventHandlerRegistry.register(EventType.DEVICE_STATUS_RECEIVED)
    def publish_status_to_ngsi_ld(event_data: Dict[str, Any]):
        """发布设备状态到 NGSI-LD"""
        try:
            device_id = event_data.get('metadata', {}).get('device_id')
            if device_id:
                ngsi_status = NGSIExchangeService.get_device_status(device_id)
                if ngsi_status:
                    cache.set(f"ngsi:status:{device_id}", ngsi_status, timeout=60)
        except Exception as e:
            logger.warning(f"NGSI-LD 状态发布失败: {e}")


class PredictionEventHandler:
    """
    预测事件处理器
    处理 AI 预测相关事件
    """

    @staticmethod
    @EventHandlerRegistry.register(EventType.PREDICTION_GENERATED)
    def on_prediction_generated(event_data: Dict[str, Any]):
        """处理预测生成事件"""
        metadata = event_data.get('metadata', {})
        device_id = metadata.get('device_id')
        metric = metadata.get('metric')
        is_anomaly = metadata.get('is_anomaly', False)

        if is_anomaly:
            logger.warning(f"预测异常: 设备 {device_id} 指标 {metric}")
            cache.set(f"prediction:anomaly:{device_id}:{metric}", True, timeout=3600)


class DeviceEventHandler:
    """
    设备事件处理器
    处理设备上下线等事件
    """

    @staticmethod
    @EventHandlerRegistry.register(EventType.DEVICE_OFFLINE)
    def on_device_offline(event_data: Dict[str, Any]):
        """处理设备离线事件"""
        device_id = event_data.get('metadata', {}).get('device_id')
        logger.warning(f"设备离线: {device_id}")
        cache.set(f"device:offline:{device_id}", True, timeout=86400)

    @staticmethod
    @EventHandlerRegistry.register(EventType.DEVICE_ONLINE)
    def on_device_online(event_data: Dict[str, Any]):
        """处理设备上线事件"""
        device_id = event_data.get('metadata', {}).get('device_id')
        logger.info(f"设备上线: {device_id}")
        cache.delete(f"device:offline:{device_id}")


def initialize_event_handlers():
    """
    初始化所有事件处理器
    在系统启动时调用
    """
    from .events import EventBus

    handlers = [
        AlarmEventHandler,
        WebSocketEventHandler,
        NGsiLdEventHandler,
        PredictionEventHandler,
        DeviceEventHandler,
    ]

    for handler_class in handlers:
        for attr_name in dir(handler_class):
            attr = getattr(handler_class, attr_name)
            if callable(attr) and hasattr(attr, '_event_type'):
                EventBus.subscribe(attr._event_type, attr)

    logger.info(f"事件处理器初始化完成，共注册 {len(handlers)} 个处理器类")
