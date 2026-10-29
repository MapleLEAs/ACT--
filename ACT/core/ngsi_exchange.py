"""
NGSI-LD 标准化数据交换服务层
负责统一实体查询、实体转换、标准输出。
"""
from monitor.models import Device, DeviceStatusLog, Alarm
from core.ngsi_ld import NGSI_LD_Converter
from core.cache_service import NGSICacheService


class NGSIExchangeService:
    """
    NGSI-LD 标准化数据交换服务层
    负责统一实体查询、实体转换、标准输出。
    集成缓存机制提高查询性能。
    """

    @staticmethod
    def list_entities(entity_type=None, limit=50, offset=0):
        """
        列出实体（带缓存）
        :param entity_type: 实体类型（Device/DeviceStatus/Alarm），None表示返回所有类型
        :param limit: 返回数量限制
        :param offset: 偏移量
        :return: NGSI-LD 格式的实体列表
        """
        # 尝试从缓存获取
        cached = NGSICacheService.get_entities(entity_type, limit, offset)
        if cached is not None:
            return cached

        # 缓存未命中，从数据库查询
        if entity_type == "Device":
            qs = Device.objects.all()[offset:offset + limit]
            result = [NGSI_LD_Converter.device_to_ngsi_ld(item) for item in qs]

        elif entity_type == "DeviceStatus":
            qs = DeviceStatusLog.objects.select_related("device").order_by("-collect_time")[offset:offset + limit]
            result = [NGSI_LD_Converter.status_log_to_ngsi_ld(item) for item in qs]

        elif entity_type == "Alarm":
            qs = Alarm.objects.select_related("device").order_by("-trigger_time")[offset:offset + limit]
            result = [NGSI_LD_Converter.alarm_to_ngsi_ld(item) for item in qs]

        else:
            # 返回所有类型实体
            devices = [NGSI_LD_Converter.device_to_ngsi_ld(d) for d in Device.objects.all()[:limit]]
            statuses = [
                NGSI_LD_Converter.status_log_to_ngsi_ld(s)
                for s in DeviceStatusLog.objects.select_related("device").order_by("-collect_time")[:limit]
            ]
            alarms = [
                NGSI_LD_Converter.alarm_to_ngsi_ld(a)
                for a in Alarm.objects.select_related("device").order_by("-trigger_time")[:limit]
            ]
            result = devices + statuses + alarms

        # 设置缓存
        NGSICacheService.set_entities(result, entity_type, limit, offset)
        return result

    @staticmethod
    def get_entity_by_urn(urn):
        """
        根据 URN 获取实体（带缓存）
        :param urn: 实体统一资源名称（如 urn:ngsi-ld:Device:VHF001）
        :return: NGSI-LD 格式的实体，不存在返回 None
        """
        # 尝试从缓存获取
        cached = NGSICacheService.get_entity(urn)
        if cached is not None:
            return cached

        parts = urn.split(":")
        if len(parts) < 4:
            return None

        entity_type = parts[2]
        entity_id = parts[3]
        result = None

        if entity_type == "Device":
            device = Device.objects.filter(device_id=entity_id).first()
            result = NGSI_LD_Converter.device_to_ngsi_ld(device) if device else None

        elif entity_type == "DeviceStatus":
            status = DeviceStatusLog.objects.filter(id=entity_id).select_related("device").first()
            result = NGSI_LD_Converter.status_log_to_ngsi_ld(status) if status else None

        elif entity_type == "Alarm":
            alarm = Alarm.objects.filter(alarm_id=entity_id).select_related("device").first()
            result = NGSI_LD_Converter.alarm_to_ngsi_ld(alarm) if alarm else None

        elif entity_type == "PredictionResult":
            from monitor.models import PredictionResult
            prediction = PredictionResult.objects.filter(id=entity_id).select_related("device").first()
            result = NGSI_LD_Converter.prediction_to_ngsi_ld(prediction) if prediction else None

        # 设置缓存
        if result:
            NGSICacheService.set_entity(urn, result)

        return result

    @staticmethod
    def query_entities(entity_type, q=None, attrs=None, limit=50, offset=0):
        """
        查询实体（带缓存）
        :param entity_type: 实体类型
        :param q: 查询条件（如 "deviceType=='VHF'"）
        :param attrs: 需要返回的属性列表
        :param limit: 返回数量限制
        :param offset: 偏移量
        :return: NGSI-LD 格式的实体列表
        """
        # 构建查询参数用于缓存键
        query_params = {
            'entity_type': entity_type,
            'q': q,
            'attrs': attrs,
            'limit': limit,
            'offset': offset
        }

        # 尝试从缓存获取
        cached = NGSICacheService.get_query_result(query_params)
        if cached is not None:
            return cached

        # 缓存未命中，从数据库查询
        if entity_type == "Device":
            qs = Device.objects.all()

            if q:
                qs = NGSIExchangeService.apply_device_query(qs, q)

            qs = qs[offset:offset + limit]
            data = [NGSI_LD_Converter.device_to_ngsi_ld(item) for item in qs]

        elif entity_type == "Alarm":
            qs = Alarm.objects.select_related("device").all()

            if q:
                qs = NGSIExchangeService.apply_alarm_query(qs, q)

            qs = qs.order_by("-trigger_time")[offset:offset + limit]
            data = [NGSI_LD_Converter.alarm_to_ngsi_ld(item) for item in qs]

        elif entity_type == "DeviceStatus":
            qs = DeviceStatusLog.objects.select_related("device").all()

            if q:
                qs = NGSIExchangeService.apply_status_query(qs, q)

            qs = qs.order_by("-collect_time")[offset:offset + limit]
            data = [NGSI_LD_Converter.status_log_to_ngsi_ld(item) for item in qs]

        elif entity_type == "PredictionResult":
            from monitor.models import PredictionResult
            qs = PredictionResult.objects.select_related("device").all()

            if q:
                qs = NGSIExchangeService.apply_prediction_query(qs, q)

            qs = qs.order_by("-prediction_time")[offset:offset + limit]
            data = [NGSI_LD_Converter.prediction_to_ngsi_ld(item) for item in qs]

        else:
            return []

        if attrs:
            data = [NGSIExchangeService.filter_attrs(item, attrs) for item in data]

        # 设置缓存（查询结果缓存）
        NGSICacheService.set_query_result(query_params, data)

        return data

    @staticmethod
    def apply_device_query(qs, q):
        """
        应用设备查询条件
        """
        if "deviceType=='VHF'" in q:
            qs = qs.filter(device_type="VHF")
        if "deviceType=='ILS'" in q:
            qs = qs.filter(device_type="ILS")
        if "deviceType=='VOR'" in q:
            qs = qs.filter(device_type="VOR")
        if "deviceType=='DME'" in q:
            qs = qs.filter(device_type="DME")
        if "deviceType=='HF'" in q:
            qs = qs.filter(device_type="HF")
        if "status=='online'" in q.lower():
            qs = qs.filter(status="online")
        if "status=='offline'" in q.lower():
            qs = qs.filter(status="offline")
        return qs

    @staticmethod
    def apply_alarm_query(qs, q):
        """
        应用告警查询条件
        """
        if "status=='OPEN'" in q:
            qs = qs.filter(status="OPEN")
        if "status=='ACK'" in q:
            qs = qs.filter(status="ACK")
        if "status=='CLEARED'" in q:
            qs = qs.filter(status="CLEARED")
        if "severity=='CRITICAL'" in q:
            qs = qs.filter(severity="CRITICAL")
        if "severity=='ERROR'" in q:
            qs = qs.filter(severity="ERROR")
        if "severity=='WARNING'" in q:
            qs = qs.filter(severity="WARNING")
        if "severity=='INFO'" in q:
            qs = qs.filter(severity="INFO")
        return qs

    @staticmethod
    def apply_status_query(qs, q):
        """
        应用状态查询条件
        """
        if "alarmFlag==true" in q:
            qs = qs.filter(alarm_flag=True)
        if "alarmFlag==false" in q:
            qs = qs.filter(alarm_flag=False)
        if "onlineStatus==true" in q:
            qs = qs.filter(online_status=True)
        if "onlineStatus==false" in q:
            qs = qs.filter(online_status=False)
        return qs

    @staticmethod
    def apply_prediction_query(qs, q):
        """
        应用预测结果查询条件
        """
        if "isAboveThreshold==true" in q:
            qs = qs.filter(is_above_threshold=True)
        if "isAboveThreshold==false" in q:
            qs = qs.filter(is_above_threshold=False)
        if "severity=='HIGH'" in q:
            qs = qs.filter(severity="HIGH")
        if "severity=='MEDIUM'" in q:
            qs = qs.filter(severity="MEDIUM")
        if "severity=='LOW'" in q:
            qs = qs.filter(severity="LOW")
        return qs

    @staticmethod
    def filter_attrs(entity, attrs):
        """
        过滤实体属性，只保留指定属性
        :param entity: NGSI-LD 实体
        :param attrs: 需要保留的属性列表
        :return: 过滤后的实体
        """
        base = {
            "id": entity.get("id"),
            "type": entity.get("type"),
            "@context": entity.get("@context"),
        }

        for attr in attrs:
            if attr in entity:
                base[attr] = entity[attr]

        return base

    @staticmethod
    def get_device_status(device_id):
        """
        获取设备最新状态的 NGSI-LD 格式（带缓存）
        :param device_id: 设备ID
        :return: NGSI-LD 格式的设备状态
        """
        # 尝试从缓存获取（设备状态缓存时间较短，保证实时性）
        cached = NGSICacheService.get_device_status(device_id)
        if cached is not None:
            return cached

        device = Device.objects.filter(device_id=device_id).first()
        if not device:
            return None

        latest_status = DeviceStatusLog.objects.filter(
            device=device
        ).select_related("device").order_by("-collect_time").first()

        if not latest_status:
            return None

        result = NGSI_LD_Converter.status_log_to_ngsi_ld(latest_status)
        
        # 设置缓存（设备状态缓存时间较短）
        NGSICacheService.set_device_status(device_id, result)

        return result

    @staticmethod
    def export_all_entities(entity_type=None):
        """
        导出所有实体数据
        :param entity_type: 实体类型，None表示导出所有
        :return: 所有实体的 NGSI-LD 格式列表
        """
        return NGSIExchangeService.list_entities(entity_type, limit=1000)
