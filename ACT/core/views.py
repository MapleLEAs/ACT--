from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.db.models import Avg, Max, Min
from django.utils import timezone
from datetime import timedelta
from core.services.threejs_service import ThreeJSSceneService
from core.models import Personnel, WorkOrder, WorkOrderProcessLog, MaintenancePlan, MaintenanceRecord, DeviceAlarmLink
from core.serializers import (
    PersonnelSerializer, PermissionUpdateSerializer, RoleAssignSerializer,
    WorkOrderSerializer, WorkOrderProcessSerializer,
    MaintenancePlanSerializer, MaintenanceExecuteSerializer, MaintenanceCompleteSerializer,
    DeviceSerializer, DeviceAlarmLinkSerializer
)
from monitor.models import Device, DeviceStatusLog, Alarm
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings

class ThreeJSView(APIView):
    """3D场景数据API"""
    
    def get(self, request):
        """获取3D场景数据"""
        force = request.query_params.get('force', 'false').lower() == 'true'
        service = ThreeJSSceneService()
        data = service.get_scene_data(force_refresh=force)
        return Response(data)

class DeviceHistoryView(APIView):
    """设备历史数据API"""
    
    def get(self, request, device_id):
        hours = int(request.query_params.get('hours', 24))
        service = ThreeJSSceneService()
        data = service.get_device_history(device_id, hours)
        
        return Response({
            'device_id': device_id,
            'data': data,
            'data_points': len(data)
        })

