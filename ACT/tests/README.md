# ATC监控系统 - 测试文档

## 📋 测试概述

本测试套件为ATC监控系统提供全面的测试覆盖，包括单元测试、集成测试、压力测试，确保业务逻辑在迭代中不被破坏。

## 🧪 测试类型

### 1. 单元测试 (Unit Tests)
**文件位置**: `monitor/tests.py`

**覆盖范围**:
- 设备模型 (Device Model)
- 告警规则模型 (AlarmRule Model)
- 设备状态日志模型 (DeviceStatusLog Model)
- 告警模型 (Alarm Model)
- 告警事件模型 (AlarmEvent Model)
- 告警通知模型 (AlarmNotification Model)
- 序列化器 (Serializers)
- 业务逻辑 (Business Logic)

### 2. 集成测试 (Integration Tests)
**文件位置**: `tests/integration_tests.py`

**覆盖范围**:
- 认证流程 (Authentication)
- 设备管理 (Device Management)
- 告警规则管理 (Alarm Rule Management)
- 设备状态日志 (Device Status Logs)
- 告警操作 (Alarm Operations)
- NGSI-LD端点 (NGSI-LD Endpoints)
- 端到端工作流 (End-to-End Workflow)
- 错误处理 (Error Handling)

### 3. 压力测试 (Stress Tests)
**文件位置**: `tests/stress_test.py`

**测试场景**:
- 基础API压力测试
  - 获取设备列表
  - 创建状态日志
  - 并发请求测试
- 算法性能测试
  - 趋势分析算法性能
  - 预测模型响应时间

## 🚀 快速开始

### 运行测试套件工具

推荐使用 `tests/run_tests.py` 工具运行各类测试：

- **运行所有测试**:
  ```bash
  python tests/run_tests.py --all
  ```

- **运行特定测试**:
  - 单元测试: `python tests/run_tests.py --unit`
  - 集成测试: `python tests/run_tests.py --integration`
  - 压力测试: `python tests/run_tests.py --stress`

## 📊 测试指标

### 压力测试等级评估
- 平均响应时间 < 100ms: ⭐⭐⭐⭐⭐ 优秀
- 平均响应时间 < 300ms: ⭐⭐⭐⭐ 良好
- 平均响应时间 < 500ms: ⭐⭐⭐ 一般
- 平均响应时间 < 1000ms: ⭐⭐ 较慢
- 平均响应时间 >= 1000ms: ⭐ 需要优化

## 📁 测试文件结构

```
tests/
├── README.md              # 测试文档
├── 测试文档.md            # 详细测试文档
├── integration_tests.py   # 集成测试
├── stress_test.py         # 压力测试
├── run_tests.py           # 测试运行工具
└── __pycache__/           # 缓存文件
```

## 📝 详细文档

详细测试文档请参考 `测试文档.md` 文件，包含：
- 测试团队核心职责
- 设备阈值参考
- 告警规则配置指南
- 测试流程
- 测试注意事项
- 持续集成建议
