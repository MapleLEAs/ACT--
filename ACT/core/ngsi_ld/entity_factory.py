from typing import Optional, Any, Dict
from .device_entity import DeviceEntity
from .alarm_entity import AlarmEntity
from .prediction_entity import PredictionEntity
from .status_entity import DeviceStatusEntity


class EntityFactory:
    """
    NGSI-LD实体工厂类
    负责从Django模型实例创建标准化的NGSI-LD实体对象
    """

    @staticmethod
    def create_device_entity(device_model, related_device_ids: Optional[Dict[str, list]] = None) -> DeviceEntity:
        """
        从Device模型创建NGSI-LD设备实体
        :param device_model: Django Device模型实例
        :param related_device_ids: 关联设备ID字典 {relationship_type: [device_ids]}
        :return: DeviceEntity实例
        """
        entity = DeviceEntity(
            device_id=device_model.device_id,
            device_type=device_model.device_type
        )

        entity.add_property("deviceId", device_model.device_id)
        entity.add_property("deviceType", device_model.device_type)

        if hasattr(device_model, 'device_model') and device_model.device_model:
            entity.add_property("deviceModel", device_model.device_model)

        if device_model.location:
            entity.add_property("location", device_model.location)

        if hasattr(device_model, 'geo_location') and device_model.geo_location:
            entity.add_geo_property("location", (
                device_model.geo_location.x,
                device_model.geo_location.y
            ))

        if hasattr(device_model, 'manufacturer') and device_model.manufacturer:
            entity.add_property("manufacturer", device_model.manufacturer)

        if hasattr(device_model, 'install_time') and device_model.install_time:
            entity.add_property("installTime", device_model.install_time.isoformat())

        if hasattr(device_model, 'protocol_version') and device_model.protocol_version:
            entity.add_property("protocolVersion", device_model.protocol_version)

        if hasattr(device_model, 'created_at') and device_model.created_at:
            entity.add_property("createdAt", device_model.created_at.isoformat())

        if hasattr(device_model, 'updated_at') and device_model.updated_at:
            entity.add_property("modifiedAt", device_model.updated_at.isoformat())

        EntityFactory._add_coupling_relationships(entity, device_model, related_device_ids)

        return entity

    @staticmethod
    def _add_coupling_relationships(entity: DeviceEntity, device_model,
                                    related_device_ids: Optional[Dict[str, list]] = None):
        """
        添加设备耦合关系（根据设备类型自动添加语义化关系）
        :param entity: DeviceEntity实例
        :param device_model: Django Device模型实例
        :param related_device_ids: 实际关联设备ID字典
        """
        if related_device_ids:
            for rel_type, device_ids in related_device_ids.items():
                for device_id in device_ids:
                    entity.add_coupling_relationship(device_id, rel_type)
            return

        coupling_rules = {
            "VHF": [("interferesWith", "ILS"), ("interferesWith", "VOR"), ("locatedAt", "Tower")],
            "ILS": [("dependsOn", "VHF"), ("connectedTo", "DME"), ("locatedAt", "Runway")],
            "VOR": [("interferesWith", "VHF"), ("connectedTo", "DME"), ("locatedAt", "Tower")],
            "DME": [("connectedTo", "VOR"), ("connectedTo", "ILS"), ("locatedAt", "Tower")],
            "HF": [("locatedAt", "Tower"), ("connectedTo", "VHF")]
        }

        if device_model.device_type in coupling_rules:
            for rel_type, target_type in coupling_rules[device_model.device_type]:
                target_urn = f"urn:ngsi-ld:Device:{target_type}-001"
                entity.add_relationship(rel_type, target_urn)

    @staticmethod
    def create_alarm_entity(alarm_model) -> AlarmEntity:
        """
        从Alarm模型创建NGSI-LD告警实体
        :param alarm_model: Django Alarm模型实例
        :return: AlarmEntity实例
        """
        entity = AlarmEntity(alarm_id=alarm_model.alarm_id)

        device_urn = f"urn:ngsi-ld:Device:{alarm_model.device.device_id}"
        entity.add_alarm_details(
            severity=alarm_model.severity,
            message=alarm_model.message if hasattr(alarm_model, 'message') else "Alarm triggered",
            device_urn=device_urn
        )

        entity.add_metric_details(
            metric=alarm_model.metric,
            value=float(alarm_model.value) if alarm_model.value is not None else alarm_model.value_str,
            threshold=getattr(alarm_model, 'threshold_value', None)
        )

        entity.add_temporal_properties(
            trigger_time=alarm_model.trigger_time,
            ack_time=getattr(alarm_model, 'ack_time', None),
            clear_time=getattr(alarm_model, 'clear_time', None)
        )

        if hasattr(alarm_model, 'status'):
            entity.add_property("status", alarm_model.status)

        if hasattr(alarm_model, 'rule') and alarm_model.rule:
            rule_urn = f"urn:ngsi-ld:AlarmRule:{alarm_model.rule.id}"
            entity.add_relationship("refRule", rule_urn)

        return entity

    @staticmethod
    def create_prediction_entity(prediction_model) -> PredictionEntity:
        """
        从PredictionResult模型创建NGSI-LD预测实体
        :param prediction_model: Django PredictionResult模型实例
        :return: PredictionEntity实例
        """
        entity = PredictionEntity(prediction_id=str(prediction_model.id))

        device_urn = f"urn:ngsi-ld:Device:{prediction_model.device.device_id}"
        entity.add_prediction_details(
            metric=prediction_model.metric,
            predicted_value=prediction_model.prediction_time,
            device_urn=device_urn,
            prediction_time=prediction_model.prediction_time
        )

        entity.add_confidence_interval(
            confidence_score=prediction_model.confidence_score,
            error_margin=prediction_model.error_margin
        )

        entity.add_threshold_info(
            threshold_value=prediction_model.threshold_value,
            is_above_threshold=prediction_model.is_above_threshold
        )

        entity.add_horizon_and_severity(
            horizon=prediction_model.prediction_horizon,
            severity=prediction_model.severity
        )

        if hasattr(prediction_model, 'physics_value') and prediction_model.physics_value:
            entity.add_hybrid_model_info(
                physics_value=prediction_model.physics_value,
                ai_residual=getattr(prediction_model, 'ai_residual', None)
            )

        if hasattr(prediction_model, 'status'):
            entity.add_property("status", prediction_model.status)

        if hasattr(prediction_model, 'created_at') and prediction_model.created_at:
            entity.add_property("createdAt", prediction_model.created_at.isoformat())

        return entity

    @staticmethod
    def create_status_entity(status_log_model) -> DeviceStatusEntity:
        """
        从DeviceStatusLog模型创建NGSI-LD设备状态实体
        :param status_log_model: Django DeviceStatusLog模型实例
        :return: DeviceStatusEntity实例
        """
        entity = DeviceStatusEntity(status_id=str(status_log_model.id))

        device_urn = f"urn:ngsi-ld:Device:{status_log_model.device.device_id}"
        entity.add_status_details(
            online_status=status_log_model.online_status,
            device_status=status_log_model.device_status,
            alarm_flag=status_log_model.alarm_flag,
            device_urn=device_urn,
            collect_time=status_log_model.collect_time
        )

        if hasattr(status_log_model, 'created_at') and status_log_model.created_at:
            entity.add_property("createdAt", status_log_model.created_at.isoformat())

        dynamic_fields = [
            'power_voltage', 'device_temperature', 'signal_strength',
            'link_status', 'bit_error_rate', 'loc_guidance_deviation',
            'gs_guidance_deviation', 'signal_power', 'antenna_swr'
        ]
        metrics = {}
        for field in dynamic_fields:
            val = getattr(status_log_model, field, None)
            if val is not None:
                metrics[field] = val
        entity.add_dynamic_metrics(metrics)

        return entity

    @staticmethod
    def create_from_model(model_instance) -> Optional[Any]:
        """
        根据模型类型自动创建对应的NGSI-LD实体
        :param model_instance: Django模型实例
        :return: NGSI-LD实体实例
        """
        model_class = type(model_instance).__name__

        if model_class == "Device":
            return EntityFactory.create_device_entity(model_instance)
        elif model_class == "Alarm":
            return EntityFactory.create_alarm_entity(model_instance)
        elif model_class == "PredictionResult":
            return EntityFactory.create_prediction_entity(model_instance)
        elif model_class == "DeviceStatusLog":
            return EntityFactory.create_status_entity(model_instance)

        return None