def api_root_index(request):
    """项目后端框架 - 根路径导航视图"""
    data = {
        "project_name": "项目后端框架 (ATC Monitor Base)",
        "status": "Running",
        "endpoints": {
            "admin_interface": request.build_absolute_uri('/admin/'),
            "api_root": request.build_absolute_uri('/api/'),
            "device_list": request.build_absolute_uri('/api/devices/'),
            "status_logs": request.build_absolute_uri('/api/status_logs/'),
            "dashboard_overview": request.build_absolute_uri('/api/dashboard/overview/'),
        }
    }
    return JsonResponse(data, json_dumps_params={'ensure_ascii': False, 'indent': 4})

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_overview(request):
    """
    仪表盘概览 API
    优化版：增强健壮性，防止 500 错误
    """
    from django.db.models import Count
    from monitor.models import Alarm, DeviceStatusLog, Device
    from monitor.serializers import AlarmSerializer
    
    try:
        # 1. 基础统计
        total_devices = Device.objects.count()
        
        # 统计在线设备 (直接查询，避免复杂的 Subquery 导致可能的数据库兼容性问题)
        # 获取每个设备最新的状态记录 ID
        from django.db.models import Max
        latest_log_ids = DeviceStatusLog.objects.values('device_id').annotate(max_id=Max('id')).values_list('max_id', flat=True)
        online_devices = DeviceStatusLog.objects.filter(id__in=latest_log_ids, online_status=True).count()
        
        today = timezone.now().date()
        today_alarm_count = Alarm.objects.filter(trigger_time__date=today).count()
        
        operation_rate = round(online_devices / total_devices * 100, 2) if total_devices > 0 else 0
        
        # 2. 告警分布
        severity_distribution = list(Alarm.objects.filter(
            status__in=['OPEN', 'ACK']
        ).values('severity').annotate(count=Count('id')))
        
        # 3. 最近告警 (Top 5)
        recent_alarms = Alarm.objects.select_related('device', 'rule').order_by('-trigger_time')[:5]
        recent_alarms_data = AlarmSerializer(recent_alarms, many=True).data
        
        # 4. 设备类型分布
        device_type_distribution = list(Device.objects.values('device_type').annotate(count=Count('id')))

        return Response({
            "stats": {
                "total_devices": total_devices,
                "online_devices": online_devices,
                "operation_rate": operation_rate,
                "today_alarm_count": today_alarm_count,
            },
            "severity_distribution": severity_distribution,
            "device_type_distribution": device_type_distribution,
            "recent_alarms": recent_alarms_data
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Dashboard Overview Error: {str(e)}")
        return Response({
            "error": "获取概览数据失败",
            "detail": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 趋势分析
@api_view(['GET'])
@permission_classes([AllowAny])
def trend_analysis(request):
    end = timezone.now()
    start = end - timedelta(days=7)
    metric = request.query_params.get('metric', 'device_temperature')
    
    logs = DeviceStatusLog.objects.filter(
        collect_time__gte=start,
        collect_time__lte=end
    ).order_by('collect_time')
    
    labels, values = [], []
    current = start
    while current <= end:
        labels.append(current.strftime('%Y-%m-%d %H:%M'))
        val = logs.filter(collect_time__gte=current, collect_time__lt=current+timedelta(hours=1)).aggregate(a=Avg(metric))['a']
        values.append(round(val, 2) if val else None)
        current += timedelta(hours=1)
    return Response({"labels": labels, "values": values})

# 环境数据
@api_view(['GET'])
@permission_classes([AllowAny])
def environment_data(request):
    end = timezone.now()
    start = end - timedelta(days=1)
    logs = DeviceStatusLog.objects.filter(collect_time__gte=start, collect_time__lte=end)
    stats = logs.aggregate(avg=Avg('device_temperature'), max=Max('device_temperature'), min=Min('device_temperature'))
    data = list(logs.values('collect_time', 'device_temperature').order_by('collect_time'))
    return Response({
        "statistics": {
            "avg": round(stats['avg'], 2) if stats['avg'] else None,
            "max": round(stats['max'], 2) if stats['max'] else None,
            "min": round(stats['min'], 2) if stats['min'] else None
        },
        "data": data
    })

# 设备管理
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def device_detail(request, id):
    try:
        device = Device.objects.get(id=id)
    except Device.DoesNotExist:
        return Response({"detail": "设备不存在"}, status=404)
    if request.method == 'GET':
        return Response(DeviceSerializer(device).data)
    serializer = DeviceSerializer(device, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_alarm_rule(request, device_id):
    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        return Response({"detail": "设备不存在"}, status=404)
    serializer = DeviceAlarmLinkSerializer(data=request.data)
    if serializer.is_valid():
        rule_ids = serializer.validated_data['alarm_rule_ids']
        DeviceAlarmLink.objects.filter(device=device).delete()
        links = [DeviceAlarmLink(device=device, alarm_rule_id=rid) for rid in rule_ids]
        DeviceAlarmLink.objects.bulk_create(links)
        return Response({"message": "关联成功"})
    return Response(serializer.errors, status=400)

# 人员管理
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def personnel_list(request):
    if request.method == 'GET':
        return Response(PersonnelSerializer(Personnel.objects.all(), many=True).data)
    serializer = PersonnelSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['user']['username']
        user, _ = User.objects.get_or_create(username=username)
        personnel = serializer.save(user=user)
        return Response(PersonnelSerializer(personnel).data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_permissions(request, user_id):
    serializer = PermissionUpdateSerializer(data=request.data)
    if serializer.is_valid():
        return Response({"message": "权限更新成功"})
    return Response(serializer.errors, status=400)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def assign_roles(request, user_id):
    serializer = RoleAssignSerializer(data=request.data)
    if serializer.is_valid():
        return Response({"message": "角色分配成功"})
    return Response(serializer.errors, status=400)

# 工单管理
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_workorder(request):
    serializer = WorkOrderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claim_workorder(request, order_id):
    try:
        order = WorkOrder.objects.get(id=order_id)
    except WorkOrder.DoesNotExist:
        return Response({"detail": "工单不存在"}, status=404)
    order.status = 'claimed'
    order.assignee = getattr(request.user, 'personnel', None)
    order.claim_time = timezone.now()
    order.save()
    return Response(WorkOrderSerializer(order).data)

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def workorder_list(request):
    if request.method == 'GET':
        orders = WorkOrder.objects.all()
        status_param = request.query_params.get('status')
        if status_param: orders = orders.filter(status=status_param)
        return Response(WorkOrderSerializer(orders, many=True).data)
    return Response({"detail": "Method not allowed"}, status=405)

# 维护计划
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def maintenance_plan_list(request):
    if request.method == 'GET':
        return Response(MaintenancePlanSerializer(MaintenancePlan.objects.all(), many=True).data)
    serializer = MaintenancePlanSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

# ==================== HttpOnly Cookie 认证 ====================

class CookieTokenObtainPairSerializer(TokenObtainPairSerializer):
    """自定义 Token 序列化器，支持 HttpOnly Cookie"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # 添加自定义的 claims
        token['username'] = user.username
        token['email'] = user.email
        
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # 返回 token 数据（前端会自动处理）
        return data

class CookieTokenObtainPairView(TokenObtainPairView):
    """自定义登录视图，返回 HttpOnly Cookie"""
    
    serializer_class = CookieTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # 获取 JWT 配置
            jwt_settings = settings.SIMPLE_JWT
            
            # 设置 Access Token Cookie
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            
            if access_token:
                # Access Token Cookie
                response.set_cookie(
                    'access_token',
                    access_token,
                    max_age=jwt_settings.get('ACCESS_TOKEN_LIFETIME').total_seconds(),
                    httponly=jwt_settings.get('AUTH_COOKIE_HTTP_ONLY', True),
                    secure=jwt_settings.get('AUTH_COOKIE_SECURE', False),
                    samesite=jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Lax'),
                    domain=jwt_settings.get('AUTH_COOKIE_DOMAIN'),
                    path=jwt_settings.get('AUTH_COOKIE_PATH', '/'),
                )
            
            if refresh_token:
                # Refresh Token Cookie
                response.set_cookie(
                    'refresh_token',
                    refresh_token,
                    max_age=jwt_settings.get('REFRESH_TOKEN_LIFETIME').total_seconds(),
                    httponly=True,
                    secure=jwt_settings.get('AUTH_COOKIE_SECURE', False),
                    samesite=jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Lax'),
                    domain=jwt_settings.get('AUTH_COOKIE_DOMAIN'),
                    path='/',
                )
            
            # 移除响应体中的 token（可选，因为 Cookie 已经设置）
            # 如果前端不需要在响应体中获取 token，可以注释掉下面这行
            # del response.data['access']
            # del response.data['refresh']
        
        return response
