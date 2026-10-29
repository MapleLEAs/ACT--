from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SimulationError(Exception):
    """模拟引擎异常基类"""
    def __init__(self, code: str, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class CouplingCalculationError(SimulationError):
    """耦合计算异常"""
    pass


class EventQueueOverflowError(SimulationError):
    """事件队列溢出异常"""
    pass


class SpatialQueryTimeoutError(SimulationError):
    """空间查询超时异常"""
    pass


class PredictionConfidenceError(SimulationError):
    """预测置信度不足异常"""
    pass


class DataQualityError(SimulationError):
    """数据质量异常"""
    pass


class AlarmCascadeError(SimulationError):
    """级联告警异常"""
    pass


class GISCalculationError(SimulationError):
    """GIS计算异常"""
    pass


class ExceptionHandler:
    """
    统一异常处理器
    实现文档要求的异常场景处理策略
    """

    def __init__(self):
        self.error_logs: Dict[str, Dict[str, Any]] = {}

    def handle_coupling_error(self, error: CouplingCalculationError) -> Dict[str, Any]:
        """
        处理设备耦合计算异常
        策略：降级为单设备模式，记录警告日志
        """
        logger.warning(f"耦合计算异常，降级为单设备模式: {error.message}")
        
        return {
            'status': 'degraded',
            'mode': 'single_device',
            'error': {
                'code': error.code,
                'message': error.message,
                'details': error.details
            },
            'timestamp': datetime.now().isoformat(),
            'impact': '不影响数据生成，但耦合效果失效'
        }

    def handle_queue_overflow(self, error: EventQueueOverflowError) -> Dict[str, Any]:
        """
        处理事件队列溢出
        策略：丢弃低优先级事件，保留关键故障事件
        """
        logger.warning(f"事件队列溢出，丢弃低优先级事件: {error.message}")
        
        return {
            'status': 'degraded',
            'action': 'discarded_low_priority',
            'error': {
                'code': error.code,
                'message': error.message,
                'details': error.details
            },
            'timestamp': datetime.now().isoformat(),
            'impact': '可能丢失部分正常波动事件'
        }

    def handle_spatial_timeout(self, error: SpatialQueryTimeoutError) -> Dict[str, Any]:
        """
        处理空间查询超时
        策略：返回降级结果（仅返回基础区域信息）
        """
        logger.warning(f"空间查询超时，返回降级结果: {error.message}")
        
        return {
            'status': 'degraded',
            'action': 'return_basic_info',
            'error': {
                'code': error.code,
                'message': error.message,
                'details': error.details
            },
            'timestamp': datetime.now().isoformat(),
            'impact': '空间分析功能受限，但主业务可用'
        }

    def handle_prediction_confidence(self, error: PredictionConfidenceError) -> Dict[str, Any]:
        """
        处理预测置信度不足
        策略：返回预测结果，但标记"样本不足"
        """
        logger.warning(f"预测置信度不足: {error.message}")
        
        return {
            'status': 'warning',
            'action': 'mark_insufficient_samples',
            'error': {
                'code': error.code,
                'message': error.message,
                'details': error.details
            },
            'timestamp': datetime.now().isoformat(),
            'impact': '预测可信度降低，但结果仍可用'
        }

    def handle_data_quality(self, error: DataQualityError) -> Dict[str, Any]:
        """
        处理数据质量评分过低
        策略：阻断数据入库，触发人工审核流程
        """
        logger.error(f"数据质量评分过低，阻断入库: {error.message}")
        
        return {
            'status': 'blocked',
            'action': 'trigger_manual_review',
            'error': {
                'code': error.code,
                'message': error.message,
                'details': error.details
            },
            'timestamp': datetime.now().isoformat(),
            'impact': '数据生成暂停，需人工介入'
        }

    def handle_cascade_error(self, error: AlarmCascadeError) -> Dict[str, Any]:
        """
        处理级联告警异常（死循环）
        策略：设置传播深度上限（≤3层）
        """
        logger.warning(f"级联告警异常，限制传播深度: {error.message}")
        
        return {
            'status': 'limited',
            'action': 'limit_propagation_depth',
            'max_depth': 3,
            'error': {
                'code': error.code,
                'message': error.message,
                'details': error.details
            },
            'timestamp': datetime.now().isoformat(),
            'impact': '防止告警传播失控'
        }

    def handle_gis_error(self, error: GISCalculationError) -> Dict[str, Any]:
        """
        处理GIS坐标计算失败
        策略：使用默认坐标，标记为"位置缺失"
        """
        logger.warning(f"GIS坐标计算失败，使用默认坐标: {error.message}")
        
        return {
            'status': 'degraded',
            'action': 'use_default_coordinates',
            'error': {
                'code': error.code,
                'message': error.message,
                'details': error.details
            },
            'timestamp': datetime.now().isoformat(),
            'impact': '空间分析受限，但设备数据正常'
        }

    def log_error(self, error_type: str, error: SimulationError):
        """
        记录错误日志
        """
        error_id = f"ERR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(self.error_logs) + 1:03d}"
        self.error_logs[error_id] = {
            'error_id': error_id,
            'error_type': error_type,
            'code': error.code,
            'message': error.message,
            'details': error.details,
            'timestamp': datetime.now().isoformat()
        }

    def get_error_logs(self, limit: int = 10) -> Dict[str, Any]:
        """
        获取最近的错误日志
        :param limit: 返回数量限制
        :return: 错误日志字典
        """
        recent_ids = sorted(self.error_logs.keys(), reverse=True)[:limit]
        return {id: self.error_logs[id] for id in recent_ids}

    def reset_error_logs(self):
        """重置错误日志"""
        self.error_logs = {}
