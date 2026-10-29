"""
设备标准阈值模型 - 基于民航标准和自定义的双轨制阈值系统
"""
from django.db import models
from django.core.cache import cache

# 设备类型枚举（与 Device 模型保持一致）
DEVICE_TYPE_CHOICES = (
    ('VHF', '甚高频通信设备'),
    ('ILS', '仪表着陆系统'),
    ('VOR', '全向信标'),
    ('DME', '测距仪'),
    ('HF', '短波通信设备'),
)


class DeviceThresholdStandard(models.Model):
    """
    设备标准阈值库
    基于 ICAO Annex 10 和 CAAC 标准文件的标准值
    """
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES, verbose_name="设备类型")
    metric_name = models.CharField(max_length=100, verbose_name="指标名称")
    metric_field = models.CharField(max_length=50, verbose_name="字段名")
    unit = models.CharField(max_length=20, blank=True, null=True, verbose_name="单位")
    
    # 标准值范围
    standard_min = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="标准下限")
    standard_max = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="标准上限")
    
    # 预警门限
    warning_low = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="预警下限")
    warning_high = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="预警上限")
    
    # 硬告警门限
    critical_low = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="硬告警下限")
    critical_high = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="硬告警上限")
    
    # 标准来源
    standard_source = models.CharField(max_length=200, verbose_name="标准来源", blank=True, null=True)
    is_enabled = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device_threshold_standards'
        verbose_name = '设备标准阈值'
        verbose_name_plural = verbose_name
        unique_together = ('device_type', 'metric_field')
        indexes = [
            models.Index(fields=['device_type', 'metric_field']),
        ]
    
    def __str__(self):
        return f"{self.get_device_type_display()} - {self.metric_name}"


class DeviceThresholdOverride(models.Model):
    """
    设备自定义阈值覆盖
    允许对特定设备的阈值进行自定义设置
    """
    device = models.ForeignKey(
        'monitor.Device', 
        to_field='device_id',
        on_delete=models.CASCADE,
        related_name='threshold_overrides',
        verbose_name="设备"
    )
    standard = models.ForeignKey(
        DeviceThresholdStandard,
        on_delete=models.CASCADE,
        related_name='overrides',
        verbose_name="标准基准"
    )
    
    # 自定义覆盖值
    override_warning_low = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="自定义预警下限")
    override_warning_high = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="自定义预警上限")
    override_critical_low = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="自定义硬告警下限")
    override_critical_high = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="自定义硬告警上限")
    
    is_enabled = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device_threshold_overrides'
        verbose_name = '设备自定义阈值'
        verbose_name_plural = verbose_name
        unique_together = ('device', 'standard')
    
    def __str__(self):
        return f"{self.device} - {self.standard.metric_name}"
    
    def get_effective_thresholds(self):
        """获取生效的阈值
        """
        return {
            'warning_low': self.override_warning_low or self.standard.warning_low,
            'warning_high': self.override_warning_high or self.standard.warning_high,
            'critical_low': self.override_critical_low or self.standard.critical_low,
            'critical_high': self.override_critical_high or self.standard.critical_high,
        }


