#!/usr/bin/env python
"""
历史数据回填脚本 - 将现有数据库中的设备、告警、工单等数据同步到 Neo4j

Usage:
    python scripts/sync_historical_data_to_neo4j.py [--clear] [--batch-size N]
    
Options:
    --clear         先清空 Neo4j 中的所有数据（谨慎使用）
    --batch-size N  批量同步大小，默认 100
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atc_monitor.settings')

import django
django.setup()

from monitor.models import Device, Alarm, AlarmEvent, DeviceStatusLog, PredictionResult
from monitor.graph_service import RootCauseGraphService


def sync_all_devices(graph_service, batch_size=100):
    """同步设备数据到 Neo4j"""
    print("=== 同步设备数据 ===")
    devices = Device.objects.all()
    total = devices.count()
    print(f"待同步设备数量: {total}")
    
    count = 0
    errors = 0
    for device in devices.iterator(chunk_size=batch_size):
        try:
            if graph_service._driver:
                with graph_service._driver.session() as session:
                    session.run(
                        """
                        MERGE (d:Device {id: $id})
                        SET d.name = $name, d.type = $type, d.location = $location,
                            d.model = $model, d.manufacturer = $manufacturer
                        """,
                        id=device.device_id,
                        name=device.device_id,
                        type=device.device_type,
                        location=device.location or '',
                        model=device.device_model or '',
                        manufacturer=device.manufacturer or '',
                    )
            count += 1
            if count % batch_size == 0:
                print(f"已同步设备: {count}/{total}")
        except Exception as e:
            errors += 1
            print(f"同步设备 {device.device_id} 失败: {str(e)}")
    
    print(f"设备同步完成，成功: {count}/{total}，失败: {errors}")
    return count, errors


def sync_all_alarms(graph_service, batch_size=100):
    """同步告警数据到 Neo4j"""
    print("\n=== 同步告警数据 ===")
    alarms = Alarm.objects.select_related('device', 'rule').all()
    total = alarms.count()
    print(f"待同步告警数量: {total}")
    
    count = 0
    errors = 0
    for alarm in alarms.iterator(chunk_size=batch_size):
        try:
            if graph_service._driver and alarm.device:
                with graph_service._driver.session() as session:
                    session.run(
                        """
                        MERGE (d:Device {id: $device_id})
                        SET d.name = $device_id, d.type = $device_type
                        MERGE (a:Alarm {id: $alarm_id})
                        SET a.name = $alarm_name, a.severity = $severity, 
                            a.status = $status, a.trigger_time = $trigger_time
                        MERGE (d)-[:TRIGGERED]->(a)
                        """,
                        device_id=alarm.device.device_id,
                        device_type=alarm.device.device_type,
                        alarm_id=str(alarm.id),
                        alarm_name=alarm.alarm_id,
                        severity=alarm.severity,
                        status=alarm.status,
                        trigger_time=alarm.trigger_time.isoformat() if alarm.trigger_time else '',
                    )
                    if alarm.rule_id and alarm.rule:
                        session.run(
                            """
                            MERGE (r:AlarmRule {id: $rule_id})
                            SET r.name = $rule_name
                            WITH r
                            MATCH (a:Alarm {id: $alarm_id})
                            MERGE (r)-[:DERIVED_FROM]->(a)
                            """,
                            rule_id=str(alarm.rule_id),
                            rule_name=alarm.rule.name,
                            alarm_id=str(alarm.id),
                        )
            count += 1
            if count % batch_size == 0:
                print(f"已同步告警: {count}/{total}")
        except Exception as e:
            errors += 1
            print(f"同步告警 {alarm.id} 失败: {str(e)}")
    
    print(f"告警同步完成，成功: {count}/{total}，失败: {errors}")
    return count, errors


def sync_all_alarm_events(graph_service, batch_size=100):
    """同步告警事件数据到 Neo4j"""
    print("\n=== 同步告警事件数据 ===")
    events = AlarmEvent.objects.select_related('alarm').all()
    total = events.count()
    print(f"待同步告警事件数量: {total}")
    
    count = 0
    errors = 0
    for event in events.iterator(chunk_size=batch_size):
        try:
            if graph_service._driver and event.alarm:
                with graph_service._driver.session() as session:
                    session.run(
                        """
                        MERGE (e:AlarmEvent {id: $event_id})
                        SET e.type = $event_type, e.event_time = $event_time, 
                            e.operator = $operator, e.description = $description
                        WITH e
                        MATCH (a:Alarm {id: $alarm_id})
                        MERGE (a)-[:HAS_EVENT]->(e)
                        """,
                        event_id=str(event.id),
                        event_type=event.get_event_type_display(),
                        event_time=event.event_time.isoformat() if event.event_time else '',
                        operator=event.operator or '',
                        description=event.description or '',
                        alarm_id=str(event.alarm.id),
                    )
            count += 1
            if count % batch_size == 0:
                print(f"已同步告警事件: {count}/{total}")
        except Exception as e:
            errors += 1
            print(f"同步告警事件 {event.id} 失败: {str(e)}")
    
    print(f"告警事件同步完成，成功: {count}/{total}，失败: {errors}")
    return count, errors


def sync_all_status_logs(graph_service, batch_size=100):
    """同步设备状态日志到 Neo4j"""
    print("\n=== 同步设备状态日志 ===")
    logs = DeviceStatusLog.objects.select_related('device').all()
    total = logs.count()
    print(f"待同步状态日志数量: {total}")
    
    count = 0
    errors = 0
    for log in logs.iterator(chunk_size=batch_size):
        try:
            if graph_service._driver and log.device:
                with graph_service._driver.session() as session:
                    session.run(
                        """
                        MERGE (s:DeviceStatusLog {id: $log_id})
                        SET s.collect_time = $collect_time, s.alarm_flag = $alarm_flag,
                            s.device_status = $device_status, s.signal_strength = $signal_strength
                        WITH s
                        MATCH (d:Device {id: $device_id})
                        MERGE (d)-[:HAS_STATUS]->(s)
                        """,
                        log_id=str(log.id),
                        collect_time=log.collect_time.isoformat() if log.collect_time else '',
                        alarm_flag=log.alarm_flag,
                        device_status=log.device_status or '',
                        signal_strength=log.signal_strength or 0,
                        device_id=log.device.device_id,
                    )
            count += 1
            if count % batch_size == 0:
                print(f"已同步状态日志: {count}/{total}")
        except Exception as e:
            errors += 1
            print(f"同步状态日志 {log.id} 失败: {str(e)}")
    
    print(f"状态日志同步完成，成功: {count}/{total}，失败: {errors}")
    return count, errors


def sync_all_predictions(graph_service, batch_size=100):
    """同步预测结果数据到 Neo4j"""
    print("\n=== 同步预测结果数据 ===")
    predictions = PredictionResult.objects.select_related('device').all()
    total = predictions.count()
    print(f"待同步预测结果数量: {total}")
    
    count = 0
    errors = 0
    for prediction in predictions.iterator(chunk_size=batch_size):
        try:
            if graph_service._driver and prediction.device:
                with graph_service._driver.session() as session:
                    session.run(
                        """
                        MERGE (p:Prediction {id: $pred_id})
                        SET p.metric = $metric, p.prediction_value = $prediction_value,
                            p.confidence = $confidence, p.prediction_time = $prediction_time
                        WITH p
                        MATCH (d:Device {id: $device_id})
                        MERGE (p)-[:RELATED_TO]->(d)
                        """,
                        pred_id=str(prediction.id),
                        metric=prediction.metric or '',
                        prediction_value=prediction.prediction_value or 0,
                        confidence=float(prediction.confidence_score or 0),
                        prediction_time=prediction.prediction_time.isoformat() if prediction.prediction_time else '',
                        device_id=prediction.device.device_id,
                    )
            count += 1
            if count % batch_size == 0:
                print(f"已同步预测结果: {count}/{total}")
        except Exception as e:
            errors += 1
            print(f"同步预测结果 {prediction.id} 失败: {str(e)}")
    
    print(f"预测结果同步完成，成功: {count}/{total}，失败: {errors}")
    return count, errors


def clear_all_data(graph_service):
    """清空 Neo4j 中的所有数据"""
    if not graph_service._driver:
        print("Neo4j 未连接，跳过清空操作")
        return
    
    print("=== 清空 Neo4j 中的所有数据 ===")
    confirm = input("确定要清空所有数据吗？(y/N): ")
    if confirm.lower() == 'y':
        with graph_service._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("数据已清空")
    else:
        print("取消清空操作")


def main():
    parser = argparse.ArgumentParser(description='历史数据回填到 Neo4j')
    parser.add_argument('--clear', action='store_true', help='先清空 Neo4j 数据')
    parser.add_argument('--batch-size', type=int, default=100, help='批量同步大小')
    args = parser.parse_args()
    
    print("=" * 60)
    print("历史数据回填脚本")
    print("=" * 60)
    
    try:
        graph_service = RootCauseGraphService()
        if graph_service.available:
            print(f"Neo4j 连接状态: 已连接")
        else:
            print(f"Neo4j 连接状态: 未连接（将使用降级模式）")
    except Exception as e:
        print(f"初始化图服务失败: {str(e)}")
        sys.exit(1)
    
    if args.clear:
        clear_all_data(graph_service)
    
    print("\n" + "=" * 60)
    print("开始同步数据...")
    print("=" * 60)
    
    results = []
    results.append(("设备", sync_all_devices(graph_service, args.batch_size)))
    results.append(("告警", sync_all_alarms(graph_service, args.batch_size)))
    results.append(("告警事件", sync_all_alarm_events(graph_service, args.batch_size)))
    results.append(("状态日志", sync_all_status_logs(graph_service, args.batch_size)))
    results.append(("预测结果", sync_all_predictions(graph_service, args.batch_size)))
    
    print("\n" + "=" * 60)
    print("同步完成！")
    print("=" * 60)
    total_success = 0
    total_errors = 0
    for name, (success, errors) in results:
        print(f"{name}: 成功 {success} 条, 失败 {errors} 条")
        total_success += success
        total_errors += errors
    
    print(f"\n总计: 成功 {total_success} 条, 失败 {total_errors} 条")
    print("\n提示：同步完成后，可通过 Neo4j Browser (http://localhost:7474) 查看图谱")


if __name__ == '__main__':
    main()