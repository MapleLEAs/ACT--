from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Personnel, Permission, Role, WorkOrder, WorkOrderProcessLog, MaintenancePlan, MaintenanceRecord, DeviceAlarmLink
from monitor.models import Device


# 设备管理序列化器
class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

class DeviceAlarmLinkSerializer(serializers.Serializer):
    alarm_rule_ids = serializers.ListField(child=serializers.IntegerField())
    link_type = serializers.CharField(default='threshold')

# 人员管理序列化器
class PersonnelSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    initial_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Personnel
        fields = ['id', 'username', 'real_name', 'email', 'phone', 'department', 'position', 'role_ids', 'initial_password']


class PermissionUpdateSerializer(serializers.Serializer):
    permissions = serializers.ListField(child=serializers.CharField())
    operation_type = serializers.CharField(default='replace')


class RoleAssignSerializer(serializers.Serializer):
    role_ids = serializers.ListField(child=serializers.IntegerField())


# 工单管理序列化器
class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = '__all__'


class WorkOrderProcessSerializer(serializers.Serializer):
    action = serializers.CharField()
    progress_percent = serializers.IntegerField(default=0)
    notes = serializers.CharField(required=False, allow_blank=True)
    attachments = serializers.JSONField(default=list)
    next_step = serializers.CharField(required=False, allow_blank=True)


# 维护计划序列化器
class MaintenancePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenancePlan
        fields = '__all__'


class MaintenanceExecuteSerializer(serializers.Serializer):
    execution_date = serializers.DateTimeField()
    executor_id = serializers.IntegerField()
    generate_workorder = serializers.BooleanField(default=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class MaintenanceCompleteSerializer(serializers.Serializer):
    actual_finish_time = serializers.DateTimeField()
    details = serializers.JSONField()
    attachments = serializers.JSONField(default=list)
    summary = serializers.CharField(required=False, allow_blank=True)
