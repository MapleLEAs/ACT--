from typing import Dict, Any, List
from datetime import datetime, timedelta
from core.simulation import (
    DeviceCouplingMatrix, EventDrivenGenerator, SpatialQueryEngine,
    DataQualityEngine, CascadeAlarmEngine, TrendBasedPredictor
)


class DataGenerationManager:
    """
    数据生成管理器
    统一管理设备数据生成、耦合数据查询、事件触发等功能
    """

    def __init__(self):
        self.coupling_matrix = DeviceCouplingMatrix()
        self.event_generator = EventDrivenGenerator()
        self.spatial_engine = SpatialQueryEngine()
        self.quality_engine = DataQualityEngine()
        self.alarm_engine = CascadeAlarmEngine()

    def generate_device_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成设备数据
        :param config: 生成配置
        :return: 生成结果
        """
        device_count = config.get('device_count', 30)
        time_range = config.get('time_range', {})
        coupling_enabled = config.get('coupling_enabled', True)
        
        start_time = datetime.fromisoformat(time_range.get('start', '2024-01-08T00:00:00'))
        end_time = datetime.fromisoformat(time_range.get('end', '2024-01-15T00:00:00'))
        
        total_minutes = int((end_time - start_time).total_seconds() / 60)
        records_per_device = total_minutes // 5
        
        device_types = ['VHF', 'ILS', 'VOR', 'DME', 'HF']
        devices = []
        for i in range(device_count):
            dev_type = device_types[i % len(device_types)]
            devices.append(f'{dev_type}-{i+1:03d}')
        
        self.event_generator.initialize_device_states(devices)
        duration_hours = total_minutes // 60
        self.event_generator.run_simulation(start_time, duration_hours)
        
        device_states = self.event_generator.get_device_states()
        
        data_stream = []
        for device_id, state in device_states.items():
            for i in range(records_per_device):
                timestamp = start_time + timedelta(minutes=i * 5)
                data_point = {
                    'device_id': device_id,
                    'timestamp': timestamp.isoformat(),
                    'temperature': state.get('temperature', 35.0),
                    'signal_strength': state.get('signal_strength', 95.0),
                    'status': state.get('status', 'NORMAL'),
                    'load': state.get('internal_load', 0.5)
                }
                data_stream.append(data_point)
        
        quality_report = self.quality_engine.validate_data_quality(data_stream)
        
        return {
            'generation_id': f'GEN-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            'status': 'completed',
            'generated_records': len(data_stream),
            'generation_time': datetime.now().isoformat(),
            'quality_score': quality_report.get('overall_score', 0),
            'quality_report': quality_report
        }

    def get_coupled_data(self, device_id: str) -> Dict[str, Any]:
        """
        获取耦合数据
        :param device_id: 设备ID
        :return: 耦合数据
        """
        coupled_devices = []
        couplings = self.coupling_matrix.get_coupled_devices(device_id)
        
        for coupling in couplings:
            effect = coupling['effect']
            for rel_type, strength in effect.items():
                if strength > 0:
                    coupled_devices.append({
                        'device_id': coupling['device_id'],
                        'coupling_type': rel_type,
                        'coupling_strength': strength
                    })
        
        region_id = self.spatial_engine.get_device_region(device_id)
        env_state = {}
        if region_id:
            env_state = self.spatial_engine.get_regional_env_state(region_id)
            env_state['region'] = region_id
        
        return {
            'device_id': device_id,
            'coupled_devices': coupled_devices,
            'env_coupling': env_state
        }

    def trigger_event(self, event_type: str, device_id: str, **kwargs) -> Dict[str, Any]:
        """
        触发事件
        :param event_type: 事件类型
        :param device_id: 设备ID
        :param kwargs: 其他参数
        :return: 事件结果
        """
        from core.simulation import EventType
        
        fault_type = kwargs.get('fault_type', 'overheat')
        trigger_value = kwargs.get('trigger_value', 68.5)
        
        if event_type == 'FAULT_EVENT':
            alarm = self.alarm_engine.trigger_device_alarm(device_id, fault_type, trigger_value)
            
            cascade_events = []
            alarms_generated = [alarm['alarm_id']]
            
            for alarm_record in self.alarm_engine.alarm_history:
                if alarm_record.get('propagation_source') == alarm['alarm_id']:
                    cascade_events.append({
                        'event_id': alarm_record['alarm_id'],
                        'type': 'CASCADE_EVENT',
                        'affected_device': alarm_record.get('device_id', ''),
                        'effect': 'signal_drop'
                    })
                    alarms_generated.append(alarm_record['alarm_id'])
            
            return {
                'event_id': f'EVT-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
                'triggered_time': datetime.now().isoformat(),
                'cascade_events': cascade_events,
                'alarms_generated': alarms_generated
            }
        
        return {
            'event_id': f'EVT-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            'triggered_time': datetime.now().isoformat(),
            'message': f'{event_type} triggered for {device_id}'
        }

    def get_spatial_regions(self) -> Dict[str, Any]:
        """
        获取空间区域数据
        :return: 空间区域数据
        """
        regions = []
        heat_map_data = []
        
        for region_id, region in self.spatial_engine.AIRPORT_REGIONS.items():
            avg_temp = 0.0
            alarm_count = 0
            
            for device_id in region.devices:
                avg_temp += 35.0 + len(region.devices) * 2
                alarm_count = len(region.devices) // 2
            
            avg_temp /= max(len(region.devices), 1)
            
            regions.append({
                'region_id': region_id,
                'name': region.name,
                'boundary': {
                    'lat': region.center[1],
                    'lon': region.center[0],
                    'radius': region.radius_km * 1000
                },
                'device_count': len(region.devices),
                'alarm_density': round(0.1 + len(region.devices) * 0.02, 2),
                'avg_temperature': round(avg_temp, 2)
            })
            
            heat_map_data.append({
                'grid_id': region_id.upper(),
                'center': {'lat': region.center[1], 'lon': region.center[0]},
                'temperature_avg': round(avg_temp, 2),
                'alarm_count': alarm_count,
                'device_density': len(region.devices)
            })
        
        return {
            'regions': regions,
            'heat_map_data': heat_map_data
        }

    def get_quality_report(self, generation_id: str = None) -> Dict[str, Any]:
        """
        获取质量报告
        :param generation_id: 生成ID
        :return: 质量报告
        """
        report = self.quality_engine.get_quality_report()
        
        if not report:
            return {
                'error': 'No quality report available'
            }
        
        quality_issues = []
        for category in ['completeness', 'consistency', 'timeliness', 'accuracy']:
            issues = report.get(category, {}).get('issues', [])
            for issue in issues[:3]:
                quality_issues.append({
                    'issue_id': f'ISSUE-{len(quality_issues) + 1:03d}',
                    'type': issue.get('type', category),
                    'severity': 'WARN',
                    'description': f'{category} issue detected'
                })
        
        return {
            'quality_report_id': report.get('quality_report_id', f'QR-{datetime.now().strftime("%Y%m%d-%H%M%S")}'),
            'generation_time': report.get('generation_time', datetime.now().isoformat()),
            'quality_scores': {
                'completeness': report.get('completeness', {}).get('score', 0),
                'consistency': report.get('consistency', {}).get('score', 0),
                'timeliness': report.get('timeliness', {}).get('score', 0),
                'accuracy': report.get('accuracy', {}).get('score', 0),
                'overall_score': report.get('overall_score', 0)
            },
            'quality_issues': quality_issues
        }

    def get_alarm_propagation_chain(self, alarm_id: str) -> Dict[str, Any]:
        """
        获取告警传播链
        :param alarm_id: 告警ID
        :return: 告警传播链
        """
        chain = self.alarm_engine.get_alarm_propagation_chain(alarm_id)
        
        alarm_propagation_chain = []
        for alarm in chain:
            alarm_propagation_chain.append({
                'alarm_id': alarm['alarm_id'],
                'level': alarm['level'],
                'type': alarm['type'],
                'severity': alarm['severity'],
                'propagation_source': alarm.get('propagation_source')
            })
        
        correlation_matrix = self.alarm_engine.get_alarm_correlation_matrix()
        
        return {
            'alarm_propagation_chain': alarm_propagation_chain,
            'alarm_correlation_matrix': correlation_matrix
        }

    def get_trend_analysis(self, device_id: str, historical_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取趋势分析
        :param device_id: 设备ID
        :param historical_data: 历史数据
        :return: 趋势分析结果
        """
        if not historical_data:
            historical_data = []
            for i in range(100):
                historical_data.append({
                    'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                    'value': 35.0 + i * 0.15 + (i % 24) * 0.5 + (i % 168) * 0.1
                })
        
        predictor = TrendBasedPredictor(historical_data)
        components = predictor.decompose_time_series()
        prediction = predictor.predict_with_uncertainty(components)
        
        return {
            'device_id': device_id,
            'trend_analysis': {
                'trend_direction': components.get('trend_direction', 'stable'),
                'trend_slope': components.get('trend_slope', 0),
                'seasonal_pattern': components.get('seasonal_pattern', 'daily_cycle'),
                'residual_std': components.get('residual_std', 0)
            },
            'prediction_result': prediction
        }
