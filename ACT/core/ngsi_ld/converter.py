"""
NGSI-LD 转换器
用于将 Django 模型数据转换为 NGSI-LD 格式
集成语义化实体模型体系
"""
from .entity_factory import EntityFactory


class NGSI_LD_Converter:
    NGSI_LD_CORE_CONTEXT = "/static/ngsi-ld/ngsi-ld-core-context.jsonld"
    ATC_MONITOR_CONTEXT = "/static/ngsi-ld/atc-monitor-context.jsonld"

    @classmethod
    def get_context(cls, include_app_context=True):
        if include_app_context:
            return [
                cls.NGSI_LD_CORE_CONTEXT,
                cls.ATC_MONITOR_CONTEXT
            ]
        return cls.NGSI_LD_CORE_CONTEXT

    @classmethod
    def device_to_ngsi_ld(cls, device):
        entity = EntityFactory.create_device_entity(device)
        result = entity.to_ngsi_ld()
        result["@context"] = cls.get_context()
        return result

    @classmethod
    def batch_to_ngsi_ld(cls, items, item_type):
        """批量转换"""
        if item_type == "Device":
            return [cls.device_to_ngsi_ld(item) for item in items]
        elif item_type == "Alarm":
            return [cls.alarm_to_ngsi_ld(item) for item in items]
        elif item_type == "DeviceStatus":
            return [cls.status_log_to_ngsi_ld(item) for item in items]
        return []

    @classmethod
    def alarm_to_ngsi_ld(cls, alarm):
        """将 Alarm 模型实例转换为 NGSI-LD 格式"""
        entity = EntityFactory.create_alarm_entity(alarm)
        result = entity.to_ngsi_ld()
        result["@context"] = cls.get_context()
        return result

    @classmethod
    def status_log_to_ngsi_ld(cls, status_log):
        """将 DeviceStatusLog 模型实例转换为 NGSI-LD 格式"""
        entity = EntityFactory.create_status_entity(status_log)
        result = entity.to_ngsi_ld()
        result["@context"] = cls.get_context()
        return result

    @classmethod
    def prediction_to_ngsi_ld(cls, prediction):
        """将 PredictionResult 模型实例转换为 NGSI-LD 格式"""
        entity = EntityFactory.create_prediction_entity(prediction)
        result = entity.to_ngsi_ld()
        result["@context"] = cls.get_context()
        return result
