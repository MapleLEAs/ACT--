from __future__ import annotations

from datetime import timedelta
from typing import Any

import numpy as np
from django.db.models import Q
from django.utils.timezone import now

from monitor.algorithms import TrendCalculator
from monitor.models import Alarm, AlarmRule, Device, DeviceStatusLog, EnvironmentData, PredictionResult


SEVERITY_PENALTY = {
    'CRITICAL': 25,
    'ERROR': 15,
    'WARN': 8,
    'INFO': 3,
}

HEALTH_LEVELS = (
    (85, '健康'),
    (70, '关注'),
    (50, '预警'),
    (0, '高危'),
)


def _score_to_level(score: float) -> str:
    for threshold, label in HEALTH_LEVELS:
        if score >= threshold:
            return label
    return '高危'


def _volatility_penalty(values: list[float]) -> float:
    if len(values) < 3:
        return 0
    std = float(np.std(values))
    mean = float(np.mean(values)) or 1.0
    cv = std / abs(mean)
    return min(15, cv * 30)


def _continuous_anomaly_hours(logs: list[DeviceStatusLog]) -> float:
    if not logs:
        return 0
    streak_start = None
    max_hours = 0
    for log in logs:
        if log.alarm_flag or log.device_status == 'ALARM':
            if streak_start is None:
                streak_start = log.collect_time
        elif streak_start is not None:
            hours = (log.collect_time - streak_start).total_seconds() / 3600
            max_hours = max(max_hours, hours)
            streak_start = None
    if streak_start is not None:
        hours = (logs[-1].collect_time - streak_start).total_seconds() / 3600
        max_hours = max(max_hours, hours)
    return max_hours


def _threshold_deviation_penalty(device: Device, latest_log: DeviceStatusLog | None) -> tuple[float, list[str]]:
    if not latest_log:
        return 0, []

    rules = AlarmRule.objects.filter(
        Q(device=device) | Q(device_type=device.device_type, device__isnull=True),
        is_enabled=True,
    ).exclude(threshold__isnull=True)[:5]

    penalty = 0
    risks: list[str] = []
    for rule in rules:
        metric_value = getattr(latest_log, rule.metric, None)
        if metric_value is None:
            continue
        value = float(metric_value)
        threshold = float(rule.threshold)
        operator = rule.operator or '>'
        exceeded = False
        if operator == '>':
            exceeded = value > threshold
        elif operator == '>=':
            exceeded = value >= threshold
        elif operator == '<':
            exceeded = value < threshold
        elif operator == '<=':
            exceeded = value <= threshold
        if exceeded:
            deviation = abs(value - threshold) / (abs(threshold) or 1)
            penalty += min(12, deviation * 10)
            risks.append(f'{rule.metric} 偏离阈值 ({rule.operator} {threshold})')
    return min(20, penalty), risks


def _environment_penalty(device: Device) -> tuple[float, list[str]]:
    env = EnvironmentData.objects.filter(device=device).order_by('-collect_time').first()
    if not env:
        return 0, []
    penalty = 0
    risks: list[str] = []
    if env.ambient_temperature is not None and float(env.ambient_temperature) > 40:
        penalty += 5
        risks.append('环境温度过高')
    if env.humidity is not None and float(env.humidity) > 85:
        penalty += 4
        risks.append('环境湿度过高')
    if env.wind_speed is not None and float(env.wind_speed) > 15:
        penalty += 3
        risks.append('风速偏大')
    return min(10, penalty), risks


def calculate_device_health(device: Device) -> dict[str, Any]:
    score = 100.0
    top_risks: list[str] = []

    latest_log = DeviceStatusLog.objects.filter(device=device).order_by('-collect_time').first()
    if latest_log and not latest_log.online_status:
        score -= 30
        top_risks.append('设备当前离线')

    open_alarms = Alarm.objects.filter(device=device, status='OPEN').order_by('-severity')
    for alarm in open_alarms[:3]:
        penalty = SEVERITY_PENALTY.get(alarm.severity, 5)
        score -= penalty
        top_risks.append(f'未处理告警: {alarm.alarm_id} ({alarm.severity})')

    recent_logs = list(
        DeviceStatusLog.objects.filter(device=device).order_by('-collect_time')[:48]
    )
    recent_logs.reverse()

    anomaly_hours = _continuous_anomaly_hours(recent_logs)
    if anomaly_hours > 0:
        anomaly_penalty = min(15, anomaly_hours * 2)
        score -= anomaly_penalty
        top_risks.append(f'连续异常约 {anomaly_hours:.1f} 小时')

    metrics = ['device_temperature', 'signal_strength', 'power_voltage']
    for metric in metrics:
        values = [
            float(getattr(log, metric))
            for log in recent_logs
            if getattr(log, metric, None) is not None
        ]
        if len(values) >= 3:
            vol_penalty = _volatility_penalty(values)
            if vol_penalty > 5:
                score -= vol_penalty
                top_risks.append(f'{metric} 波动率偏高')

    threshold_penalty, threshold_risks = _threshold_deviation_penalty(device, latest_log)
    score -= threshold_penalty
    top_risks.extend(threshold_risks)

    env_penalty, env_risks = _environment_penalty(device)
    score -= env_penalty
    top_risks.extend(env_risks)

    score = max(0, min(100, round(score, 1)))
    health_level = _score_to_level(score)

    risk_trend = _build_risk_trend(device, recent_logs)
    maintenance_suggestion = _build_maintenance_suggestion(score, health_level, anomaly_hours, open_alarms.exists())
    prediction_window = _estimate_prediction_window(device, recent_logs)

    return {
        'device_id': device.device_id,
        'device_type': device.device_type,
        'health_score': score,
        'health_level': health_level,
        'risk_trend': risk_trend,
        'top_risks': top_risks[:5],
        'risk_factors': top_risks[:5],
        'maintenance_suggestion': maintenance_suggestion,
        'prediction_window_hours': prediction_window,
        'last_evaluated': latest_log.collect_time.isoformat() if latest_log else None,
        'sample_sufficient': len(recent_logs) >= 10,
    }


