"""
民航设备标准阈值配置
基于：
  - ICAO Annex 10 Volume I (2023)
  - ICAO Annex 10 Volume V
  - ICAO Doc 9718-2 (2022)
  - 中国民航 CAAC 《民用航空通信导航监视工作规则》
  - 用户提供的后台观察阈值实测数据
"""
from typing import Dict, Any


STANDARD_THRESHOLDS: Dict[str, Dict[str, Dict[str, Any]]] = {
    # =========================================================================
    # VHF - 甚高频通信设备
    # =========================================================================
    'VHF': {
        'signal_strength': {
            'name': '信号强度',
            'unit': 'dBm',
            'standard_min': -107.0,
            'standard_max': -60.0,
            'warning_low': -100.0,
            'warning_high': -70.0,
            'critical_low': -107.0,
            'critical_high': -90.0,
            'source': '厂家手册',
        },
        'power_voltage': {
            'name': '电源电压',
            'unit': 'V',
            'standard_min': 198.0,
            'standard_max': 242.0,
            'warning_low': 210.0,
            'warning_high': 230.0,
            'critical_low': 198.0,
            'critical_high': 242.0,
            'source': '厂家手册',
        },
        'temperature': {
            'name': '运行温度',
            'unit': '℃',
            'standard_min': -10.0,
            'standard_max': 55.0,
            'warning_low': 0.0,
            'warning_high': 50.0,
            'critical_low': -10.0,
            'critical_high': 55.0,
            'source': 'GB/T 2423/厂家',
        },
        'vswr': {
            'name': '驻波比',
            'unit': '',
            'standard_min': None,
            'standard_max': 3.0,
            'warning_low': None,
            'warning_high': 2.0,
            'critical_low': None,
            'critical_high': 3.0,
            'source': '新西兰CAA',
        },
        'link_status': {
            'name': '链路状态',
            'unit': '',
            'normal_value': 'CONNECTED',
            'alarm_value': 'DISCONNECTED',
            'source': '监控定义',
        }
    },

    # =========================================================================
    # ILS - 仪表着陆系统
    # =========================================================================
    'ILS': {
        'signal_power': {
            'name': '信号功率',
            'unit': 'dBm',
            'standard_min': -90.0,
            'standard_max': -75.0,
            'warning_low': -85.0,
            'warning_high': -80.0,
            'critical_low': -90.0,
            'critical_high': -75.0,
            'source': 'ICAO Annex10 Vol I',
        },
        'power_voltage': {
            'name': '电源电压',
            'unit': 'V',
            'standard_min': 198.0,
            'standard_max': 242.0,
            'warning_low': 210.0,
            'warning_high': 230.0,
            'critical_low': 198.0,
            'critical_high': 242.0,
            'source': '厂家手册',
        },
        'temperature': {
            'name': '运行温度',
            'unit': '℃',
            'standard_min': -10.0,
            'standard_max': 55.0,
            'warning_low': 0.0,
            'warning_high': 50.0,
            'critical_low': -10.0,
            'critical_high': 55.0,
            'source': 'GB/T 2423/厂家',
        },
        'loc_ddm': {
            'name': 'LOC引导偏差(DDM)',
            'unit': '',
            'standard_min': 0.001,
            'standard_max': 0.005,
            'warning_low': 0.002,
            'warning_high': 0.004,
            'critical_low': 0.001,
            'critical_high': 0.005,
            'source': '飞行校验技术要求',
        },
        'gs_ddm': {
            'name': 'GS下滑偏差(DDM)',
            'unit': '',
            'standard_min': 0.001,
            'standard_max': 0.004,
            'warning_low': 0.0015,
            'warning_high': 0.0035,
            'critical_low': 0.001,
            'critical_high': 0.004,
            'source': '飞行校验技术要求',
        },
        'link_status': {
            'name': '链路状态',
            'unit': '',
            'normal_value': 'CONNECTED',
            'alarm_value': 'DISCONNECTED',
            'source': '监控定义',
        }
    },

    # =========================================================================
    # VOR - 全向信标
    # =========================================================================
    'VOR': {
        'bearing_error': {
            'name': '方位角误差',
            'unit': '°',
            'standard_min': -1.0,
            'standard_max': 1.0,
            'warning_low': -0.5,
            'warning_high': 0.5,
            'critical_low': -1.0,
            'critical_high': 1.0,
            'source': 'ICAO Annex 10',
        },
        'rf_power': {
            'name': '射频功率',
            'unit': 'W',
            'standard_min_ratio': 0.9,
            'standard_max_ratio': 1.1,
            'warning_low_ratio': 0.9,
            'warning_high_ratio': 1.1,
            'critical_low_ratio': 0.8,
            'critical_high_ratio': 1.2,
            'source': '按设备型号填写',
        },
        'modulation_diff': {
            'name': '调制度差(MD)',
            'unit': '%',
            'standard_min': 28.0,
            'standard_max': 32.0,
            'warning_low': 29.0,
            'warning_high': 31.0,
            'critical_low': 27.0,
            'critical_high': 33.0,
            'source': '标准为30%',
        },
        'vswr': {
            'name': '驻波比',
            'unit': '',
            'standard_min': None,
            'standard_max': 1.5,
            'warning_low': None,
            'warning_high': 2.0,
            'critical_low': None,
            'critical_high': 3.0,
            'source': '＞3:1触发告警',
        },
        'power_voltage': {
            'name': '电源电压',
            'unit': 'V',
            'standard_min': 198.0,
            'standard_max': 242.0,
            'warning_low': 210.0,
            'warning_high': 230.0,
            'critical_low': 198.0,
            'critical_high': 242.0,
            'source': '市电标准',
        },
        'temperature': {
            'name': '运行温度',
            'unit': '℃',
            'standard_min': -10.0,
            'standard_max': 55.0,
            'warning_low': 0.0,
            'warning_high': 50.0,
            'critical_low': -10.0,
            'critical_high': 55.0,
            'source': '工业通用范围',
        },
        'link_status': {
            'name': '链路状态',
            'unit': '',
            'normal_value': 'CONNECTED',
            'alarm_value': 'DISCONNECTED',
            'source': '断开即告警',
        }
    },

    # =========================================================================
    # DME - 测距仪
    # =========================================================================
    'DME': {
        'reply_efficiency': {
            'name': '应答效率',
            'unit': '%',
            'standard_min': 90.0,
            'standard_max': 100.0,
            'warning_low': 75.0,
            'warning_high': 100.0,
            'critical_low': 70.0,
            'critical_high': 100.0,
            'source': '低于70%触发告警',
        },
        'transmit_power': {
            'name': '发射功率',
            'unit': 'W',
            'standard_min_ratio': 0.9,
            'standard_max_ratio': 1.1,
            'warning_low_ratio': 0.85,
            'warning_high_ratio': 1.15,
            'critical_low_ratio': 0.7,
            'critical_high_ratio': 1.3,
            'source': '典型100–1000W',
        },
        'pulse_interval_x': {
            'name': '脉冲间隔(X模式)',
            'unit': 'μs',
            'standard_min': 11.9,
            'standard_max': 12.1,
            'warning_low': 11.95,
            'warning_high': 12.05,
            'critical_low': 11.9,
            'critical_high': 12.1,
            'source': '标准12μs',
        },
        'pulse_interval_y': {
            'name': '脉冲间隔(Y模式)',
            'unit': 'μs',
            'standard_min': 35.9,
            'standard_max': 36.1,
            'warning_low': 35.95,
            'warning_high': 36.05,
            'critical_low': 35.9,
            'critical_high': 36.1,
            'source': '标准36μs',
        },
        'vswr': {
            'name': '驻波比',
            'unit': '',
            'standard_min': None,
            'standard_max': 1.5,
            'warning_low': None,
            'warning_high': 2.0,
            'critical_low': None,
            'critical_high': 3.0,
            'source': '＞3:1触发告警',
        },
        'power_voltage': {
            'name': '电源电压',
            'unit': 'V',
            'standard_min': 198.0,
            'standard_max': 242.0,
            'warning_low': 210.0,
            'warning_high': 230.0,
            'critical_low': 198.0,
            'critical_high': 242.0,
            'source': '市电标准',
        },
        'temperature': {
            'name': '运行温度',
            'unit': '℃',
            'standard_min': -10.0,
            'standard_max': 55.0,
            'warning_low': 0.0,
            'warning_high': 50.0,
            'critical_low': -10.0,
            'critical_high': 55.0,
            'source': '工业通用范围',
        },
        'link_status': {
            'name': '链路状态',
            'unit': '',
            'normal_value': 'CONNECTED',
            'alarm_value': 'DISCONNECTED',
            'source': '断开即告警',
        }
    },

    # =========================================================================
    # HF - 短波通信设备
    # =========================================================================
    'HF': {
        'transmit_pep': {
            'name': '发射功率(PEP)',
            'unit': 'W',
            'standard_min_ratio': 0.9,
            'standard_max_ratio': 1.1,
            'warning_low_ratio': 0.85,
            'warning_high_ratio': 1.15,
            'critical_low_ratio': 0.7,
            'critical_high_ratio': 1.3,
            'source': '典型100–400W',
        },
        'work_frequency': {
            'name': '工作频率',
            'unit': 'MHz',
            'standard_min': 2.0,
            'standard_max': 30.0,
            'warning_low': None,
            'warning_high': None,
            'critical_low': 2.0,
            'critical_high': 30.0,
            'source': '民航HF通信频段',
        },
        'vswr': {
            'name': '驻波比',
            'unit': '',
            'standard_min': None,
            'standard_max': 1.5,
            'warning_low': None,
            'warning_high': 2.0,
            'critical_low': None,
            'critical_high': 3.0,
            'source': '＞3:1触发告警',
        },
        'power_voltage': {
            'name': '电源电压',
            'unit': 'V',
            'standard_min': 198.0,
            'standard_max': 242.0,
            'warning_low': 210.0,
            'warning_high': 230.0,
            'critical_low': 198.0,
            'critical_high': 242.0,
            'source': '市电标准',
        },
        'temperature': {
            'name': '运行温度',
            'unit': '℃',
            'standard_min': -10.0,
            'standard_max': 55.0,
            'warning_low': 0.0,
            'warning_high': 50.0,
            'critical_low': -10.0,
            'critical_high': 55.0,
            'source': '工业通用范围',
        },
        'link_status': {
            'name': '链路状态',
            'unit': '',
            'normal_value': 'CONNECTED',
            'alarm_value': 'DISCONNECTED',
            'source': '断开即告警',
        }
    }
}


def get_standard_threshold(device_type: str, metric: str) -> Dict[str, Any]:
    """获取指定设备类型和指标的标准阈值"""
    if device_type not in STANDARD_THRESHOLDS:
        return {}
    if metric not in STANDARD_THRESHOLDS[device_type]:
        return {}
    return STANDARD_THRESHOLDS[device_type][metric]


def get_all_thresholds_for_device(device_type: str) -> Dict[str, Dict[str, Any]]:
    """获取指定设备类型的所有阈值配置"""
    return STANDARD_THRESHOLDS.get(device_type, {})
