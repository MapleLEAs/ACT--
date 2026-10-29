"""
初始化标准阈值数据的 Django 管理命令
"""
from django.core.management.base import BaseCommand
from monitor.threshold_models import initialize_standard_thresholds


class Command(BaseCommand):
    help = '初始化民航设备标准阈值数据'

    def handle(self, *args, **options):
        self.stdout.write('正在初始化标准阈值数据...')
        
        try:
            count = initialize_standard_thresholds()
            self.stdout.write(self.style.SUCCESS(f'成功初始化 {count} 条标准阈值记录！'))
            
            self.stdout.write('')
            self.stdout.write('阈值标准包括：')
            self.stdout.write('  - VHF 甚高频通信设备')
            self.stdout.write('  - ILS 仪表着陆系统')
            self.stdout.write('  - VOR 全向信标')
            self.stdout.write('  - DME 测距仪')
            self.stdout.write('  - HF 短波通信设备')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'初始化失败: {str(e)}'))
