import random
from typing import Dict
from .environment_state import EnvironmentState


class DeviceSimulator:
    """
    设备模拟器：不再独立生成，而是受环境和其他设备影响
    """

    def __init__(self, device_id: str, device_type: str, base_temp: float, sensitivity: float):
        self.device_id = device_id
        self.device_type = device_type
        self.base_temp = base_temp
        self.sensitivity = sensitivity
        self.health = 1.0
        self.status = "NORMAL"

    def update(self, env: EnvironmentState, neighbor_load: float = 0) -> Dict:
        """
        更新设备状态（受环境 + 邻居设备影响）
        """
        temperature = (
            self.base_temp
            + env.current_temp * self.sensitivity
            + neighbor_load * 5
            + random.uniform(-1, 1)
        )

        signal_strength = 0
        if self.device_type == "VHF":
            signal_strength = -60 - env.interference_level * 20 - neighbor_load * 10
        elif self.device_type == "ILS":
            signal_strength = -65 - env.interference_level * 15 - neighbor_load * 8

        if temperature > 70:
            self.health -= 0.01
        if signal_strength < -85:
            self.health -= 0.02

        if self.health < 0.7:
            self.status = "WARN"
        if self.health < 0.4:
            self.status = "ALARM"

        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "temperature": round(temperature, 2),
            "signal_strength": round(signal_strength, 2),
            "health": round(self.health, 3),
            "status": self.status
        }