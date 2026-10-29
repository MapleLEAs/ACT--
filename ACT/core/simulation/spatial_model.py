from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import math
import time
from .exception_handler import SpatialQueryTimeoutError, GISCalculationError, ExceptionHandler


@dataclass
class Region:
    name: str
    center: Tuple[float, float]
    radius_km: float
    devices: List[str]
    env_zone: str


class SpatialQueryEngine:
    """空间关系查询引擎"""

    DEFAULT_COORDINATE = (116.4074, 39.9042)

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds
        self.exception_handler = ExceptionHandler()

    AIRPORT_REGIONS = {
        'tower': Region(
            name='塔台区域',
            center=(116.4074, 39.9042),
            radius_km=0.5,
            devices=['VHF-001', 'VHF-002', 'VHF-003'],
            env_zone='controlled'
        ),
        'runway_A': Region(
            name='跑道18L区域',
            center=(116.4124, 39.9092),
            radius_km=3.0,
            devices=['ILS-001', 'DME-001', 'VOR-001'],
            env_zone='outdoor'
        ),
        'runway_B': Region(
            name='跑道36R区域',
            center=(116.4024, 39.8992),
            radius_km=3.0,
            devices=['ILS-002', 'DME-002', 'VOR-002'],
            env_zone='outdoor'
        ),
        'navigation_station': Region(
            name='导航站',
            center=(116.4174, 39.9142),
            radius_km=1.0,
            devices=['HF-001', 'HF-002', 'HF-003'],
            env_zone='semi_outdoor'
        )
    }

    DEVICE_LOCATIONS = {
        'VHF-001': (116.4074, 39.9042),
        'VHF-002': (116.4076, 39.9044),
        'VHF-003': (116.4072, 39.9040),
        'ILS-001': (116.4124, 39.9092),
        'ILS-002': (116.4024, 39.8992),
        'VOR-001': (116.4134, 39.9102),
        'VOR-002': (116.4034, 39.9002),
        'DME-001': (116.4114, 39.9082),
        'DME-002': (116.4014, 39.8982),
        'HF-001': (116.4174, 39.9142),
        'HF-002': (116.4176, 39.9144),
        'HF-003': (116.4172, 39.9140),
    }

    @staticmethod
    def calculate_geodesic_distance(loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """
        计算两点间的地理距离（公里）
        异常处理策略：GIS坐标计算失败时使用默认坐标，标记为"位置缺失"
        :param loc1: (经度, 纬度)
        :param loc2: (经度, 纬度)
        :return: 距离（公里）
        """
        try:
            if not isinstance(loc1, tuple) or len(loc1) != 2:
                raise GISCalculationError(
                    code='INVALID_COORDINATE',
                    message=f'无效坐标格式: loc1={loc1}'
                )
            
            if not isinstance(loc2, tuple) or len(loc2) != 2:
                raise GISCalculationError(
                    code='INVALID_COORDINATE',
                    message=f'无效坐标格式: loc2={loc2}'
                )
            
            lon1, lat1 = loc1
            lon2, lat2 = loc2
            
            if not (-180 <= lon1 <= 180 and -90 <= lat1 <= 90):
                raise GISCalculationError(
                    code='OUT_OF_RANGE',
                    message=f'坐标超出范围: loc1={loc1}'
                )
            
            if not (-180 <= lon2 <= 180 and -90 <= lat2 <= 90):
                raise GISCalculationError(
                    code='OUT_OF_RANGE',
                    message=f'坐标超出范围: loc2={loc2}'
                )
            
            R = 6371.0
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)
            
            a = (math.sin(delta_phi / 2) ** 2 +
                 math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            return R * c
            
        except GISCalculationError as e:
            handler = ExceptionHandler()
            handler.log_error('gis_calculation', e)
            handler.handle_gis_error(e)
            return float('inf')
        except Exception as e:
            handler = ExceptionHandler()
            handler.log_error('gis_calculation', GISCalculationError(
                code='CALCULATION_FAILED',
                message=f'GIS计算失败: {str(e)}'
            ))
            return float('inf')

    def get_devices_within_radius(self, center_device: str, radius_km: float) -> List[Dict[str, Any]]:
        """
        获取半径范围内的设备
        :param center_device: 中心设备ID
        :param radius_km: 半径（公里）
        :return: 附近设备列表
        """
        center_location = self.DEVICE_LOCATIONS.get(center_device)
        if not center_location:
            return []
        
        nearby_devices = []
        
        for device_id, location in self.DEVICE_LOCATIONS.items():
            if device_id != center_device:
                distance = self.calculate_geodesic_distance(center_location, location)
                if distance <= radius_km:
                    nearby_devices.append({
                        'device_id': device_id,
                        'distance_km': round(distance, 4),
                        'coupling_strength': round(1.0 / (distance + 0.1), 4)
                    })
        
        nearby_devices.sort(key=lambda x: x['distance_km'])
        return nearby_devices

    def get_regional_env_state(self, region_id: str) -> Dict[str, float]:
        """
        获取区域环境状态
        :param region_id: 区域ID
        :return: 环境状态字典
        """
        region = self.AIRPORT_REGIONS.get(region_id)
        if not region:
            return {}
        
        if region.env_zone == 'controlled':
            return {
                'temperature': 25.0,
                'humidity': 50.0,
                'weather_factor': 0.0,
                'env_zone': 'controlled'
            }
        elif region.env_zone == 'semi_outdoor':
            return {
                'temperature': 30.0,
                'humidity': 60.0,
                'weather_factor': 0.3,
                'env_zone': 'semi_outdoor'
            }
        else:
            return {
                'temperature': 35.0,
                'humidity': 70.0,
                'weather_factor': 1.0,
                'env_zone': 'outdoor'
            }

    def get_device_region(self, device_id: str) -> Optional[str]:
        """
        获取设备所属区域
        :param device_id: 设备ID
        :return: 区域ID
        """
        for region_id, region in self.AIRPORT_REGIONS.items():
            if device_id in region.devices:
                return region_id
        return None

    def get_spatial_output(self, device_states: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取空间数据输出格式（用于可视化）
        :param device_states: 设备状态字典
        :return: 空间数据输出
        """
        regions = []
        heat_map_data = []
        fault_diffusion_map = []
        
        for region_id, region in self.AIRPORT_REGIONS.items():
            region_devices = region.devices
            device_count = len(region_devices)
            
            avg_temp = 0.0
            alarm_count = 0
            
            for device_id in region_devices:
                state = device_states.get(device_id, {})
                avg_temp += state.get('temperature', 0)
                if state.get('status') in ['FAULT', 'DEGRADED']:
                    alarm_count += 1
            
            avg_temp /= max(device_count, 1)
            alarm_density = alarm_count / max(device_count, 1)
            
            regions.append({
                'region_id': region_id,
                'name': region.name,
                'boundary': {
                    'lat': region.center[1],
                    'lon': region.center[0],
                    'radius': region.radius_km * 1000
                },
                'device_count': device_count,
                'alarm_density': round(alarm_density, 2),
                'avg_temperature': round(avg_temp, 2)
            })
            
            heat_map_data.append({
                'grid_id': region_id,
                'center': region.center,
                'temperature_avg': round(avg_temp, 2),
                'alarm_count': alarm_count,
                'device_density': device_count
            })
            
            if alarm_count > 0:
                fault_diffusion_map.append({
                    'source_device': region_devices[0],
                    'affected_region': region_id,
                    'diffusion_radius': int(region.radius_km * 500),
                    'affected_devices': region_devices
                })
        
        return {
            'regions': regions,
            'heat_map_data': heat_map_data,
            'fault_diffusion_map': fault_diffusion_map
        }

    def get_all_regions(self) -> Dict[str, Any]:
        """获取所有区域信息"""
        result = {}
        for region_id, region in self.AIRPORT_REGIONS.items():
            result[region_id] = {
                'name': region.name,
                'center': region.center,
                'radius_km': region.radius_km,
                'devices': region.devices,
                'env_zone': region.env_zone
            }
        return result
