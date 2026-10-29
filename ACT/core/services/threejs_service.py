"""
3D场景数据服务
"""

from django.db import connection
from django.core.cache import cache
from datetime import datetime
import json
import logging
from monitor.models import Device, Alarm

logger = logging.getLogger(__name__)


class ThreeJSSceneService:
    """3D场景数据服务"""
    
    CACHE_KEY = 'threejs_scene_data'
    CACHE_TIMEOUT = 60  # 60秒缓存
    
    def get_scene_data(self, force_refresh=False):
        """
        获取3D场景所需的所有数据
        返回格式：直接可用于Three.js渲染
        """
        # 尝试从缓存获取
        if not force_refresh:
            cached = cache.get(self.CACHE_KEY)
            if cached:
                return cached
        
        # 从数据库获取
        data = {
            'devices': self._get_devices(),
            'alarms': self._get_active_alarms(),
            'statistics': self._get_statistics(),
            'timestamp': datetime.now().isoformat()
        }
        
        # 存入缓存
        cache.set(self.CACHE_KEY, data, self.CACHE_TIMEOUT)
        
        return data
    
    def _get_devices(self):
        """获取设备数据及其最新状态"""
        # 使用原生 SQL 模拟 1.md 中的视图逻辑
        # 考虑到性能，我们直接查询 device_status_logs (热表)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    d.device_id,
                    d.device_model as device_name,
                    d.device_type,
                    d.location,
                    l.online_status,
                    l.device_status as current_status,
                    l.alarm_flag,
                    l.power_voltage,
                    l.device_temperature,
                    l.signal_strength,
                    l.antenna_swr,
                    l.bit_error_rate,
                    l.loc_guidance_deviation
                FROM devices d
                LEFT JOIN (
                    SELECT * FROM device_status_logs 
                    WHERE id IN (
                        SELECT MAX(id) FROM device_status_logs GROUP BY device_id
                    )
                ) l ON d.device_id = l.device_id
            """)
            
            columns = [col[0] for col in cursor.description]
            devices = []
            
            for row in cursor.fetchall():
                device = dict(zip(columns, row))
                
                # 状态颜色逻辑 (参考 1.md 5.1)
                status_color = '#44FF44'  # 绿色：正常
                if device.get('alarm_flag'):
                    status_color = '#FF4444'  # 红色：告警
                elif device.get('online_status') == False:
                    status_color = '#888888'  # 灰色：离线
                elif device.get('current_status') == 'ALARM':
                    status_color = '#FFA500'  # 橙色：异常
                
                # 转换为Three.js友好格式
                devices.append({
                    'id': device['device_id'],
                    'name': device['device_name'] or device['device_id'],
                    'type': device['device_type'],
                    'position': self._get_position(device['location']),
                    'color': status_color,
                    'status': {
                        'online': bool(device.get('online_status', True)),
                        'alarm': bool(device.get('alarm_flag', False)),
                        'current_status': device.get('current_status'),
                        'message': self._build_status_message(device)
                    }
                })
            
            return devices

    def _build_status_message(self, device):
        """构建设备状态详情文字"""
        msg_parts = []
        if device.get('power_voltage') is not None:
            msg_parts.append(f"电压: {device['power_voltage']}V")
        if device.get('device_temperature') is not None:
            msg_parts.append(f"温度: {device['device_temperature']}℃")
        
        if device['device_type'] == 'VHF':
            if device.get('signal_strength') is not None:
                msg_parts.append(f"信号: {device['signal_strength']}dBm")
            if device.get('bit_error_rate') is not None:
                msg_parts.append(f"误码率: {device['bit_error_rate']}")
        elif device['device_type'] == 'ILS':
            if device.get('antenna_swr') is not None:
                msg_parts.append(f"驻波比: {device['antenna_swr']}")
            if device.get('loc_guidance_deviation') is not None:
                msg_parts.append(f"LOC偏差: {device['loc_guidance_deviation']}")
        
        return ", ".join(msg_parts) if msg_parts else "暂无数据"

    def _get_position(self, location):
        """位置映射逻辑 (参考 1.md 5.2)"""
        # 实际项目中应从配置表读取，这里提供预设映射
        presets = {
            '塔台': {'x': 0, 'y': 0.5, 'z': 0},
            '导航台': {'x': 8, 'y': 0.5, 'z': 5},
            '跑道18L': {'x': -10, 'y': 0.5, 'z': 15},
            '跑道36R': {'x': 10, 'y': 0.5, 'z': 15},
            '场面监控': {'x': 0, 'y': 0.5, 'z': 10},
        }
        if not location:
            return {'x': 0, 'y': 0.5, 'z': 0}
            
        for key, pos in presets.items():
            if key in location:
                return pos
        
        # 如果没有匹配到预设，根据 location 字符串生成一个相对固定的随机位置
        h = hash(location)
        return {
            'x': (h % 30 - 15), 
            'y': 0.5, 
            'z': (h // 30 % 30 - 15)
        }
    
    def _get_active_alarms(self):
        """获取激活告警"""
        active_alarms = Alarm.objects.filter(status__in=['OPEN', 'ACK']).order_by('-trigger_time')[:20]
        return [{
            'id': a.id,
            'device_id': a.device_id,
            'severity': a.severity,
            'metric': a.metric,
            'trigger_time': a.trigger_time.isoformat()
        } for a in active_alarms]
    
    def _get_statistics(self):
        """获取统计信息"""
        total = Device.objects.count()
        # 通过子查询获取最新状态为online的设备数量
        from django.db.models import Subquery, OuterRef
        from monitor.models import DeviceStatusLog
        
        latest_logs = DeviceStatusLog.objects.filter(
            device=OuterRef('pk')
        ).order_by('-id').values('online_status')[:1]
        
        online = Device.objects.filter(
            status_logs__in=Subquery(latest_logs),
            status_logs__online_status=True
        ).distinct().count()
        
        active_alarms = Alarm.objects.filter(status__in=['OPEN', 'ACK']).count()
        
        return {
            'devices': {
                'total': total,
                'online': online,
                'offline': total - online
            },
            'alarms': {
                'active': active_alarms
            }
        }
