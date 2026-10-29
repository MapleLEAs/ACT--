from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
from core.models import AbstractDevice, AbstractStatusLog
from .threshold_models import DeviceThresholdStandard, DeviceThresholdOverride, initialize_standard_thresholds


class Device(AbstractDevice):
    """
    设备基础信息表
    继承自 core.models.AbstractDevice
    """
    DEVICE_TYPE_CHOICES = (
        ('VHF', '甚高频通信设备'),
        ('ILS', '仪表着陆系统'),
        ('VOR', '全向信标'),
        ('DME', '测距仪'),
        ('HF', '短波通信设备'),
    )

    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES, verbose_name="设备类型")
    # 新增数据隔离字段：所属用户
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices', verbose_name="所属用户", null=True, blank=True)
    # 新增 3D 位置坐标字段
    position_x = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="X 坐标")
    position_y = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Y 坐标")
    position_z = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Z 坐标")
    # NGSI‑LD GeoProperty 位置字段（使用 JSONField 替代 GIS，支持 GeoJSON 格式）
    geo_location = models.JSONField(blank=True, null=True, verbose_name="地理坐标")

    def __str__(self):
        return f"{self.device_id} ({self.device_type})"

    class Meta:
        db_table = 'devices'
        verbose_name = '设备信息'
        verbose_name_plural = verbose_name


class AlarmRule(models.Model):
    """
    告警规则表：定义设备在何种条件下触发告警
    """
    LEVEL_CHOICES = (
        ('GLOBAL', '全局'),
        ('DEVICE_TYPE', '设备类型级'),
        ('DEVICE', '设备级'),
    )

    SEVERITY_CHOICES = (
        ('INFO', '信息'),
        ('WARN', '警告'),
        ('ERROR', '错误'),
        ('CRITICAL', '严重'),
    )

    OPERATOR_CHOICES = (
        ('<', '小于'),
        ('>', '大于'),
        ('<=', '小于等于'),
        ('>=', '大于等于'),
        ('==', '等于'),
        ('!=', '不等于'),
        ('abs>', '绝对值大于'),
    )

    name = models.CharField(max_length=100, verbose_name="规则名称")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='GLOBAL', verbose_name="规则层级")
    device_type = models.CharField(max_length=20, choices=Device.DEVICE_TYPE_CHOICES, blank=True, null=True, verbose_name="适用设备类型")
    device = models.ForeignKey(Device, to_field='device_id', on_delete=models.CASCADE, blank=True, null=True, related_name='rules', verbose_name="适用特定设备")
    metric = models.CharField(max_length=50, verbose_name="监控指标")
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES, verbose_name="比较符")
    threshold = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="数值阈值")
    threshold_str = models.CharField(max_length=50, blank=True, null=True, verbose_name="字符串阈值")
    recovery_operator = models.CharField(
        max_length=10,
        choices=OPERATOR_CHOICES,
        blank=True,
        null=True,
        verbose_name="恢复比较符"
    )
    recovery_threshold = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="恢复数值阈值")
    recovery_threshold_str = models.CharField(max_length=50, blank=True, null=True, verbose_name="恢复字符串阈值")
    cooldown_seconds = models.PositiveIntegerField(default=0, verbose_name="重复触发冷却时间(秒)")
    auto_clear = models.BooleanField(default=True, verbose_name="恢复后自动清除")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='WARN', verbose_name="告警严重性")
    is_enabled = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        cache.delete('alarm_rules_cache')
        return result

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        cache.delete('alarm_rules_cache')
        return result

    class Meta:
        db_table = 'alarm_rules'
        verbose_name = '告警规则'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['level', 'device_type', 'is_enabled']),
        ]


