from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from core.ngsi_exchange import NGSIExchangeService


@api_view(["GET"])
@permission_classes([AllowAny])
def ngsi_root(request):
    """
    NGSI-LD 标准数据交换层 - 根路径
    GET /api/ngsi/
    
    返回可用的NGSI-LD接口列表
    """
    return JsonResponse({
        "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
        "description": "ATC Monitor NGSI-LD Exchange Layer",
        "version": "1.0.0",
        "available_endpoints": {
            "entities": {
                "method": "GET",
                "url": "/api/ngsi/entities/",
                "description": "获取实体列表，支持按类型筛选",
                "params": {
                    "type": "Device/DeviceStatus/Alarm/PredictionResult",
                    "limit": "返回数量（默认50）",
                    "offset": "偏移量（默认0）"
                }
            },
            "entity": {
                "method": "GET",
                "url": "/api/ngsi/entity/?id={urn}",
                "description": "根据URN获取单个实体"
            },
            "query": {
                "method": "POST",
                "url": "/api/ngsi/query/",
                "description": "标准查询接口，支持条件过滤"
            },
            "export": {
                "method": "GET",
                "url": "/api/ngsi/export/",
                "description": "导出实体数据交换包"
            },
            "device": {
                "method": "GET",
                "url": "/api/ngsi/devices/{device_id}/",
                "description": "获取指定设备的NGSI-LD实体"
            },
            "device_status": {
                "method": "GET",
                "url": "/api/ngsi/devices/{device_id}/status/",
                "description": "获取指定设备的最新状态"
            },
            "device_alarms": {
                "method": "GET",
                "url": "/api/ngsi/devices/{device_id}/alarms/",
                "description": "获取指定设备的告警列表"
            },
            "alarms": {
                "method": "GET",
                "url": "/api/ngsi/alarms/",
                "description": "获取所有告警的NGSI-LD实体"
            },
            "predictions": {
                "method": "GET",
                "url": "/api/ngsi/predictions/{device_id}/",
                "description": "获取指定设备的预测结果"
            }
        },
        "supported_entity_types": ["Device", "DeviceStatus", "Alarm", "PredictionResult"],
        "content_type": "application/ld+json"
    }, content_type="application/ld+json", encoder=DjangoJSONEncoder)


