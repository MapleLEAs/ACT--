from django.contrib import admin
from .models import Device, DeviceStatusLog, AlarmRule, Alarm, AlarmEvent, AlarmNotification
from .alarm_engine import AlarmEngineService
from django.utils.timezone import now

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'device_type', 'location', 'manufacturer', 'created_at')
    list_filter = ('device_type', 'location')
    search_fields = ('device_id', 'device_type', 'location', 'manufacturer')
    ordering = ('device_id',)

@admin.register(AlarmRule)
class AlarmRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'device_type', 'metric', 'operator', 'threshold', 'severity', 'is_enabled')
    list_filter = ('level', 'device_type', 'severity', 'is_enabled')
    search_fields = ('name', 'metric')
    ordering = ('-created_at',)

@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ('alarm_id', 'device', 'metric', 'severity', 'status', 'trigger_time')
    list_filter = ('status', 'severity', 'device__device_type')
    search_fields = ('alarm_id', 'device__device_id', 'metric')
    ordering = ('-trigger_time',)
    readonly_fields = ('alarm_id', 'trigger_time')

@admin.register(AlarmEvent)
class AlarmEventAdmin(admin.ModelAdmin):
    list_display = ('alarm', 'event_type', 'event_time', 'operator')
    list_filter = ('event_type',)
    ordering = ('-event_time',)

@admin.register(AlarmNotification)
class AlarmNotificationAdmin(admin.ModelAdmin):
    list_display = ('alarm', 'notification_type', 'recipient', 'status', 'created_at')
    list_filter = ('notification_type', 'status')
    ordering = ('-created_at',)

@admin.register(DeviceStatusLog)
class DeviceStatusLogAdmin(admin.ModelAdmin):
    list_display = ('device', 'collect_time', 'device_status', 'alarm_flag', 'online_status')
    list_filter = ('device_status', 'alarm_flag', 'online_status', 'device__device_type')
    search_fields = ('device__device_id',)
    ordering = ('-collect_time',)
    raw_id_fields = ('device',)
    
    def save_model(self, request, obj, form, change):
        """保存模型时触发告警引擎"""
        if not obj.collect_time:
            obj.collect_time = now()
        
        # 保存前准备数据
        data = {
            'online_status': obj.online_status,
            'signal_strength': obj.signal_strength,
            'collect_time': obj.collect_time
        }
        
        # 保存模型
        super().save_model(request, obj, form, change)
        
        # 触发告警引擎
        engine = AlarmEngineService()
        result = engine.process_status(obj.device, data)
        
        # 更新告警标识和设备状态
        obj.alarm_flag = result['alarm_flag']
        obj.device_status = result['device_status']
        obj.save(update_fields=['alarm_flag', 'device_status'])
