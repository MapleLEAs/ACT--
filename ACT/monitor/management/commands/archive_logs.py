from django.core.management.base import BaseCommand
from django.utils import timezone
from monitor.models import DeviceStatusLog, DeviceStatusLogCold
from django.db import transaction
import datetime

class Command(BaseCommand):
    help = '将旧的设备状态日志移动到冷存储表 (archive_logs)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='保留多少天的数据在热表中 (默认 7 天)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - datetime.timedelta(days=days)
        
        self.stdout.write(f"正在迁移 {cutoff_date} 之前的数据...")
        
        # 使用事务保证迁移的原子性
        with transaction.atomic():
            # 1. 获取需要迁移的数据
            old_logs = DeviceStatusLog.objects.filter(collect_time__lt=cutoff_date)
            count = old_logs.count()
            
            if count == 0:
                self.stdout.write(self.style.SUCCESS("没有需要迁移的数据。"))
                return

            # 2. 批量插入到冷表
            # 注意：由于字段完全一致，我们可以直接插入
            # 这里为了简单直接使用模型操作，大规模数据下可以使用 Raw SQL
            cold_logs = []
            for log in old_logs:
                cold_logs.append(DeviceStatusLogCold(
                    device=log.device,
                    online_status=log.online_status,
                    device_status=log.device_status,
                    alarm_flag=log.alarm_flag,
                    collect_time=log.collect_time,
                    power_voltage=log.power_voltage,
                    device_temperature=log.device_temperature,
                    signal_strength=log.signal_strength,
                    link_status=log.link_status,
                    bit_error_rate=log.bit_error_rate,
                    loc_guidance_deviation=log.loc_guidance_deviation,
                    gs_guidance_deviation=log.gs_guidance_deviation,
                    signal_power=log.signal_power,
                    antenna_swr=log.antenna_swr
                ))
            
            DeviceStatusLogCold.objects.bulk_create(cold_logs, batch_size=1000)
            
            # 3. 从热表删除
            old_logs.delete()
            
            self.stdout.write(self.style.SUCCESS(f"成功迁移 {count} 条记录到冷存储。"))
