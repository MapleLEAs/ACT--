import random
from datetime import datetime
from typing import List
from .event_bus import EventBus
from .events import Event, EventType


def random_event_generator(bus: EventBus, devices: List[object]) -> None:
    """
    随机事件生成器：按概率触发各类事件
    """

    if random.random() < 0.02:
        bus.emit(Event(EventType.WEATHER_CHANGE, {
            "weather": random.choice(["RAIN", "WIND", "CLEAR"]),
            "intensity": random.uniform(0.5, 1.0)
        }))

    if random.random() < 0.01:
        fault_device = random.choice(devices)
        bus.emit(Event(EventType.DEVICE_FAILURE, {
            "device_id": fault_device.device_id,
            "fault_type": random.choice(["overheat", "signal_loss", "hardware_failure"]),
            "severity": random.choice(["WARN", "ERROR", "CRITICAL"])
        }))

    if random.random() < 0.03:
        bus.emit(Event(EventType.LOAD_SPIKE, {
            "region": random.choice(["tower", "runway_A", "runway_B"]),
            "load_increase": random.uniform(0.2, 0.5)
        }))