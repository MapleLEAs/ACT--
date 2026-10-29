"""
Rule Engine Core - 规则引擎核心
负责规则评估、告警触发、冷却管理、自动恢复等核心逻辑
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RuleType(Enum):
    THRESHOLD = "THRESHOLD"
    RANGE = "RANGE"
    TREND = "TREND"
    COMPOSITE = "COMPOSITE"


class ComparisonOperator:
    OPERATORS = {
        '<': lambda a, b: a < b,
        '>': lambda a, b: a > b,
        '<=': lambda a, b: a <= b,
        '>=': lambda a, b: a >= b,
        '==': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
        'abs>': lambda a, b: abs(a) > b,
    }

    @classmethod
    def evaluate(cls, operator: str, value: Any, threshold: Any) -> bool:
        op_func = cls.OPERATORS.get(operator)
        if op_func is None:
            logger.warning(f"未知操作符: {operator}")
            return False
        try:
            return op_func(float(value), float(threshold))
        except (ValueError, TypeError) as e:
            logger.error(f"比较失败: {e}")
            return False


@dataclass
class RuleMatchResult:
    rule_id: int
    rule_name: str
    matched: bool
    metric: str
    value: float
    threshold: float
    operator: str
    severity: str
    message: str = ""


class RuleContext:
    """
    规则执行上下文
    维护规则状态和冷却时间
    """

    def __init__(self):
        self._last_trigger_time: Dict[int, datetime] = {}
        self._cooldown_end_time: Dict[int, datetime] = {}
        self._active_alarms: Dict[str, str] = {}

    def is_in_cooldown(self, rule_id: int) -> bool:
        """检查规则是否在冷却中"""
        if rule_id not in self._cooldown_end_time:
            return False
        if datetime.now() < self._cooldown_end_time[rule_id]:
            return True
        del self._cooldown_end_time[rule_id]
        return False

    def start_cooldown(self, rule_id: int, cooldown_seconds: int):
        """开始冷却"""
        if cooldown_seconds > 0:
            self._cooldown_end_time[rule_id] = datetime.now() + timedelta(seconds=cooldown_seconds)

    def set_alarm_active(self, device_id: str, metric: str, alarm_id: str):
        """标记告警已触发"""
        key = f"{device_id}:{metric}"
        self._active_alarms[key] = alarm_id

    def is_alarm_active(self, device_id: str, metric: str) -> bool:
        """检查告警是否已触发"""
        key = f"{device_id}:{metric}"
        return key in self._active_alarms

    def clear_alarm(self, device_id: str, metric: str):
        """清除告警标记"""
        key = f"{device_id}:{metric}"
        if key in self._active_alarms:
            del self._active_alarms[key]

    def get_active_alarm_id(self, device_id: str, metric: str) -> Optional[str]:
        """获取活跃告警ID"""
        key = f"{device_id}:{metric}"
        return self._active_alarms.get(key)


class RuleEvaluator:
    """
    规则评估器
    负责评估单条规则
    """

    @staticmethod
    def evaluate_standard_threshold(
        value: float,
        threshold_config: Dict[str, Any]
    ) -> Tuple[bool, str, float]:
        """
        评估标准阈值
        :param value: 当前值
        :param threshold_config: 标准阈值配置
        :return: (是否告警, 严重级别, 阈值值)
        """
        name = threshold_config.get('name', '')
        unit = threshold_config.get('unit', '')
        
        # 检查硬告警门限
        crit_low = threshold_config.get('critical_low')
        crit_high = threshold_config.get('critical_high')
        
        if crit_low is not None and value < crit_low:
            return True, 'CRITICAL', crit_low
        if crit_high is not None and value > crit_high:
            return True, 'CRITICAL', crit_high
        
        # 检查预警门限
        warn_low = threshold_config.get('warning_low')
        warn_high = threshold_config.get('warning_high')
        
        if warn_low is not None and value < warn_low:
            return True, 'WARN', warn_low
        if warn_high is not None and value > warn_high:
            return True, 'WARN', warn_high
        
        return False, 'INFO', 0.0

    @staticmethod
    def evaluate_threshold(
        value: float,
        operator: str,
        threshold: float
    ) -> bool:
        """评估阈值规则"""
        return ComparisonOperator.evaluate(operator, value, threshold)

    @staticmethod
    def evaluate_range(
        value: float,
        min_threshold: float,
        max_threshold: float
    ) -> bool:
        """评估范围规则"""
        return min_threshold <= value <= max_threshold

    @staticmethod
    def evaluate_composite(
        conditions: List[Dict[str, Any]],
        logic: str = "AND"
    ) -> bool:
        """
        评估复合条件
        logic: "AND" 或 "OR"
        conditions: [{"metric": "xxx", "operator": ">", "threshold": 100}, ...]
        """
        results = []
        for cond in conditions:
            value = cond.get('value')
            operator = cond.get('operator')
            threshold = cond.get('threshold')
            if value is not None and operator and threshold is not None:
                result = ComparisonOperator.evaluate(operator, value, threshold)
                results.append(result)

        if not results:
            return False

        if logic == "AND":
            return all(results)
        elif logic == "OR":
            return any(results)
        return False


class RuleEngine:
    """
    规则引擎核心
    统一管理所有规则评估和告警生成
    """

    def __init__(self):
        self.context = RuleContext()
        self.evaluator = RuleEvaluator()

    def evaluate_device_status(self, status_data: Dict[str, Any]) -> List[RuleMatchResult]:
        """
        评估设备状态，触发匹配规则
        优先使用标准阈值，同时保留自定义规则功能
        :param status_data: 设备状态数据
        :return: 匹配的规则结果列表
        """
        from monitor.models import AlarmRule
        from monitor.standard_thresholds import get_all_thresholds_for_device

        results = []
        device_id = status_data.get('device_id')
        device_type = status_data.get('device_type')

        # ========================================
        # 第一步：使用标准阈值进行评估
        # ========================================
        if device_type:
            standard_thresholds = get_all_thresholds_for_device(device_type)
            
            for metric, threshold_config in standard_thresholds.items():
                value = self._get_metric_value(status_data, metric)
                
                if value is None:
                    continue
                
                matched, severity, threshold_val = self.evaluator.evaluate_standard_threshold(
                    value,
                    threshold_config
                )
                
                result = RuleMatchResult(
                    rule_id=0,  # 标准阈值没有 rule_id
                    rule_name=f"标准阈值-{threshold_config.get('name', metric)}",
                    matched=matched,
                    metric=metric,
                    value=value,
                    threshold=threshold_val,
                    operator='STANDARD',
                    severity=severity,
                    message=f"{threshold_config.get('name', metric)}: 当前值={value}{threshold_config.get('unit', '')}（阈值={threshold_val}）"
                )
                results.append(result)

        # ========================================
        # 第二步：使用自定义规则进行评估（保留原有功能）
        # ========================================
        applicable_rules = self._get_applicable_rules(device_id, device_type)

        for rule in applicable_rules:
            if self.context.is_in_cooldown(rule.id):
                continue

            metric = rule.metric
            value = self._get_metric_value(status_data, metric)

            if value is None:
                continue

            matched = self.evaluator.evaluate_threshold(
                value,
                rule.operator,
                float(rule.threshold) if rule.threshold else 0
            )

            result = RuleMatchResult(
                rule_id=rule.id,
                rule_name=rule.name,
                matched=matched,
                metric=metric,
                value=value,
                threshold=float(rule.threshold) if rule.threshold else 0,
                operator=rule.operator,
                severity=rule.severity,
                message=f"{metric} {rule.operator} {rule.threshold}: 当前值={value}"
            )
            results.append(result)

            if matched:
                self.context.start_cooldown(rule.id, rule.cooldown_seconds)

        return results

    def check_alarm_recovery(
        self,
        device_id: str,
        metric: str,
        current_value: float,
        rule: Any
    ) -> Tuple[bool, Optional[float]]:
        """
        检查告警是否可恢复
        :return: (可恢复, 恢复阈值)
        """
        if not rule.auto_clear or not rule.recovery_threshold:
            return False, None

        recovery_op = rule.recovery_operator or rule.operator
        recovery_val = float(rule.recovery_threshold)

        recovered = not ComparisonOperator.evaluate(recovery_op, current_value, recovery_val)
        return recovered, recovery_val

    def _get_applicable_rules(self, device_id: str, device_type: str) -> List:
        """获取适用的规则"""
        from monitor.models import AlarmRule
        from django.core.cache import cache

        cache_key = 'alarm_rules_cache'
        all_rules = cache.get(cache_key)

        if all_rules is None:
            all_rules = list(AlarmRule.objects.filter(is_enabled=True))
            cache.set(cache_key, all_rules, timeout=300)

        applicable = []
        for rule in all_rules:
            if rule.level == 'GLOBAL':
                applicable.append(rule)
            elif rule.level == 'DEVICE_TYPE' and rule.device_type == device_type:
                applicable.append(rule)
            elif rule.level == 'DEVICE' and rule.device_id == device_id:
                applicable.append(rule)

        return applicable

    def _get_metric_value(self, status_data: Dict[str, Any], metric: str) -> Optional[float]:
        """从状态数据中获取指标值"""
        field_map = {
            'signal_strength': 'signal_strength',
            'signal_power': 'signal_power',
            'power_voltage': 'power_voltage',
            'device_temperature': 'device_temperature',
            'bit_error_rate': 'bit_error_rate',
            'loc_guidance_deviation': 'loc_guidance_deviation',
            'gs_guidance_deviation': 'gs_guidance_deviation',
            'antenna_swr': 'antenna_swr',
            'temperature': 'device_temperature',
            'vswr': 'antenna_swr',
            'loc_ddm': 'loc_guidance_deviation',
            'gs_ddm': 'gs_guidance_deviation',
            'bearing_error': 'loc_guidance_deviation',
            'rf_power': 'signal_power',
            'modulation_diff': 'bit_error_rate',
            'reply_efficiency': 'bit_error_rate',
            'transmit_power': 'signal_power',
            'pulse_interval_x': 'bit_error_rate',
            'pulse_interval_y': 'bit_error_rate',
            'transmit_pep': 'signal_power',
            'work_frequency': 'signal_power',
        }

        field_name = field_map.get(metric, metric)
        value = status_data.get(field_name)
        
        if value is None:
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None


class AlarmGenerator:
    """
    告警生成器
    负责创建告警记录
    """

    @staticmethod
    def generate_alarm(
        device,
        rule,
        metric: str,
        value: float,
        trigger_time: datetime
    ) -> 'Alarm':
        """
        生成告警记录
        :return: Alarm 实例
        """
        from monitor.models import Alarm
        import uuid

        alarm_id = f"ALM-{device.device_id}-{uuid.uuid4().hex[:8].upper()}"

        alarm = Alarm.objects.create(
            device=device,
            rule=rule,
            metric=metric,
            value=value,
            severity=rule.severity,
            status='OPEN',
            alarm_id=alarm_id,
            trigger_time=trigger_time,
        )

        logger.info(f"告警生成: {alarm_id} - {rule.name}")
        return alarm

    @staticmethod
    def clear_alarm(alarm: 'Alarm', recover_value: Optional[float] = None):
        """清除告警"""
        alarm.status = 'CLEARED'
        alarm.clear_time = datetime.now()
        if recover_value is not None:
            alarm.recover_value = Decimal(str(recover_value))
        alarm.save()
        logger.info(f"告警清除: {alarm.alarm_id}")
