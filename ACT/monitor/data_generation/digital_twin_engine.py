import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atc_monitor.settings')
django.setup()

from datetime import timedelta, datetime
from typing import List, Dict

from django.utils import timezone

from core.simulation import (
    DeviceCouplingMatrix,
    EventDrivenGenerator,
    SpatialQueryEngine,
    TrendBasedPredictor,
    CascadeAlarmEngine,
    DataQualityEngine,
    DataGenerationManager
)

from .environment_state import EnvironmentState
from monitor.models import Device, DeviceStatusLog, EnvironmentData, PredictionResult


class DigitalTwinEngine:
    """
    数字孪生引擎：整合所有模块，真正运行的系统
    集成 core/simulation 模块和 Django ORM
    """

    def __init__(self):
        self.env = EnvironmentState()
        self.coupling_matrix = DeviceCouplingMatrix()
        self.event_generator = EventDrivenGenerator()
        self.spatial_engine = SpatialQueryEngine()
        self.predictor = TrendBasedPredictor()
        self.alarm_engine = CascadeAlarmEngine()
        self.quality_engine = DataQualityEngine()
        self.data_manager = DataGenerationManager()

        self._init_devices()

        self.history = []

    def _init_devices(self):
        """初始化设备：从数据库加载或创建测试设备"""
        from django.contrib.auth.models import User
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')

        device_configs = [
            {'device_id': 'VHF-001', 'device_type': 'VHF', 'position_x': 0, 'position_y': 10},
            {'device_id': 'VHF-002', 'device_type': 'VHF', 'position_x': 0, 'position_y': 20},
            {'device_id': 'ILS-001', 'device_type': 'ILS', 'position_x': 100, 'position_y': 50},
            {'device_id': 'DME-001', 'device_type': 'DME', 'position_x': 120, 'position_y': 60},
            {'device_id': 'VOR-001', 'device_type': 'VOR', 'position_x': 80, 'position_y': 40},
            {'device_id': 'HF-001', 'device_type': 'HF', 'position_x': 200, 'position_y': 100},
        ]

        for config in device_configs:
            Device.objects.get_or_create(
                device_id=config['device_id'],
                defaults={
                    'device_type': config['device_type'],
                    'position_x': config['position_x'],
                    'position_y': config['position_y'],
                    'position_z': 0,
                    'geo_location': {'type': 'Point', 'coordinates': [config['position_x'], config['position_y']]},
                    'owner': admin_user,
                }
            )

        self.devices = Device.objects.all()

    def simulate_step(self, t: datetime) -> Dict:
        """
        模拟一个时间步（核心循环）
        """
        self.env.update(t)

        self.event_generator.initialize_device_states([d.device_id for d in self.devices])

        device_states = []
        for device in self.devices:
            device_state = self._update_device_state(device, t)
            device_states.append(device_state)

        event = self.event_generator.generate_next_event(t)
        if event:
            self.event_generator.event_handlers[event.type](event)

        predictions = self._generate_predictions(device_states, t)

        warnings = self._generate_warnings(predictions, device_states)

        heat_map = self._generate_spatial_heat_map(device_states)

        self._persist_data(t, device_states, predictions)

        return {
            'timestamp': t,
            'environment': self.env.to_dict(),
            'devices': device_states,
            'predictions': predictions,
            'warnings': warnings,
            'heat_map': heat_map,
        }

    def _update_device_state(self, device: Device, t: datetime) -> Dict:
        """更新单个设备状态"""
        env_effect = self.env.current_temp * 0.1
        neighbor_effect = self._calculate_neighbor_effect(device)

        temperature = round(
            25.0
            + env_effect
            + neighbor_effect * 5
            + (self.env.interference_level - 0.5) * 2,
            2
        )

        signal_strength = -60.0
        if device.device_type == "VHF":
            signal_strength = round(
                -60 - self.env.interference_level * 20 - neighbor_effect * 10,
                2
            )
        elif device.device_type == "ILS":
            signal_strength = round(
                -65 - self.env.interference_level * 15 - neighbor_effect * 8,
                2
            )

        health = 1.0
        if temperature > 70:
            health -= 0.01
        if signal_strength < -85:
            health -= 0.02

        status = "NORMAL"
        if health < 0.7:
            status = "WARN"
        if health < 0.4:
            status = "ALARM"

        return {
            'device_id': device.device_id,
            'device_type': device.device_type,
            'temperature': temperature,
            'signal_strength': signal_strength,
            'health': round(health, 3),
            'status': status,
            'position_x': float(device.position_x),
            'position_y': float(device.position_y),
        }

    def _calculate_neighbor_effect(self, device: Device) -> float:
        """计算邻居设备影响"""
        effect = 0.0
        for other in self.devices:
            if other != device:
                dist = ((float(other.position_x) - float(device.position_x)) ** 2 +
                        (float(other.position_y) - float(device.position_y)) ** 2) ** 0.5
                if dist < 50:
                    effect += 0.1
        return effect

    def _generate_predictions(self, device_states: List[Dict], t: datetime) -> Dict:
        """生成预测结果"""
        predictions = {}
        for state in device_states:
            try:
                prediction = self.predictor.predict_with_uncertainty(
                    {'device_type': state['device_type']},
                    horizon_hours=24
                )
                predictions[state['device_id']] = prediction
            except Exception:
                predictions[state['device_id']] = {'status': 'prediction_failed'}
        return predictions

    def _generate_warnings(self, predictions: Dict, device_states: List[Dict]) -> Dict:
        """生成预警信息"""
        warnings = {}
        for state in device_states:
            device_warnings = []
            pred = predictions.get(state['device_id'], {})

            if pred.get('confidence_warning'):
                device_warnings.append({
                    'type': 'LOW_CONFIDENCE',
                    'severity': 'WARN',
                    'message': '预测置信度不足',
                })

            if state['health'] < 0.7:
                device_warnings.append({
                    'type': 'HEALTH_DECLINING',
                    'severity': 'WARN',
                    'message': '设备健康度下降',
                })

            if state['temperature'] > 60:
                device_warnings.append({
                    'type': 'HIGH_TEMPERATURE',
                    'severity': 'ERROR',
                    'message': '设备温度过高',
                })

            if device_warnings:
                warnings[state['device_id']] = {
                    'has_warning': True,
                    'warnings': device_warnings,
                    'recommended_action': self._generate_action_recommendation(device_warnings)
                }
        return warnings

    def _generate_action_recommendation(self, warnings: List[Dict]) -> str:
        """生成行动建议"""
        if not warnings:
            return "设备状态正常，无需特殊关注"

        severities = [w['severity'] for w in warnings]
        if 'ERROR' in severities:
            return "建议立即安排维护人员检查"
        elif 'WARN' in severities:
            return "建议安排巡检计划"
        else:
            return "建议持续监控"

    def _generate_spatial_heat_map(self, device_states: List[Dict]) -> List[Dict]:
        """生成空间热力图数据"""
        grid_size = 20
        heat_map = []
        for x in range(-150, 151, grid_size):
            for y in range(-150, 151, grid_size):
                grid_devices = []
                for state in device_states:
                    dist = ((state['position_x'] - x)**2 + (state['position_y'] - y)**2)**0.5
                    if dist < grid_size:
                        grid_devices.append(state)

                avg_temp = sum([d['temperature'] for d in grid_devices]) / len(grid_devices) if grid_devices else 0
                alarm_count = sum([1 for d in grid_devices if d['status'] == "ALARM"])

                heat_map.append({
                    'grid_id': f"G{x}_{y}",
                    'center': {'x': x, 'y': y},
                    'avg_temperature': round(avg_temp, 2),
                    'alarm_count': alarm_count,
                    'device_count': len(grid_devices)
                })

        return heat_map

    def _persist_data(self, t, device_states: List[Dict], predictions: Dict):
        """持久化数据到数据库"""
        device_map = {d.device_id: d for d in self.devices}
        
        for state in device_states:
            device = device_map.get(state['device_id'])

            DeviceStatusLog.objects.create(
                device=device,
                collect_time=t,
                online_status=True,
                device_status=state['status'],
                alarm_flag=(state['status'] == 'ALARM'),
                device_temperature=state['temperature'],
                signal_strength=state['signal_strength'],
            )

            EnvironmentData.objects.create(
                device=device,
                collect_time=t,
                ambient_temperature=self.env.current_temp,
                humidity=self.env.humidity,
            )

            pred = predictions.get(state['device_id'], {})
            if pred.get('predicted_value'):
                PredictionResult.objects.create(
                    device=device,
                    metric='temperature',
                    predicted_value=pred['predicted_value'],
                    prediction_time=t + timedelta(hours=24),
                    prediction_horizon=24 * 60,
                    confidence_score=pred.get('confidence', 0),
                    status='PREDICTED',
                )

    def run_simulation(self, start_time: datetime, duration_hours: int) -> List[Dict]:
        """运行完整模拟"""
        results = []
        current_time = start_time

        for _ in range(duration_hours * 12):
            step_result = self.simulate_step(current_time)
            results.append(step_result)
            current_time += timedelta(minutes=5)

        return results