class Alarm(models.Model):
    """
    告警记录表：记录已触发的告警实例及其状态
    """
    STATUS_CHOICES = (
        ('OPEN', '已触发'),
        ('ACK', '已确认'),
        ('CLEARED', '已清除'),
    )

    device = models.ForeignKey(
        Device,
        to_field='device_id',
        on_delete=models.CASCADE,
        related_name='alarms',
        verbose_name="关联设备"
    )
    rule = models.ForeignKey(
        AlarmRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alarms',
        verbose_name="触发规则"
    )

    metric = models.CharField(max_length=50, verbose_name="触发指标")

    # 触发时值
    value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="触发时的数值")
    value_str = models.CharField(max_length=100, blank=True, null=True, verbose_name="触发时的字符串值")

    # 恢复时值
    recover_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="恢复时的数值")
    recover_value_str = models.CharField(max_length=100, blank=True, null=True, verbose_name="恢复时的字符串值")

    severity = models.CharField(max_length=20, choices=AlarmRule.SEVERITY_CHOICES, verbose_name="严重性")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', verbose_name="告警状态")
    alarm_id = models.CharField(max_length=100, unique=True, verbose_name="唯一告警流水号")

    trigger_time = models.DateTimeField(verbose_name="触发时间")
    ack_time = models.DateTimeField(blank=True, null=True, verbose_name="确认时间")
    clear_time = models.DateTimeField(blank=True, null=True, verbose_name="清除时间")

    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="confirmed_alarms",
        verbose_name="确认人"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.alarm_id} [{self.status}]"

    class Meta:
        db_table = 'alarms'
        verbose_name = '告警记录'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['device', 'status', 'trigger_time']),
            models.Index(fields=['rule', 'status']),
            models.Index(fields=['metric', 'status']),
        ]


class AlarmEvent(models.Model):
    """
    告警生命周期事件表：记录告警的触发、确认、清除等操作日志
    """
    EVENT_TYPE_CHOICES = (
        ('TRIGGER', '系统触发'),
        ('ACK', '人工确认'),
        ('CLEAR', '系统/人工清除'),
    )

    alarm = models.ForeignKey(Alarm, on_delete=models.CASCADE, related_name='events', verbose_name="关联告警")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, verbose_name="事件类型")
    event_time = models.DateTimeField(auto_now_add=True, verbose_name="发生时间")
    operator = models.CharField(max_length=50, blank=True, null=True, verbose_name="操作人")
    description = models.TextField(blank=True, null=True, verbose_name="描述详情")

    class Meta:
        db_table = 'alarm_events'
        verbose_name = '告警事件'
        verbose_name_plural = verbose_name


class AlarmNotification(models.Model):
    """
    告警通知历史表
    """
    TYPE_CHOICES = (
        ('SYSTEM', '系统站内信'),
        ('EMAIL', '邮件'),
    )
    STATUS_CHOICES = (
        ('SENT', '已发送'),
        ('Failed', '发送失败'),
    )

    alarm = models.ForeignKey(Alarm, on_delete=models.CASCADE, related_name='notifications', verbose_name="关联告警")
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='SYSTEM')
    recipient = models.CharField(max_length=100, verbose_name="接收人")
    content = models.TextField(verbose_name="通知内容")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SENT')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'alarm_notifications'
        verbose_name = '告警通知'
        verbose_name_plural = verbose_name


class AbstractDeviceStatusLog(AbstractStatusLog):
    """
    设备状态时序数据抽象基类
    """
    LINK_STATUS_CHOICES = (
        ('CONNECTED', 'CONNECTED'),
        ('DISCONNECTED', 'DISCONNECTED'),
    )

    device = models.ForeignKey(Device, to_field='device_id', on_delete=models.CASCADE, related_name='%(class)s_logs', verbose_name="关联设备")

    # 通用物理量
    power_voltage = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="电源电压")
    device_temperature = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="运行温度")

    # VHF 专属字段
    signal_strength = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="信号强度")
    link_status = models.CharField(max_length=20, choices=LINK_STATUS_CHOICES, blank=True, null=True, verbose_name="链路状态")
    bit_error_rate = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True, verbose_name="误码率")

    # ILS 专属字段
    loc_guidance_deviation = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="LOC引导偏差")
    gs_guidance_deviation = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="GS下滑偏差")
    signal_power = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="信号功率")
    antenna_swr = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="天线驻波比")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['device', 'collect_time']),
            models.Index(fields=['device', 'collect_time', 'online_status', 'device_status', 'alarm_flag'], name='idx_%(class)s_latest'),
            models.Index(fields=['collect_time', 'device', 'power_voltage', 'device_temperature'], name='idx_%(class)s_time_range'),
            models.Index(fields=['alarm_flag', 'collect_time', 'device'], name='idx_%(class)s_alarm_query'),
        ]


class DeviceStatusLog(AbstractDeviceStatusLog):
    """
    默认设备状态记录表（热数据表）
    """
    device = models.ForeignKey(Device, to_field='device_id', on_delete=models.CASCADE, related_name='status_logs', verbose_name="关联设备")

    class Meta(AbstractDeviceStatusLog.Meta):
        db_table = 'device_status_logs'
        verbose_name = '设备状态记录'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['device', 'collect_time']),
            models.Index(fields=['device', 'collect_time', 'online_status', 'device_status', 'alarm_flag'], name='idx_device_latest'),
            models.Index(fields=['collect_time', 'device', 'power_voltage', 'device_temperature'], name='idx_time_range'),
            models.Index(fields=['alarm_flag', 'collect_time', 'device'], name='idx_alarm_query'),
        ]


