from uuid import uuid4
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db.models import Q
from django.utils.timezone import now

from .models import Alarm, AlarmEvent, AlarmNotification, AlarmRule


class AlarmEngineService:
    """
    告警引擎：
    1. 根据规则判断是否触发告警
    2. 对同一 device + rule 的活跃告警去重
    3. 支持恢复自动清除
    4. 支持离线告警特殊处理
    5. 支持规则缓存
    """

    CACHE_KEY = 'alarm_rules_cache'
    CACHE_TIMEOUT = 3600

    def process_status(self, device, payload):
        """
        处理单次设备状态上报
        :param device: Device 实例
        :param payload: dict，上报的状态数据
        :return: {
            'alarm_flag': bool,
            'device_status': 'NORMAL'/'ALARM'/'OFFLINE',
            'triggered_alarms': [...],
            'cleared_alarms': [...]
        }
        """
        triggered_alarms = []
        cleared_alarms = []

        # 1. 常规规则处理
        for rule in self._get_applicable_rules(device):
            if rule.metric not in payload:
                continue

            current_value = payload.get(rule.metric)
            active_alarm = self._find_active_alarm(device, rule)

            triggered = self._is_triggered(rule, current_value)

            if triggered:
                if not active_alarm and not self._in_cooldown(device, rule):
                    alarm = self._create_alarm(device, rule, current_value)
                    triggered_alarms.append(alarm)
            else:
                # 只有已存在活跃告警时才考虑恢复
                auto_clear = getattr(rule, 'auto_clear', True)
                if active_alarm and auto_clear and self._is_recovered(rule, current_value):
                    self._clear_alarm(active_alarm, current_value)
                    cleared_alarms.append(active_alarm)

        # 2. 离线告警特殊处理
        offline_alarm = self._find_active_offline_alarm(device)
        online_status = payload.get('online_status')

        if online_status is False:
            if not offline_alarm:
                alarm = self._create_offline_alarm(device)
                triggered_alarms.append(alarm)
        elif online_status is True:
            if offline_alarm:
                self._clear_alarm(offline_alarm, True)
                cleared_alarms.append(offline_alarm)

        # 3. 重新计算当前设备状态
        remaining_active_count = Alarm.objects.filter(
            device=device,
            status__in=['OPEN', 'ACK']
        ).count()

        if online_status is False:
            device_status = 'OFFLINE'
        elif remaining_active_count > 0:
            device_status = 'ALARM'
        else:
            device_status = 'NORMAL'

        return {
            'alarm_flag': remaining_active_count > 0,
            'device_status': device_status,
            'triggered_alarms': triggered_alarms,
            'cleared_alarms': cleared_alarms,
        }

    def _get_applicable_rules(self, device):
        """
        获取设备适用规则：
        - GLOBAL
        - DEVICE_TYPE
        - DEVICE
        注意：这里要求 AlarmRule.level 支持 DEVICE_TYPE
        """
        cache_key = f'{self.CACHE_KEY}:{device.device_type}:{device.device_id}'
        rules = cache.get(cache_key)

        if rules is None:
            rules = list(
                AlarmRule.objects.filter(is_enabled=True).filter(
                    Q(level='GLOBAL') |
                    Q(level='DEVICE_TYPE', device_type=device.device_type) |
                    Q(level='DEVICE', device=device)
                )
            )
            cache.set(cache_key, rules, self.CACHE_TIMEOUT)

        return rules

    def _compare(self, value, operator, threshold):
        if value is None or threshold is None:
            return False

        if operator == '<':
            return value < threshold
        if operator == '<=':
            return value <= threshold
        if operator == '>':
            return value > threshold
        if operator == '>=':
            return value >= threshold
        if operator == '==':
            return value == threshold
        if operator == '!=':
            return value != threshold
        if operator == 'abs>':
            return abs(value) > threshold

        return False

    def _is_triggered(self, rule, current_value):
        """
        触发判断：
        - 数值型：threshold
        - 字符串型：threshold_str
        """
        if isinstance(current_value, str):
            return self._compare(current_value, rule.operator, rule.threshold_str)
        return self._compare(current_value, rule.operator, rule.threshold)

    def _is_recovered(self, rule, current_value):
        """
        恢复判断：
        - 优先使用恢复阈值（滞回）
        - 若未配置，则采用 trigger 逻辑取反
        """
        if isinstance(current_value, str):
            recovery_operator = getattr(rule, 'recovery_operator', None)
            recovery_threshold_str = getattr(rule, 'recovery_threshold_str', None)

            if recovery_operator and recovery_threshold_str not in (None, ''):
                return self._compare(current_value, recovery_operator, recovery_threshold_str)

            return not self._compare(current_value, rule.operator, rule.threshold_str)

        recovery_operator = getattr(rule, 'recovery_operator', None)
        recovery_threshold = getattr(rule, 'recovery_threshold', None)

        if recovery_operator and recovery_threshold is not None:
            return self._compare(current_value, recovery_operator, recovery_threshold)

        return not self._compare(current_value, rule.operator, rule.threshold)

    def _find_active_alarm(self, device, rule):
        """
        查找 device + rule 的活跃告警（OPEN / ACK）
        """
        return Alarm.objects.filter(
            device=device,
            rule=rule,
            status__in=['OPEN', 'ACK']
        ).order_by('-trigger_time').first()

    def _find_active_offline_alarm(self, device):
        """
        离线告警没有 rule，按 metric=online_status + rule为空 查找
        """
        return Alarm.objects.filter(
            device=device,
            metric='online_status',
            rule__isnull=True,
            status__in=['OPEN', 'ACK']
        ).order_by('-trigger_time').first()

    def _in_cooldown(self, device, rule):
        """
        冷却时间内不重复触发
        """
        cooldown_seconds = getattr(rule, 'cooldown_seconds', 0) or 0
        if cooldown_seconds <= 0:
            return False

        last_alarm = Alarm.objects.filter(
            device=device,
            rule=rule
        ).order_by('-trigger_time').first()

        if not last_alarm:
            return False

        delta_seconds = (now() - last_alarm.trigger_time).total_seconds()
        return delta_seconds < cooldown_seconds

    def _build_alarm_id(self, device_id, metric):
        return f'ALARM_{device_id}_{metric}_{now().strftime("%Y%m%d%H%M%S")}_{uuid4().hex[:6]}'

    def _create_alarm(self, device, rule, value):
        is_numeric = isinstance(value, (int, float)) and not isinstance(value, bool)

        alarm = Alarm.objects.create(
            alarm_id=self._build_alarm_id(device.device_id, rule.metric),
            device=device,
            rule=rule,
            metric=rule.metric,
            value=value if is_numeric else None,
            value_str=None if is_numeric else str(value),
            severity=rule.severity,
            status='OPEN',
            trigger_time=now(),
        )

        AlarmEvent.objects.create(
            alarm=alarm,
            event_type='TRIGGER',
            operator='system',
            description=f'{device.device_id} 的 {rule.metric} 触发告警，当前值={value}'
        )

        AlarmNotification.objects.create(
            alarm=alarm,
            recipient='admin',
            content=f'设备 {device.device_id} 指标 {rule.metric} 异常: {value}'
        )

        self._broadcast(
            'alarm_opened',
            alarm,
            extra={
                'value': value,
                'title': rule.name,
                'rule_id': rule.id,
                'rule_name': rule.name,
            }
        )

        return alarm

    def _create_offline_alarm(self, device):
        alarm = Alarm.objects.create(
            alarm_id=self._build_alarm_id(device.device_id, 'online_status'),
            device=device,
            rule=None,
            metric='online_status',
            value=None,
            value_str='False',
            severity='CRITICAL',
            status='OPEN',
            trigger_time=now(),
        )

        AlarmEvent.objects.create(
            alarm=alarm,
            event_type='TRIGGER',
            operator='system',
            description='设备离线'
        )

        AlarmNotification.objects.create(
            alarm=alarm,
            recipient='admin',
            content=f'设备 {device.device_id} 离线'
        )

        self._broadcast(
            'alarm_opened',
            alarm,
            extra={
                'value': False,
                'title': '设备离线'
            }
        )

        return alarm

    def _clear_alarm(self, alarm, current_value=None):
        """
        清除告警：
        - 保留原触发值 value / value_str
        - 恢复值写入 recover_value / recover_value_str（如果模型已有）
        """
        alarm.status = 'CLEARED'
        alarm.clear_time = now()

        update_fields = ['status', 'clear_time']

        # 兼容：只有模型存在字段时才写入
        if hasattr(alarm, 'recover_value') and hasattr(alarm, 'recover_value_str'):
            if isinstance(current_value, (int, float)) and not isinstance(current_value, bool):
                alarm.recover_value = current_value
                alarm.recover_value_str = None
            elif current_value is not None:
                alarm.recover_value = None
                alarm.recover_value_str = str(current_value)
            update_fields.extend(['recover_value', 'recover_value_str'])

        alarm.save(update_fields=update_fields)

        AlarmEvent.objects.create(
            alarm=alarm,
            event_type='CLEAR',
            operator='system',
            description=f'指标恢复正常，系统自动清除告警，当前值={current_value}'
        )

        AlarmNotification.objects.create(
            alarm=alarm,
            recipient='admin',
            content=f'设备 {alarm.device.device_id} 告警恢复: {alarm.metric}'
        )

        self._broadcast(
            'alarm_cleared',
            alarm,
            extra={
                'value': current_value
            }
        )

    def _broadcast(self, event, alarm, extra=None):
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        payload = {
            'event': event,
            'timestamp': now().isoformat(),
            'alarm': {
                'id': alarm.alarm_id,
                'device_id': alarm.device.device_id,
                'device_type': alarm.device.device_type,
                'metric': alarm.metric,
                'severity': alarm.severity,
                'status': alarm.status,
                'trigger_time': alarm.trigger_time.isoformat() if alarm.trigger_time else None,
                'ack_time': alarm.ack_time.isoformat() if alarm.ack_time else None,
                'clear_time': alarm.clear_time.isoformat() if alarm.clear_time else None,
                'rule_id': alarm.rule_id,
            }
        }

        if extra:
            payload['alarm'].update(extra)

        async_to_sync(channel_layer.group_send)(
            'notifications',
            {
                'type': 'send_notification',
                'message': payload
            }
        )
