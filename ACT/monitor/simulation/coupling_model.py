import math
import random
from typing import Dict, Any, List


class ATCCouplingModel:
    """
    空管设备四维耦合统一模型（工业级升级版本）
    包含:
    1. 空间耦合 (Spatial Coupling)
    2. 电磁干扰耦合 (Interference Coupling)
    3. 运行负载耦合 (Load Coupling)
    4. 故障传播耦合 (Failure Propagation Coupling)

    升级特性:
    - NGSI-LD 语义对齐输出
    - 耦合强度矩阵 (Coupling Matrix)
    - ODE风格连续微分演化
    - 状态传播图 (Graph Dynamics)
    """

    DEFAULT_COUPLING_MATRIX = {
        ("VHF", "VHF"): 1.0,
        ("VHF", "ILS"): 0.6,
        ("VHF", "VOR"): 0.7,
        ("VHF", "DME"): 0.5,
        ("VHF", "HF"): 0.4,
        ("ILS", "VHF"): 0.6,
        ("ILS", "ILS"): 1.0,
        ("ILS", "VOR"): 0.8,
        ("ILS", "DME"): 0.9,
        ("VOR", "VHF"): 0.7,
        ("VOR", "ILS"): 0.8,
        ("VOR", "VOR"): 1.0,
        ("VOR", "DME"): 0.6,
        ("DME", "VHF"): 0.5,
        ("DME", "ILS"): 0.9,
        ("DME", "VOR"): 0.6,
        ("DME", "DME"): 1.0,
        ("HF", "VHF"): 0.4,
        ("HF", "HF"): 1.0,
    }

    DEFAULT_SPATIAL_COUPLING = {
        ("VHF", "VHF"): 0.8,
        ("VHF", "ILS"): 0.3,
        ("ILS", "ILS"): 0.9,
        ("ILS", "VOR"): 0.4,
    }

    DEFAULT_INTERFERENCE_COUPLING = {
        ("VHF", "VHF"): 1.2,
        ("VHF", "ILS"): 0.5,
        ("ILS", "VOR"): 0.3,
    }

    DEFAULT_LOAD_COUPLING = {
        ("VHF", "VHF"): 0.9,
        ("VHF", "ILS"): 0.7,
        ("ILS", "VOR"): 0.5,
    }

    DEFAULT_FAULT_COUPLING = {
        ("VHF", "VHF"): 1.0,
        ("VHF", "ILS"): 0.8,
        ("ILS", "VOR"): 0.6,
        ("DME", "ILS"): 0.9,
    }

    def __init__(self, devices: List[Any], dt: float = 0.1, coupling_matrix: Dict = None):
        """
        初始化耦合模型
        :param devices: 设备列表 (包含坐标等属性)
        :param dt: 时间步长 (微分演化步长)
        :param coupling_matrix: 自定义耦合强度矩阵
        """
        self.devices = devices
        self.dt = dt

        self.coupling_matrix = coupling_matrix if coupling_matrix else self.DEFAULT_COUPLING_MATRIX

        self.spatial_coupling = self.DEFAULT_SPATIAL_COUPLING
        self.interference_coupling = self.DEFAULT_INTERFERENCE_COUPLING
        self.load_coupling = self.DEFAULT_LOAD_COUPLING
        self.fault_coupling = self.DEFAULT_FAULT_COUPLING

        self.adjacency_graph = self._build_adjacency_graph()

        self.state_cache = {
            dev.device_id: {
                "temperature": 40.0,
                "signal_strength": -70.0,
                "load": random.uniform(0.3, 0.5),
                "fault": False,
                "voltage": 220.0,
                "device_type": dev.device_type,
                "position_x": float(dev.position_x) if hasattr(dev, 'position_x') else 0.0,
                "position_y": float(dev.position_y) if hasattr(dev, 'position_y') else 0.0,
                "position_z": float(dev.position_z) if hasattr(dev, 'position_z') else 0.0,
            } for dev in devices
        }

    def _build_adjacency_graph(self) -> Dict[str, List[str]]:
        """
        构建设备邻接图
        根据设备类型和距离自动构建传播关系图
        """
        graph = {}
        for dev in self.devices:
            graph[dev.device_id] = []
            for other in self.devices:
                if dev.device_id != other.device_id:
                    dist = self._distance(dev, other)
                    if dist < 5000.0:
                        coupling_weight = self.coupling_matrix.get(
                            (dev.device_type, other.device_type),
                            0.2
                        )
                        if coupling_weight > 0.1:
                            graph[dev.device_id].append(other.device_id)
        return graph

    def _distance(self, d1: Any, d2: Any) -> float:
        """计算两设备间的欧式距离"""
        dx = float(d1.position_x) - float(d2.position_x) if hasattr(d1, 'position_x') else 0.0
        dy = float(d1.position_y) - float(d2.position_y) if hasattr(d1, 'position_y') else 0.0
        dz = float(d1.position_z) - float(d2.position_z) if hasattr(d1, 'position_z') else 0.0
        dist = math.sqrt(dx**2 + dy**2 + dz**2)
        return max(dist, 0.1)

    def _get_coupling_weight(self, source_type: str, target_type: str,
                             coupling_type: str = "general") -> float:
        """
        获取耦合强度权重
        :param source_type: 源设备类型
        :param target_type: 目标设备类型
        :param coupling_type: 耦合类型 (general/spatial/interference/load/fault)
        """
        matrices = {
            "general": self.coupling_matrix,
            "spatial": self.spatial_coupling,
            "interference": self.interference_coupling,
            "load": self.load_coupling,
            "fault": self.fault_coupling,
        }
        matrix = matrices.get(coupling_type, self.coupling_matrix)
        return matrix.get((source_type, target_type), 0.2)

    def step(self, env_state: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """
        时间步进演化计算（ODE风格连续微分演化）
        dS/dt = F(S, E, C)
        :param env_state: 字典, 包含当前环境状态
        :return: 字典, 每个设备的新状态（原始数值格式，保持兼容性）
        """
        new_states = {}

        for target_dev in self.devices:
            target_id = target_dev.device_id
            target_type = target_dev.device_type
            curr_state = self.state_cache[target_id]

            neighbors = [d for d in self.devices if d.device_id != target_id]

            spatial_effect_temp = 0.0
            interference_effect = 0.0
            propagation_load_increase = 0.0
            propagation_signal_drop = 0.0

            for neighbor in neighbors:
                dist = self._distance(target_dev, neighbor)
                neighbor_state = self.state_cache[neighbor.device_id]
                neighbor_type = neighbor.device_type

                spatial_weight = self._get_coupling_weight(target_type, neighbor_type, "spatial")
                interference_weight = self._get_coupling_weight(target_type, neighbor_type, "interference")
                load_weight = self._get_coupling_weight(target_type, neighbor_type, "load")
                fault_weight = self._get_coupling_weight(target_type, neighbor_type, "fault")

                if dist < 50.0:
                    spatial_effect_temp += 0.5 / dist * spatial_weight

                power = 50.0
                interference_effect += power / ((dist ** 2) * (1.0 / interference_weight))

                if neighbor_state["fault"]:
                    propagation_load_increase += 0.2 / max(dist / 100, 1.0) * load_weight
                    propagation_signal_drop += 1.5 / max(dist / 100, 1.0) * fault_weight

            total_interference = env_state.get('interference_level', 0.1) + interference_effect * 0.01

            base_load = env_state.get('traffic_pressure', 0.5)
            dLoad = (base_load - curr_state["load"]) * 0.5 + random.uniform(-0.05, 0.05)
            new_load = curr_state["load"] + dLoad * self.dt
            new_load = min(new_load + propagation_load_increase, 1.0)
            new_load = max(new_load, 0.1)

            env_temp = env_state.get('env_temp', 25.0)
            target_temp = env_temp + (new_load * 15.0) + spatial_effect_temp
            dT = (target_temp - curr_state["temperature"]) * 0.8 + random.uniform(-0.3, 0.3)
            new_temp = curr_state["temperature"] + dT * self.dt

            base_signal = -60.0
            target_signal = base_signal - (total_interference * 20.0) - propagation_signal_drop
            dS = (target_signal - curr_state["signal_strength"]) * 0.6 + random.uniform(-1.0, 1.0)
            new_signal = curr_state["signal_strength"] + dS * self.dt

            base_voltage = 220.0 if target_type in ['VHF', 'ILS', 'VOR', 'DME', 'HF'] else 12.0
            dV = -(new_load * (base_voltage * 0.02)) + random.uniform(-0.3, 0.3)
            new_voltage = curr_state["voltage"] + dV * self.dt

            is_fault = new_temp > 65.0 or new_signal < -95.0 or new_load >= 0.98

            new_states[target_id] = {
                "temperature": round(new_temp, 2),
                "signal_strength": round(new_signal, 2),
                "load": round(new_load, 2),
                "voltage": round(new_voltage, 2),
                "fault": is_fault,
                "interference": round(total_interference, 3),
                "device_type": target_type,
            }

        self.state_cache = new_states
        return new_states

    def propagate_graph(self, steps: int = 1) -> Dict[str, Dict[str, Any]]:
        """
        基于状态传播图的故障传播模拟
        :param steps: 传播步数
        :return: 传播后的设备状态
        """
        for _ in range(steps):
            new_states = self.state_cache.copy()

            for node_id, neighbors in self.adjacency_graph.items():
                if self.state_cache[node_id]["fault"]:
                    fault_impact = self.state_cache[node_id]["load"] * 0.3
                    for neighbor_id in neighbors:
                        if neighbor_id in new_states:
                            new_states[neighbor_id]["load"] = min(
                                new_states[neighbor_id]["load"] + fault_impact * self.dt,
                                1.0
                            )
                            new_states[neighbor_id]["signal_strength"] = max(
                                new_states[neighbor_id]["signal_strength"] - fault_impact * 2.0 * self.dt,
                                -120.0
                            )

            self.state_cache = new_states

        return self.state_cache

    def to_ngsi_ld(self) -> List[Dict[str, Any]]:
        """
        将当前状态转换为 NGSI-LD Entity 格式
        对齐 FIWARE Context Broker 标准
        """
        ngsi_entities = []
        for target_dev in self.devices:
            target_id = target_dev.device_id
            state = self.state_cache[target_id]

            entity = {
                "id": f"urn:ngsi-ld:Device:{target_id}",
                "type": "Device",
                "@context": [
                    "/static/ngsi-ld/ngsi-ld-core-context.jsonld",
                    "/static/ngsi-ld/atc-monitor-context.jsonld"
                ],
                "deviceId": {
                    "type": "Property",
                    "value": target_id
                },
                "deviceType": {
                    "type": "Property",
                    "value": state["device_type"]
                },
                "temperature": {
                    "type": "Property",
                    "value": state["temperature"]
                },
                "signalStrength": {
                    "type": "Property",
                    "value": state["signal_strength"]
                },
                "load": {
                    "type": "Property",
                    "value": state["load"]
                },
                "voltage": {
                    "type": "Property",
                    "value": state["voltage"]
                },
                "fault": {
                    "type": "Property",
                    "value": state["fault"]
                },
                "interference": {
                    "type": "Property",
                    "value": state["interference"]
                },
                "observedAt": {
                    "type": "Property",
                    "value": random.uniform(0, 1e18)
                }
            }

            if hasattr(target_dev, 'location') and target_dev.location:
                entity["location"] = {
                    "type": "Property",
                    "value": target_dev.location
                }

            ngsi_entities.append(entity)

        return ngsi_entities

    def get_coupling_matrix(self) -> Dict:
        """获取当前耦合矩阵"""
        return self.coupling_matrix

    def get_adjacency_graph(self) -> Dict[str, List[str]]:
        """获取邻接图结构"""
        return self.adjacency_graph

    def get_device_state(self, device_id: str) -> Dict[str, Any]:
        """获取单个设备的当前状态"""
        return self.state_cache.get(device_id, {})

    def set_device_state(self, device_id: str, state: Dict[str, Any]) -> None:
        """设置单个设备的状态"""
        if device_id in self.state_cache:
            self.state_cache[device_id].update(state)

    def inject_fault(self, device_id: str, fault_type: str = "temperature") -> None:
        """
        注入故障模拟
        :param device_id: 设备ID
        :param fault_type: 故障类型 (temperature/signal/load)
        """
        if device_id in self.state_cache:
            if fault_type == "temperature":
                self.state_cache[device_id]["temperature"] = 75.0
            elif fault_type == "signal":
                self.state_cache[device_id]["signal_strength"] = -100.0
            elif fault_type == "load":
                self.state_cache[device_id]["load"] = 0.99