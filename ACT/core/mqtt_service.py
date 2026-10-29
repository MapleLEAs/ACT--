"""
MQTT 设备接入服务模块
提供设备通过 MQTT 协议上报状态数据的能力
"""
import json
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

class MQTTService:
    """
    MQTT 服务类
    处理设备状态上报和命令下发
    """
    
    # MQTT Topic 配置
    TOPIC_PATTERNS = {
        'status': 'atc/{device_type}/{device_id}/status',
        'command': 'atc/{device_type}/{device_id}/command',
        'alarm': 'atc/{device_type}/{device_id}/alarm',
        'prediction': 'atc/{device_type}/{device_id}/prediction'
    }
    
    @staticmethod
    def get_topic(topic_type, device_type, device_id):
        """
        获取指定类型的 MQTT Topic
        """
        pattern = MQTTService.TOPIC_PATTERNS.get(topic_type)
        if pattern:
            return pattern.format(device_type=device_type, device_id=device_id)
        return None
    
    @staticmethod
    def parse_status_message(payload):
        """
        解析设备状态上报消息
        :param payload: MQTT 消息负载（JSON 字符串）
        :return: 解析后的状态数据字典
        """
        try:
            data = json.loads(payload)
            
            # 标准化字段名称
            status_data = {
                'collect_time': data.get('collect_time') or datetime.now().isoformat(),
                'online_status': data.get('online_status', True),
                'device_status': data.get('device_status', 'normal'),
                'alarm_flag': data.get('alarm_flag', False),
            }
            
            # 物理量字段
            physical_fields = [
                'power_voltage', 'device_temperature', 'signal_strength',
                'link_status', 'bit_error_rate', 'loc_guidance_deviation',
                'gs_guidance_deviation', 'signal_power', 'antenna_swr'
            ]
            
            for field in physical_fields:
                if field in data:
                    status_data[field] = data[field]
            
            return status_data
            
        except json.JSONDecodeError as e:
            logger.error(f"解析 MQTT 消息失败: {str(e)}")
            return None
    
    @staticmethod
    def create_status_log(device, payload):
        """
        从 MQTT 消息创建设备状态日志
        :param device: Device 实例
        :param payload: MQTT 消息负载
        :return: DeviceStatusLog 实例或 None
        """
        from monitor.models import DeviceStatusLog
        
        try:
            status_data = MQTTService.parse_status_message(payload)
            if not status_data:
                return None
            
            # 转换 collect_time
            collect_time = status_data.get('collect_time')
            if isinstance(collect_time, str):
                try:
                    collect_time = datetime.fromisoformat(collect_time.replace('Z', '+00:00'))
                except ValueError:
                    collect_time = datetime.now()
            elif not isinstance(collect_time, datetime):
                collect_time = datetime.now()
            
            # 创建状态日志
            status_log = DeviceStatusLog(
                device=device,
                collect_time=collect_time,
                online_status=status_data.get('online_status', True),
                device_status=status_data.get('device_status', 'normal'),
                alarm_flag=status_data.get('alarm_flag', False),
            )
            
            # 设置动态字段
            dynamic_fields = [
                'power_voltage', 'device_temperature', 'signal_strength',
                'link_status', 'bit_error_rate', 'loc_guidance_deviation',
                'gs_guidance_deviation', 'signal_power', 'antenna_swr'
            ]
            
            for field in dynamic_fields:
                if field in status_data:
                    setattr(status_log, field, status_data[field])
            
            status_log.save()
            logger.info(f"设备 {device.device_id} 状态日志创建成功")
            
            return status_log
            
        except Exception as e:
            logger.error(f"创建设备状态日志失败: {str(e)}")
            return None
    
    @staticmethod
    def build_command_message(command_type, params=None):
        """
        构建命令消息
        :param command_type: 命令类型
        :param params: 命令参数
        :return: JSON 格式的命令消息
        """
        message = {
            'command': command_type,
            'timestamp': datetime.now().isoformat(),
            'params': params or {}
        }
        return json.dumps(message)
    
    @staticmethod
    def handle_message(device_type, device_id, topic, payload):
        """
        处理 MQTT 消息
        :param device_type: 设备类型
        :param device_id: 设备ID
        :param topic: MQTT Topic
        :param payload: 消息负载
        """
        from monitor.models import Device
        
        try:
            # 查找设备
            device = Device.objects.filter(device_id=device_id).first()
            if not device:
                logger.warning(f"未找到设备: {device_id}")
                return False
            
            # 根据 Topic 类型处理消息
            if 'status' in topic:
                MQTTService.create_status_log(device, payload)
                return True
            
            elif 'alarm' in topic:
                # 处理告警消息
                MQTTService._handle_alarm_message(device, payload)
                return True
            
            elif 'prediction' in topic:
                # 处理预测消息
                MQTTService._handle_prediction_message(device, payload)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"处理 MQTT 消息失败: {str(e)}")
            return False
    
    @staticmethod
    def _handle_alarm_message(device, payload):
        """
        处理告警消息
        """
        from monitor.models import Alarm, AlarmRule
        
        try:
            data = json.loads(payload)
            
            # 创建或更新告警
            alarm, created = Alarm.objects.get_or_create(
                device=device,
                metric=data.get('metric', ''),
                status='OPEN',
                defaults={
                    'alarm_id': f"ALM-{device.device_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'severity': data.get('severity', 'WARN'),
                    'value': data.get('value'),
                    'trigger_time': datetime.now(),
                }
            )
            
            if created:
                logger.info(f"告警创建成功: {alarm.alarm_id}")
            else:
                logger.info(f"告警已存在: {alarm.alarm_id}")
                
        except Exception as e:
            logger.error(f"处理告警消息失败: {str(e)}")
    
    @staticmethod
    def _handle_prediction_message(device, payload):
        """
        处理预测消息
        """
        from monitor.models import PredictionResult
        
        try:
            data = json.loads(payload)
            
            prediction = PredictionResult(
                device=device,
                metric=data.get('metric', ''),
                predicted_value=data.get('predicted_value'),
                prediction_time=datetime.now(),
                prediction_horizon=data.get('horizon', 60),
                confidence_score=data.get('confidence', 0.8),
                threshold_value=data.get('threshold'),
                is_above_threshold=data.get('is_above_threshold', False),
                severity=data.get('severity', 'WARN'),
            )
            prediction.save()
            
            logger.info(f"预测结果保存成功: {device.device_id}")
            
        except Exception as e:
            logger.error(f"处理预测消息失败: {str(e)}")
