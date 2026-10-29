from typing import Dict, List, Any


def compute_network_effect(devices: List[Any]) -> Dict[str, float]:
    """
    模拟设备间互相影响：一个设备异常 → 影响周围设备
    """
    effects: Dict[str, float] = {}

    for device in devices:
        if device.health < 0.5:
            for other in devices:
                if other != device:
                    device_type = other.device_type
                    effects[device_type] = effects.get(device_type, 0) + 0.2

    return effects


def get_device_chain(device_id: str, coupling_matrix: Dict) -> List[Dict]:
    """
    获取设备上下游链路关系
    """
    chain = []
    for (src, dst), coupling in coupling_matrix.items():
        if src == device_id:
            chain.append({
                'device_id': dst,
                'coupling_type': coupling.get('type', 'unknown'),
                'coupling_strength': coupling.get('strength', 0.1)
            })
    return chain