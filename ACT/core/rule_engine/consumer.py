"""
Event Consumer - 事件消费者
异步处理事件流
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from django.core.cache import cache
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    事件消费者
    从 Redis Stream 消费事件并处理
    """

    def __init__(self):
        self.channel_layer = get_channel_layer()

    def process_device_status(self, event_data: Dict[str, Any]):
        """
        处理设备状态事件
        1. 规则评估（标准阈值 + 自定义规则）
        2. 告警生成
        3. WebSocket 推送
        """
        from core.rule_engine.engine import RuleEngine, AlarmGenerator
        from core.rule_engine.events import EventBus, DeviceStatusEvent, AlarmTriggeredEvent

        metadata = event_data.get('metadata', {})
        device_id = metadata.get('device_id')
        device_type = metadata.get('device_type')
        metrics = metadata.get('metrics', {})

        logger.info(f"处理设备状态事件: {device_id}")

        status_data = {
            'device_id': device_id,
            'device_type': device_type,
            **metrics
        }

        rule_engine = RuleEngine()
        rule_results = rule_engine.evaluate_device_status(status_data)

        for result in rule_results:
            if result.matched and not rule_engine.context.is_alarm_active(device_id, result.metric):
                try:
                    from monitor.models import Device
                    device = Device.objects.filter(device_id=device_id).first()
                    if device:
                        alarm = AlarmGenerator.generate_alarm(
                            device=device,
                            rule=type('Rule', (), {
                                'id': result.rule_id,
                                'name': result.rule_name,
                                'severity': result.severity,
                                'auto_clear': True
                            })(),
                            metric=result.metric,
                            value=result.value,
                            trigger_time=datetime.now()
                        )

                        rule_engine.context.set_alarm_active(device_id, result.metric, alarm.alarm_id)

                        alarm_event = AlarmTriggeredEvent(
                            event_id=f"evt-{datetime.now().timestamp()}",
                            timestamp=datetime.now(),
                            source=f"rule:{result.rule_id}",
                            priority=result.severity,
                            alarm_id=alarm.alarm_id,
                            device_id=device_id,
                            rule_id=result.rule_id,
                            metric=result.metric,
                            value=result.value,
                            threshold=result.threshold,
                            severity=result.severity,
                            message=result.message
                        )
                        EventBus.publish(alarm_event)

                except Exception as e:
                    logger.error(f"告警生成失败: {e}")

        # AI 异常检测模块已暂时禁用
        # 如需启用，可在未来重新集成

    def process_alarm_event(self, event_data: Dict[str, Any]):
        """处理告警事件"""
        event_type = event_data.get('event_type')

        if event_type == 'AlarmTriggered':
            self._broadcast_alarm(event_data)
        elif event_type == 'AlarmCleared':
            self._broadcast_alarm_cleared(event_data)

    def _broadcast_alarm(self, event_data: Dict[str, Any]):
        """广播告警到 WebSocket"""
        try:
            if self.channel_layer:
                async_to_sync(self.channel_layer.group_send)(
                    "notifications",
                    {
                        "type": "alarm_message",
                        "event": event_data
                    }
                )
        except Exception as e:
            logger.warning(f"告警广播失败: {e}")

    def _broadcast_alarm_cleared(self, event_data: Dict[str, Any]):
        """广播告警清除"""
        try:
            if self.channel_layer:
                async_to_sync(self.channel_layer.group_send)(
                    "notifications",
                    {
                        "type": "alarm_cleared_message",
                        "event": event_data
                    }
                )
        except Exception as e:
            logger.warning(f"告警清除广播失败: {e}")


class RedisStreamConsumer:
    """
    Redis Stream 事件消费者
    从 Redis Stream 读取事件并处理
    """

    def __init__(self, stream_name: str = "events:stream"):
        self.stream_name = stream_name
        self.consumer = EventConsumer()