def initialize_standard_thresholds():
    """初始化民航标准阈值数据 (基于用户提供的文档)
    """
    thresholds_data = [
        # ==================== VHF 甚高频通信设备 ====================
        {
            'device_type': 'VHF',
            'metric_name': '信号强度',
            'metric_field': 'signal_strength',
            'unit': 'dBm',
            'standard_min': -107.0,
            'standard_max': -60.0,
            'warning_low': -100.0,
            'warning_high': -70.0,
            'critical_low': -107.0,
            'critical_high': -90.0,
            'standard_source': 'ICAO Annex 10 Volume I',
        },
        {
            'device_type': 'VHF',
            'metric_name': '发射功率',
            'metric_field': 'transmit_power',
            'unit': 'W',
            'standard_min': 90.0,
            'standard_max': 110.0,
            'warning_low': 95.0,
            'warning_high': 105.0,
            'critical_low': 90.0,
            'critical_high': 110.0,
            'standard_source': '典型设备规格',
        },
        {
            'device_type': 'VHF',
            'metric_name': '驻波比',
            'metric_field': 'vswr',
            'unit': '',
            'standard_min': 1.0,
            'standard_max': 1.5,
            'warning_low': None,
            'warning_high': 2.0,
            'critical_low': None,
            'critical_high': 3.0,
            'standard_source': '工业射频标准',
        },
        {
            'device_type': 'VHF',
            'metric_name': '电源电压',
            'metric_field': 'power_voltage',
            'unit': 'V',
            'standard_min': 198.0,
            'standard_max': 242.0,
            'warning_low': 210.0,
            'warning_high': 230.0,
            'critical_low': 198.0,
            'critical_high': 242.0,
            'standard_source': '市电标准 220V±10%',
        },
        # ==================== ILS 仪表着陆系统 ====================
        {
            'device_type': 'ILS',
            'metric_name': '信号强度',
            'metric_field': 'signal_strength',
            'unit': 'dBm',
            'standard_min': -100.0,
            'standard_max': -60.0,
            'warning_low': -90.0,
            'warning_high': -70.0,
            'critical_low': -100.0,
            'critical_high': -90.0,
            'standard_source': 'ICAO Annex 10 Volume I',
        },
        {
            'device_type': 'ILS',
            'metric_name': '调制深度',
            'metric_field': 'modulation_depth',
            'unit': '%',
            'standard_min': 18.0,
            'standard_max': 22.0,
            'warning_low': 19.0,
            'warning_high': 21.0,
            'critical_low': 18.0,
            'critical_high': 22.0,
            'standard_source': 'ILS 标准',
        },
        # ==================== VOR 全向信标 ====================
        {
            'device_type': 'VOR',
            'metric_name': '信号强度',
            'metric_field': 'signal_strength',
            'unit': 'dBm',
            'standard_min': -105.0,
            'standard_max': -60.0,
            'warning_low': -95.0,
            'warning_high': -70.0,
            'critical_low': -105.0,
            'critical_high': -95.0,
            'standard_source': 'ICAO Annex 10',
        },
        {
            'device_type': 'VOR',
            'metric_name': '方位精度',
            'metric_field': 'bearing_accuracy',
            'unit': '°',
            'standard_min': -1.0,
            'standard_max': 1.0,
            'warning_low': -0.5,
            'warning_high': 0.5,
            'critical_low': -1.0,
            'critical_high': 1.0,
            'standard_source': 'VOR 导航标准',
        },
        # ==================== DME 测距仪 ====================
        {
            'device_type': 'DME',
            'metric_name': '信号强度',
            'metric_field': 'signal_strength',
            'unit': 'dBm',
            'standard_min': -100.0,
            'standard_max': -60.0,
            'warning_low': -90.0,
            'warning_high': -70.0,
            'critical_low': -100.0,
            'critical_high': -90.0,
            'standard_source': 'ICAO Annex 10',
        },
        {
            'device_type': 'DME',
            'metric_name': '脉冲间隔(X模式)',
            'metric_field': 'pulse_interval_x',
            'unit': 'μs',
            'standard_min': 11.9,
            'standard_max': 12.1,
            'warning_low': 11.95,
            'warning_high': 12.05,
            'critical_low': 11.9,
            'critical_high': 12.1,
            'standard_source': '标准 12μs',
        },
        {
            'device_type': 'DME',
            'metric_name': '脉冲间隔(Y模式)',
            'metric_field': 'pulse_interval_y',
            'unit': 'μs',
            'standard_min': 35.9,
            'standard_max': 36.1,
            'warning_low': 35.95,
            'warning_high': 36.05,
            'critical_low': 35.9,
            'critical_high': 36.1,
            'standard_source': '标准 36μs',
        },
        # ==================== HF 短波通信设备 ====================
        {
            'device_type': 'HF',
            'metric_name': '发射功率(PEP)',
            'metric_field': 'transmit_power',
            'unit': 'W',
            'standard_min': 70.0,
            'standard_max': 440.0,
            'warning_low': 85.0,
            'warning_high': 400.0,
            'critical_low': 70.0,
            'critical_high': 440.0,
            'standard_source': '典型 100-400W',
        },
        {
            'device_type': 'HF',
            'metric_name': '工作频率',
            'metric_field': 'work_frequency',
            'unit': 'MHz',
            'standard_min': 2.0,
            'standard_max': 30.0,
            'warning_low': None,
            'warning_high': None,
            'critical_low': 2.0,
            'critical_high': 30.0,
            'standard_source': '民航HF通信频段',
        },
    ]
    
    # 清空并重建
    DeviceThresholdStandard.objects.all().delete()
    
    for data in thresholds_data:
        DeviceThresholdStandard.objects.create(**data)
    
    cache.delete('threshold_standards')
    
    return len(thresholds_data)
