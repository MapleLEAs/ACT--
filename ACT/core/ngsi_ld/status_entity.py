from typing import Dict, Any, Optional
from datetime import datetime


class DeviceStatusEntity:
    """
    NGSI-LD设备状态实体模型
    实现设备实时状态的语义化表达，支持动态属性
    """

    def __init__(self, status_id: str):
        self.id = f"urn:ngsi-ld:DeviceStatus:{status_id}"
        self.type = "DeviceStatus"
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

    def add_status_details(self, online_status: bool, device_status: str,
                           alarm_flag: bool, device_urn: str, collect_time: datetime):
        """
        添加状态详情
        :param online_status: 在线状态
        :param device_status: 设备状态
        :param alarm_flag: 告警标志
        :param device_urn: 关联设备URN
        :param collect_time: 采集时间
        """
        self.add_property("onlineStatus", online_status)
        self.add_property("deviceStatus", device_status)
        self.add_property("alarmFlag", alarm_flag)
        self.add_property("collectTime", collect_time.isoformat())
        self.add_relationship("belongsTo", device_urn)

    def add_dynamic_metrics(self, metrics: Dict[str, Any]):
        """
        添加动态指标属性
        :param metrics: 指标字典 {metric_name: value}
        """
        for name, value in metrics.items():
            if value is not None:
                camel_name = ''.join(word.capitalize() for word in name.split('_'))
                camel_name = camel_name[0].lower() + camel_name[1:]
                self.add_property(camel_name, value)

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
        return f"<DeviceStatusEntity: {self.id}>"
