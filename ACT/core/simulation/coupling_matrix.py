from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from .exception_handler import CouplingCalculationError, ExceptionHandler


@dataclass
class CouplingEffect:
    signal_interference: float = 0.0
    thermal_coupling: float = 0.0
    signal_coupling: float = 0.0
    navigation_coupling: float = 0.0
    fault_propagation: float = 0.0
    env_coupling: float = 0.0
    status_sync: bool = False


class DeviceCouplingMatrix:
    """
    设备耦合关系矩阵
    定义设备间的耦合影响因子，支持系统级联动建模
    异常处理策略：耦合计算异常时降级为单设备模式
    """

    def __init__(self):
        self.coupling_matrix: Dict[Tuple[str, str], CouplingEffect] = {}
        self.exception_handler = ExceptionHandler()
        self._initialize_default_coupling()

    def _initialize_default_coupling(self):
        """初始化默认耦合关系矩阵"""
        # VHF设备间信号干扰
        self.add_coupling('VHF-001', 'VHF-002', signal_interference=0.15, thermal_coupling=0.08)
        self.add_coupling('VHF-001', 'VHF-003', signal_interference=0.10, thermal_coupling=0.05)
        self.add_coupling('VHF-002', 'VHF-003', signal_interference=0.12, thermal_coupling=0.06)

        # ILS与导航设备关联
        self.add_coupling('ILS-001', 'DME-001', signal_coupling=0.20, status_sync=True)
        self.add_coupling('ILS-002', 'VOR-001', navigation_coupling=0.25, fault_propagation=0.12)
        self.add_coupling('ILS-001', 'VOR-001', navigation_coupling=0.18, fault_propagation=0.08)

        # VOR与DME关联
        self.add_coupling('VOR-001', 'DME-001', signal_coupling=0.15, status_sync=True)
        self.add_coupling('VOR-002', 'DME-002', signal_coupling=0.15, status_sync=True)

        # HF设备关联
        self.add_coupling('HF-001', 'HF-002', signal_interference=0.05, thermal_coupling=0.03)

    def add_coupling(self, source: str, target: str, **kwargs):
        """
        添加耦合关系
        :param source: 源设备ID
        :param target: 目标设备ID
        :param kwargs: 耦合参数
        """
        effect = CouplingEffect(**kwargs)
        self.coupling_matrix[(source, target)] = effect

    def get_coupling_effect(self, source: str, target: str) -> CouplingEffect:
        """
        获取耦合影响
        :param source: 源设备ID
        :param target: 目标设备ID
        :return: 耦合影响对象
        """
        return self.coupling_matrix.get((source, target), CouplingEffect())

    def get_coupled_devices(self, device_id: str) -> List[Dict[str, Any]]:
        """
        获取与指定设备耦合的所有设备
        :param device_id: 设备ID
        :return: 耦合设备列表
        """
        coupled = []
        for (source, target), effect in self.coupling_matrix.items():
            if source == device_id:
                coupled.append({
                    'device_id': target,
                    'relationship': 'affects',
                    'effect': effect.__dict__
                })
            elif target == device_id:
                coupled.append({
                    'device_id': source,
                    'relationship': 'affected_by',
                    'effect': effect.__dict__
                })
        return coupled

    def calculate_system_effect(self, source_device: str, source_state: Dict[str, Any],
                               target_device: str) -> Dict[str, float]:
        """
        计算系统级耦合影响
        异常处理策略：耦合计算异常时降级为单设备模式，记录警告日志
        :param source_device: 源设备ID
        :param source_state: 源设备状态
        :param target_device: 目标设备ID
        :return: 影响字典
        """
        try:
            if not source_device or not target_device:
                raise CouplingCalculationError(
                    code='INVALID_DEVICE_ID',
                    message=f'无效设备ID: source={source_device}, target={target_device}'
                )
            
            if not isinstance(source_state, dict):
                raise CouplingCalculationError(
                    code='INVALID_STATE',
                    message=f'源设备状态格式错误: {type(source_state)}'
                )
            
            effect = self.get_coupling_effect(source_device, target_device)
            
            effects = {}
            
            if effect.signal_interference > 0:
                effects['signal_drop'] = source_state.get('temperature', 0) * effect.signal_interference * 0.1
            
            if effect.thermal_coupling > 0:
                effects['temp_rise'] = source_state.get('temperature', 0) * effect.thermal_coupling * 0.05
            
            if effect.fault_propagation > 0 and source_state.get('fault', False):
                effects['fault_probability'] = effect.fault_propagation
            
            return effects
            
        except CouplingCalculationError as e:
            self.exception_handler.log_error('coupling_error', e)
            self.exception_handler.handle_coupling_error(e)
            return {'status': 'degraded', 'mode': 'single_device', 'error': e.message}
        except Exception as e:
            self.exception_handler.log_error('coupling_error', CouplingCalculationError(
                code='UNKNOWN_ERROR',
                message=f'耦合计算异常: {str(e)}'
            ))
            return {'status': 'degraded', 'mode': 'single_device', 'error': str(e)}

    def get_matrix_data(self) -> List[Dict[str, Any]]:
        """
        获取矩阵数据（用于可视化）
        :return: 矩阵数据列表
        """
        data = []
        for (source, target), effect in self.coupling_matrix.items():
            data.append({
                'source': source,
                'target': target,
                'signal_interference': effect.signal_interference,
                'thermal_coupling': effect.thermal_coupling,
                'signal_coupling': effect.signal_coupling,
                'navigation_coupling': effect.navigation_coupling,
                'fault_propagation': effect.fault_propagation,
                'env_coupling': effect.env_coupling,
                'status_sync': effect.status_sync
            })
        return data
