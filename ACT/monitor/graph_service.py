from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from django.conf import settings

from core.models import DeviceAlarmLink, WorkOrder
from core.knowledge_graph import DeviceKnowledgeGraph
from monitor.models import Alarm, AlarmEvent, Device, DeviceStatusLog, PredictionResult

try:
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover - optional dependency
    GraphDatabase = None


@dataclass
class GraphPayload:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    root_candidates: list[dict[str, Any]]
    path_explanations: list[str]
    provider: str


class RootCauseGraphService:
    def __init__(self) -> None:
        self._driver = None
        if GraphDatabase is not None:
            try:
                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                )
            except Exception:
                self._driver = None

    @property
    def available(self) -> bool:
        return self._driver is not None

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()

    def build_alarm_graph(self, alarm_id: int) -> GraphPayload:
        alarm = Alarm.objects.select_related('device', 'rule').filter(id=alarm_id).first()
        if not alarm:
            return GraphPayload([], [], [], ['未找到对应告警'], 'relational')

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        def add_node(node_id: str, label: str, category: str, **extra: Any) -> None:
            if not any(node['id'] == node_id for node in nodes):
                nodes.append({'id': node_id, 'name': label, 'category': category, **extra})

        def add_edge(source: str, target: str, relation: str) -> None:
            edges.append({'source': source, 'target': target, 'value': relation})

        device = alarm.device
        device_node_id = f'device:{device.device_id}'
        alarm_node_id = f'alarm:{alarm.id}'
        add_node(device_node_id, device.device_id, 'device', device_type=device.device_type)
        add_node(alarm_node_id, alarm.alarm_id, 'alarm', severity=alarm.severity, status=alarm.status)
        add_edge(device_node_id, alarm_node_id, 'TRIGGERED')

        if alarm.rule_id:
            rule_node_id = f'rule:{alarm.rule_id}'
            add_node(rule_node_id, alarm.rule.name if alarm.rule else f'规则 {alarm.rule_id}', 'rule')
            add_edge(rule_node_id, alarm_node_id, 'DERIVED_FROM')

        latest_log = DeviceStatusLog.objects.filter(device=device).order_by('-collect_time').first()
        if latest_log:
            log_node_id = f'log:{latest_log.id}'
            add_node(
                log_node_id,
                latest_log.collect_time.strftime('%m-%d %H:%M'),
                'status',
                alarm_flag=latest_log.alarm_flag,
                device_status=latest_log.device_status,
            )
            add_edge(device_node_id, log_node_id, 'LATEST_STATUS')
            add_edge(log_node_id, alarm_node_id, 'AFFECTS')

        recent_predictions = PredictionResult.objects.filter(device=device).order_by('-prediction_time')[:3]
        for prediction in recent_predictions:
            pred_node_id = f'prediction:{prediction.id}'
            add_node(
                pred_node_id,
                prediction.metric if hasattr(prediction, 'metric') else '预测结果',
                'prediction',
                confidence=getattr(prediction, 'confidence_score', None),
            )
            add_edge(pred_node_id, device_node_id, 'RELATED_TO')

        related_links = DeviceAlarmLink.objects.filter(device=device).select_related('alarm_rule')[:5]
        for link in related_links:
            link_rule_id = f'link-rule:{link.alarm_rule_id}'
            add_node(link_rule_id, link.alarm_rule.name, 'rule')
            add_edge(device_node_id, link_rule_id, 'RULE_BOUND')

        work_orders = WorkOrder.objects.filter(device=device).order_by('-created_at')[:3]
        for order in work_orders:
            order_node_id = f'workorder:{order.id}'
            add_node(order_node_id, order.title, 'workorder', status=order.status, priority=order.priority)
            add_edge(order_node_id, device_node_id, 'HANDLED_BY')

        alarm_events = AlarmEvent.objects.filter(alarm=alarm).order_by('event_time')[:5]
        for event in alarm_events:
            event_node_id = f'event:{event.id}'
            add_node(event_node_id, event.get_event_type_display(), 'event', operator=event.operator)
            add_edge(alarm_node_id, event_node_id, 'HAS_EVENT')

        root_candidates = [
            {
                'node_id': device_node_id,
                'name': device.device_id,
                'score': 0.92,
                'reason': '告警、最新状态和关联规则均指向同一设备',
            }
        ]
        path_explanations = [
            f"设备 {device.device_id} 的最新状态与告警 {alarm.alarm_id} 直接关联",
        ]

        return GraphPayload(nodes, edges, root_candidates, path_explanations, 'relational')

    def build_device_path(self, device_id: str) -> GraphPayload:
        device = Device.objects.filter(device_id=device_id).first()
        if not device:
            return GraphPayload([], [], [], ['未找到对应设备'], 'relational')

        recent_alarms = Alarm.objects.filter(device=device).order_by('-trigger_time')[:5]
        payload = self.build_alarm_graph(recent_alarms[0].id) if recent_alarms else GraphPayload([], [], [], [], 'relational')
        if not recent_alarms:
            payload.nodes.append({'id': f'device:{device.device_id}', 'name': device.device_id, 'category': 'device'})
            payload.path_explanations.append('该设备暂无告警，当前仅展示设备节点')
        return payload

    def sync_recent_data(self) -> dict[str, Any]:
        if not self.available:
            return {'synced': False, 'provider': 'relational', 'message': 'Neo4j 未连接，已跳过实际同步'}

        synced_nodes = 0
        synced_edges = 0
        try:
            with self._driver.session() as session:
                devices = Device.objects.all()[:200]
                for device in devices:
                    session.run(
                        """
                        MERGE (d:Device {id: $id})
                        SET d.name = $name, d.type = $type, d.location = $location
                        """,
                        id=device.device_id,
                        name=device.device_id,
                        type=device.device_type,
                        location=device.location or '',
                    )
                    synced_nodes += 1
                    if device.location:
                        session.run(
                            """
                            MERGE (l:Location {name: $location})
                            WITH l
                            MATCH (d:Device {id: $device_id})
                            MERGE (d)-[:LOCATED_IN]->(l)
                            """,
                            location=device.location,
                            device_id=device.device_id,
                        )
                        synced_edges += 1

                alarms = Alarm.objects.select_related('device', 'rule').order_by('-trigger_time')[:200]
                for alarm in alarms:
                    session.run(
                        """
                        MERGE (a:Alarm {id: $id})
                        SET a.name = $name, a.severity = $severity, a.status = $status
                        WITH a
                        MATCH (d:Device {id: $device_id})
                        MERGE (d)-[:TRIGGERED]->(a)
                        """,
                        id=str(alarm.id),
                        name=alarm.alarm_id,
                        severity=alarm.severity,
                        status=alarm.status,
                        device_id=alarm.device.device_id,
                    )
                    synced_nodes += 1
                    synced_edges += 1
                    if alarm.rule_id:
                        session.run(
                            """
                            MERGE (r:AlarmRule {id: $id})
                            SET r.name = $name
                            WITH r
                            MATCH (a:Alarm {id: $alarm_id})
                            MERGE (r)-[:DERIVED_FROM]->(a)
                            """,
                            id=str(alarm.rule_id),
                            name=alarm.rule.name if alarm.rule else f'规则 {alarm.rule_id}',
                            alarm_id=str(alarm.id),
                        )
                        synced_nodes += 1
                        synced_edges += 1

                predictions = PredictionResult.objects.select_related('device').order_by('-prediction_time')[:100]
                for prediction in predictions:
                    session.run(
                        """
                        MERGE (p:Prediction {id: $id})
                        SET p.metric = $metric, p.confidence = $confidence
                        WITH p
                        MATCH (d:Device {id: $device_id})
                        MERGE (p)-[:RELATED_TO]->(d)
                        """,
                        id=str(prediction.id),
                        metric=prediction.metric,
                        confidence=float(prediction.confidence_score or 0),
                        device_id=prediction.device.device_id,
                    )
                    synced_nodes += 1
                    synced_edges += 1
        except Exception as exc:
            return {
                'synced': False,
                'provider': 'neo4j',
                'message': f'Neo4j 同步失败: {exc}',
            }

        return {
            'synced': True,
            'provider': 'neo4j',
            'message': 'Neo4j 同步完成',
            'synced_nodes': synced_nodes,
            'synced_edges': synced_edges,
        }

    def sync_alarm(self, alarm: Alarm) -> None:
        if not self.available:
            return
        alarm = Alarm.objects.select_related('device', 'rule').get(pk=alarm.pk)
        with self._driver.session() as session:
            session.run(
                """
                MERGE (d:Device {id: $device_id})
                SET d.name = $device_id, d.type = $device_type
                MERGE (a:Alarm {id: $alarm_id})
                SET a.name = $alarm_name, a.severity = $severity, a.status = $status
                MERGE (d)-[:TRIGGERED]->(a)
                """,
                device_id=alarm.device.device_id,
                device_type=alarm.device.device_type,
                alarm_id=str(alarm.id),
                alarm_name=alarm.alarm_id,
                severity=alarm.severity,
                status=alarm.status,
            )
            if alarm.rule_id:
                session.run(
                    """
                    MERGE (r:AlarmRule {id: $rule_id})
                    SET r.name = $rule_name
                    WITH r
                    MATCH (a:Alarm {id: $alarm_id})
                    MERGE (r)-[:DERIVED_FROM]->(a)
                    """,
                    rule_id=str(alarm.rule_id),
                    rule_name=alarm.rule.name if alarm.rule else f'规则 {alarm.rule_id}',
                    alarm_id=str(alarm.id),
                )

    def build_coupling_graph(self) -> GraphPayload:
        kg = DeviceKnowledgeGraph()
        kg.build_coupling_graph()
        graph_data = kg.get_graph_data()
        
        return GraphPayload(
            nodes=graph_data["nodes"],
            edges=graph_data["edges"],
            root_candidates=[],
            path_explanations=["设备耦合关系图已构建完成"],
            provider='knowledge_graph'
        )

    def build_device_knowledge_graph(self) -> Dict[str, Any]:
        kg = DeviceKnowledgeGraph()
        devices = Device.objects.all()
        
        from core.ngsi_ld import EntityFactory
        entities = []
        for device in devices:
            entity = EntityFactory.create_device_entity(device)
            entities.append(entity)
        
        kg.build_from_ngsi_entities(entities)
        graph_data = kg.get_graph_data()
        
        return {
            **graph_data,
            'statistics': kg.get_graph_statistics(),
            'provider': 'knowledge_graph'
        }

    def find_interference_path(self, source_id: str, target_id: str) -> Dict[str, Any]:
        kg = DeviceKnowledgeGraph()
        kg.build_coupling_graph()
        
        path = kg.find_interference_path(source_id, target_id)
        
        if path:
            return {
                'path': path,
                'path_length': len(path) - 1,
                'message': f'找到从 {source_id} 到 {target_id} 的干扰路径',
                'success': True
            }
        else:
            return {
                'path': [],
                'path_length': 0,
                'message': f'未找到从 {source_id} 到 {target_id} 的路径',
                'success': False
            }

    def get_device_dependencies(self, device_id: str) -> Dict[str, Any]:
        kg = DeviceKnowledgeGraph()
        kg.build_coupling_graph()
        
        dependencies = kg.find_all_dependencies(device_id)
        interferers = kg.find_interfering_devices(device_id)
        
        return {
            'device_id': device_id,
            'dependencies': dependencies,
            'interferers': interferers,
            'total_dependencies': len(dependencies),
            'total_interferers': len(interferers)
        }

    def sync_coupling_graph(self) -> Dict[str, Any]:
        if not self.available:
            return {'synced': False, 'provider': 'knowledge_graph', 'message': 'Neo4j 未连接，已跳过同步'}

        kg = DeviceKnowledgeGraph()
        kg.build_coupling_graph()
        cypher = kg.to_cypher()

        try:
            with self._driver.session() as session:
                for query in cypher.split('\n'):
                    if query.strip():
                        session.run(query.strip())
            
            return {
                'synced': True,
                'provider': 'neo4j',
                'message': '设备耦合关系图已同步到Neo4j',
                'nodes': kg.graph.number_of_nodes(),
                'edges': kg.graph.number_of_edges()
            }
        except Exception as exc:
            return {
                'synced': False,
                'provider': 'neo4j',
                'message': f'同步失败: {exc}'
            }
