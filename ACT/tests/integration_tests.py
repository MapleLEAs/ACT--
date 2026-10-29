from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils.timezone import now
from rest_framework.test import APIClient
from rest_framework import status
from monitor.models import Device, DeviceStatusLog, AlarmRule, Alarm, AlarmEvent
import json


class AuthenticationIntegrationTest(TestCase):
    """认证集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )

    def test_obtain_jwt_token(self):
        """测试获取JWT令牌"""
        response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'test123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 注意：这里可能需要根据 CustomJSONRenderer 的包装逻辑进行调整
        # 如果使用了包装器，res.data 会包含 code, msg, data
        if 'code' in response.data:
            self.assertEqual(response.data['code'], 200)
            self.assertIn('access', response.data['data'])
            self.assertIn('refresh', response.data['data'])
        else:
            self.assertIn('access', response.data)
            self.assertIn('refresh', response.data)

    def test_invalid_credentials(self):
        """测试无效凭证"""
        response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_without_token(self):
        """测试无令牌访问受保护端点"""
        response = self.client.get('/api/devices/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_token(self):
        """测试有令牌访问受保护端点"""
        token_response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'test123'
        })
        
        if 'code' in token_response.data:
            token = token_response.data['data']['access']
        else:
            token = token_response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/devices/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DeviceManagementIntegrationTest(TestCase):
    """设备管理集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        token_response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'test123'
        })
        if 'code' in token_response.data:
            self.token = token_response.data['data']['access']
        else:
            self.token = token_response.data['access']
            
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_create_device(self):
        """测试创建设备"""
        device_data = {
            'device_id': 'VHF-INTEGRATION-001',
            'device_type': 'VHF',
            'device_model': 'THALES VHF-3000',
            'location': '集成测试位置',
            'manufacturer': '泰雷兹'
        }
        response = self.client.post('/api/devices/', device_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        res_data = response.data['data'] if 'data' in response.data else response.data
        self.assertEqual(res_data['device_id'], 'VHF-INTEGRATION-001')

    def test_list_devices(self):
        """测试列出设备"""
        Device.objects.create(
            device_id='VHF-LIST-001',
            device_type='VHF',
            owner=self.user
        )
        response = self.client.get('/api/devices/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.data['data'] if 'data' in response.data else response.data
        self.assertEqual(len(res_data), 1)

    def test_retrieve_device(self):
        """测试获取单个设备"""
        device = Device.objects.create(
            device_id='VHF-RETRIEVE-001',
            device_type='VHF',
            owner=self.user
        )
        response = self.client.get(f'/api/devices/{device.device_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.data['data'] if 'data' in response.data else response.data
        self.assertEqual(res_data['device_id'], 'VHF-RETRIEVE-001')

    def test_update_device(self):
        """测试更新设备"""
        device = Device.objects.create(
            device_id='VHF-UPDATE-001',
            device_type='VHF',
            location='原始位置',
            owner=self.user
        )
        update_data = {
            'device_id': 'VHF-UPDATE-001',
            'device_type': 'VHF',
            'location': '更新后的位置'
        }
        response = self.client.put(f'/api/devices/{device.device_id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.data['data'] if 'data' in response.data else response.data
        self.assertEqual(res_data['location'], '更新后的位置')

    def test_delete_device(self):
        """测试删除设备"""
        device = Device.objects.create(
            device_id='VHF-DELETE-001',
            device_type='VHF',
            owner=self.user
        )
        response = self.client.delete(f'/api/devices/{device.device_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Device.objects.filter(device_id='VHF-DELETE-001').exists())

    def test_user_data_isolation(self):
        """测试用户数据隔离"""
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='test123'
        )
        Device.objects.create(
            device_id='VHF-USER1-001',
            device_type='VHF',
            owner=self.user
        )
        Device.objects.create(
            device_id='VHF-USER2-001',
            device_type='VHF',
            owner=user2
        )
        
        response = self.client.get('/api/devices/')
        res_data = response.data['data'] if 'data' in response.data else response.data
        self.assertEqual(len(res_data), 1)
        self.assertEqual(res_data[0]['device_id'], 'VHF-USER1-001')


class AlarmRuleIntegrationTest(TestCase):
    """告警规则集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        self.device = Device.objects.create(
            device_id='VHF-RULE-001',
            device_type='VHF',
            owner=self.user
        )
        
        token_response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'test123'
        })
        if 'code' in token_response.data:
            self.token = token_response.data['data']['access']
        else:
            self.token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_create_global_rule(self):
        """测试创建全局规则"""
        rule_data = {
            'name': '集成测试全局规则',
            'level': 'GLOBAL',
            'device_type': 'VHF',
            'metric': 'signal_strength',
            'operator': '<',
            'threshold': -85.0,
            'severity': 'WARN',
            'is_enabled': True
        }
        response = self.client.post('/api/alarm_rules/', rule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        res_data = response.data['data'] if 'data' in response.data else response.data
        self.assertEqual(res_data['name'], '集成测试全局规则')

    def test_list_rules(self):
        """测试列出规则"""
        AlarmRule.objects.create(
            name='测试规则1',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN'
        )
        response = self.client.get('/api/alarm_rules/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.data['data'] if 'data' in response.data else response.data
        self.assertGreaterEqual(len(res_data), 1)


class DeviceStatusLogIntegrationTest(TestCase):
    """设备状态日志集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        self.device = Device.objects.create(
            device_id='VHF-LOG-001',
            device_type='VHF',
            owner=self.user
        )
        
        token_response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'test123'
        })
        if 'code' in token_response.data:
            self.token = token_response.data['data']['access']
        else:
            self.token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_create_vhf_status_log(self):
        """测试创建VHF状态日志"""
        log_data = {
            'device': 'VHF-LOG-001',
            'online_status': True,
            'signal_strength': -60.0,
            'link_status': 'CONNECTED',
            'bit_error_rate': 0.001,
            'device_temperature': 45.0,
            'collect_time': now().isoformat()
        }
        response = self.client.post('/api/status_logs/', log_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_status_logs(self):
        """测试列出状态日志"""
        DeviceStatusLog.objects.create(
            device=self.device,
            online_status=True,
            device_status='NORMAL',
            alarm_flag=False,
            collect_time=now()
        )
        response = self.client.get('/api/status_logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.data['data'] if 'data' in response.data else response.data
        self.assertGreaterEqual(len(res_data), 1)

    def test_fault_alarm_recovery_closed_loop(self):
        AlarmRule.objects.create(
            name='闭环集成规则',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN',
            is_enabled=True
        )

        fault_response = self.client.post('/api/status_logs/', {
            'device': 'VHF-LOG-001',
            'online_status': True,
            'signal_strength': -95.0,
            'collect_time': now().isoformat()
        }, format='json')
        self.assertEqual(fault_response.status_code, status.HTTP_201_CREATED)

        alarm = Alarm.objects.get(device=self.device, metric='signal_strength')
        self.assertEqual(alarm.status, 'OPEN')

        ack_response = self.client.post(f'/api/alarms/{alarm.id}/operate/', {
            'action': 'ACK',
            'operator': 'testuser',
            'message': '收到告警'
        })
        self.assertEqual(ack_response.status_code, status.HTTP_200_OK)

        recovery_response = self.client.post('/api/status_logs/', {
            'device': 'VHF-LOG-001',
            'online_status': True,
            'signal_strength': -55.0,
            'collect_time': now().isoformat()
        }, format='json')
        self.assertEqual(recovery_response.status_code, status.HTTP_201_CREATED)

        alarm.refresh_from_db()
        self.assertEqual(alarm.status, 'CLEARED')
        self.assertEqual(AlarmEvent.objects.filter(alarm=alarm, event_type='CLEAR').count(), 1)


class AlarmIntegrationTest(TestCase):
    """告警集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123'
        )
        self.device = Device.objects.create(
            device_id='VHF-ALARM-001',
            device_type='VHF',
            owner=self.user
        )
        self.rule = AlarmRule.objects.create(
            name='集成测试规则',
            level='GLOBAL',
            device_type='VHF',
            metric='signal_strength',
            operator='<',
            threshold=-85.0,
            severity='WARN'
        )
        
        token_response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'test123'
        })
        if 'code' in token_response.data:
            self.token = token_response.data['data']['access']
        else:
            self.token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_list_alarms(self):
        """测试列出告警"""
        alarm = Alarm.objects.create(
            device=self.device,
            rule=self.rule,
            metric='signal_strength',
            value=-90.0,
            severity='WARN',
            status='OPEN',
            alarm_id='ALARM-INT-001',
            trigger_time=now()
        )
        response = self.client.get('/api/alarms/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.data['data'] if 'data' in response.data else response.data
        # 考虑到分页，如果使用了分页，data 可能是个字典，包含 results
        if isinstance(res_data, dict) and 'results' in res_data:
            self.assertGreaterEqual(len(res_data['results']), 1)
        else:
            self.assertGreaterEqual(len(res_data), 1)

    def test_acknowledge_alarm(self):
        """测试确认告警"""
        alarm = Alarm.objects.create(
            device=self.device,
            rule=self.rule,
            metric='signal_strength',
            value=-90.0,
            severity='WARN',
            status='OPEN',
            alarm_id='ALARM-INT-001',
            trigger_time=now()
        )
        response = self.client.post(f'/api/alarms/{alarm.id}/operate/', {
            'action': 'ACK',
            'operator': 'testuser',
            'message': '确认告警'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alarm.refresh_from_db()
        self.assertEqual(alarm.status, 'ACK')

    def test_clear_alarm(self):
        """测试清除告警"""
        alarm = Alarm.objects.create(
            device=self.device,
            rule=self.rule,
            metric='signal_strength',
            value=-90.0,
            severity='WARN',
            status='OPEN',
            alarm_id='ALARM-INT-001',
            trigger_time=now()
        )
        response = self.client.post(f'/api/alarms/{alarm.id}/operate/', {
            'action': 'CLEAR',
            'operator': 'testuser',
            'message': '清除告警'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alarm.refresh_from_db()
        self.assertEqual(alarm.status, 'CLEARED')
