import math
from typing import List, Dict, Tuple
from .spatial_device import SpatialDevice


def calculate_distance(a: SpatialDevice, b: SpatialDevice) -> float:
    """
    计算两个设备间的欧几里得距离
    """
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)


def get_neighbors(device: SpatialDevice, devices: List[SpatialDevice], radius: float = 5.0) -> List[Dict]:
    """
    获取半径范围内的邻居设备（核心GIS功能）
    """
    neighbors = []
    for d in devices:
        if d != device:
            dist = calculate_distance(d, device)
            if dist < radius:
                neighbors.append({
                    'device_id': d.device_id,
                    'distance': round(dist, 2),
                    'health': d.health
                })
    return neighbors


def get_regional_devices(center: Tuple[float, float], devices: List[SpatialDevice], radius: float) -> List[Dict]:
    """
    获取区域内所有设备
    """
    center_device = SpatialDevice("CENTER", "VIRTUAL", center[0], center[1])
    return get_neighbors(center_device, devices, radius)