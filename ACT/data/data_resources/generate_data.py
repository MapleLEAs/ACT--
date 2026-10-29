#!/usr/bin/env python3
"""
数据生成脚本
用于生成项目前期可以使用的测试数据
包括设备基础信息和状态时序数据
"""

import os
import django
from datetime import datetime, timedelta
import random
import json
import math

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atc_monitor.settings')
django.setup()

from monitor.models import Device, DeviceStatusLog

class DataGenerator:
    """数据生成器类"""
    
    def __init__(self):
        self.devices_data = [
            {
                'device_id': 'VHF-001',
                'device_type': 'VHF',
                'device_model': 'THALES VHF-3000',
                'location': '塔台通信室',
                'manufacturer': '泰雷兹',
                'install_time': datetime(2023, 1, 15),
                'protocol_version': 'v2.1'
            },
            {
                'device_id': 'VHF-002',
                'device_type': 'VHF',
                'device_model': 'SIEMENS VHF-8000',
                'location': '终端管制室',
                'manufacturer': '西门子',
                'install_time': datetime(2022, 8, 10),
                'protocol_version': 'v1.8'
            },
            {
                'device_id': 'ILS-001',
                'device_type': 'ILS',
                'device_model': 'INDRA ILS-2000',
                'location': '跑道18L',
                'manufacturer': '因德拉',
                'install_time': datetime(2023, 5, 20),
                'protocol_version': 'v3.0'
            },
            {
                'device_id': 'ILS-002',
                'device_type': 'ILS',
                'device_model': 'THALES ILS-420',
                'location': '跑道36R',
                'manufacturer': '泰雷兹',
                'install_time': datetime(2022, 12, 5),
                'protocol_version': 'v2.5'
            }
        ]
    
    def create_devices(self):
        """创建设备基础信息"""
        created_devices = []
        
        for device_data in self.devices_data:
            device, created = Device.objects.get_or_create(
                device_id=device_data['device_id'],
                defaults=device_data
            )
            if created:
                print(f"创建设备: {device.device_id} ({device.device_type})")
            created_devices.append(device)
        
        return created_devices
    
    def generate_vhf_status(self, device, start_time, end_time, interval_minutes=5):
        """生成VHF设备状态数据"""
        status_logs = []
        current_time = start_time
        
        while current_time <= end_time:
            # 生成基础数据
            online_status = random.random() > 0.05  # 95%的概率在线
            power_voltage = random.uniform(220, 240)  # 电源电压
            device_temperature = random.uniform(30, 55)  # 运行温度
            
            # VHF专属数据
            signal_strength = random.uniform(-70, -95)  # 信号强度
            link_status = random.choice(['CONNECTED', 'DISCONNECTED']) if random.random() > 0.9 else 'CONNECTED'
            bit_error_rate = random.uniform(0, 0.01)  # 误码率
            
            # 计算告警状态
            alarm_flag = False
            device_status = 'NORMAL'
            
            if not online_status:
                device_status = 'OFFLINE'
                alarm_flag = True
            elif signal_strength < DeviceStatusLog.VHF_SIGNAL_MIN or link_status == 'DISCONNECTED':
                device_status = 'ALARM'
                alarm_flag = True
            
            # 创建状态日志
            status_log = DeviceStatusLog(
                device=device,
                online_status=online_status,
                device_status=device_status,
                alarm_flag=alarm_flag,
                collect_time=current_time,
                power_voltage=power_voltage,
                device_temperature=device_temperature,
                signal_strength=signal_strength,
                link_status=link_status,
                bit_error_rate=bit_error_rate
            )
            status_logs.append(status_log)
            
            current_time += timedelta(minutes=interval_minutes)
        
        return status_logs
    
    def generate_ils_status(self, device, start_time, end_time, interval_minutes=5):
        """生成ILS设备状态数据"""
        status_logs = []
        current_time = start_time
        
        while current_time <= end_time:
            # 生成基础数据
            online_status = random.random() > 0.05  # 95%的概率在线
            power_voltage = random.uniform(220, 240)  # 电源电压
            device_temperature = random.uniform(30, 55)  # 运行温度
            
            # ILS专属数据
            loc_guidance_deviation = random.uniform(-2.0, 2.0)  # LOC引导偏差
            gs_guidance_deviation = random.uniform(-1.0, 1.0)  # GS下滑偏差
            signal_power = random.uniform(8, 15)  # 信号功率
            antenna_swr = random.uniform(1.0, 1.5)  # 天线驻波比
            
            # 计算告警状态
            alarm_flag = False
            device_status = 'NORMAL'
            
            if not online_status:
                device_status = 'OFFLINE'
                alarm_flag = True
            elif abs(loc_guidance_deviation) > DeviceStatusLog.ILS_LOC_DEV_MAX or signal_power < DeviceStatusLog.ILS_POWER_MIN:
                device_status = 'ALARM'
                alarm_flag = True
            
            # 创建状态日志
            status_log = DeviceStatusLog(
                device=device,
                online_status=online_status,
                device_status=device_status,
                alarm_flag=alarm_flag,
                collect_time=current_time,
                power_voltage=power_voltage,
                device_temperature=device_temperature,
                loc_guidance_deviation=loc_guidance_deviation,
                gs_guidance_deviation=gs_guidance_deviation,
                signal_power=signal_power,
                antenna_swr=antenna_swr
            )
            status_logs.append(status_log)
            
            current_time += timedelta(minutes=interval_minutes)
        
        return status_logs
    
    def generate_status_data(self, devices, days=7):
        """生成状态时序数据 (基于四维耦合统一模型)"""
        import sys
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        from monitor.simulation.coupling_model import ATCCouplingModel
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 初始化设备地理位置 (为了耦合模型)
        for i, device in enumerate(devices):
            device.position_x = i * 1000.0  # 简单拉开距离
            device.position_y = i * 500.0
            device.save()
            
        coupling_model = ATCCouplingModel(devices)
        all_status_logs = []
        
        current_time = start_time
        interval_minutes = 5
        
        print("基于四维耦合模型生成状态数据...")
        while current_time <= end_time:
            # 模拟环境变化 (如昼夜温度循环、流量高峰)
            hour = current_time.hour
            env_temp = 20.0 + 10.0 * math.sin(math.pi * (hour - 6) / 12)  # 昼夜温差
            
            # 流量高峰 (早上9点，晚上8点)
            if 8 <= hour <= 10 or 19 <= hour <= 21:
                traffic_pressure = 0.8
            else:
                traffic_pressure = 0.4
                
            env_state = {
                'env_temp': env_temp,
                'traffic_pressure': traffic_pressure,
                'interference_level': random.uniform(0.05, 0.2)
            }
            
            # 步进演化所有设备状态
            new_states = coupling_model.step(env_state)
            
            for device in devices:
                state = new_states[device.device_id]
                
                # 提取状态并转换为对应的模型字段
                online_status = not state["fault"]
                device_status = 'ALARM' if state["fault"] else 'NORMAL'
                alarm_flag = state["fault"]
                
                log_kwargs = {
                    'device': device,
                    'online_status': online_status,
                    'device_status': device_status,
                    'alarm_flag': alarm_flag,
                    'collect_time': current_time,
                    'power_voltage': state["voltage"],
                    'device_temperature': state["temperature"],
                }
                
                if device.device_type == 'VHF':
                    log_kwargs.update({
                        'signal_strength': state["signal_strength"],
                        'link_status': 'DISCONNECTED' if alarm_flag else 'CONNECTED',
                        'bit_error_rate': random.uniform(0, 0.05) if alarm_flag else random.uniform(0, 0.001)
                    })
                elif device.device_type == 'ILS':
                    log_kwargs.update({
                        'signal_power': 10.0 + state["signal_strength"] * 0.1,  # 映射到 ILS 功率范围
                        'loc_guidance_deviation': random.uniform(-0.005, 0.005),
                        'gs_guidance_deviation': random.uniform(-0.004, 0.004),
                        'antenna_swr': random.uniform(1.0, 1.5)
                    })
                else:
                    log_kwargs.update({
                        'signal_strength': state["signal_strength"],
                    })
                    
                status_log = DeviceStatusLog(**log_kwargs)
                all_status_logs.append(status_log)
                
            current_time += timedelta(minutes=interval_minutes)
        
        # 批量创建数据
        if all_status_logs:
            batch_size = 500
            for i in range(0, len(all_status_logs), batch_size):
                batch = all_status_logs[i:i+batch_size]
                DeviceStatusLog.objects.bulk_create(batch)
                print(f"创建状态日志: {min(i+batch_size, len(all_status_logs))}/{len(all_status_logs)}", end='\r')
        
        print("\n状态数据生成完成")
        return len(all_status_logs)
    
    def clear_data(self):
        """清空现有数据"""
        print("清空现有数据...")
        DeviceStatusLog.objects.all().delete()
        Device.objects.all().delete()
        print("数据清空完成")
    
    def export_device_info(self, output_file):
        """导出设备信息到JSON文件"""
        devices = Device.objects.all()
        device_list = []
        
        for device in devices:
            device_info = {
                'device_id': device.device_id,
                'device_type': device.device_type,
                'device_model': device.device_model,
                'location': device.location,
                'manufacturer': device.manufacturer,
                'install_time': device.install_time.isoformat() if device.install_time else None,
                'protocol_version': device.protocol_version
            }
            device_list.append(device_info)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(device_list, f, ensure_ascii=False, indent=2)
        
        print(f"设备信息已导出到: {output_file}")

def main():
    """主函数"""
    print("开始生成数据...")
    
    generator = DataGenerator()
    
    # 清空现有数据
    generator.clear_data()
    
    # 创建设备
    devices = generator.create_devices()
    
    # 生成状态数据
    status_count = generator.generate_status_data(devices)
    
    # 导出设备信息
    output_file = os.path.join(os.path.dirname(__file__), 'device_info.json')
    generator.export_device_info(output_file)
    
    print("\n数据生成完成！")
    print(f"创建设备数量: {len(devices)}")
    print(f"生成状态日志数量: {status_count}")
    print(f"设备信息已导出到: {output_file}")

if __name__ == '__main__':
    main()