@api_view(["GET"])
@permission_classes([AllowAny])
def ngsi_entities(request):
    """
    获取实体列表
    GET /api/ngsi/entities/
    
    查询参数:
        - type: 实体类型（Device/DeviceStatus/Alarm/PredictionResult）
        - limit: 返回数量（默认50）
        - offset: 偏移量（默认0）
    """
    entity_type = request.GET.get("type")
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))

    data = NGSIExchangeService.list_entities(
        entity_type=entity_type,
        limit=limit,
        offset=offset
    )

    return JsonResponse(
        data,
        safe=False,
        content_type="application/ld+json", encoder=DjangoJSONEncoder
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ngsi_entity_detail(request):
    """
    根据URN获取单个实体
    GET /api/ngsi/entity/?id=urn:ngsi-ld:Device:VHF001
    """
    urn = request.GET.get("id")

    if not urn:
        return JsonResponse({"error": "missing entity id"}, status=400)

    data = NGSIExchangeService.get_entity_by_urn(urn)

    if not data:
        return JsonResponse({"error": "entity not found"}, status=404)

    return JsonResponse(
        data,
        content_type="application/ld+json", encoder=DjangoJSONEncoder
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def ngsi_query(request):
    """
    统一NGSI-LD查询接口
    POST /api/ngsi/query/
    
    请求体:
    {
        "type": "Device",
        "q": "deviceType=='VHF'",
        "attrs": ["deviceId", "deviceType"],
        "limit": 50,
        "offset": 0
    }
    """
    entity_type = request.data.get("type")
    q = request.data.get("q")
    attrs = request.data.get("attrs")
    limit = int(request.data.get("limit", 50))
    offset = int(request.data.get("offset", 0))

    if not entity_type:
        return JsonResponse({"error": "missing entity type"}, status=400)

    data = NGSIExchangeService.query_entities(
        entity_type=entity_type,
        q=q,
        attrs=attrs,
        limit=limit,
        offset=offset
    )

    return JsonResponse(
        data,
        safe=False,
        content_type="application/ld+json", encoder=DjangoJSONEncoder
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ngsi_export(request):
    """
    导出所有核心实体，作为外部系统交换包。
    GET /api/ngsi/export/
    """
    entity_type = request.GET.get("type")
    
    data = {
        "@context": [
            "/static/ngsi-ld/ngsi-ld-core-context.jsonld",
            "/static/ngsi-ld/atc-monitor-context.jsonld"
        ],
        "type": "NGSI-LD-ExportPackage",
        "entities": NGSIExchangeService.list_entities(entity_type)
    }

    return JsonResponse(
        data,
        content_type="application/ld+json", encoder=DjangoJSONEncoder
    )


# ==================== 设备专用接口 ====================

@api_view(["GET"])
@permission_classes([AllowAny])
def ngsi_device(request, device_id):
    """
    获取设备的NGSI-LD格式数据
    GET /api/ngsi/devices/{device_id}/
    """
    urn = f"urn:ngsi-ld:Device:{device_id}"
    data = NGSIExchangeService.get_entity_by_urn(urn)

    if not data:
        return JsonResponse({"error": "device not found"}, status=404)

    return JsonResponse(
        data,
        content_type="application/ld+json", encoder=DjangoJSONEncoder
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ngsi_device_status(request, device_id):
    """
    获取设备最新状态的NGSI-LD格式
    GET /api/ngsi/devices/{device_id}/status/
    """
    data = NGSIExchangeService.get_device_status(device_id)

    if not data:
        return JsonResponse({"error": "no status data found"}, status=404)

    return JsonResponse(
        data,
        content_type="application/ld+json", encoder=DjangoJSONEncoder
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ngsi_device_alarms(request, device_id):
    """
    获取设备相关告警的NGSI-LD格式
    GET /api/ngsi/devices/{device_id}/alarms/
    """
    from .models import Device, Alarm
    from core.ngsi_ld import NGSI_LD_Converter

    device = Device.objects.filter(device_id=device_id).first()
    if not device:
        return JsonResponse({"error": "device not found"}, status=404)

    alarms = Alarm.objects.filter(device=device).select_related("device").order_by("-trigger_time")[:20]
    data = [NGSI_LD_Converter.alarm_to_ngsi_ld(a) for a in alarms]

    return JsonResponse(
        data,
        safe=False,
        content_type="application/ld+json", encoder=DjangoJSONEncoder
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ngsi_predictions(request, device_id):
    """
    获取设备预测结果的NGSI-LD格式
    GET /api/ngsi/predictions/{device_id}/
    """
    from .models import Device, PredictionResult
    from core.ngsi_ld import NGSI_LD_Converter

    device = Device.objects.filter(device_id=device_id).first()
    if not device:
        return JsonResponse({"error": "device not found"}, status=404)

    predictions = PredictionResult.objects.filter(device=device).order_by("-prediction_time")[:10]
    data = [NGSI_LD_Converter.prediction_to_ngsi_ld(p) for p in predictions]

    return JsonResponse(
        data,
        safe=False,
        content_type="application/ld+json", encoder=DjangoJSONEncoder
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ngsi_alarms(request):
    """
    返回符合NGSI-LD格式的告警列表（兼容旧接口）
    GET /api/ngsi/alarms/?status=OPEN&device_id=VHF001
    """
    status_filter = request.GET.get("status", "OPEN")
    device_id = request.GET.get("device_id")

    query = f"status=='{status_filter}'" if status_filter else None
    data = NGSIExchangeService.query_entities("Alarm", query, None, 50, 0)

    if device_id and data:
        data = [r for r in data if r.get("refDevice", {}).get("object") == f"urn:ngsi-ld:Device:{device_id}"]

    return JsonResponse(
        data,
        safe=False,
        content_type="application/ld+json", encoder=DjangoJSONEncoder
    )
