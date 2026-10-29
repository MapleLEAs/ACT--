from enum import Enum
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime, timedelta
import random
from queue import PriorityQueue, Full
from dataclasses import dataclass, field
from .exception_handler import EventQueueOverflowError, ExceptionHandler


class EventType(Enum):
    NORMAL_EVENT = "normal"
    WEATHER_EVENT = "weather"
    FAULT_EVENT = "fault"
    RECOVERY_EVENT = "recovery"
    CASCADE_EVENT = "cascade"


@dataclass(order=True)
class Event:
    time: datetime
    type: EventType = field(compare=False)
    payload: Dict[str, Any] = field(compare=False)
    priority: int = field(compare=False, default=0)


class EventDrivenGenerator:
    """事件驱动数据生成引擎"""

    def __init__(self, max_queue_size: int = 10000):
        self.event_queue = PriorityQueue(maxsize=max_queue_size)
        self.max_queue_size = max_queue_size
        self.exception_handler = ExceptionHandler()
        self.event_handlers: Dict[EventType, Callable] = {
            EventType.NORMAL_EVENT: self.handle_normal_event,
            EventType.WEATHER_EVENT: self.handle_weather_event,
            EventType.FAULT_EVENT: self.handle_fault_event,
            EventType.RECOVERY_EVENT: self.handle_recovery_event,
            EventType.CASCADE_EVENT: self.handle_cascade_event,
        }
        self.device_states: Dict[str, Dict[str, Any]] = {}

    def _add_event_safely(self, event: Event):
        """
        安全添加事件到队列
        异常处理策略：队列溢出时丢弃低优先级事件，保留关键故障事件
        """
        try:
            self.event_queue.put(event, block=False)
        except Full:
            if event.priority >= 2:
                while True:
                    try:
                        removed_event = self.event_queue.get(block=False)
                        if removed_event.priority < event.priority:
                            self.event_queue.put(event, block=False)
                            break
                        else:
                            self.event_queue.put(removed_event, block=False)
                            break
                    except:
                        self.event_queue.put(event, block=False)
                        break
            else:
                overflow_error = EventQueueOverflowError(
                    code='QUEUE_OVERFLOW',
                    message=f'事件队列溢出，丢弃低优先级事件: {event.type.value}'
                )
                self.exception_handler.log_error('queue_overflow', overflow_error)
                self.exception_handler.handle_queue_overflow(overflow_error)

    def initialize_device_states(self, devices: List[str]):
        """
        初始化设备状态
        :param devices: 设备ID列表
        """
        for device_id in devices:
            device_type = device_id.split('-')[0]
            base_temp = 35.0 if device_type in ['VHF', 'ILS'] else 30.0
            base_signal = 95.0 if device_type in ['VHF', 'ILS', 'VOR'] else 90.0
            
            self.device_states[device_id] = {
                'temperature': base_temp,
                'signal_strength': base_signal,
                'status': 'NORMAL',
                'fault': False,
                'internal_load': random.uniform(0.3, 0.7)
            }

    def generate_next_event(self, current_time: datetime) -> Optional[Event]:
        """
        基于概率模型生成下一个事件
        :param current_time: 当前时间
        :return: 事件对象
        """
        rand = random.random()
        
        if rand < 0.95:
            return Event(
                type=EventType.NORMAL_EVENT,
                time=current_time + timedelta(minutes=5),
                payload={'fluctuation': random.gauss(0, 0.5)}
            )
        elif rand < 0.98:
            weather_types = ['rain_start', 'rain_stop', 'temperature_rise', 'temperature_drop']
            return Event(
                type=EventType.WEATHER_EVENT,
                time=current_time,
                payload={
                    'weather_change': random.choice(weather_types),
                    'intensity': random.uniform(0.3, 0.9)
                },
                priority=1
            )
        else:
            device_ids = list(self.device_states.keys())
            if device_ids:
                target_device = random.choice(device_ids)
                fault_types = ['overheat', 'signal_loss', 'power_fluctuation', 'communication_error']
                return Event(
                    type=EventType.FAULT_EVENT,
                    time=current_time,
                    payload={
                        'device_id': target_device,
                        'fault_type': random.choice(fault_types)
                    },
                    priority=2
                )
        
        return None

    def handle_normal_event(self, event: Event):
        """处理正常波动事件"""
        for device_id, state in self.device_states.items():
            fluctuation = event.payload.get('fluctuation', 0)
            state['temperature'] += fluctuation * 0.5
            state['signal_strength'] += fluctuation * 1.0
            
            state['temperature'] = max(25, min(85, state['temperature']))
            state['signal_strength'] = max(60, min(100, state['signal_strength']))

    def handle_weather_event(self, event: Event):
        """处理天气变化事件"""
        weather_change = event.payload.get('weather_change')
        intensity = event.payload.get('intensity', 0.5)
        
        for device_id, state in self.device_states.items():
            if weather_change == 'rain_start':
                state['signal_strength'] -= intensity * 15
            elif weather_change == 'rain_stop':
                state['signal_strength'] += intensity * 10
            elif weather_change == 'temperature_rise':
                state['temperature'] += intensity * 5
            elif weather_change == 'temperature_drop':
                state['temperature'] -= intensity * 3

    def handle_fault_event(self, event: Event):
        """处理设备故障事件"""
        device_id = event.payload['device_id']
        fault_type = event.payload['fault_type']
        
        if device_id not in self.device_states:
            return
        
        state = self.device_states[device_id]
        
        if fault_type == 'overheat':
            state['temperature'] += random.uniform(10, 15)
            state['status'] = 'FAULT'
            state['fault'] = True
            
            cascade_device = self._get_coupled_device(device_id)
            if cascade_device:
                cascade_event = Event(
                    type=EventType.CASCADE_EVENT,
                    time=event.time + timedelta(seconds=30),
                    payload={
                        'source': device_id,
                        'target': cascade_device,
                        'effect': 'signal_drop'
                    },
                    priority=1
                )
                self._add_event_safely(cascade_event)
        
        elif fault_type == 'signal_loss':
            state['signal_strength'] -= random.uniform(20, 40)
            state['status'] = 'DEGRADED'
        
        recovery_time = event.time + timedelta(minutes=random.randint(5, 30))
        recovery_event = Event(
            type=EventType.RECOVERY_EVENT,
            time=recovery_time,
            payload={'device_id': device_id, 'fault_type': fault_type}
        )
        self._add_event_safely(recovery_event)

    def handle_recovery_event(self, event: Event):
        """处理故障恢复事件"""
        device_id = event.payload['device_id']
        
        if device_id in self.device_states:
            self.device_states[device_id]['status'] = 'NORMAL'
            self.device_states[device_id]['fault'] = False
            
            device_type = device_id.split('-')[0]
            base_temp = 35.0 if device_type in ['VHF', 'ILS'] else 30.0
            self.device_states[device_id]['temperature'] = base_temp + random.uniform(0, 5)

    def handle_cascade_event(self, event: Event):
        """处理级联影响事件"""
        target_device = event.payload['target']
        
        if target_device in self.device_states:
            effect = event.payload.get('effect', 'signal_drop')
            
            if effect == 'signal_drop':
                self.device_states[target_device]['signal_strength'] -= random.uniform(5, 15)
                self.device_states[target_device]['status'] = 'DEGRADED'

    def _get_coupled_device(self, device_id: str) -> Optional[str]:
        """获取耦合设备"""
        coupling_map = {
            'VHF-001': ['ILS-001', 'VOR-001'],
            'VHF-002': ['ILS-002', 'VOR-002'],
            'ILS-001': ['DME-001'],
            'ILS-002': ['DME-002'],
            'VOR-001': ['DME-001'],
            'VOR-002': ['DME-002'],
        }
        coupled = coupling_map.get(device_id, [])
        return random.choice(coupled) if coupled else None

    def run_simulation(self, start_time: datetime, duration_hours: int = 24):
        """
        运行模拟
        :param start_time: 开始时间
        :param duration_hours: 持续时间（小时）
        """
        current_time = start_time
        end_time = start_time + timedelta(hours=duration_hours)
        
        while current_time < end_time:
            event = self.generate_next_event(current_time)
            if event:
                self.event_handlers[event.type](event)
            
            current_time += timedelta(minutes=5)

    def get_device_states(self) -> Dict[str, Dict[str, Any]]:
        """获取当前设备状态"""
        return self.device_states.copy()