def _build_risk_trend(device: Device, logs: list[DeviceStatusLog]) -> list[dict[str, Any]]:
    if len(logs) < 5:
        return []
    chunk_size = max(1, len(logs) // 5)
    trend: list[dict[str, Any]] = []
    for index in range(0, len(logs), chunk_size):
        chunk = logs[index:index + chunk_size]
        alarm_ratio = sum(1 for log in chunk if log.alarm_flag) / len(chunk)
        risk_score = round((1 - alarm_ratio) * 100, 1)
        trend.append({
            'time': chunk[-1].collect_time.isoformat(),
            'risk_score': risk_score,
        })
    return trend


def _build_maintenance_suggestion(
    score: float,
    health_level: str,
    anomaly_hours: float,
    has_open_alarm: bool,
) -> str:
    if has_open_alarm and score < 50:
        return '建议立即派单处理未关闭告警，并在 24 小时内完成巡检'
    if health_level == '高危':
        return '建议 24 小时内安排现场巡检并复核关键指标'
    if health_level == '预警':
        return '建议 72 小时内巡检，并关注连续异常时段'
    if anomaly_hours > 6:
        return '建议排查连续异常根因，必要时创建预防性工单'
    if health_level == '关注':
        return '建议纳入下一周期维护计划，持续观察趋势'
    return '设备运行正常，保持例行巡检即可'


def _estimate_prediction_window(device: Device, logs: list[DeviceStatusLog]) -> int | None:
    values = [
        float(log.device_temperature)
        for log in logs
        if log.device_temperature is not None
    ]
    if len(values) < 10:
        return None
    calculator = TrendCalculator()
    trend = calculator.calculate_trend(values)
    slope = abs(trend.get('slope', 0))
    if slope > 0.5:
        return 24
    if slope > 0.1:
        return 72
    return 168


def get_health_summary(devices: list[Device] | None = None) -> dict[str, Any]:
    queryset = devices if devices is not None else list(Device.objects.all())
    details = [calculate_device_health(device) for device in queryset]
    details.sort(key=lambda item: item['health_score'])

    level_counts = {'健康': 0, '关注': 0, '预警': 0, '高危': 0}
    for item in details:
        level_counts[item['health_level']] = level_counts.get(item['health_level'], 0) + 1

    return {
        'total_devices': len(details),
        'level_counts': level_counts,
        'avg_health_score': round(
            sum(item['health_score'] for item in details) / len(details), 1
        ) if details else 0,
        'high_risk_devices': details[:5],
        'devices': details,
    }


def recalculate_predictions(device: Device, metrics: list[str] | None = None) -> list[PredictionResult]:
    metrics = metrics or ['device_temperature', 'signal_strength', 'power_voltage']
    created: list[PredictionResult] = []
    logs = list(DeviceStatusLog.objects.filter(device=device).order_by('-collect_time')[:100])
    logs.reverse()

    for metric in metrics:
        values = [float(getattr(log, metric)) for log in logs if getattr(log, metric, None) is not None]
        if len(values) < 5:
            continue
        calculator = TrendCalculator()
        trend = calculator.calculate_trend(values)
        last_value = values[-1]
        slope = trend.get('slope', 0)
        predicted = last_value + slope * 4
        confidence = min(100, trend.get('r_squared', 0) * 100)

        result = PredictionResult.objects.create(
            device=device,
            metric=metric,
            predicted_value=predicted,
            prediction_time=now() + timedelta(hours=24),
            prediction_horizon=1440,
            confidence_score=confidence,
            status='PREDICTED',
            severity='WARN' if predicted > last_value * 1.1 else 'INFO',
            is_above_threshold=predicted > last_value * 1.15,
        )
        created.append(result)
    return created
