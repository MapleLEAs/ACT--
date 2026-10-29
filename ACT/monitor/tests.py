from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.cache import cache
from monitor.models import Device, DeviceStatusLog, AlarmRule, Alarm, AlarmEvent, AlarmNotification
from monitor.serializers import DeviceSerializer, DeviceStatusLogSerializer, AlarmRuleSerializer, AlarmSerializer
from monitor.alarm_engine import AlarmEngineService


class DeviceModelTest(TestCase):
    """设备模型单元测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )

    def test_create_vhf_device(self):
        """测试创建VHF设备"""
        device = Device.objects.create(
            device_id='VHF-TEST-001',
            device_type='VHF',
            device_model='THALES VHF-3000',
            location='测试位置',
            manufacturer='泰雷兹',
            owner=self.user
        )
        self.assertEqual(device.device_id, 'VHF-TEST-001')
        self.assertEqual(device.device_type, 'VHF')
        self.assertEqual(device.owner, self.user)
        self.assertTrue(device.created_at)
        self.assertTrue(device.updated_at)

    def test_create_ils_device(self):
        """测试创建ILS设备"""
        device = Device.objects.create(
            device_id='ILS-TEST-001',
            device_type='ILS',
            device_model='INDRA ILS-2000',
            location='测试跑道',
            manufacturer='因德拉',
            owner=self.user
        )
        self.assertEqual(device.device_type, 'ILS')
        self.assertEqual(device.device_id, 'ILS-TEST-001')

    def test_device_str_representation(self):
        """测试设备字符串表示"""
        device = Device.objects.create(
            device_id='VHF-TEST-001',
            device_type='VHF',
            owner=self.user
        )
        expected = 'VHF-TEST-001 (VHF)'
        self.assertEqual(str(device), expected)

    def test_device_unique_constraint(self):
        """测试设备ID唯一性约束"""
        Device.objects.create(
            device_id='VHF-TEST-001',
            device_type='VHF',
            owner=self.user
        )
        with self.assertRaises(Exception):
            Device.objects.create(
                device_id='VHF-TEST-001',
                device_type='VHF',
                owner=self.user
            )


class AlarmRuleModelTest(TestCase):
    """告警规则模型单元测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        self.device = Device.objects.create(
            device_id='VHF-TEST-001',
            device_type='VHF',
            owner=self.user
        )

    def test_create_global_rule(self):
        """测试创建全局规则"""
        rule = AlarmRule.objects.create(
            name='信号强度过低告警',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN',
            is_enabled=True
        )
        self.assertEqual(rule.level, 'GLOBAL')
        self.assertEqual(rule.metric, 'signal_strength')
        self.assertEqual(rule.threshold, -85.0)
        self.assertTrue(rule.is_enabled)

    def test_create_device_specific_rule(self):
        """测试创建设备级规则"""
        rule = AlarmRule.objects.create(
            name='设备特定规则',
            level='DEVICE',
            device=self.device,
            metric='device_temperature',
            operator='>',
            threshold=80.0,
            severity='ERROR',
            is_enabled=True
        )
        self.assertEqual(rule.level, 'DEVICE')
        self.assertEqual(rule.device, self.device)

    def test_rule_operators(self):
        """测试所有比较运算符"""
        operators = ['<', '>', '<=', '>=', '==', '!=', 'abs>']
        for op in operators:
            rule = AlarmRule.objects.create(
                name=f'测试{op}运算符',
                level='GLOBAL',
                device_type='VHF',
                metric='test_metric',
                operator=op,
                threshold=10.0,
                severity='WARN'
            )
            self.assertEqual(rule.operator, op)

    def test_rule_severity_levels(self):
        """测试所有严重级别"""
        severities = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
        for severity in severities:
            rule = AlarmRule.objects.create(
                name=f'测试{severity}级别',
                level='GLOBAL',
                device_type='VHF',
                metric='test_metric',
                operator='>',
                threshold=10.0,
                severity=severity
            )
            self.assertEqual(rule.severity, severity)

    def test_rule_str_representation(self):
        """测试规则字符串表示"""
        rule = AlarmRule.objects.create(
            name='测试规则',
            level='GLOBAL',
            device_type='VHF',
            metric='test_metric',
            operator='>',
            threshold=10.0,
            severity='WARN'
        )
        # 检查字符串表示包含规则名称和严重级别
        self.assertIn('测试规则', str(rule))
        self.assertIn('警告', str(rule))


