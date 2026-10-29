from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DeviceStatusLog, Alarm, Device
from core.ngsi_ld import NGSI_LD_Converter
from core.cache_service import NGSICacheService
from core.rule_engine.events import EventBus, DeviceStatusEvent
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def handle_status_created(status_log):
    """
    处理状态日志创建后的 NGSI-LD 事件生成
    """
    ngsi_status = NGSI_LD_Converter.status_log_to_ngsi_ld(status_log)
    result = {
        "event": "DeviceStatusChanged",
        "timestamp": status_log.collect_time.isoformat(),
        "status": ngsi_status
    }
    if status_log.alarm_flag:
        latest_alarm = Alarm.objects.filter(
            device=status_log.device,
            status="OPEN"
        ).order_by("-trigger_time").first()
        if latest_alarm:
            ngsi_alarm = NGSI_LD_Converter.alarm_to_ngsi_ld(latest_alarm)
            result["alarm"] = ngsi_alarm
    return result

def handle_alarm_created(alarm):
    """处理告警创建后的 NGSI-LD 事件生成"""
    ngsi_alarm = NGSI_LD_Converter.alarm_to_ngsi_ld(alarm)
    return {
        "event": "AlarmTriggered",
        "timestamp": alarm.trigger_time.isoformat(),
        "alarm": ngsi_alarm
    }

def handle_alarm_updated(alarm):
    """处理告警更新后的 NGSI-LD 事件生成"""
    ngsi_alarm = NGSI_LD_Converter.alarm_to_ngsi_ld(alarm)
    event_type = "AlarmUpdated"
    if alarm.status == "ACK":
        event_type = "AlarmAcknowledged"
    elif alarm.status == "CLEARED":
        event_type = "AlarmCleared"
    return {
        "event": event_type,
        "timestamp": alarm.update_time.isoformat() if hasattr(alarm, 'update_time') and alarm.update_time else alarm.trigger_time.isoformat(),
        "alarm": ngsi_alarm
    }

# ==================== 信号接收器 ====================

@receiver(post_save, sender=DeviceStatusLog)
def on_status_created(sender, instance, created, **kwargs):
    """
    状态日志创建信号接收器
    仅负责发布原始设备状态事件，所有复杂逻辑由 Event Bus 后端异步处理
    """
    if created:
        try:
            # 1. 组装设备状态数据
            status_data = {
                'device_id': instance.device.device_id,
                'device_type': instance.device.device_type,
                'online_status': instance.online_status,
                'device_status': instance.device_status,
                'alarm_flag': instance.alarm_flag,
                'metrics': {
                    'signal_strength': float(instance.signal_strength) if instance.signal_strength else None,
                    'power_voltage': float(instance.power_voltage) if instance.power_voltage else None,
                    'device_temperature': float(instance.device_temperature) if instance.device_temperature else None,
                    'signal_power': float(instance.signal_power) if instance.signal_power else None,
                    'bit_error_rate': float(instance.bit_error_rate) if instance.bit_error_rate else None,
                    'loc_guidance_deviation': float(instance.loc_guidance_deviation) if instance.loc_guidance_deviation else None,
                    'gs_guidance_deviation': float(instance.gs_guidance_deviation) if instance.gs_guidance_deviation else None,
                    'antenna_swr': float(instance.antenna_swr) if instance.antenna_swr else None,
                }
            }

            # 2. 发布事件到 Event Bus
            event = DeviceStatusEvent(
                event_id=f"evt-{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                source=f"device:{instance.device.device_id}",
                **status_data
            )
            EventBus.publish(event)
            
            # 3. 清理相关缓存
            NGSICacheService.delete_device_status(instance.device.device_id)
            
        except Exception as e:
            logger.error(f"处理设备状态事件失败: {e}")

@receiver(post_save, sender=Alarm)
def on_alarm_created_or_updated(sender, instance, created, **kwargs):
    """告警创建/更新信号接收器"""
    try:
        NGSICacheService.delete_entities("Alarm")
        NGSICacheService.delete_query_cache()
        if instance.device:
            NGSICacheService.delete_device_status(instance.device.device_id)

        if created:
            handle_alarm_created(instance)
        else:
            handle_alarm_updated(instance)

        try:
            from monitor.graph_service import RootCauseGraphService
            graph_service = RootCauseGraphService()
            try:
                graph_service.sync_alarm(instance)
            finally:
                graph_service.close()
        except Exception as graph_error:
            logger.warning(f"Neo4j 告警同步跳过: {graph_error}")
    except Exception as e:
        logger.error(f"Failed to generate NGSI-LD event for alarm: {str(e)}")

@receiver(post_save, sender=Device)
def on_device_updated(sender, instance, created, **kwargs):
    """设备更新信号接收器"""
    try:
        NGSICacheService.invalidate_device_cache(instance.device_id)
    except Exception as e:
        logger.error(f"Failed to invalidate cache for device: {str(e)}")
