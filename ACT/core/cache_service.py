"""
NGSI-LD 缓存服务
提供实体数据的缓存管理，减少数据库查询压力
"""
from django.core.cache import cache
import json
from django.core.serializers.json import DjangoJSONEncoder
from typing import List, Dict, Optional, Any
import hashlib

# 缓存键前缀
CACHE_PREFIX = {
    'entity': 'ngsi:entity:',
    'entities': 'ngsi:entities:',
    'device_status': 'ngsi:device_status:',
    'query': 'ngsi:query:',
}

# 缓存时间配置（秒）
CACHE_TIMEOUT = {
    'entity': 300,           # 实体数据缓存5分钟
    'device_status': 10,     # 设备状态缓存10秒（实时性要求高）
    'query': 60,             # 查询结果缓存1分钟
    'export': 300,           # 导出数据缓存5分钟
}


class NGSICacheService:
    """
    NGSI-LD 数据缓存服务
    """

    @staticmethod
    def get_entity(urn: str) -> Optional[Dict]:
        """
        获取单个实体的缓存数据
        """
        key = f"{CACHE_PREFIX['entity']}{urn}"
        data = cache.get(key)
        if data:
            return json.loads(data)
        return None

    @staticmethod
    def set_entity(urn: str, entity: Dict):
        """
        设置单个实体的缓存
        """
        key = f"{CACHE_PREFIX['entity']}{urn}"
        cache.set(key, json.dumps(entity, cls=DjangoJSONEncoder), timeout=CACHE_TIMEOUT['entity'])

    @staticmethod
    def delete_entity(urn: str):
        """
        删除单个实体的缓存
        """
        key = f"{CACHE_PREFIX['entity']}{urn}"
        cache.delete(key)

    @staticmethod
    def get_entities(entity_type: Optional[str] = None, limit: int = 50, offset: int = 0) -> Optional[List]:
        """
        获取实体列表的缓存数据
        """
        key = f"{CACHE_PREFIX['entities']}{entity_type or 'all'}_{limit}_{offset}"
        data = cache.get(key)
        if data:
            return json.loads(data)
        return None

    @staticmethod
    def set_entities(entities: List, entity_type: Optional[str] = None, limit: int = 50, offset: int = 0):
        """
        设置实体列表的缓存
        """
        key = f"{CACHE_PREFIX['entities']}{entity_type or 'all'}_{limit}_{offset}"
        cache.set(key, json.dumps(entities, cls=DjangoJSONEncoder), timeout=CACHE_TIMEOUT['entity'])

    @staticmethod
    def delete_entities(entity_type: Optional[str] = None):
        """
        删除实体列表的缓存
        """
        if entity_type:
            # 删除特定类型的缓存（通过模式匹配）
            keys = cache.keys(f"{CACHE_PREFIX['entities']}{entity_type}_*")
            if keys:
                cache.delete_many(keys)
        else:
            # 删除所有实体列表缓存
            keys = cache.keys(f"{CACHE_PREFIX['entities']}*")
            if keys:
                cache.delete_many(keys)

    @staticmethod
    def get_device_status(device_id: str) -> Optional[Dict]:
        """
        获取设备状态的缓存数据
        """
        key = f"{CACHE_PREFIX['device_status']}{device_id}"
        data = cache.get(key)
        if data:
            return json.loads(data)
        return None

    @staticmethod
    def set_device_status(device_id: str, status: Dict):
        """
        设置设备状态的缓存
        """
        key = f"{CACHE_PREFIX['device_status']}{device_id}"
        cache.set(key, json.dumps(status, cls=DjangoJSONEncoder), timeout=CACHE_TIMEOUT['device_status'])

    @staticmethod
    def delete_device_status(device_id: str):
        """
        删除设备状态的缓存
        """
        key = f"{CACHE_PREFIX['device_status']}{device_id}"
        cache.delete(key)

    @staticmethod
    def get_query_result(query_params: Dict) -> Optional[List]:
        """
        获取查询结果的缓存数据
        """
        # 生成查询参数的哈希作为缓存键
        query_str = json.dumps(query_params, sort_keys=True)
        query_hash = hashlib.md5(query_str.encode()).hexdigest()
        key = f"{CACHE_PREFIX['query']}{query_hash}"
        
        data = cache.get(key)
        if data:
            return json.loads(data)
        return None

    @staticmethod
    def set_query_result(query_params: Dict, result: List):
        """
        设置查询结果的缓存
        """
        query_str = json.dumps(query_params, sort_keys=True)
        query_hash = hashlib.md5(query_str.encode()).hexdigest()
        key = f"{CACHE_PREFIX['query']}{query_hash}"

        cache.set(key, json.dumps(result, cls=DjangoJSONEncoder), timeout=CACHE_TIMEOUT['query'])

    @staticmethod
    def delete_query_cache():
        """
        删除所有查询缓存
        """
        keys = cache.keys(f"{CACHE_PREFIX['query']}*")
        if keys:
            cache.delete_many(keys)

    @staticmethod
    def invalidate_device_cache(device_id: str):
        """
        使设备相关的所有缓存失效
        """
        # 删除设备实体缓存
        urn = f"urn:ngsi-ld:Device:{device_id}"
        NGSICacheService.delete_entity(urn)
        
        # 删除设备状态缓存
        NGSICacheService.delete_device_status(device_id)
        
        # 删除所有实体列表缓存（因为设备可能在列表中）
        NGSICacheService.delete_entities()
        
        # 删除所有查询缓存（可能包含该设备）
        NGSICacheService.delete_query_cache()

    @staticmethod
    def invalidate_all_cache():
        """
        使所有 NGSI-LD 相关缓存失效
        """
        keys = []
        for prefix in CACHE_PREFIX.values():
            keys.extend(cache.keys(f"{prefix}*"))
        
        if keys:
            cache.delete_many(keys)

    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """
        获取缓存统计信息
        """
        try:
            info = cache.client.info()
            return {
                'used_memory': info.get('used_memory_human', 'N/A'),
                'keys_count': info.get('db0', {}).get('keys', 'N/A'),
                'hit_rate': f"{info.get('keyspace_hits', 0) / (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)) * 100:.2f}%"
            }
        except Exception:
            return {
                'error': 'Redis not available, falling back to default cache'
            }
