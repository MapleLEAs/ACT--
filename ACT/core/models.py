from django.db import models

class BaseModel(models.Model):
    """
    基础抽象模型 (Common Base Model)
    所有业务模型都应继承此类，以统一字段标准
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True

class AbstractDevice(BaseModel):
    """
    通用设备抽象模型
    对应《最小闭环.md》Section 3: 设备基础字段清单
    适用于所有业务线 (通信导航、监视气象等)
    """
    device_id = models.CharField(max_length=50, unique=True, verbose_name="设备唯一标识")
    # device_type 需在具体子类中定义，以支持不同的 choices
    device_model = models.CharField(max_length=50, blank=True, null=True, verbose_name="设备型号")
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name="安装位置")
    manufacturer = models.CharField(max_length=100, blank=True, null=True, verbose_name="生产厂家")
    install_time = models.DateTimeField(blank=True, null=True, verbose_name="投用时间")
    protocol_version = models.CharField(max_length=20, blank=True, null=True, verbose_name="协议版本")

    class Meta:
        abstract = True

class AbstractStatusLog(BaseModel):
    """
    通用状态日志抽象模型
    对应《最小闭环.md》Section 6: 统一设备状态字段
    """
    DEVICE_STATUS_CHOICES = (
        ('NORMAL', '正常运行'),
        ('ALARM', '存在告警'),
        ('OFFLINE', '设备离线'),
    )

    # 核心状态字段
    online_status = models.BooleanField(default=False, verbose_name="在线状态")
    device_status = models.CharField(max_length=20, choices=DEVICE_STATUS_CHOICES, blank=True, null=True, verbose_name="综合状态")
    alarm_flag = models.BooleanField(default=False, verbose_name="告警标识")
    collect_time = models.DateTimeField(verbose_name="数据采集时间")

    class Meta:
        abstract = True


# 人员管理模块
class Personnel(BaseModel):
    """人员信息模型"""
    from django.contrib.auth.models import User
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personnel', verbose_name="关联用户")
    real_name = models.CharField(max_length=50, verbose_name="真实姓名")
    email = models.EmailField(verbose_name="邮箱")
    phone = models.CharField(max_length=20, verbose_name="电话")
    department = models.CharField(max_length=50, verbose_name="部门")
    position = models.CharField(max_length=50, verbose_name="职位")
    role_ids = models.JSONField(default=list, verbose_name="角色ID列表")

    def __str__(self):
        return self.real_name

    class Meta:
        verbose_name = "人员信息"
        verbose_name_plural = "人员信息"


class Permission(BaseModel):
    """权限模型"""
    name = models.CharField(max_length=50, verbose_name="权限名称")
    codename = models.CharField(max_length=100, unique=True, verbose_name="权限编码")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "权限"
        verbose_name_plural = "权限"


class Role(BaseModel):
    """角色模型"""
    name = models.CharField(max_length=50, verbose_name="角色名称")
    permissions = models.ManyToManyField(Permission, blank=True, verbose_name="权限列表")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "角色"
        verbose_name_plural = "角色"


# 工单管理模块
class WorkOrder(BaseModel):
    """工单模型"""
    STATUS_CHOICES = (
        ('pending', '待认领'),
        ('claimed', '已认领'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('canceled', '已取消')
    )
    title = models.CharField(max_length=100, verbose_name="工单标题")
    work_type = models.CharField(max_length=20, default='repair', verbose_name="工单类型")
    priority = models.CharField(max_length=20, default='medium', verbose_name="优先级")
    device = models.ForeignKey('monitor.Device', on_delete=models.CASCADE, related_name='work_orders', verbose_name="关联设备")
    description = models.TextField(verbose_name="描述")
    scheduled_time = models.DateTimeField(verbose_name="计划时间")
    estimated_duration = models.IntegerField(default=120, verbose_name="预计时长(分钟)")
    assignee = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders', verbose_name="处理人")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    progress_percent = models.IntegerField(default=0, verbose_name="进度百分比")
    attachments = models.JSONField(default=list, verbose_name="附件列表")
    claim_time = models.DateTimeField(null=True, blank=True, verbose_name="认领时间")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "工单"
        verbose_name_plural = "工单"


class WorkOrderProcessLog(BaseModel):
    """工单处理日志模型"""
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='process_logs', verbose_name="关联工单")
    action = models.CharField(max_length=20, verbose_name="操作类型")
    progress_percent = models.IntegerField(default=0, verbose_name="进度百分比")
    notes = models.TextField(blank=True, null=True, verbose_name="备注")
    attachments = models.JSONField(default=list, verbose_name="附件列表")
    next_step = models.TextField(blank=True, null=True, verbose_name="下一步")

    class Meta:
        verbose_name = "工单处理日志"
        verbose_name_plural = "工单处理日志"


# 维护计划模块
class MaintenancePlan(BaseModel):
    """维护计划模型"""
    name = models.CharField(max_length=100, verbose_name="计划名称")
    plan_type = models.CharField(max_length=20, default='inspection', verbose_name="计划类型")
    device_ids = models.JSONField(default=list, verbose_name="设备ID列表")
    cycle_type = models.CharField(max_length=20, default='monthly', verbose_name="周期类型")
    cycle_value = models.IntegerField(default=1, verbose_name="周期值")
    start_date = models.DateField(verbose_name="开始日期")
    estimated_hours = models.IntegerField(default=4, verbose_name="预计时长(小时)")
    check_items = models.JSONField(default=list, verbose_name="检查项")
    assignee = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="负责人")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "维护计划"
        verbose_name_plural = "维护计划"


class MaintenanceRecord(BaseModel):
    """维护记录模型"""
    plan = models.ForeignKey(MaintenancePlan, on_delete=models.CASCADE, related_name='records', verbose_name="关联计划")
    execution_date = models.DateTimeField(verbose_name="执行日期")
    executor = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, verbose_name="执行人")
    status = models.CharField(max_length=20, default='pending', verbose_name="状态")
    actual_finish_time = models.DateTimeField(null=True, blank=True, verbose_name="实际完成时间")
    details = models.JSONField(default=dict, verbose_name="详情")
    attachments = models.JSONField(default=list, verbose_name="附件列表")
    summary = models.TextField(blank=True, null=True, verbose_name="总结")

    class Meta:
        verbose_name = "维护记录"
        verbose_name_plural = "维护记录"


# 设备告警关联模块
class DeviceAlarmLink(BaseModel):
    """设备告警规则关联模型"""
    device = models.ForeignKey('monitor.Device', on_delete=models.CASCADE, related_name='alarm_links', verbose_name="关联设备")
    alarm_rule = models.ForeignKey('monitor.AlarmRule', on_delete=models.CASCADE, verbose_name="关联告警规则")
    link_type = models.CharField(max_length=20, default='threshold', verbose_name="关联类型")

    def __str__(self):
        return f"{self.device.device_id} - {self.alarm_rule.name}"

    class Meta:
        verbose_name = "设备告警关联"
        verbose_name_plural = "设备告警关联"
