from typing import Dict, Any, Optional
from datetime import datetime


class AlarmEntity:
    """
    NGSI-LD告警实体模型
    实现告警的语义化表达，支持与设备的关联关系
    """

    def __init__(self, alarm_id: str):
        self.id = f"urn:ngsi-ld:Alarm:{alarm_id}"
        self.type = "Alarm"
        self.properties: Dict[str, Dict[str, Any]] = {}
        self.relationships: Dict[str, Dict[str, str]] = {}
        self.context = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"

    def add_property(self, name: str, value: Any, unit: Optional[str] = None):
        """
        添加属性（Property）
        :param name: 属性名称
        :param value: 属性值
        :param unit: 单位代码
        """
        prop = {
            "type": "Property",
            "value": value
        }
        if unit:
            prop["unitCode"] = unit
        self.properties[name] = prop

    def add_relationship(self, name: str, target_urn: str):
        """
        添加关系（Relationship）
        :param name: 关系名称
        :param target_urn: 目标实体URN
        """
        self.relationships[name] = {
            "type": "Relationship",
            "object": target_urn
        }

    def add_alarm_details(self, severity: str, message: str, device_urn: str):
        """
        添加告警详情
        :param severity: 告警级别（CRITICAL/ERROR/WARNING/INFO）
        :param message: 告警消息
        :param device_urn: 关联设备URN
        """
        self.add_property("severity", severity)
        self.add_property("message", message)
        self.add_relationship("refDevice", device_urn)

    def add_temporal_properties(self, trigger_time: Optional[datetime] = None,
                               ack_time: Optional[datetime] = None,
                               clear_time: Optional[datetime] = None):
        """
        添加时间属性
        :param trigger_time: 触发时间
        :param ack_time: 确认时间
        :param clear_time: 清除时间
        """
        if trigger_time:
            self.add_property("triggerTime", trigger_time.isoformat())
        if ack_time:
            self.add_property("ackTime", ack_time.isoformat())
        if clear_time:
            self.add_property("clearTime", clear_time.isoformat())

    def add_metric_details(self, metric: str, value: Any, threshold: Optional[Any] = None):
        """
        添加指标详情
        :param metric: 指标名称
        :param value: 指标值
        :param threshold: 阈值
        """
        self.add_property("metric", metric)
        self.add_property("value", value)
        if threshold:
            self.add_property("thresholdValue", threshold)

    def to_ngsi_ld(self) -> Dict[str, Any]:
        """
        转换为NGSI-LD JSON格式
        :return: NGSI-LD实体字典
        """
        entity = {
            "id": self.id,
            "type": self.type,
            "@context": self.context
        }

        for name, prop in self.properties.items():
            entity[name] = prop

        for name, rel in self.relationships.items():
            entity[name] = rel

        return entity

    def __repr__(self):
        return f"<AlarmEntity: {self.id}>"