class DeviceStatusLogModelTest(TestCase):
    """设备状态日志模型单元测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        self.device = Device.objects.create(
            device_id='VHF-TEST-001',
            device_type='VHF',
            owner=self.user
        )

    def test_create_vhf_status_log(self):
        """测试创建VHF状态日志"""
        log = DeviceStatusLog.objects.create(
            device=self.device,
            online_status=True,
            device_status='NORMAL',
            alarm_flag=False,
            signal_strength=-60.0,
            link_status='CONNECTED',
            bit_error_rate=0.001,
            device_temperature=45.0,
            collect_time=now()
        )
        self.assertEqual(log.device, self.device)
        self.assertTrue(log.online_status)
        self.assertEqual(log.signal_strength, -60.0)
        self.assertEqual(log.link_status, 'CONNECTED')

    def test_create_ils_status_log(self):
        """测试创建ILS状态日志"""
        log = DeviceStatusLog.objects.create(
            device=Device.objects.create(
                device_id='ILS-TEST-001',
                device_type='ILS',
                owner=self.user
            ),
            online_status=True,
            device_status='NORMAL',
            alarm_flag=False,
            loc_guidance_deviation=0.5,
            gs_guidance_deviation=0.3,
            signal_power=20.0,
            antenna_swr=1.5,
            collect_time=now()
        )
        self.assertEqual(log.loc_guidance_deviation, 0.5)
        self.assertEqual(log.signal_power, 20.0)

    def test_status_choices(self):
        """测试设备状态选项"""
        statuses = ['NORMAL', 'ALARM', 'OFFLINE']
        for status in statuses:
            log = DeviceStatusLog.objects.create(
                device=self.device,
                online_status=True,
                device_status=status,
                alarm_flag=False,
                collect_time=now()
            )
            self.assertEqual(log.device_status, status)

    def test_alarm_flag_behavior(self):
        """测试告警标识行为"""
        log = DeviceStatusLog.objects.create(
            device=self.device,
            online_status=True,
            device_status='ALARM',
            alarm_flag=True,
            collect_time=now()
        )
        self.assertTrue(log.alarm_flag)
        self.assertEqual(log.device_status, 'ALARM')


class AlarmModelTest(TestCase):
    """告警模型单元测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        self.device = Device.objects.create(
            device_id='VHF-TEST-001',
            device_type='VHF',
            owner=self.user
        )
        self.rule = AlarmRule.objects.create(
            name='信号强度过低告警',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN'
        )

    def test_create_alarm(self):
        """测试创建告警"""
        alarm = Alarm.objects.create(
            device=self.device,
            rule=self.rule,
            metric='signal_strength',
            value=-90.0,
            severity='WARN',
            status='OPEN',
            alarm_id='ALARM_TEST_001',
            trigger_time=now()
        )
        self.assertEqual(alarm.device, self.device)
        self.assertEqual(alarm.rule, self.rule)
        self.assertEqual(alarm.value, -90.0)
        self.assertEqual(alarm.status, 'OPEN')

    def test_alarm_status_transitions(self):
        """测试告警状态转换"""
        alarm = Alarm.objects.create(
            device=self.device,
            rule=self.rule,
            metric='signal_strength',
            value=-90.0,
            severity='WARN',
            status='OPEN',
            alarm_id='ALARM_TEST_001',
            trigger_time=now()
        )
        
        alarm.status = 'ACK'
        alarm.ack_time = now()
        alarm.save()
        self.assertEqual(alarm.status, 'ACK')
        self.assertIsNotNone(alarm.ack_time)
        
        alarm.status = 'CLEARED'
        alarm.clear_time = now()
        alarm.save()
        self.assertEqual(alarm.status, 'CLEARED')
        self.assertIsNotNone(alarm.clear_time)

    def test_alarm_str_representation(self):
        """测试告警字符串表示"""
        alarm = Alarm.objects.create(
            device=self.device,
            rule=self.rule,
            metric='signal_strength',
            value=-90.0,
            severity='WARN',
            status='OPEN',
            alarm_id='ALARM_TEST_001',
            trigger_time=now()
        )
        expected = 'ALARM_TEST_001 [OPEN]'
        self.assertEqual(str(alarm), expected)


