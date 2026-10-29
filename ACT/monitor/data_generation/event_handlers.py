from typing import List
from .events import Event, EventType
from .environment_state import EnvironmentState


def handle_weather_change(event: Event, env: EnvironmentState) -> None:
    """处理天气变化事件"""
    if event.type != EventType.WEATHER_CHANGE:
        return
    new_weather = event.payload['weather']
    env.weather = new_weather


def handle_device_failure(event: Event, devices: List[object]) -> None:
    """处理设备故障事件"""
    if event.type != EventType.DEVICE_FAILURE:
        return
    device_id = event.payload['device_id']
    fault_type = event.payload['fault_type']

    target_device = next((d for d in devices if d.device_id == device_id), None)

    if target_device:
        if fault_type == "overheat":
            target_device.health -= 0.3
            target_device.status = "ALARM"
        elif fault_type == "signal_loss":
            target_device.health -= 0.2
            target_device.status = "WARN"


def handle_load_spike(event: Event, devices: List[object]) -> None:
    """处理负载突增事件"""
    if event.type != EventType.LOAD_SPIKE:
        return
    region = event.payload['region']
    load_increase = event.payload['load_increase']

    for device in devices:
        device.health -= load_increase * 0.1