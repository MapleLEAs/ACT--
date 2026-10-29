import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atc_monitor.settings')
django.setup()

import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from monitor.data_generation import (
    EnvironmentState,
    DeviceSimulator,
    EventBus,
    Event,
    EventType,
    SpatialDevice,
    calculate_distance,
    get_neighbors,
    PredictionModel,
    EarlyWarningModel,
    DigitalTwinEngine,
    compute_network_effect,
)


class TestEnvironmentState(unittest.TestCase):
    """测试全局环境状态类"""

    def test_initial_state(self):
        env = EnvironmentState()
        self.assertEqual(env.base_temp, 25.0)
        self.assertEqual(env.weather, "CLEAR")
        self.assertEqual(env.humidity, 60)

    def test_update(self):
        env = EnvironmentState()
        t = datetime(2026, 1, 1, 12, 0, 0)
        env.update(t)
        self.assertIsNotNone(env.current_temp)
        self.assertIn(env.weather, ["CLEAR", "RAIN", "WIND"])

    def test_to_dict(self):
        env = EnvironmentState()
        data = env.to_dict()
        self.assertIn('temperature', data)
        self.assertIn('weather', data)
        self.assertIn('humidity', data)
        self.assertIn('interference_level', data)


class TestDeviceSimulator(unittest.TestCase):
    """测试设备模拟器"""

    def test_initialization(self):
        device = DeviceSimulator("VHF-001", "VHF", 35.0, 0.8)
        self.assertEqual(device.device_id, "VHF-001")
        self.assertEqual(device.device_type, "VHF")
        self.assertEqual(device.health, 1.0)
        self.assertEqual(device.status, "NORMAL")

    def test_update(self):
        device = DeviceSimulator("VHF-001", "VHF", 35.0, 0.8)
        env = EnvironmentState()
        state = device.update(env)
        self.assertIn('temperature', state)
        self.assertIn('signal_strength', state)
        self.assertIn('health', state)
        self.assertIn('status', state)


class TestEventBus(unittest.TestCase):
    """测试事件总线"""

    def test_subscribe_and_emit(self):
        bus = EventBus()
        events_received = []

        def handler(event):
            events_received.append(event)

        bus.subscribe(handler)
        event = Event(EventType.WEATHER_CHANGE, {"weather": "RAIN"})
        bus.emit(event)

        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0].type, EventType.WEATHER_CHANGE)

    def test_event_history(self):
        bus = EventBus()
        event = Event(EventType.WEATHER_CHANGE, {"weather": "RAIN"})
        bus.emit(event)
        history = bus.get_event_history()
        self.assertEqual(len(history), 1)


class TestSpatialFunctions(unittest.TestCase):
    """测试空间计算函数"""

    def test_calculate_distance(self):
        device_a = SpatialDevice("DEV-A", "VHF", 0, 0)
        device_b = SpatialDevice("DEV-B", "VHF", 3, 4)
        distance = calculate_distance(device_a, device_b)
        self.assertEqual(distance, 5.0)

    def test_get_neighbors(self):
        devices = [
            SpatialDevice("DEV-A", "VHF", 0, 0),
            SpatialDevice("DEV-B", "VHF", 3, 4),
            SpatialDevice("DEV-C", "VHF", 100, 100),
        ]
        neighbors = get_neighbors(devices[0], devices, radius=10)
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]['device_id'], "DEV-B")


class TestPredictionModel(unittest.TestCase):
    """测试预测模型"""

    def test_predict_insufficient_data(self):
        predictor = PredictionModel()
        result = predictor.predict([])
        self.assertEqual(result['status'], 'insufficient_data')

    def test_predict_with_data(self):
        predictor = PredictionModel()
        historical_data = [
            {'temperature': 30.0},
            {'temperature': 31.0},
            {'temperature': 32.0},
            {'temperature': 33.0},
            {'temperature': 34.0},
            {'temperature': 35.0},
            {'temperature': 36.0},
            {'temperature': 37.0},
            {'temperature': 38.0},
            {'temperature': 39.0},
            {'temperature': 40.0},
            {'temperature': 41.0},
        ]
        result = predictor.predict(historical_data)
        self.assertIn('predicted_temperature', result)
        self.assertIn('trend', result)
        self.assertIn('confidence_interval', result)


class TestEarlyWarningModel(unittest.TestCase):
    """测试预警模型"""

    def test_no_warning(self):
        warning_model = EarlyWarningModel()
        prediction = {'trend_slope': 0.01}
        current_state = {'health': 0.9, 'signal_strength': -60}
        result = warning_model.check_early_warning(prediction, current_state)
        self.assertFalse(result['has_warning'])

    def test_health_warning(self):
        warning_model = EarlyWarningModel()
        prediction = {}
        current_state = {'health': 0.6, 'signal_strength': -60}
        result = warning_model.check_early_warning(prediction, current_state)
        self.assertTrue(result['has_warning'])
        self.assertEqual(len(result['warnings']), 1)


class TestNetworkEffects(unittest.TestCase):
    """测试设备间影响计算"""

    def test_compute_network_effect(self):
        class MockDevice:
            def __init__(self, device_type, health):
                self.device_type = device_type
                self.health = health

        devices = [
            MockDevice("VHF", 0.3),
            MockDevice("VHF", 0.8),
            MockDevice("ILS", 0.9),
        ]
        effects = compute_network_effect(devices)
        self.assertIn('VHF', effects)
        self.assertIn('ILS', effects)


class TestDigitalTwinEngine(unittest.TestCase):
    """测试数字孪生引擎"""

    def test_engine_initialization(self):
        engine = DigitalTwinEngine()
        self.assertIsNotNone(engine.env)
        self.assertIsNotNone(engine.devices)

    def test_simulate_step(self):
        engine = DigitalTwinEngine()
        t = datetime.now()
        result = engine.simulate_step(t)
        self.assertIn('timestamp', result)
        self.assertIn('environment', result)
        self.assertIn('devices', result)
        self.assertIn('predictions', result)
        self.assertIn('warnings', result)
        self.assertIn('heat_map', result)


if __name__ == '__main__':
    unittest.main()