class AlarmEventModelTest(TestCase):
    """告警事件模型单元测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        self.device = Device.objects.create(
            device_id='VHF-TEST-001',
            device_type='VHF',
            owner=self.user
        )
        self.rule = AlarmRule.objects.create(
            name='信号强度过低告警',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN'
        )
        self.alarm = Alarm.objects.create(
            device=self.device,
            rule=self.rule,
            metric='signal_strength',
            value=-90.0,
            severity='WARN',
            status='OPEN',
            alarm_id='ALARM_TEST_001',
            trigger_time=now()
        )

    def test_create_trigger_event(self):
        """测试创建触发事件"""
        event = AlarmEvent.objects.create(
            alarm=self.alarm,
            event_type='TRIGGER',
            operator='system',
            description='规则触发'
        )
        self.assertEqual(event.alarm, self.alarm)
        self.assertEqual(event.event_type, 'TRIGGER')
        self.assertEqual(event.operator, 'system')

    def test_create_ack_event(self):
        """测试创建确认事件"""
        event = AlarmEvent.objects.create(
            alarm=self.alarm,
            event_type='ACK',
            operator='testuser',
            description='人工确认'
        )
        self.assertEqual(event.event_type, 'ACK')
        self.assertEqual(event.operator, 'testuser')

    def test_create_clear_event(self):
        """测试创建清除事件"""
        event = AlarmEvent.objects.create(
            alarm=self.alarm,
            event_type='CLEAR',
            operator='system',
            description='系统清除'
        )
        self.assertEqual(event.event_type, 'CLEAR')

    def test_event_auto_timestamp(self):
        """测试事件自动时间戳"""
        event = AlarmEvent.objects.create(
            alarm=self.alarm,
            event_type='TRIGGER',
            operator='system',
            description='测试'
        )
        self.assertIsNotNone(event.event_time)


class AlarmNotificationModelTest(TestCase):
    """告警通知模型单元测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        self.device = Device.objects.create(
            device_id='VHF-TEST-001',
            device_type='VHF',
            owner=self.user
        )
        self.rule = AlarmRule.objects.create(
            name='信号强度过低告警',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN'
        )
        self.alarm = Alarm.objects.create(
            device=self.device,
            rule=self.rule,
            metric='signal_strength',
            value=-90.0,
            severity='WARN',
            status='OPEN',
            alarm_id='ALARM_TEST_001',
            trigger_time=now()
        )

    def test_create_system_notification(self):
        """测试创建系统通知"""
        notification = AlarmNotification.objects.create(
            alarm=self.alarm,
            notification_type='SYSTEM',
            recipient='admin',
            content='告警通知内容',
            status='SENT'
        )
        self.assertEqual(notification.alarm, self.alarm)
        self.assertEqual(notification.notification_type, 'SYSTEM')
        self.assertEqual(notification.status, 'SENT')

    def test_create_email_notification(self):
        """测试创建邮件通知"""
        notification = AlarmNotification.objects.create(
            alarm=self.alarm,
            notification_type='EMAIL',
            recipient='test@example.com',
            content='告警邮件内容',
            status='SENT'
        )
        self.assertEqual(notification.notification_type, 'EMAIL')

    def test_notification_status_choices(self):
        """测试通知状态选项"""
        statuses = ['SENT', 'FAILED']
        for status in statuses:
            notification = AlarmNotification.objects.create(
                alarm=self.alarm,
                notification_type='SYSTEM',
                recipient='admin',
                content='测试通知',
                status=status
            )
            self.assertEqual(notification.status, status)