class DeviceStatusLogCold(AbstractDeviceStatusLog):
    """
    设备状态冷数据表（归档）
    """
    class Meta(AbstractDeviceStatusLog.Meta):
        db_table = 'device_status_logs_cold'
        verbose_name = '设备状态冷数据'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['collect_time']),
            models.Index(fields=['device']),
        ]


# 修复：不再继承AbstractDevice，消除冗余字段
class DeviceThreshold(models.Model):
    """
    设备参数标准阈值表
    完整对应VHF/ILS/VOR/DME/HF各类设备监测参数上下限
    """
    DEVICE_TYPE_CHOICES = (
        ("VHF", "甚高频通信设备"),
        ("ILS", "仪表着陆系统"),
        ("VOR", "全向信标"),
        ("DME", "测距仪"),
        ("HF", "短波通信设备"),
    )
    PARAM_CHOICES = (
        ("signal_strength", "信号强度"),
        ("signal_power", "信号功率"),
        ("voltage", "电源电压"),
        ("temperature", "运行温度"),
        ("azimuth_error", "方位角误差"),
        ("response_efficiency", "应答效率"),
        ("transmit_power", "发射功率"),
    )
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES, verbose_name="设备类型")
    device_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="设备编号")
    param_name = models.CharField(max_length=30, choices=PARAM_CHOICES, verbose_name="监测属性")
    min_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="标准值下限")
    max_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="标准值上限")

    class Meta:
        verbose_name = "设备标准阈值表"
        verbose_name_plural = verbose_name
        unique_together = ("device_type", "device_code", "param_name")


class EnvironmentData(models.Model):
    """
    环境数据表：温湿度、气压、气象等采集数据
    """
    device = models.ForeignKey(Device, to_field='device_id', on_delete=models.CASCADE, related_name='environment_data', verbose_name="关联设备")

    ambient_temperature = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="环境温度")
    humidity = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="湿度")
    atmospheric_pressure = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="大气压力")
    wind_speed = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="风速")
    wind_direction = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="风向")
    rain_intensity = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="降雨强度")
    visibility = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="能见度")

    collect_time = models.DateTimeField(verbose_name="数据采集时间")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'environment_data'
        verbose_name = '环境数据'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['device', 'collect_time']),
        ]


class PredictionResult(models.Model):
    """
    设备故障预测结果表
    """
    device = models.ForeignKey(Device, to_field='device_id', on_delete=models.CASCADE, related_name='predictions', verbose_name="关联设备")

    metric = models.CharField(max_length=50, verbose_name="预测指标")
    predicted_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="预测值")
    prediction_time = models.DateTimeField(verbose_name="预测时间")
    prediction_horizon = models.IntegerField(verbose_name="预测时间跨度(分钟)")

    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="置信度")
    error_margin = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="误差范围")

    threshold_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="阈值")
    is_above_threshold = models.BooleanField(blank=True, null=True, verbose_name="是否超限")
    severity = models.CharField(max_length=20, choices=AlarmRule.SEVERITY_CHOICES, blank=True, null=True, verbose_name="严重程度")

    status = models.CharField(max_length=20, default='PREDICTED', verbose_name="预测状态")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prediction_results'
        verbose_name = '预测结果'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['device', 'prediction_time']),
            models.Index(fields=['metric', 'is_above_threshold']),
        ]


# ===================== 文档管理模块 已经修复 name字段 =====================
class DocCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="文档分类")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children", verbose_name="上级分类")
    create_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="分类归属用户")

    class Meta:
        verbose_name = "文档分类"
        verbose_name_plural = verbose_name

    @property
    def doc_count(self):
        return self.document_set.count()

    def __str__(self):
        return self.name


class Document(models.Model):
    name = models.CharField(max_length=200, verbose_name="文档名称")
    category = models.ForeignKey(DocCategory, on_delete=models.SET_NULL, null=True, related_name="document_set", verbose_name="所属分类")
    file = models.FileField(upload_to="docs/", verbose_name="上传文件")
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="文档归属用户")

    def __str__(self):
        return self.name