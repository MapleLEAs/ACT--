import networkx as nx
from typing import Dict, List, Any, Optional
from core.ngsi_ld import DeviceEntity


class DeviceKnowledgeGraph:
    """
    设备知识图谱生成器
    基于networkx实现空管设备关系图的构建与分析
    """

    RELATION_TYPES = {
        "interferes": {"label": "干扰", "color": "#e74c3c"},
        "locatedAt": {"label": "位于", "color": "#3498db"},
        "dependsOn": {"label": "依赖", "color": "#f39c12"},
        "supports": {"label": "支撑", "color": "#27ae60"},
        "connectedTo": {"label": "连接", "color": "#9b59b6"},
        "monitors": {"label": "监控", "color": "#1abc9c"},
    }

    COUPLING_RULES = {
        "VHF": [("interferes", "ILS"), ("interferes", "VOR"), ("locatedAt", "Tower")],
        "ILS": [("dependsOn", "VHF"), ("connectedTo", "DME"), ("locatedAt", "Runway")],
        "VOR": [("interferes", "VHF"), ("connectedTo", "DME"), ("locatedAt", "Tower")],
        "DME": [("connectedTo", "VOR"), ("connectedTo", "ILS"), ("locatedAt", "Tower")],
        "HF": [("locatedAt", "Tower"), ("connectedTo", "VHF")],
    }

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_device(self, device_id: str, device_type: str, **kwargs):
        """
        添加设备节点
        :param device_id: 设备ID
        :param device_type: 设备类型
        """
        self.graph.add_node(
            device_id,
            type=device_type,
            label=device_id,
            category="device",
            **kwargs
        )

    def add_airport(self, airport_id: str, name: str, **kwargs):
        """
        添加机场节点
        :param airport_id: 机场ID
        :param name: 机场名称
        """
        self.graph.add_node(
            airport_id,
            type="Airport",
            label=name,
            category="airport",
            **kwargs
        )

    def add_runway(self, runway_id: str, name: str, **kwargs):
        """
        添加跑道节点
        :param runway_id: 跑道ID
        :param name: 跑道名称
        """
        self.graph.add_node(
            runway_id,
            type="Runway",
            label=name,
            category="runway",
            **kwargs
        )

    def add_relationship(
        self,
        source: str,
        target: str,
        relation: str
    ):
        """
        添加设备关系
        :param source: 源节点ID
        :param target: 目标节点ID
        :param relation: 关系类型
        """
        rel_info = self.RELATION_TYPES.get(relation, {"label": relation, "color": "#95a5a6"})
        self.graph.add_edge(
            source,
            target,
            relation=relation,
            label=rel_info["label"],
            color=rel_info["color"]
        )

    def build_from_ngsi_entities(self, entities: List[DeviceEntity]):
        """
        从NGSI-LD实体构建知识图谱
        :param entities: DeviceEntity列表
        """
        for entity in entities:
            device_data = entity.to_ngsi_ld()
            device_id = entity.id.replace("urn:ngsi-ld:Device:", "")
            dt = device_data.get("deviceType")
            device_type = dt.get("value", "Unknown") if isinstance(dt, dict) else (dt or "Unknown")

            self.add_device(device_id, device_type)

            for rel_name, rel_data in device_data.items():
                if isinstance(rel_data, dict) and rel_data.get("type") == "Relationship":
                    target_urn = rel_data.get("object", "")
                    if target_urn.startswith("urn:ngsi-ld:"):
                        target_id = target_urn.replace("urn:ngsi-ld:Device:", "")
                        target_id = target_id.replace("urn:ngsi-ld:Airport:", "")
                        target_id = target_id.replace("urn:ngsi-ld:Runway:", "")
                        
                        if not self.graph.has_node(target_id):
                            if "Airport" in rel_name or "Tower" in rel_name:
                                self.add_airport(target_id, target_id)
                            elif "Runway" in rel_name:
                                self.add_runway(target_id, target_id)
                            else:
                                self.add_device(target_id, "Unknown")
                        
                        self.add_relationship(device_id, target_id, rel_name)

    def build_coupling_graph(self, device_types: List[str] = None):
        """
        构建设备耦合关系图
        :param device_types: 设备类型列表，None表示所有类型
        """
        if device_types is None:
            device_types = list(self.COUPLING_RULES.keys())

        for device_type in device_types:
            if device_type in self.COUPLING_RULES:
                for i in range(1, 4):
                    device_id = f"{device_type}-{i:03d}"
                    if not self.graph.has_node(device_id):
                        self.add_device(device_id, device_type)

        for device_type in device_types:
            if device_type in self.COUPLING_RULES:
                for i in range(1, 4):
                    source_id = f"{device_type}-{i:03d}"
                    for rel_type, target_type in self.COUPLING_RULES[device_type]:
                        target_id = f"{target_type}-001"
                        if not self.graph.has_node(target_id):
                            if target_type == "Tower" or target_type == "Airport":
                                self.add_airport(target_id, target_type)
                            elif target_type == "Runway":
                                self.add_runway(target_id, target_type)
                            else:
                                self.add_device(target_id, target_type)
                        
                        if not self.graph.has_edge(source_id, target_id):
                            self.add_relationship(source_id, target_id, rel_type)

    def get_graph_data(self) -> Dict[str, Any]:
        """
        获取图谱数据（用于前端可视化）
        :return: 节点和边的数据字典
        """
        nodes = []
        edges = []

        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "name": attrs.get("label", node_id),
                "category": attrs.get("category", "device"),
                "type": attrs.get("type", "Unknown"),
                **attrs
            })

        for source, target, attrs in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "relation": attrs.get("relation", "unknown"),
                "label": attrs.get("label", attrs.get("relation", "unknown")),
                "color": attrs.get("color", "#95a5a6")
            })

        return {"nodes": nodes, "edges": edges}

    def find_interference_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        查找设备间干扰路径
        :param source: 源设备ID
        :param target: 目标设备ID
        :return: 路径节点列表，None表示无路径
        """
        try:
            path = nx.shortest_path(self.graph, source=source, target=target)
            return path
        except nx.NetworkXNoPath:
            return None

    def find_all_dependencies(self, device_id: str) -> List[str]:
        """
        查找设备的所有依赖设备
        :param device_id: 设备ID
        :return: 依赖设备ID列表
        """
        dependencies = []
        for neighbor in nx.descendants(self.graph, device_id):
            dependencies.append(neighbor)
        return dependencies

    def find_interfering_devices(self, device_id: str) -> List[str]:
        """
        查找可能干扰指定设备的所有设备
        :param device_id: 设备ID
        :return: 干扰设备ID列表
        """
        interferers = []
        for source, target, attrs in self.graph.in_edges(device_id, data=True):
            if attrs.get("relation") == "interferes":
                interferers.append(source)
        return interferers

    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        获取图谱统计信息
        :return: 统计字典
        """
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "avg_degree": sum(dict(self.graph.degree()).values()) / max(self.graph.number_of_nodes(), 1),
            "number_of_connected_components": nx.number_weakly_connected_components(self.graph),
            "device_nodes": sum(1 for _, attrs in self.graph.nodes(data=True) if attrs.get("category") == "device"),
            "airport_nodes": sum(1 for _, attrs in self.graph.nodes(data=True) if attrs.get("category") == "airport"),
            "relation_types": sorted(set(attrs.get("relation") for _, _, attrs in self.graph.edges(data=True)))
        }

    def to_cypher(self) -> str:
        """
        生成Neo4j Cypher语句
        :return: Cypher语句字符串
        """
        cypher_parts = []
        
        for node_id, attrs in self.graph.nodes(data=True):
            node_type = attrs.get("category", "Device").upper()
            props = []
            for key, value in attrs.items():
                if key != "category":
                    if isinstance(value, str):
                        props.append(f"{key}: '{value}'")
                    else:
                        props.append(f"{key}: {value}")
            props_str = ", ".join(props)
            cypher_parts.append(f"CREATE ({node_id}:{node_type} {{{props_str}}})")
        
        for source, target, attrs in self.graph.edges(data=True):
            rel_type = attrs.get("relation", "RELATED_TO").upper()
            cypher_parts.append(f"CREATE ({source})-[:{rel_type}]->({target})")
        
        return "\n".join(cypher_parts)

    def __repr__(self):
        return f"<DeviceKnowledgeGraph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges>"