class SerializerTest(TestCase):
    """序列化器单元测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        self.device = Device.objects.create(
            device_id='VHF-TEST-001',
            device_type='VHF',
            owner=self.user
        )

    def test_device_serializer(self):
        """测试设备序列化器"""
        serializer = DeviceSerializer(self.device)
        data = serializer.data
        self.assertEqual(data['device_id'], 'VHF-TEST-001')
        self.assertEqual(data['device_type'], 'VHF')

    def test_device_status_log_serializer(self):
        """测试设备状态日志序列化器"""
        log = DeviceStatusLog.objects.create(
            device=self.device,
            online_status=True,
            device_status='NORMAL',
            alarm_flag=False,
            signal_strength=-60.0,
            collect_time=now()
        )
        serializer = DeviceStatusLogSerializer(log)
        data = serializer.data
        self.assertEqual(data['device'], 'VHF-TEST-001')
        self.assertTrue(data['online_status'])

    def test_alarm_rule_serializer(self):
        """测试告警规则序列化器"""
        rule = AlarmRule.objects.create(
            name='测试规则',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN'
        )
        serializer = AlarmRuleSerializer(rule)
        data = serializer.data
        self.assertEqual(data['name'], '测试规则')
        self.assertEqual(data['metric'], 'signal_strength')

    def test_alarm_serializer(self):
        """测试告警序列化器"""
        rule = AlarmRule.objects.create(
            name='测试规则',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN'
        )
        alarm = Alarm.objects.create(
            device=self.device,
            rule=rule,
            metric='signal_strength',
            value=-90.0,
            severity='WARN',
            status='OPEN',
            alarm_id='ALARM_TEST_001',
            trigger_time=now()
        )
        serializer = AlarmSerializer(alarm)
        data = serializer.data
        self.assertEqual(data['alarm_id'], 'ALARM_TEST_001')
        self.assertEqual(data['status'], 'OPEN')


class BusinessLogicTest(TestCase):
    """业务逻辑单元测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        self.device = Device.objects.create(
            device_id='VHF-TEST-001',
            device_type='VHF',
            owner=self.user
        )
        cache.clear()
        self.engine = AlarmEngineService()

    def test_alarm_rule_cache(self):
        """测试告警规则缓存"""
        rule = AlarmRule.objects.create(
            name='缓存测试规则',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN',
            is_enabled=True
        )
        
        cached_rules = cache.get('alarm_rules_cache')
        self.assertIsNone(cached_rules)
        
        rules = list(AlarmRule.objects.filter(is_enabled=True))
        cache.set('alarm_rules_cache', rules, 3600)
        
        cached_rules = cache.get('alarm_rules_cache')
        self.assertEqual(len(cached_rules), 1)
        self.assertEqual(cached_rules[0].id, rule.id)

    def test_data_isolation_by_user(self):
        """测试用户数据隔离"""
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='test123'
        )
        device2 = Device.objects.create(
            device_id='VHF-TEST-002',
            device_type='VHF',
            owner=user2
        )
        
        user1_devices = Device.objects.filter(owner=self.user)
        self.assertEqual(user1_devices.count(), 1)
        self.assertEqual(user1_devices.first().device_id, 'VHF-TEST-001')

    def test_alarm_deduplication(self):
        """测试告警去重逻辑"""
        rule = AlarmRule.objects.create(
            name='去重测试规则',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN'
        )
        
        alarm1 = Alarm.objects.create(
            device=self.device,
            rule=rule,
            metric='signal_strength',
            value=-90.0,
            severity='WARN',
            status='OPEN',
            alarm_id='ALARM_TEST_001',
            trigger_time=now()
        )
        
        existing = Alarm.objects.filter(
            device=self.device,
            metric='signal_strength',
            status__in=['OPEN', 'ACK']
        ).first()
        
        self.assertIsNotNone(existing)
        self.assertEqual(existing.alarm_id, 'ALARM_TEST_001')

    def test_fault_alarm_recovery_flow(self):
        rule = AlarmRule.objects.create(
            name='闭环测试规则',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN',
            is_enabled=True
        )

        first_result = self.engine.process_status(self.device, {
            'online_status': True,
            'signal_strength': -95.0,
            'collect_time': now()
        })

        self.assertTrue(first_result['alarm_flag'])
        self.assertEqual(first_result['device_status'], 'ALARM')
        self.assertEqual(Alarm.objects.filter(device=self.device, status='OPEN').count(), 1)
        self.assertEqual(AlarmEvent.objects.filter(alarm__device=self.device, event_type='TRIGGER').count(), 1)

        second_result = self.engine.process_status(self.device, {
            'online_status': True,
            'signal_strength': -60.0,
            'collect_time': now()
        })

        self.assertFalse(second_result['alarm_flag'])
        self.assertEqual(second_result['device_status'], 'NORMAL')
        cleared_alarm = Alarm.objects.get(device=self.device, rule=rule)
        self.assertEqual(cleared_alarm.status, 'CLEARED')
        self.assertEqual(AlarmEvent.objects.filter(alarm=cleared_alarm, event_type='CLEAR').count(), 1)

    def test_ack_alarm_can_be_auto_cleared_after_recovery(self):
        rule = AlarmRule.objects.create(
            name='确认后恢复测试规则',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN',
            is_enabled=True
        )

        self.engine.process_status(self.device, {
            'online_status': True,
            'signal_strength': -92.0,
            'collect_time': now()
        })

        alarm = Alarm.objects.get(device=self.device, rule=rule)
        alarm.status = 'ACK'
        alarm.ack_time = now()
        alarm.save()

        result = self.engine.process_status(self.device, {
            'online_status': True,
            'signal_strength': -58.0,
            'collect_time': now()
        })

        alarm.refresh_from_db()
        self.assertFalse(result['alarm_flag'])
        self.assertEqual(alarm.status, 'CLEARED')

    def test_offline_alarm_recovery_flow(self):
        first_result = self.engine.process_status(self.device, {
            'online_status': False,
            'collect_time': now()
        })

        self.assertTrue(first_result['alarm_flag'])
        self.assertEqual(first_result['device_status'], 'OFFLINE')
        alarm = Alarm.objects.get(device=self.device, metric='online_status')
        self.assertEqual(alarm.status, 'OPEN')

        second_result = self.engine.process_status(self.device, {
            'online_status': True,
            'collect_time': now()
        })

        alarm.refresh_from_db()
        self.assertFalse(second_result['alarm_flag'])
        self.assertEqual(second_result['device_status'], 'NORMAL')
        self.assertEqual(alarm.status, 'CLEARED')
