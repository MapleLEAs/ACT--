import numpy as np
from django.db import models, transaction
from django.db.models import Q, Count, Avg, Max, Min, OuterRef, Subquery
from django.http import JsonResponse
from django.utils.timezone import is_naive, now
from datetime import timedelta, datetime
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from django.contrib.auth.models import User

from .models import (
    Device, DeviceStatusLog, AlarmRule, Alarm, AlarmEvent, AlarmNotification,
    PredictionResult, EnvironmentData, DocCategory, Document
)
from .serializers import (
    DeviceSerializer, DeviceStatusLogSerializer,
    AlarmRuleSerializer, AlarmSerializer, AlarmOperateSerializer,
    PredictionResultSerializer, EnvironmentDataSerializer,
    DocCategorySerializer, DocumentSerializer
)
from .algorithms import PredictionModel, TrendCalculator, ExponentialSmoothingModel
from .alarm_engine import AlarmEngineService
from .health_service import calculate_device_health, get_health_summary, recalculate_predictions
from .graph_service import RootCauseGraphService
from core.ngsi_ld import NGSI_LD_Converter
from core.ngsi_exchange import NGSIExchangeService
from core.ai.multi_device_predict import multi_device_predict
from core.ai.fault_propagation import fault_propagation, get_coupling_strength
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """健康检查API"""
    try:
        from django.db import connection
        import os
        
        checks = {
            'status': 'healthy',
            'timestamp': now().isoformat(),
            'checks': []
        }
        
        try:
            with connection.cursor():
                checks['checks'].append({'name': 'database', 'status': 'pass'})
        except Exception as e:
            checks['checks'].append({'name': 'database', 'status': 'fail', 'error': str(e)})
            checks['status'] = 'unhealthy'
        
        try:
            from redis import Redis
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            r = Redis(host=redis_host, port=redis_port, socket_timeout=5)
            r.ping()
            checks['checks'].append({'name': 'redis', 'status': 'pass'})
        except Exception as e:
            checks['checks'].append({'name': 'redis', 'status': 'fail', 'error': str(e)})
        
        return JsonResponse(checks, safe=False)
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def database_stats(request):
    """数据库统计信息API"""
    try:
        cache_key = 'database_stats_cache'
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(cached, safe=False)

        latest_log_ids = DeviceStatusLog.objects.values('device_id').annotate(
            max_id=Max('id')
        ).values('max_id')
        latest_logs = DeviceStatusLog.objects.filter(id__in=Subquery(latest_log_ids))

        device_stats = {
            'total': Device.objects.count(),
            'by_type': list(Device.objects.values('device_type').annotate(count=Count('id'))),
            'online': latest_logs.filter(online_status=True).count(),
            'offline': latest_logs.filter(online_status=False).count(),
            'error': latest_logs.filter(device_status='ALARM').count(),
        }

        alarm_stats = {
            'total': Alarm.objects.count(),
            'open': Alarm.objects.filter(status='OPEN').count(),
            'ack': Alarm.objects.filter(status='ACK').count(),
            'cleared': Alarm.objects.filter(status='CLEARED').count(),
            'by_severity': list(Alarm.objects.values('severity').annotate(count=Count('id'))),
            'recent': list(
                Alarm.objects.filter(created_at__gte=now() - timedelta(days=7))
                .values('created_at__date')
                .annotate(count=Count('id'))
                .order_by('created_at__date')
            ),
        }

        log_stats = {
            'total': DeviceStatusLog.objects.count(),
            'last_24h': DeviceStatusLog.objects.filter(created_at__gte=now() - timedelta(hours=24)).count(),
            'by_device_type': list(DeviceStatusLog.objects.values('device__device_type').annotate(count=Count('id'))),
        }

        rule_stats = {
            'total': AlarmRule.objects.count(),
            'enabled': AlarmRule.objects.filter(is_enabled=True).count(),
            'disabled': AlarmRule.objects.filter(is_enabled=False).count(),
            'by_level': list(AlarmRule.objects.values('level').annotate(count=Count('id'))),
        }

        growth_trend = []
        for i in range(29, -1, -1):
            date = now().date() - timedelta(days=i)
            growth_trend.append({
                'date': date.strftime('%Y-%m-%d'),
                'devices': Device.objects.filter(created_at__date__lte=date).count(),
                'alarms': Alarm.objects.filter(created_at__date__lte=date).count(),
                'logs': DeviceStatusLog.objects.filter(created_at__date=date).count(),
            })

        stats = {
            'timestamp': now().isoformat(),
            'devices': device_stats,
            'alarms': alarm_stats,
            'logs': log_stats,
            'rules': rule_stats,
            'growth_trend': growth_trend,
        }

        cache.set(cache_key, stats, 1800)

        return JsonResponse(stats, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def database_schema(request):
    """数据库表结构API"""
    from django.apps import apps
    from django.db.models.fields import CharField, IntegerField, FloatField, BooleanField, DateTimeField, DecimalField
    from django.db.models import JSONField
    
    try:
        app_models = apps.get_app_config('monitor').get_models()
        tables = []
        
        for model in app_models:
            fields = []
            for field in model._meta.get_fields():
                field_type = field.__class__.__name__
                fields.append({
                    'name': field.name,
                    'type': field_type,
                    'verbose_name': getattr(field, 'verbose_name', field.name),
                    'null': getattr(field, 'null', False),
                    'blank': getattr(field, 'blank', False),
                    'primary_key': getattr(field, 'primary_key', False),
                })
            
            tables.append({
                'name': model._meta.db_table,
                'verbose_name': model._meta.verbose_name,
                'fields': fields,
                'count': model.objects.count(),
            })
        
        return JsonResponse({'tables': tables}, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    lookup_field = 'device_id'
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """数据隔离与预加载优化"""
        user = self.request.user
        
        # 基础查询集
        if user.is_authenticated and not user.is_superuser:
            queryset = Device.objects.filter(owner=user)
        else:
            queryset = Device.objects.all()
            
        return queryset

    def list(self, request, *args, **kwargs):
        """
        列表接口优化：避免 N+1 查询，同时防止大量历史数据导致内存溢出
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # 分页处理
        page = self.paginate_queryset(queryset)
        target_queryset = page if page is not None else queryset
        
        # 为当前页的设备批量获取最新状态和告警 (比 prefetch_related 全表更安全)
        device_ids = [d.device_id for d in target_queryset]
        
        if device_ids:
            # 1. 获取最新状态记录 (每个设备仅一条)
            from django.db.models import Max
            latest_log_ids = DeviceStatusLog.objects.filter(device_id__in=device_ids).values('device_id').annotate(max_id=Max('id')).values_list('max_id', flat=True)
            latest_logs_dict = {log.device_id: log for log in DeviceStatusLog.objects.filter(id__in=latest_log_ids)}
            
            # 2. 获取最新活跃告警
            from monitor.models import Alarm
            latest_alarm_ids = Alarm.objects.filter(device_id__in=device_ids, status__in=['OPEN', 'ACK']).values('device_id').annotate(max_id=Max('id')).values_list('max_id', flat=True)
            latest_alarms_dict = {alarm.device_id: alarm for alarm in Alarm.objects.filter(id__in=latest_alarm_ids)}
            
            # 3. 注入属性
            for device in target_queryset:
                device._latest_log = latest_logs_dict.get(device.device_id)
                device._latest_active_alarm = latest_alarms_dict.get(device.device_id)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """创建设备时自动绑定当前用户"""
        owner = self.request.user if self.request.user.is_authenticated else None
        serializer.save(owner=owner)

    @action(detail=False, methods=['post'], url_path='batch-create')
    def batch_create(self, request):
        """批量创建设备"""
        data_list = request.data.get('data', [])
        if not isinstance(data_list, list) or not data_list:
            return Response(
                {"message": "data 必须是非空数组"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_count = 0
        errors = []
        owner = request.user if request.user.is_authenticated else None
        valid_device_types = {choice[0] for choice in Device.DEVICE_TYPE_CHOICES}

        for index, item in enumerate(data_list):
            device_id = str(item.get('device_id', '')).strip()
            if not device_id:
                errors.append({"index": index, "device_id": "", "message": "device_id 不能为空"})
                continue
            if Device.objects.filter(device_id=device_id).exists():
                errors.append({"index": index, "device_id": device_id, "message": "device_id 已存在"})
                continue

            device_type = item.get('device_type')
            if device_type not in valid_device_types:
                errors.append({"index": index, "device_id": device_id, "message": "device_type 非法"})
                continue

            serializer = self.get_serializer(
                data={
                    "device_id": device_id,
                    "device_type": device_type,
                    "device_model": item.get("device_model"),
                    "location": item.get("location"),
                    "manufacturer": item.get("manufacturer"),
                    "install_time": item.get("install_time"),
                    "position_x": item.get("position_x", 0),
                    "position_y": item.get("position_y", 0),
                    "position_z": item.get("position_z", 0),
                    "geo_location": item.get("geo_location"),
                }
            )
            if not serializer.is_valid():
                errors.append({
                    "index": index,
                    "device_id": device_id,
                    "message": serializer.errors,
                })
                continue

            serializer.save(owner=owner)
            created_count += 1

        if created_count:
            cache.delete('database_stats_cache')

        return Response(
            {
                "created_count": created_count,
                "failed_count": len(errors),
                "errors": errors,
            }
        )

    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, device_id=None):
        """快捷变更设备状态，并接入告警引擎"""
        device = self.get_object()
        new_status = request.data.get('status')

        if new_status not in ['online', 'offline', 'error']:
            return Response({"error": "无效的状态"}, status=status.HTTP_400_BAD_REQUEST)

        old_status = getattr(device, 'status', None)
        device.status = new_status
        device.save()

        payload = {
            'online_status': (new_status == 'online'),
            'device_status': new_status.upper(),
            'collect_time': now()
        }

        engine = AlarmEngineService()
        result = engine.process_status(device, payload)

        log = DeviceStatusLog.objects.create(
            device=device,
            online_status=payload['online_status'],
            device_status=result['device_status'],
            alarm_flag=result['alarm_flag'],
            collect_time=payload['collect_time']
        )

        return Response({
            "message": f"状态已从 {old_status} 变更为 {new_status}",
            "device_id": device.device_id,
            "current_status": device.status,
            "log_id": log.id,
            "alarm_flag": result["alarm_flag"],
            "device_status": result["device_status"],
            "triggered_alarm_ids": [a.alarm_id for a in result["triggered_alarms"]],
            "cleared_alarm_ids": [a.alarm_id for a in result["cleared_alarms"]],
        })

    @action(detail=False, methods=['get'], url_path='check-name')
    def check_name(self, request):
        """检查设备名称是否已存在"""
        name = request.query_params.get('name', '')
        if not name:
            return Response({'available': False, 'error': '名称不能为空'})
        
        exists = Device.objects.filter(device_model=name).exists()
        return Response({'available': not exists})
    
    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """设备统计数据"""
        from django.db.models import Subquery, OuterRef
        
        queryset = self.get_queryset()
        total_devices = queryset.count()
        
        # 获取每个设备最新的状态记录
        latest_logs = DeviceStatusLog.objects.filter(
            device=OuterRef('pk')
        ).order_by('-collect_time')
        
        # 获取在线设备数量（基于最新状态记录）
        online_devices = queryset.filter(
            status_logs__online_status=True,
            status_logs__collect_time=Subquery(latest_logs.values('collect_time')[:1])
        ).count()
        
        # 计算运行率
        operation_rate = round((online_devices / total_devices * 100), 1) if total_devices > 0 else 0
        
        return Response({
            "total_devices": total_devices,
            "online_devices": online_devices,
            "operation_rate": operation_rate
        })

class AlarmRuleViewSet(viewsets.ModelViewSet):
    queryset = AlarmRule.objects.all()
    serializer_class = AlarmRuleSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_update(self, serializer):
        serializer.save()
        # 更新规则后清除缓存
        cache.delete('alarm_rules_cache')

    def perform_create(self, serializer):
        serializer.save()
        cache.delete('alarm_rules_cache')

class AlarmViewSet(viewsets.ModelViewSet):
    # 优化：使用 select_related 预加载关联的 device 和 rule，减少 N+1 查询
    queryset = Alarm.objects.select_related('device', 'rule').all().order_by('-trigger_time')
    serializer_class = AlarmSerializer
    filterset_fields = ['device__device_id', 'status', 'severity']
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """数据隔离：用户只能看到自己名下设备的告警"""
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if not user.is_superuser:
            queryset = queryset.filter(device__owner=user)
        return queryset

    def list(self, request, *args, **kwargs):
        # 如果 URL 包含 ngsi，返回 NGSI-LD 格式
        if 'ngsi' in request.path:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                data = [NGSI_LD_Converter.alarm_to_ngsi_ld(a) for a in page]
                return self.get_paginated_response(data)
            data = [NGSI_LD_Converter.alarm_to_ngsi_ld(a) for a in queryset]
            return Response(data)
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        if 'ngsi' in request.path:
            instance = self.get_object()
            return Response(NGSI_LD_Converter.alarm_to_ngsi_ld(instance))
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='ack')
    def ack(self, request, pk=None):
        """确认告警（便捷接口）"""
        alarm = self.get_object()

        if alarm.status == 'CLEARED':
            return Response({"error": "已清除告警不能再确认"}, status=status.HTTP_400_BAD_REQUEST)

        if alarm.status == 'ACK':
            return Response(AlarmSerializer(alarm).data)

        alarm.status = 'ACK'
        alarm.ack_time = now()
        alarm.confirmed_by = request.user
        alarm.save(update_fields=['status', 'ack_time', 'confirmed_by'])

        AlarmEvent.objects.create(
            alarm=alarm,
            event_type='ACK',
            operator=request.user.username,
            description="通过便捷接口确认告警"
        )
        return Response(AlarmSerializer(alarm).data)

    @action(detail=True, methods=['post'], url_path='clear')
    def clear(self, request, pk=None):
        """清除告警（便捷接口）"""
        alarm = self.get_object()

        if alarm.status == 'CLEARED':
            return Response(AlarmSerializer(alarm).data)

        alarm.status = 'CLEARED'
        alarm.clear_time = now()
        alarm.save(update_fields=['status', 'clear_time'])

        AlarmEvent.objects.create(
            alarm=alarm,
            event_type='CLEAR',
            operator=request.user.username,
            description="通过便捷接口清除告警"
        )
        return Response(AlarmSerializer(alarm).data)

    @action(detail=True, methods=['post'], url_path='operate')
    def operate(self, request, pk=None):
        """确认或清除告警"""
        alarm = self.get_object()
        serializer = AlarmOperateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        act = serializer.validated_data['action']
        op = serializer.validated_data.get('operator', 'system')
        msg = serializer.validated_data.get('message', '')
        
        if act == 'ACK':
            alarm.status = 'ACK'
            alarm.ack_time = now()
            alarm.confirmed_by = request.user
            event_type = 'ACK'
            desc = f"告警已确认: {msg}"
        else:  # CLEAR
            alarm.status = 'CLEARED'
            alarm.clear_time = now()
            event_type = 'CLEAR'
            desc = f"告警已清除: {msg}"
            
        alarm.save()
        AlarmEvent.objects.create(
            alarm=alarm,
            event_type=event_type,
            operator=op,
            description=desc
        )
        return Response(AlarmSerializer(alarm).data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """告警统计（按状态/级别）"""
        from django.db.models import Count
        # 兼容性：如果请求路径包含 ngsi，返回级别分布
        if 'ngsi' in request.path:
            return self.level_distribution(request)
            
        stats = Alarm.objects.values("status", "severity").annotate(count=Count("id"))
        return Response(stats)

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """获取待确认告警列表（兼容性接口）"""
        queryset = self.filter_queryset(self.get_queryset().filter(status='OPEN'))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='batch-confirm')
    def batch_confirm(self, request):
        """批量确认告警（兼容性接口）"""
        alarm_ids = request.data.get('alarm_ids', [])
        operator = request.data.get('operator', 'system')
        message = request.data.get('message', '批量确认')
        
        alarms = Alarm.objects.filter(id__in=alarm_ids, status='OPEN')
        count = alarms.count()
        
        for alarm in alarms:
            alarm.status = 'ACK'
            alarm.ack_time = now()
            alarm.save()
            AlarmEvent.objects.create(
                alarm=alarm, event_type='ACK', 
                operator=operator, description=message
            )
            
        return Response({"message": f"成功确认 {count} 条告警", "count": count})

    @action(detail=False, methods=['get'], url_path='confirmation-stats')
    def confirmation_stats(self, request):
        """告警确认统计数据（兼容性接口）"""
        from django.db.models import Count
        total = Alarm.objects.count()
        pending = Alarm.objects.filter(status='OPEN').count()
        acked = Alarm.objects.filter(status='ACK').count()
        cleared = Alarm.objects.filter(status='CLEARED').count()
        
        return Response({
            "total": total,
            "pending": pending,
            "acknowledged": acked,
            "cleared": cleared
        })

    # --- NGSI-LD 兼容性接口 ---

    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """NGSI-LD 仪表盘统计"""
        total = Alarm.objects.count()
        critical = Alarm.objects.filter(severity='CRITICAL').count()
        error = Alarm.objects.filter(severity='ERROR').count()
        warn = Alarm.objects.filter(severity='WARN').count()
        return Response({
            "total_alarms": total,
            "critical_count": critical,
            "error_count": error,
            "warning_count": warn,
            "resolved_rate": 85.5 # 示例数据
        })

    @action(detail=False, methods=['get'], url_path='level-distribution')
    def level_distribution(self, request):
        """告警级别分布数据"""
        from django.db.models import Count
        data = Alarm.objects.values("severity").annotate(value=Count("id"))
        result = [{"name": item["severity"], "value": item["value"]} for item in data]
        return Response(result)

    @action(detail=False, methods=['get'], url_path='comprehensive-stats')
    def comprehensive_stats(self, request):
        """综合统计：用于验证告警闭环"""
        from django.db.models import Count
        from datetime import timedelta

        queryset = self.get_queryset()

        total = queryset.count()
        open_count = queryset.filter(status='OPEN').count()
        ack_count = queryset.filter(status='ACK').count()
        cleared_count = queryset.filter(status='CLEARED').count()

        last_24h = now() - timedelta(hours=24)
        triggered_24h = queryset.filter(trigger_time__gte=last_24h).count()
        cleared_24h = queryset.filter(clear_time__gte=last_24h).count()

        by_severity = list(
            queryset.values('severity').annotate(count=Count('id')).order_by('severity')
        )

        by_metric = list(
            queryset.values('metric').annotate(count=Count('id')).order_by('metric')
        )

        by_status = list(
            queryset.values('status').annotate(count=Count('id')).order_by('status')
        )

        auto_clear_rate = round((cleared_count / total) * 100, 2) if total > 0 else 0.0

        return Response({
            "summary": {
                "total": total,
                "open": open_count,
                "ack": ack_count,
                "cleared": cleared_count,
                "auto_clear_rate": auto_clear_rate,
            },
            "recent_24h": {
                "triggered": triggered_24h,
                "cleared": cleared_24h,
            },
            "by_status": by_status,
            "by_severity": by_severity,
            "by_metric": by_metric,
        })

    @action(detail=False, methods=['get'], url_path='scenario-check')
    def scenario_check(self, request):
        """用于演示闭环场景是否成立"""
        queryset = self.get_queryset()

        latest_alarm = queryset.order_by('-trigger_time').first()
        latest_cleared = queryset.filter(status='CLEARED').order_by('-clear_time').first()
        active_count = queryset.filter(status__in=['OPEN', 'ACK']).count()

        return Response({
            "active_alarm_count": active_count,
            "latest_alarm": {
                "alarm_id": latest_alarm.alarm_id,
                "device_id": latest_alarm.device.device_id,
                "metric": latest_alarm.metric,
                "status": latest_alarm.status,
                "trigger_time": latest_alarm.trigger_time,
            } if latest_alarm else None,
            "latest_cleared_alarm": {
                "alarm_id": latest_cleared.alarm_id,
                "device_id": latest_cleared.device.device_id,
                "metric": latest_cleared.metric,
                "clear_time": latest_cleared.clear_time,
            } if latest_cleared else None,
        })

    @action(detail=True, methods=['post'], url_path='comment')
    def add_comment(self, request, pk=None):
        """添加告警备注"""
        alarm = self.get_object()
        comment = request.data.get('comment', '')
        AlarmEvent.objects.create(
            alarm=alarm, event_type='ACK', 
            operator=request.user.username if request.user.is_authenticated else 'system',
            description=f"添加备注: {comment}"
        )
        return Response({"message": "备注添加成功"})

class DeviceStatusLogViewSet(viewsets.ModelViewSet):
    queryset = DeviceStatusLog.objects.all().order_by('-collect_time')
    serializer_class = DeviceStatusLogSerializer
    filterset_fields = ['device__device_id', 'online_status', 'alarm_flag'] 
    alarm_engine = AlarmEngineService()
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        # 优化：使用 select_related 减少 N+1 查询问题
        queryset = queryset.select_related('device')
        
        # 数据隔离：用户只能看到自己设备的日志
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if not user.is_superuser:
            queryset = queryset.filter(device__owner=user)
            
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device__device_id=device_id)
        return queryset

    def perform_create(self, serializer):
        data = dict(serializer.validated_data)
        device = data.get('device')

        if 'collect_time' not in data or data.get('collect_time') is None:
            data['collect_time'] = now()

        with transaction.atomic():
            result = self.alarm_engine.process_status(device, data)
            serializer.save(
                alarm_flag=result['alarm_flag'],
                device_status=result['device_status'],
                collect_time=data['collect_time']
            )

# ---------------------------
# NGSI-LD Exchange Layer
# ---------------------------
# 统一的 NGSI-LD 标准化数据交换层
# 提供标准接口 / 查询接口 / 导出接口

# ==================== 统一实体入口 ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def ngsi_entities(request):
    """
    统一实体查询入口
    GET /api/ngsi/entities/
    查询参数:
        - type: 实体类型（Device/DeviceStatus/Alarm/PredictionResult）
        - limit: 返回数量（默认50）
        - offset: 偏移量（默认0）
    """
    entity_type = request.GET.get('type')
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))
    
    results = NGSIExchangeService.list_entities(entity_type, limit, offset)
    return JsonResponse(results, safe=False, content_type="application/ld+json")

@api_view(['GET'])
@permission_classes([AllowAny])
def ngsi_entity_by_urn(request, urn):
    """
    根据 URN 获取单个实体
    GET /api/ngsi/entities/{urn}/
    示例: GET /api/ngsi/entities/urn:ngsi-ld:Device:VHF001/
    """
    entity = NGSIExchangeService.get_entity_by_urn(urn)
    
    if not entity:
        return JsonResponse({"error": "Entity not found"}, status=404)
    
    return JsonResponse(entity, content_type="application/ld+json")

# ==================== 标准查询接口 ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def ngsi_query(request):
    """
    统一 NGSI-LD 查询接口
    POST /api/ngsi/query/
    
    请求体:
    {
        "type": "Device",
        "q": "deviceType=='VHF'",
        "attrs": ["deviceId", "deviceType", "location"],
        "limit": 10,
        "offset": 0
    }
    """
    data = request.data
    entity_type = data.get('type')
    query = data.get('q')
    attrs = data.get('attrs')
    limit = int(data.get('limit', 50))
    offset = int(data.get('offset', 0))
    
    results = NGSIExchangeService.query_entities(entity_type, query, attrs, limit, offset)
    return JsonResponse(results, safe=False, content_type="application/ld+json")

# ==================== 设备专用接口 ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def ngsi_device(request, device_id):
    """获取设备的 NGSI-LD 格式数据"""
    urn = f"urn:ngsi-ld:Device:{device_id}"
    entity = NGSIExchangeService.get_entity_by_urn(urn)
    
    if not entity:
        return JsonResponse({"error": "Device not found"}, status=404)
    
    return JsonResponse(entity, content_type="application/ld+json")

@api_view(['GET'])
@permission_classes([AllowAny])
def ngsi_device_status(request, device_id):
    """获取设备最新状态的 NGSI-LD 格式"""
    result = NGSIExchangeService.get_device_status(device_id)
    
    if not result:
        return JsonResponse({"error": "No status data found"}, status=404)
    
    return JsonResponse(result, content_type="application/ld+json")

@api_view(['GET'])
@permission_classes([AllowAny])
def ngsi_device_alarms(request, device_id):
    """获取设备相关告警的 NGSI-LD 格式"""
    device = Device.objects.filter(device_id=device_id).first()
    if not device:
        return JsonResponse({"error": "Device not found"}, status=404)
    
    alarms = Alarm.objects.filter(device=device).select_related("device").order_by("-trigger_time")[:20]
    payload = [NGSI_LD_Converter.alarm_to_ngsi_ld(a) for a in alarms]
    return JsonResponse(payload, safe=False, content_type="application/ld+json")

@api_view(['GET'])
@permission_classes([AllowAny])
def ngsi_predictions(request, device_id):
    """获取设备预测结果的 NGSI-LD 格式"""
    try:
        device = Device.objects.get(device_id=device_id)
        predictions = PredictionResult.objects.filter(
            device=device
        ).order_by('-prediction_time')[:10]
        
        payload = [NGSI_LD_Converter.prediction_to_ngsi_ld(p) for p in predictions]
        return JsonResponse(payload, safe=False, content_type="application/ld+json")
    except Device.DoesNotExist:
        return JsonResponse({"error": "Device not found"}, status=404)

# ==================== 导出接口 ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def ngsi_export(request):
    """
    导出所有实体数据
    GET /api/ngsi/export/
    查询参数:
        - type: 实体类型（可选，不指定则导出所有）
    """
    entity_type = request.GET.get('type')
    results = NGSIExchangeService.export_all_entities(entity_type)
    return JsonResponse(results, safe=False, content_type="application/ld+json")

# ==================== 兼容旧接口 ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def ngsi_alarms(request):
    """返回符合 NGSI-LD 格式的告警列表（兼容旧接口）"""
    status_filter = request.GET.get('status', 'OPEN')
    device_id = request.GET.get('device_id')
    
    # 使用新的查询服务
    query = f"status=='{status_filter}'" if status_filter else None
    results = NGSIExchangeService.query_entities("Alarm", query, None, 50, 0)
    
    # 如果指定了设备ID，额外过滤
    if device_id and results:
        results = [r for r in results if r.get('refDevice', {}).get('object') == f"urn:ngsi-ld:Device:{device_id}"]
    
    return JsonResponse(results, safe=False, content_type="application/ld+json")


# ---------------------------
# 趋势预测模块
# ---------------------------

class PredictionViewSet(viewsets.ModelViewSet):
    """预测结果视图集"""
    queryset = PredictionResult.objects.all().order_by('-prediction_time')
    serializer_class = PredictionResultSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """数据隔离：用户只能看到自己设备的预测结果"""
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if not user.is_superuser:
            queryset = queryset.filter(device__owner=user)
        
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device__device_id=device_id)
        
        return queryset

    @action(detail=False, methods=['post'], url_path='predict')
    def predict(self, request):
        """执行预测接口"""
        device_id = request.data.get('device_id')
        metric = request.data.get('metric', 'device_temperature')
        horizon = request.data.get('horizon', 60)  # 预测时间跨度（分钟）
        
        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response({"error": "设备不存在"}, status=status.HTTP_404_NOT_FOUND)
        
        # 获取历史数据（限制数量以提高性能）
        history_data = list(DeviceStatusLog.objects.filter(
            device=device
        ).order_by('-collect_time')[:100].values(metric, 'collect_time'))
        
        # 反转以保持时间顺序
        history_data = history_data[::-1]
        
        if not history_data:
            return Response({"error": "该设备没有历史数据"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 提取数值数据
        values = [float(h.get(metric) or 0) for h in history_data if h.get(metric) is not None]
        
        if len(values) < 2:
            return Response({"error": "历史数据不足，无法进行预测"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 使用指数平滑模型进行预测
        model = ExponentialSmoothingModel(alpha=0.3, beta=0.1)
        result = model.predict(values, horizon=horizon)
        
        # 使用趋势计算器分析趋势
        trend_calculator = TrendCalculator()
        trend_result = trend_calculator.calculate_trend(values)
        
        # 构建预测结果（不保存到数据库以提高性能）
        predictions = []
        pred_times = []
        pred_values = result['predictions']
        interval = horizon // len(pred_values) if len(pred_values) > 0 else 1
        
        for i, pred_value in enumerate(pred_values):
            pred_time = now() + timedelta(minutes=(i + 1) * interval)
            pred_times.append(pred_time.isoformat())
            predictions.append({
                'device_id': device.device_id,
                'metric': metric,
                'predicted_value': pred_value,
                'prediction_time': pred_time.isoformat(),
                'prediction_horizon': horizon,
                'confidence_score': min(100, trend_result['r_squared'] * 100),
                'status': 'PREDICTED'
            })
        
        return Response({
            "device_id": device.device_id,
            "device_type": device.device_type,
            "metric": metric,
            "prediction_horizon": horizon,
            "method": result.get('method', 'auto'),
            "trend": {
                "direction": trend_result['trend_direction'],
                "slope": trend_result['slope'],
                "r_squared": trend_result['r_squared'],
                "correlation": trend_result['correlation']
            },
            "predictions": predictions,
            "prediction_times": pred_times,
            "prediction_values": pred_values,
            "historical_data": values[-20:],  # 返回最近20条历史数据用于对比
            "confidence": min(100, trend_result['r_squared'] * 100)
        })

    @action(detail=False, methods=['get'], url_path='device-trend')
    def device_trend(self, request):
        """获取设备趋势分析数据"""
        device_id = request.query_params.get('device_id')
        metric = request.query_params.get('metric', 'device_temperature')
        days = int(request.query_params.get('days', 7))
        
        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response({"error": "设备不存在"}, status=status.HTTP_404_NOT_FOUND)
        
        # 获取历史数据
        start_time = now() - timedelta(days=days)
        history_data = list(DeviceStatusLog.objects.filter(
            device=device,
            collect_time__gte=start_time
        ).order_by('collect_time').values(metric, 'collect_time'))
        
        if not history_data:
            return Response({"data": [], "trend": None})
        
        values = [float(h.get(metric) or 0) for h in history_data if h.get(metric) is not None]
        times = [h['collect_time'].isoformat() for h in history_data]
        
        if len(values) < 2:
            return Response({
                "data": list(zip(times, values)),
                "trend": {"direction": "stable", "slope": 0, "confidence": 0}
            })
        
        # 计算趋势
        trend_calculator = TrendCalculator()
        trend_result = trend_calculator.calculate_trend(values)
        
        # 计算移动平均
        ma_values = trend_calculator.calculate_moving_average(values, window_size=5)
        ma_times = times[4:]  # 移动平均从第5个数据点开始
        
        return Response({
            "device_id": device.device_id,
            "device_type": device.device_type,
            "metric": metric,
            "time_range": {
                "start": start_time.isoformat(),
                "end": now().isoformat()
            },
            "data": [{"time": t, "value": v} for t, v in zip(times, values)],
            "moving_average": [{"time": t, "value": v} for t, v in zip(ma_times, ma_values)] if ma_values else [],
            "trend": {
                "direction": trend_result['trend_direction'],
                "slope": trend_result['slope'],
                "r_squared": trend_result['r_squared'],
                "correlation": trend_result['correlation'],
                "confidence": round(trend_result['r_squared'] * 100, 2)
            },
            "statistics": {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "std": float(np.std(values)) if len(values) > 1 else 0
            }
        })

    @action(detail=False, methods=['get'], url_path='anomaly-detection')
    def anomaly_detection(self, request):
        """异常检测接口 - 与告警规则比较"""
        device_id = request.query_params.get('device_id')
        metric = request.query_params.get('metric', 'device_temperature')
        
        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response({"error": "设备不存在"}, status=status.HTTP_404_NOT_FOUND)
        
        # 获取最近数据
        recent_data = list(DeviceStatusLog.objects.filter(
            device=device
        ).order_by('-collect_time')[:50].values(metric, 'collect_time'))
        
        if not recent_data:
            return Response({"error": "没有数据"}, status=status.HTTP_400_BAD_REQUEST)
        
        recent_data.reverse()  # 按时间升序排列
        values = [float(h.get(metric) or 0) for h in recent_data if h.get(metric) is not None]
        
        if len(values) < 10:
            return Response({"error": "数据不足"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取该设备相关的告警规则
        alarm_rules = AlarmRule.objects.filter(
            Q(device=device) | 
            Q(device_type=device.device_type, device__isnull=True) |
            Q(level='GLOBAL', device_type__isnull=True, device__isnull=True)
        ).filter(metric=metric, is_enabled=True).order_by(
            '-level'  # 设备级 > 设备类型级 > 全局级
        )
        
        # 获取有效的告警阈值
        threshold_info = None
        active_rule = None
        for rule in alarm_rules:
            if rule.threshold is not None:
                threshold_info = {
                    "rule_name": rule.name,
                    "threshold": float(rule.threshold),
                    "operator": rule.operator,
                    "severity": rule.severity,
                    "level": rule.level
                }
                active_rule = rule
                break
        
        # 如果没有告警规则，使用默认阈值
        if not threshold_info:
            threshold_info = {
                "rule_name": "默认规则",
                "threshold": 30.0,  # 默认温度阈值
                "operator": ">",
                "severity": "WARN",
                "level": "GLOBAL"
            }
        
        # 使用IQR检测异常
        from .algorithms import IQRAnomalyDetector
        
        detector = IQRAnomalyDetector(k=1.5)
        detector.fit(values)
        
        anomalies = []
        alarm_triggered_count = 0
        
        for i, value in enumerate(values):
            result = detector.detect(value)
            is_anomaly = result['is_anomaly']
            
            # 检查是否超过告警阈值
            exceeds_threshold = False
            threshold_severity = None
            
            if active_rule and active_rule.threshold is not None:
                threshold = float(active_rule.threshold)
                operator = active_rule.operator
                
                # 根据比较符判断是否超过阈值
                if operator == '>':
                    exceeds_threshold = value > threshold
                elif operator == '>=':
                    exceeds_threshold = value >= threshold
                elif operator == '<':
                    exceeds_threshold = value < threshold
                elif operator == '<=':
                    exceeds_threshold = value <= threshold
                elif operator == '==':
                    exceeds_threshold = value == threshold
                elif operator == '!=':
                    exceeds_threshold = value != threshold
                elif operator == 'abs>':
                    exceeds_threshold = abs(value) > threshold
                
                if exceeds_threshold:
                    threshold_severity = active_rule.severity
                    alarm_triggered_count += 1
            
            # 只有当是IQR异常或者超过告警阈值时才记录
            if is_anomaly or exceeds_threshold:
                anomalies.append({
                    "index": i,
                    "value": value,
                    "time": recent_data[i]['collect_time'].isoformat(),
                    "score": result['anomaly_score'],
                    "reason": result['reason'],
                    "is_anomaly": is_anomaly,
                    "exceeds_threshold": exceeds_threshold,
                    "threshold_severity": threshold_severity,
                    "rule_name": threshold_info.get('rule_name') if threshold_info else None
                })
        
        return Response({
            "device_id": device.device_id,
            "device_type": device.device_type,
            "metric": metric,
            "total_data_points": len(values),
            "anomaly_count": len([a for a in anomalies if a['is_anomaly']]),
            "alarm_triggered_count": alarm_triggered_count,
            "total_issues": len(anomalies),
            "anomaly_rate": round(len([a for a in anomalies if a['is_anomaly']]) / len(values) * 100, 2),
            "alarm_rate": round(alarm_triggered_count / len(values) * 100, 2),
            "threshold_info": threshold_info,
            "bounds": {
                "lower": detector.lower_bound,
                "upper": detector.upper_bound,
                "iqr": detector.iqr
            },
            "anomalies": anomalies
        })

    @action(detail=False, methods=['get'], url_path='predictions-summary')
    def predictions_summary(self, request):
        """预测结果汇总统计"""
        queryset = self.get_queryset()
        
        high_risk_count = queryset.filter(severity__in=['ERROR', 'CRITICAL'], is_above_threshold=True).count()
        total_count = queryset.count()
        avg_confidence = queryset.aggregate(models.Avg('confidence_score'))['confidence_score__avg'] or 0
        
        recent_predictions = queryset[:10]
        
        return Response({
            "total_predictions": total_count,
            "high_risk_count": high_risk_count,
            "avg_confidence": round(avg_confidence, 2),
            "recent_predictions": PredictionResultSerializer(recent_predictions, many=True).data
        })

    @action(detail=False, methods=['get'], url_path='health-summary')
    def health_summary(self, request):
        """设备健康度汇总"""
        queryset = Device.objects.all()
        user = request.user
        if user.is_authenticated and not user.is_superuser:
            queryset = queryset.filter(owner=user)
        summary = get_health_summary(list(queryset))
        # 兼容前端 PredictiveMaintenance.vue 读取的字段名（excellent/attention/warning/critical）
        level_counts = summary.get('level_counts', {})
        summary['excellent'] = level_counts.get('健康', 0)
        summary['attention'] = level_counts.get('关注', 0)
        summary['warning'] = level_counts.get('预警', 0)
        summary['critical'] = level_counts.get('高危', 0)
        return Response(summary)

    @action(detail=False, methods=['get'], url_path='health-detail')
    def health_detail(self, request):
        """单设备健康度详情"""
        device_id = request.query_params.get('device_id')
        if not device_id:
            return Response({"error": "device_id 必填"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response({"error": "设备不存在"}, status=status.HTTP_404_NOT_FOUND)
        return Response(calculate_device_health(device))

    @action(detail=False, methods=['post'], url_path='recalculate')
    def recalculate(self, request):
        """重新计算预测结果"""
        device_id = request.data.get('device_id')
        if device_id:
            try:
                device = Device.objects.get(device_id=device_id)
            except Device.DoesNotExist:
                return Response({"error": "设备不存在"}, status=status.HTTP_404_NOT_FOUND)
            created = recalculate_predictions(device)
            return Response({
                "recalculated_count": len(created),
                "device_id": device_id,
            })

        devices = Device.objects.all()
        total = 0
        for device in devices:
            total += len(recalculate_predictions(device))
        return Response({"recalculated_count": total})


class EnvironmentDataViewSet(viewsets.ModelViewSet):
    """环境数据视图集"""
    queryset = EnvironmentData.objects.all().order_by('-collect_time')
    serializer_class = EnvironmentDataSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if not user.is_superuser:
            queryset = queryset.filter(device__owner=user)
        
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device__device_id=device_id)
        
        return queryset

    @action(detail=False, methods=['post'], url_path='batch-create')
    def batch_create(self, request):
        """批量创建环境数据"""
        data_list = request.data.get('data', [])
        if not isinstance(data_list, list) or not data_list:
            return Response(
                {"message": "data 必须是非空数组"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_count = 0
        errors = []

        for index, data in enumerate(data_list):
            device_id = str(data.get('device_id', '')).strip()
            if not device_id:
                errors.append({"index": index, "device_id": "", "message": "device_id 不能为空"})
                continue
            try:
                device = Device.objects.get(device_id=device_id)
            except Device.DoesNotExist:
                errors.append({"index": index, "device_id": device_id, "message": "device_id not found"})
                continue

            env_data = EnvironmentData(
                device=device,
                ambient_temperature=data.get('ambient_temperature'),
                humidity=data.get('humidity'),
                atmospheric_pressure=data.get('atmospheric_pressure'),
                wind_speed=data.get('wind_speed'),
                wind_direction=data.get('wind_direction'),
                rain_intensity=data.get('rain_intensity'),
                visibility=data.get('visibility'),
                collect_time=data.get('collect_time') or now(),
            )
            env_data.save()
            created_count += 1

        return Response({
            "created_count": created_count,
            "failed_count": len(errors),
            "errors": errors,
        })


def _graph_payload_to_response(payload) -> dict:
    return {
        "nodes": payload.nodes,
        "edges": payload.edges,
        "root_candidates": payload.root_candidates,
        "path_explanations": payload.path_explanations,
        "provider": payload.provider,
        "degraded": payload.provider == 'relational',
    }


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def root_cause_graph(request):
    """根因图谱查询"""
    alarm_id = request.query_params.get('alarm_id')
    if not alarm_id:
        return Response({"error": "alarm_id 必填"}, status=status.HTTP_400_BAD_REQUEST)

    service = RootCauseGraphService()
    try:
        payload = service.build_alarm_graph(int(alarm_id))
        return Response(_graph_payload_to_response(payload))
    finally:
        service.close()


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def root_cause_path(request):
    """设备根因路径查询"""
    device_id = request.query_params.get('device_id')
    if not device_id:
        return Response({"error": "device_id 必填"}, status=status.HTTP_400_BAD_REQUEST)

    service = RootCauseGraphService()
    try:
        payload = service.build_device_path(device_id)
        return Response(_graph_payload_to_response(payload))
    finally:
        service.close()


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def root_cause_sync(request):
    """同步图谱数据到 Neo4j"""
    service = RootCauseGraphService()
    try:
        result = service.sync_recent_data()
        return Response(result)
    finally:
        service.close()


# ==================== 仪表盘接口 ====================
from rest_framework.decorators import api_view

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def dashboard_overview(request):
    """仪表盘概览数据接口"""
    from django.db.models import Count
    
    # 设备统计
    total_devices = Device.objects.count()
    
    # 获取在线设备数量（基于最新状态）
    from django.db.models import Subquery, OuterRef
    latest_logs = DeviceStatusLog.objects.filter(
        device=OuterRef('pk')
    ).order_by('-collect_time')
    online_devices = Device.objects.filter(
        status_logs__online_status=True,
        status_logs__collect_time=Subquery(latest_logs.values('collect_time')[:1])
    ).count()
    operation_rate = round((online_devices / total_devices * 100), 1) if total_devices > 0 else 0
    
    # 今日告警统计
    today = now().date()
    today_alarm_count = Alarm.objects.filter(trigger_time__date=today).count()
    
    # 告警级别分布
    severity_distribution = Alarm.objects.values("severity").annotate(count=Count("id"))
    severity_dist_list = [{"severity": item["severity"], "count": item["count"]} for item in severity_distribution]
    
    # 设备类型分布
    device_type_distribution = Device.objects.values("device_type").annotate(count=Count("id"))
    device_type_dist_list = [{"device_type": item["device_type"], "count": item["count"]} for item in device_type_distribution]
    
    # 最近告警
    recent_alarms = Alarm.objects.select_related('device').order_by('-trigger_time')[:10]
    recent_alarms_list = []
    for alarm in recent_alarms:
        recent_alarms_list.append({
            "id": alarm.id,
            "device_id": alarm.device.device_id if alarm.device else "未知设备",
            "device_name": alarm.device.device_model if alarm.device else "未知设备",
            "title": f"{alarm.metric}异常",
            "level": alarm.severity,
            "status": alarm.status,
            "raised_at": alarm.trigger_time.isoformat()
        })
    
    return Response({
        "stats": {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "operation_rate": operation_rate,
            "today_alarm_count": today_alarm_count
        },
        "severity_distribution": severity_dist_list,
        "device_type_distribution": device_type_dist_list,
        "recent_alarms": recent_alarms_list
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def trend_analysis(request):
    """趋势分析接口"""
    metric = request.query_params.get('metric', 'device_temperature')
    
    # 获取最近24小时的数据
    time_range = now() - timedelta(hours=24)
    logs = DeviceStatusLog.objects.filter(
        collect_time__gte=time_range
    ).order_by('collect_time')
    
    labels = []
    values = []
    
    for log in logs:
        value = getattr(log, metric, None)
        if value is not None:
            labels.append(log.collect_time.strftime('%Y-%m-%d %H:%M:%S'))
            values.append(float(value))
    
    return Response({
        "labels": labels,
        "values": values,
        "metric": metric
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def multi_device_prediction(request):
    """
    多设备联合预测 API
    POST /api/multi-device-prediction/
    
    请求体:
    {
        "devices": {
            "VHF": {
                "device_id": "VHF-001",
                "temperature": 45.0,
                "signal_strength": -75.0,
                "power_voltage": 220.0
            },
            "ILS": {
                "device_id": "ILS-001",
                "temperature": 42.0,
                "signal_power": 10.5,
                "power_voltage": 220.0,
                "interference": 0.1
            }
        }
    }
    
    响应:
    {
        "VHF": {"device_id": "...", "temp": 45.5, "signal": -76.0, "health": 0.85, "alarm_status": "NORMAL"},
        "ILS": {"device_id": "...", "temp": 42.3, "signal": 10.2, "health": 0.88, "alarm_status": "NORMAL"},
        "system_health": 0.865
    }
    """
    devices = request.data.get('devices', {})
    
    if not devices:
        return Response({"error": "devices 参数不能为空"}, status=status.HTTP_400_BAD_REQUEST)
    
    results = multi_device_predict(devices)
    return Response(results)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def fault_propagation_prediction(request):
    """
    故障传播预测 API
    POST /api/fault-propagation/
    
    请求体:
    {
        "devices": [
            {"id": "VHF-001", "status": "FAULT", "neighbors": ["VHF-002", "ILS-001"]},
            {"id": "VHF-002", "status": "NORMAL", "neighbors": ["VHF-001"]},
            {"id": "ILS-001", "status": "NORMAL", "neighbors": ["VHF-001", "DME-001"]},
            {"id": "DME-001", "status": "NORMAL", "neighbors": ["ILS-001"]}
        ]
    }
    
    响应:
    {
        "new_faults": {"VHF-002": "DEGRADED", "ILS-001": "DEGRADED"},
        "total_devices": 4,
        "faulty_devices": 1,
        "propagated_count": 2
    }
    """
    devices = request.data.get('devices', [])
    
    if not devices:
        return Response({"error": "devices 参数不能为空"}, status=status.HTTP_400_BAD_REQUEST)
    
    new_faults = fault_propagation(devices)
    
    faulty_count = sum(1 for d in devices if d.get('status') in ['FAULT', 'ALARM', 'CRITICAL'])
    
    return Response({
        "new_faults": new_faults,
        "total_devices": len(devices),
        "faulty_devices": faulty_count,
        "propagated_count": len(new_faults)
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def coupling_matrix(request):
    """
    获取设备耦合矩阵
    GET /api/coupling-matrix/
    """
    matrix = {
        ('VHF', 'VHF'): 1.0,
        ('VHF', 'ILS'): 0.6,
        ('VHF', 'VOR'): 0.7,
        ('VHF', 'DME'): 0.5,
        ('ILS', 'ILS'): 1.0,
        ('ILS', 'VOR'): 0.8,
        ('ILS', 'DME'): 0.9,
        ('VOR', 'VOR'): 1.0,
        ('VOR', 'DME'): 0.6,
        ('DME', 'DME'): 1.0,
    }
    
    formatted_matrix = {}
    for (dev1, dev2), strength in matrix.items():
        key = f"{dev1}-{dev2}"
        formatted_matrix[key] = strength
    
    return Response({
        "coupling_matrix": formatted_matrix,
        "description": "设备类型间的耦合强度（0-1，值越大耦合越强）",
        "legend": {
            "VHF": "甚高频通信设备",
            "ILS": "仪表着陆系统",
            "VOR": "甚高频全向信标",
            "DME": "测距仪"
        }
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def device_coupling(request, device_id):
    """
    获取指定设备与其他设备的耦合强度
    GET /api/device-coupling/{device_id}/
    """
    try:
        device = Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        return Response({"error": "设备不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    all_devices = Device.objects.all()
    coupling_info = []
    
    for other in all_devices:
        if other.device_id != device_id:
            strength = get_coupling_strength(device_id, other.device_id)
            coupling_info.append({
                "device_id": other.device_id,
                "device_type": other.device_type,
                "coupling_strength": strength,
                "location": other.location
            })
    
    return Response({
        "device_id": device_id,
        "device_type": device.device_type,
        "coupling_devices": coupling_info
    })


# ==================== 知识图谱接口 ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def knowledge_graph_coupling(request):
    """
    获取设备耦合知识图谱
    GET /api/knowledge-graph/coupling/
    """
    service = RootCauseGraphService()
    try:
        payload = service.build_coupling_graph()
        return Response(_graph_payload_to_response(payload))
    finally:
        service.close()


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def knowledge_graph_devices(request):
    """
    获取基于设备数据构建的知识图谱
    GET /api/knowledge-graph/devices/
    """
    service = RootCauseGraphService()
    try:
        result = service.build_device_knowledge_graph()
        return Response(result)
    finally:
        service.close()


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def knowledge_graph_path(request):
    """
    查找设备间干扰路径
    GET /api/knowledge-graph/path/?source={source_id}&target={target_id}
    """
    source_id = request.query_params.get('source')
    target_id = request.query_params.get('target')
    
    if not source_id or not target_id:
        return Response({"error": "source 和 target 参数必填"}, status=status.HTTP_400_BAD_REQUEST)
    
    service = RootCauseGraphService()
    try:
        result = service.find_interference_path(source_id, target_id)
        return Response(result)
    finally:
        service.close()


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def knowledge_graph_dependencies(request, device_id):
    """
    获取设备依赖关系
    GET /api/knowledge-graph/dependencies/{device_id}/
    """
    service = RootCauseGraphService()
    try:
        result = service.get_device_dependencies(device_id)
        return Response(result)
    finally:
        service.close()


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def knowledge_graph_sync(request):
    """
    同步耦合图谱到Neo4j
    POST /api/knowledge-graph/sync/
    """
    service = RootCauseGraphService()
    try:
        result = service.sync_coupling_graph()
        return Response(result)
    finally:
        service.close()


# ==================== 系统级耦合模拟接口 ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def coupling_matrix_data(request):
    """
    获取设备耦合矩阵数据
    GET /api/simulation/coupling-matrix/
    """
    from core.simulation import DeviceCouplingMatrix
    matrix = DeviceCouplingMatrix()
    return Response({
        'matrix': matrix.get_matrix_data(),
        'total_couplings': len(matrix.coupling_matrix)
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def coupling_effect(request, source_id, target_id):
    """
    获取设备间耦合影响
    GET /api/simulation/coupling-effect/{source_id}/{target_id}/
    """
    from core.simulation import DeviceCouplingMatrix
    matrix = DeviceCouplingMatrix()
    effect = matrix.get_coupling_effect(source_id, target_id)
    return Response(effect.__dict__)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def coupled_devices(request, device_id):
    """
    获取耦合设备列表
    GET /api/simulation/coupled-devices/{device_id}/
    """
    from core.simulation import DeviceCouplingMatrix
    matrix = DeviceCouplingMatrix()
    coupled = matrix.get_coupled_devices(device_id)
    return Response({'device_id': device_id, 'coupled_devices': coupled})


# ==================== 事件驱动模拟接口 ====================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def event_simulation(request):
    """
    运行事件驱动模拟
    POST /api/simulation/event-drive/
    """
    from core.simulation import EventDrivenGenerator
    from datetime import datetime
    
    devices = request.data.get('devices', ['VHF-001', 'VHF-002', 'ILS-001', 'ILS-002'])
    duration_hours = request.data.get('duration_hours', 24)
    
    generator = EventDrivenGenerator()
    generator.initialize_device_states(devices)
    generator.run_simulation(datetime.now(), duration_hours)
    
    return Response({
        'simulation_result': 'completed',
        'device_states': generator.get_device_states()
    })


# ==================== 空间GIS建模接口 ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def spatial_regions(request):
    """
    获取机场区域信息
    GET /api/simulation/spatial/regions/
    """
    from core.simulation import SpatialQueryEngine
    engine = SpatialQueryEngine()
    return Response(engine.get_all_regions())


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def spatial_devices_within_radius(request, device_id):
    """
    获取指定设备半径范围内的设备
    GET /api/simulation/spatial/devices-within-radius/{device_id}/?radius=1.0
    """
    from core.simulation import SpatialQueryEngine
    engine = SpatialQueryEngine()
    radius = float(request.query_params.get('radius', 1.0))
    devices = engine.get_devices_within_radius(device_id, radius)
    return Response({'center_device': device_id, 'radius_km': radius, 'devices': devices})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def spatial_regional_env(request, region_id):
    """
    获取区域环境状态
    GET /api/simulation/spatial/regional-env/{region_id}/
    """
    from core.simulation import SpatialQueryEngine
    engine = SpatialQueryEngine()
    env_state = engine.get_regional_env_state(region_id)
    return Response({'region_id': region_id, 'env_state': env_state})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def spatial_visualization(request):
    """
    获取空间可视化数据（热力图、故障扩散图）
    GET /api/simulation/spatial/visualization/
    """
    from core.simulation import SpatialQueryEngine, EventDrivenGenerator
    from datetime import datetime
    
    engine = SpatialQueryEngine()
    
    generator = EventDrivenGenerator()
    generator.initialize_device_states(list(engine.DEVICE_LOCATIONS.keys()))
    generator.run_simulation(datetime.now(), 1)
    
    spatial_output = engine.get_spatial_output(generator.get_device_states())
    return Response(spatial_output)


# ==================== 趋势预测接口 ====================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def trend_prediction(request):
    """
    趋势预测
    POST /api/simulation/trend-prediction/
    """
    from core.simulation import TrendBasedPredictor
    
    historical_data = request.data.get('historical_data', [])
    device_id = request.data.get('device_id', '')
    metric = request.data.get('metric', 'temperature')
    horizon_hours = request.data.get('horizon_hours', 24)
    
    predictor = TrendBasedPredictor(historical_data)
    output = predictor.get_prediction_output(device_id, metric)
    
    return Response(output)


# ==================== 数据分层架构接口 ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def data_layers_summary(request):
    """
    获取数据分层架构摘要
    GET /api/simulation/data-layers/summary/
    """
    from core.simulation import DataLayerManager
    
    manager = DataLayerManager()
    summary = manager.get_data_flow_summary()
    return Response(summary)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def data_layers_ingest(request):
    """
    数据入口：将数据写入三层架构
    POST /api/simulation/data-layers/ingest/
    """
    from core.simulation import DataLayerManager
    
    device_id = request.data.get('device_id')
    data = request.data.get('data', {})
    
    if not device_id:
        return Response({"error": "device_id 必填"}, status=status.HTTP_400_BAD_REQUEST)
    
    manager = DataLayerManager()
    manager.ingest_data(device_id, data)
    
    return Response({'status': 'success', 'device_id': device_id})


# ==================== 数据质量接口 ====================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def data_quality_check(request):
    """
    数据质量检测
    POST /api/simulation/data-quality/check/
    """
    from core.simulation import DataQualityEngine
    
    data_stream = request.data.get('data_stream', [])
    
    engine = DataQualityEngine()
    report = engine.validate_data_quality(data_stream)
    
    return Response(report)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def data_quality_report(request, report_id=None):
    """
    获取质量报告
    GET /api/simulation/data-quality/report/
    GET /api/simulation/data-quality/report/{report_id}/
    """
    from core.simulation import DataQualityEngine
    
    engine = DataQualityEngine()
    
    if report_id:
        report = engine.get_quality_report(report_id)
    else:
        report = engine.get_quality_report()
    
    if not report:
        return Response({"error": "报告不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(report)


# ==================== 级联告警接口 ====================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def cascade_alarm_trigger(request):
    """
    触发级联告警
    POST /api/simulation/cascade-alarm/trigger/
    """
    from core.simulation import CascadeAlarmEngine
    
    device_id = request.data.get('device_id')
    alarm_type = request.data.get('alarm_type', 'overheat')
    trigger_value = request.data.get('trigger_value', 68.5)
    
    if not device_id:
        return Response({"error": "device_id 必填"}, status=status.HTTP_400_BAD_REQUEST)
    
    engine = CascadeAlarmEngine()
    alarm = engine.trigger_device_alarm(device_id, alarm_type, trigger_value)
    
    return Response(alarm)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cascade_alarm_chain(request, alarm_id):
    """
    获取告警传播链
    GET /api/simulation/cascade-alarm/chain/{alarm_id}/
    """
    from core.simulation import CascadeAlarmEngine
    
    engine = CascadeAlarmEngine()
    chain = engine.get_alarm_propagation_chain(alarm_id)
    
    return Response({'alarm_id': alarm_id, 'propagation_chain': chain})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cascade_alarm_correlation(request):
    """
    获取告警关联矩阵
    GET /api/simulation/cascade-alarm/correlation/
    """
    from core.simulation import CascadeAlarmEngine
    
    engine = CascadeAlarmEngine()
    matrix = engine.get_alarm_correlation_matrix()
    
    return Response(matrix)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cascade_alarm_active(request):
    """
    获取活动告警列表
    GET /api/simulation/cascade-alarm/active/
    """
    from core.simulation import CascadeAlarmEngine
    
    engine = CascadeAlarmEngine()
    alarms = engine.get_active_alarms()
    
    return Response({'active_alarms': alarms})


# ==================== 数据生成API接口 ====================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def data_generation_devices(request):
    """
    设备数据生成接口
    POST /api/data-generation/devices/
    """
    from core.simulation import DataGenerationManager
    
    config = request.data.get('generation_config', {})
    
    manager = DataGenerationManager()
    result = manager.generate_device_data(config)
    
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def data_generation_coupled_data(request):
    """
    系统耦合数据查询接口
    GET /api/data-generation/coupled-data/?device_id=VHF-001
    """
    from core.simulation import DataGenerationManager
    
    device_id = request.query_params.get('device_id')
    if not device_id:
        return Response({"error": "device_id 参数必填"}, status=status.HTTP_400_BAD_REQUEST)
    
    manager = DataGenerationManager()
    result = manager.get_coupled_data(device_id)
    
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def data_generation_events_trigger(request):
    """
    事件驱动数据流接口
    POST /api/data-generation/events/trigger/
    """
    from core.simulation import DataGenerationManager
    
    event_type = request.data.get('event_type')
    device_id = request.data.get('device_id')
    
    if not event_type or not device_id:
        return Response({"error": "event_type 和 device_id 参数必填"}, status=status.HTTP_400_BAD_REQUEST)
    
    manager = DataGenerationManager()
    result = manager.trigger_event(event_type, device_id, **request.data)
    
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def data_generation_spatial_regions(request):
    """
    空间数据查询接口
    GET /api/data-generation/spatial/regions/
    """
    from core.simulation import DataGenerationManager
    
    manager = DataGenerationManager()
    result = manager.get_spatial_regions()
    
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def data_generation_quality_report(request):
    """
    数据质量报告接口
    GET /api/data-generation/quality-report/?generation_id=GEN-xxx
    """
    from core.simulation import DataGenerationManager
    
    generation_id = request.query_params.get('generation_id')
    
    manager = DataGenerationManager()
    result = manager.get_quality_report(generation_id)
    
    return Response(result)


# ==================== 预测数据查询接口 ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def predictions_trend_analysis(request):
    """
    预测数据查询接口（升级版）
    GET /api/predictions/trend-analysis/?device_id=VHF-001
    """
    from core.simulation import DataGenerationManager
    
    device_id = request.query_params.get('device_id')
    if not device_id:
        return Response({"error": "device_id 参数必填"}, status=status.HTTP_400_BAD_REQUEST)
    
    manager = DataGenerationManager()
    result = manager.get_trend_analysis(device_id)
    
    return Response(result)


# ==================== 级联告警API接口 ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def alarm_cascade_propagation_chain(request):
    """
    级联告警查询接口
    GET /api/alarm-cascade/propagation-chain/?alarm_id=ALM-VHF003-001
    """
    from core.simulation import DataGenerationManager
    
    alarm_id = request.query_params.get('alarm_id')
    if not alarm_id:
        return Response({"error": "alarm_id 参数必填"}, status=status.HTTP_400_BAD_REQUEST)
    
    manager = DataGenerationManager()
    result = manager.get_alarm_propagation_chain(alarm_id)
    
    return Response(result)

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count

# 文档分类
class DocCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = DocCategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = DocCategory.objects.all()
        # 只有列表接口才做文档数量统计
        if self.action == 'list':
            qs = qs.annotate(
                _doc_count=Count("document_set")
            )
        return qs

    def perform_create(self, serializer):
        first_user = User.objects.first()
        if first_user:
            serializer.save(user=first_user)
        else:
            serializer.save()


# 文档
class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Document.objects.select_related("category").all()
        cid = self.request.query_params.get("category_id")
        if cid:
            qs = qs.filter(category_id=cid)
        return qs

    @action(methods=["post"], detail=False)
    def upload(self, request):
        file = request.FILES.get("file")
        cid = request.data.get("category_id")
        if not file:
            return Response({"code":400,"msg":"没有上传文件","data":None}, status=status.HTTP_400_BAD_REQUEST)
        first_user = User.objects.first()
        ins = Document.objects.create(
            name=file.name,
            file=file,
            category_id=cid,
            user=first_user
        )
        return Response({"code":200,"msg":"上传成功","data":DocumentSerializer(ins).data})