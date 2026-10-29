from typing import Dict


class SpatialDevice:
    """
    空间设备类：设备拥有空间坐标
    """

    def __init__(self, device_id: str, device_type: str, x: float, y: float):
        self.device_id = device_id
        self.device_type = device_type
        self.x = x
        self.y = y
        self.health = 1.0
        self.status = "NORMAL"
        self.temperature = 25.0
        self.signal_strength = -60.0

    def to_dict(self) -> Dict:
        return {
            'device_id': self.device_id,
            'device_type': self.device_type,
            'location': {'x': self.x, 'y': self.y},
            'health': self.health,
            'status': self.status,
            'temperature': self.temperature,
            'signal_strength': self.signal_strength
        }