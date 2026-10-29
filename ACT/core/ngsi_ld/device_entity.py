from typing import Dict, Any, Optional


class DeviceEntity:
    """
    NGSI-LD设备实体模型
    实现空管设备的语义化数据建模，支持Property属性和Relationship关系表达
    """

    def __init__(self, device_id: str, device_type: str):
        self.id = f"urn:ngsi-ld:Device:{device_id}"
        self.type = "Device"
        self.properties: Dict[str, Dict[str, Any]] = {}
        self.relationships: Dict[str, Dict[str, str]] = {}
        self.context = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"

    def add_property(self, name: str, value: Any, unit: Optional[str] = None):
        """
        添加属性（Property）
        :param name: 属性名称
        :param value: 属性值
        :param unit: 单位代码（如 CEL, dBm）
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
        :param name: 关系名称（如 interferesWith, locatedAt, dependsOn）
        :param target_urn: 目标实体URN（如 urn:ngsi-ld:Device:ILS-002）
        """
        self.relationships[name] = {
            "type": "Relationship",
            "object": target_urn
        }

    def add_geo_property(self, name: str, coordinates: tuple):
        """
        添加地理属性（GeoProperty）
        :param name: 属性名称
        :param coordinates: 坐标元组 (longitude, latitude)
        """
        self.properties[name] = {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": list(coordinates)
            }
        }

    def add_coupling_relationship(self, target_device_id: str, relationship_type: str = "interferesWith"):
        """
        添加设备耦合关系（语义化表达设备间影响）
        :param target_device_id: 目标设备ID
        :param relationship_type: 关系类型（interferesWith/locatedAt/dependsOn/connectedTo）
        """
        target_urn = f"urn:ngsi-ld:Device:{target_device_id}"
        self.add_relationship(relationship_type, target_urn)

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
        return f"<DeviceEntity: {self.id} ({self.type})>"
