from rest_framework import serializers
from .models import (
    Device, DeviceStatusLog, AlarmRule, Alarm, AlarmEvent,
    AlarmNotification, PredictionResult, EnvironmentData,
    DocCategory, Document
)


class DeviceSerializer(serializers.ModelSerializer):
    latest_status = serializers.SerializerMethodField()
    latest_status_time = serializers.SerializerMethodField()
    online_status = serializers.SerializerMethodField()
    alarm_level = serializers.SerializerMethodField()
    name = serializers.CharField(source='device_model', read_only=True)

    def get_latest_status(self, obj):
        latest_log = getattr(obj, '_latest_log', None)
        if latest_log is None:
            latest_log = obj.status_logs.order_by('-collect_time').first()
        return latest_log.device_status if latest_log else 'NORMAL'

    def get_latest_status_time(self, obj):
        latest_log = getattr(obj, '_latest_log', None)
        if latest_log is None:
            latest_log = obj.status_logs.order_by('-collect_time').first()
        return latest_log.collect_time if latest_log else None

    def get_online_status(self, obj):
        latest_log = getattr(obj, '_latest_log', None)
        if latest_log is None:
            latest_log = obj.status_logs.order_by('-collect_time').first()
        return latest_log.online_status if latest_log else False

    def get_alarm_level(self, obj):
        latest_alarm = getattr(obj, '_latest_active_alarm', None)
        if latest_alarm is None:
            latest_alarm = obj.alarms.filter(status__in=['OPEN', 'ACK']).order_by('-trigger_time').first()
        return latest_alarm.severity.lower() if latest_alarm else 'none'

    class Meta:
        model = Device
        fields = [
            'id', 'device_id', 'device_type', 'device_model', 'name', 'location',
            'manufacturer', 'install_time', 'owner', 'position_x', 'position_y',
            'position_z', 'geo_location', 'created_at', 'updated_at',
            'latest_status', 'latest_status_time', 'online_status', 'alarm_level'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class DeviceStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceStatusLog
        fields = '__all__'


class AlarmRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlarmRule
        fields = '__all__'


class AlarmEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlarmEvent
        fields = '__all__'


class AlarmNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlarmNotification
        fields = '__all__'


class AlarmDeviceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='device_model', read_only=True)

    class Meta:
        model = Device
        fields = ['device_id', 'device_type', 'name']


class AlarmRuleInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlarmRule
        fields = ['id', 'name']


class AlarmSerializer(serializers.ModelSerializer):
    device = AlarmDeviceSerializer(read_only=True)
    device_name = serializers.CharField(source='device.device_id', read_only=True)
    device_id = serializers.CharField(source='device.device_id', read_only=True)
    device_type = serializers.CharField(source='device.device_type', read_only=True)
    rule = AlarmRuleInfoSerializer(read_only=True)
    title = serializers.CharField(source='rule.name', read_only=True)
    description = serializers.SerializerMethodField()
    level = serializers.CharField(source='severity', read_only=True)
    raised_at = serializers.DateTimeField(source='trigger_time', read_only=True)
    acknowledged_at = serializers.DateTimeField(source='ack_time', read_only=True)
    handler_name = serializers.SerializerMethodField()
    confirmed_by_name = serializers.CharField(source='confirmed_by.username', read_only=True)
    message = serializers.SerializerMethodField()

    def get_description(self, obj):
        return f"{obj.metric}: {obj.value}"

    def get_message(self, obj):
        op = obj.rule.operator if obj.rule else ""
        return f"{obj.metric} {op} {obj.value}"

    def get_handler_name(self, obj):
        if obj.confirmed_by:
            return obj.confirmed_by.username
        ack_event = obj.events.filter(event_type='ACK').last()
        return ack_event.operator if ack_event else None

    class Meta:
        model = Alarm
        fields = [
            'id', 'device', 'device_name', 'device_id', 'device_type',
            'rule', 'title', 'description', 'message',
            'level', 'severity', 'status', 'raised_at', 'acknowledged_at',
            'handler_name', 'confirmed_by', 'confirmed_by_name',
            'metric', 'value', 'value_str', 'recover_value', 'recover_value_str',
            'alarm_id', 'trigger_time'
        ]


class AlarmOperateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['ACK', 'CLEAR'])
    operator = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)


class PredictionResultSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source='device.device_id', read_only=True)
    device_type = serializers.CharField(source='device.device_type', read_only=True)

    class Meta:
        model = PredictionResult
        fields = [
            'id', 'device', 'device_id', 'device_type', 'metric', 'predicted_value',
            'prediction_time', 'prediction_horizon', 'confidence_score',
            'error_margin', 'threshold_value', 'is_above_threshold',
            'severity', 'status', 'created_at'
        ]


class EnvironmentDataSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source='device.device_id', read_only=True)

    class Meta:
        model = EnvironmentData
        fields = [
            'id', 'device', 'device_id', 'ambient_temperature', 'humidity',
            'atmospheric_pressure', 'wind_speed', 'wind_direction',
            'rain_intensity', 'visibility', 'collect_time', 'created_at'
        ]


# ============文档模块序列化器【最终修复版】============
class DocCategorySerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="name", read_only=True)
    doc_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DocCategory
        fields = ["id", "name", "label", "parent", "create_time", "doc_count"]

    def get_doc_count(self, obj):
        #优先读取视图annotate预计算的 _doc_count，没有就实时统计
        if hasattr(obj, "_doc_count"):
            return obj._doc_count
        return obj.document_set.count()


class DocumentSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Document
        fields = ["id", "name", "category", "category_name", "file", "upload_time"]