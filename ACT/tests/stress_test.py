import os
import sys
import django
from django.utils.timezone import now
import time
import random
import statistics
import threading

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atc_monitor.settings')
django.setup()

from django.contrib.auth.models import User
from monitor.models import Device, DeviceStatusLog, AlarmRule, Alarm
from rest_framework.test import APIClient


class APIStressTest:
    """API压力测试类"""

    def __init__(self, base_url='http://127.0.0.1:8000'):
        self.base_url = base_url
        self.client = APIClient()
        self.token = None
        self.results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'errors': []
        }

    def authenticate(self, username='admin', password='admin123456'):
        """认证获取token"""
        response = self.client.post(f'{self.base_url}/api/token/', {
            'username': username,
            'password': password
        })
        if response.status_code == 200:
            if 'code' in response.data:
                self.token = response.data['data']['access']
            else:
                self.token = response.data['access']
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
            print(f"✅ 认证成功: {username}")
            return True
        else:
            print(f"❌ 认证失败: {response.data}")
            return False

    def measure_request(self, request_func, *args, **kwargs):
        """测量请求性能"""
        start_time = time.time()
        try:
            response = request_func(*args, **kwargs)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            self.results['total_requests'] += 1
            self.results['response_times'].append(response_time)
            
            if 200 <= response.status_code < 300:
                self.results['successful_requests'] += 1
                return response_time, True
            else:
                self.results['failed_requests'] += 1
                self.results['errors'].append({
                    'status_code': response.status_code,
                    'error': str(response.data)
                })
                return response_time, False
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            self.results['total_requests'] += 1
            self.results['failed_requests'] += 1
            self.results['errors'].append({
                'error': str(e)
            })
            return response_time, False

    def test_get_devices(self, count=100):
        """测试获取设备列表"""
        print(f"\n📱 测试获取设备列表 ({count}次请求)...")
        for i in range(count):
            response_time, success = self.measure_request(
                self.client.get, f'{self.base_url}/api/devices/'
            )
            if i % 20 == 0:
                print(f"  进度: {i+1}/{count}, 响应时间: {response_time:.2f}ms")

    def test_create_status_log(self, count=200):
        """测试创建状态日志"""
        print(f"\n📊 测试创建状态日志 ({count}次请求)...")
        # 获取现有设备，如果没有则创建
        if not Device.objects.exists():
            Device.objects.create(device_id='VHF-STRESS-001', device_type='VHF', owner=User.objects.first())
        
        device_ids = list(Device.objects.values_list('device_id', flat=True))
        
        for i in range(count):
            device_id = random.choice(device_ids)
            log_data = {
                'device': device_id,
                'online_status': random.choice([True, False]),
                'signal_strength': random.uniform(-100, -50),
                'link_status': random.choice(['CONNECTED', 'DISCONNECTED']),
                'device_temperature': random.uniform(20, 80),
                'collect_time': now().isoformat()
            }
            response_time, success = self.measure_request(
                self.client.post,
                f'{self.base_url}/api/status_logs/',
                log_data,
                format='json'
            )
            if i % 40 == 0:
                print(f"  进度: {i+1}/{count}, 响应时间: {response_time:.2f}ms")

    def print_statistics(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("📊 API压力测试统计报告")
        print("="*60)
        
        total = self.results['total_requests']
        successful = self.results['successful_requests']
        failed = self.results['failed_requests']
        
        print(f"   总请求数: {total}")
        print(f"   成功请求: {successful} ({successful/total*100:.2f}%)")
        print(f"   失败请求: {failed} ({failed/total*100:.2f}%)")
        
        if self.results['response_times']:
            response_times = self.results['response_times']
            print(f"   平均响应时间: {statistics.mean(response_times):.2f}ms")
            print(f"   中位数响应时间: {statistics.median(response_times):.2f}ms")
            print(f"   最大响应时间: {max(response_times):.2f}ms")
            
        print("\n" + "="*60)

    def run_full_test(self):
        """运行测试"""
        print("="*60)
        print("🚀 开始API压力测试")
        print("="*60)
        
        if not self.authenticate():
            print("❌ 认证失败，无法继续测试")
            return
        
        self.test_get_devices(50)
        self.test_create_status_log(100)
        self.print_statistics()


def main():
    stress_test = APIStressTest()
    stress_test.run_full_test()


if __name__ == '__main__':
    main()
