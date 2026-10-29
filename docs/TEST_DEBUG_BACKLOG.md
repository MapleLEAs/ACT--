# 待测试/调试任务记录

> 版本: v1.0
> 日期: 2026-07-01
> 作者: ATC开发团队
> 状态: 待处理

---

## 概述

本文件记录系统优化实施过程中，需要在所有优化完成后统一进行测试和调试的任务清单。

---

## 一、Hybrid AI 预测模型体系

### 1.1 核心模块验证

| 任务ID | 任务描述 | 关联文件 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| AI-001 | `hybrid_model.py` - PhysicsModel 物理预测逻辑验证 | `ACT/core/ai/hybrid_model.py` | 高 | 待测试 |
| AI-002 | `hybrid_model.py` - AIResidualModel XGBoost残差训练验证 | `ACT/core/ai/hybrid_model.py` | 高 | 待测试 |
| AI-003 | `hybrid_model.py` - HybridPredictor 融合预测输出验证 | `ACT/core/ai/hybrid_model.py` | 高 | 待测试 |
| AI-004 | `inference.py` - InferenceEngine 实时流式推理验证 | `ACT/core/ai/inference.py` | 高 | 待测试 |
| AI-005 | `trainer.py` - train_hybrid_predictor 批量训练流水线验证 | `ACT/core/ai/trainer.py` | 高 | 待测试 |
| AI-006 | 置信区间计算精度验证 (95% CI) | `ACT/core/ai/hybrid_model.py` | 中 | 待测试 |

### 1.2 数据流转验证

| 任务ID | 任务描述 | 关联文件 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| AI-007 | DeviceStatusLog → 训练样本转换完整性 | `ACT/core/ai/trainer.py` | 高 | 待测试 |
| AI-008 | 历史序列缓冲 (deque滑动窗口) 数据正确性 | `ACT/core/ai/inference.py` | 中 | 待测试 |
| AI-009 | 预测结果写入 PredictionResult 模型验证 | `ACT/core/ai/inference.py` | 高 | 待测试 |

---

## 二、前端预测性维护仪表盘

### 2.1 数据对齐

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| FE-001 | 预测API接口对接 (后端 → 前端数据格式匹配) | NGSI-LD API / 前端组件 | 高 | 待调试 |
| FE-002 | 混合预测结果展示 (物理基础值 + AI修正值 + 置信区间) | 预测图表组件 | 高 | 待调试 |
| FE-003 | 健康度评分计算逻辑对齐 (0-100分) | 仪表盘核心指标 | 中 | 待调试 |

### 2.2 UI对接

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| FE-004 | 预测趋势图 ECharts 配置与数据绑定 | 预测性维护页面 | 高 | 待调试 |
| FE-005 | 置信区间可视化 (上下限阴影区域) | 预测图表组件 | 高 | 待调试 |
| FE-006 | 故障预警时间轴展示 | 设备详情页面 | 中 | 待调试 |
| FE-007 | 预测模型状态指示器 (已训练/未训练) | 设备状态卡片 | 低 | 待调试 |

---

## 三、四维耦合数字孪生仿真引擎

### 3.1 模块验证

| 任务ID | 任务描述 | 关联文件 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| SIM-001 | `coupling_model.py` - 耦合强度矩阵正确性验证 | `ACT/monitor/simulation/coupling_model.py` | 高 | 待测试 |
| SIM-002 | `coupling_model.py` - ODE连续微分演化数值稳定性 | `ACT/monitor/simulation/coupling_model.py` | 高 | 待测试 |
| SIM-003 | `coupling_model.py` - 状态传播图 (Graph Dynamics) 验证 | `ACT/monitor/simulation/coupling_model.py` | 中 | 待测试 |
| SIM-004 | `coupling_model.py` - NGSI-LD输出格式与FIWARE兼容性 | `ACT/monitor/simulation/coupling_model.py` | 高 | 待测试 |

### 3.2 集成验证

| 任务ID | 任务描述 | 关联文件 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| SIM-005 | `generate_data.py` 调用兼容性验证 | `ACT/data/data_resources/generate_data.py` | 高 | 已通过 |
| SIM-006 | 耦合模型与混合预测模型协同验证 | 跨模块 | 高 | 待测试 |

---

## 四、系统级数字孪生（预测-传播-联动）

### 4.1 WebSocket实时预测流

| 任务ID | 任务描述 | 关联文件 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| DT-001 | `consumers.py` - PredictConsumer 单设备预测推送 | `ACT/monitor/consumers.py` | 高 | 待测试 |
| DT-002 | `consumers.py` - 多设备联合预测 WebSocket 推送 | `ACT/monitor/consumers.py` | 高 | 待测试 |
| DT-003 | `consumers.py` - 故障传播预测 WebSocket 推送 | `ACT/monitor/consumers.py` | 高 | 待测试 |
| DT-004 | `routing.py` - WebSocket URL 配置验证 | `ACT/monitor/routing.py` | 高 | 待测试 |

### 4.2 多设备联合预测

| 任务ID | 任务描述 | 关联文件 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| DT-005 | `multi_device_predict.py` - VHF→ILS 耦合影响模型验证 | `ACT/core/ai/multi_device_predict.py` | 高 | 待测试 |
| DT-006 | `views.py` - 多设备联合预测 API 接口验证 | `ACT/monitor/views.py` | 高 | 待测试 |
| DT-007 | 系统健康度计算逻辑验证 (H_system = Σ H_i × weight_i) | `ACT/core/ai/multi_device_predict.py` | 中 | 待测试 |

### 4.3 故障传播预测

| 任务ID | 任务描述 | 关联文件 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| DT-008 | `fault_propagation.py` - 故障传播概率模型验证 | `ACT/core/ai/fault_propagation.py` | 高 | 待测试 |
| DT-009 | `fault_propagation.py` - 耦合强度矩阵正确性 | `ACT/core/ai/fault_propagation.py` | 高 | 待测试 |
| DT-010 | `views.py` - 故障传播预测 API 接口验证 | `ACT/monitor/views.py` | 高 | 待测试 |
| DT-011 | 级联故障预测完整性验证（多点故障同时传播） | `ACT/core/ai/fault_propagation.py` | 中 | 待测试 |

### 4.4 耦合矩阵 API

| 任务ID | 任务描述 | 关联文件 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| DT-012 | `views.py` - 耦合矩阵查询 API 验证 | `ACT/monitor/views.py` | 中 | 待测试 |
| DT-013 | `views.py` - 设备耦合关系查询 API 验证 | `ACT/monitor/views.py` | 中 | 待测试 |

---

## 五、NGSI-LD / FIWARE 集成

### 5.1 Context Broker 对接

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| NGSI-001 | Orion Context Broker 连接测试 | `ACT/core/ngsi_exchange.py` | 高 | 待测试 |
| NGSI-002 | Entity 创建/更新/查询 API 验证 | `ACT/core/ngsi_ld.py` | 高 | 待测试 |
| NGSI-003 | 耦合模型状态实时推送到 Context Broker | `ACT/monitor/simulation/coupling_model.py` | 高 | 待调试 |

### 5.2 语义化实体模型

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| NGSI-004 | `DeviceEntity` - Property属性添加验证 | `ACT/core/ngsi_ld/device_entity.py` | 高 | 待测试 |
| NGSI-005 | `DeviceEntity` - Relationship关系添加验证 | `ACT/core/ngsi_ld/device_entity.py` | 高 | 待测试 |
| NGSI-006 | `DeviceEntity` - GeoProperty地理属性验证 | `ACT/core/ngsi_ld/device_entity.py` | 高 | 待测试 |
| NGSI-007 | `DeviceEntity` - 耦合关系自动添加验证 | `ACT/core/ngsi_ld/device_entity.py` | 高 | 待测试 |
| NGSI-008 | `AlarmEntity` - 告警详情添加验证 | `ACT/core/ngsi_ld/alarm_entity.py` | 高 | 待测试 |
| NGSI-009 | `AlarmEntity` - 时间属性（触发/确认/清除）验证 | `ACT/core/ngsi_ld/alarm_entity.py` | 高 | 待测试 |
| NGSI-010 | `PredictionEntity` - 置信区间添加验证 | `ACT/core/ngsi_ld/prediction_entity.py` | 高 | 待测试 |
| NGSI-011 | `PredictionEntity` - 混合模型信息添加验证 | `ACT/core/ngsi_ld/prediction_entity.py` | 高 | 待测试 |
| NGSI-012 | `DeviceStatusEntity` - 状态详情添加验证 | `ACT/core/ngsi_ld/status_entity.py` | 高 | 待测试 |
| NGSI-013 | `DeviceStatusEntity` - 动态指标添加验证 | `ACT/core/ngsi_ld/status_entity.py` | 高 | 待测试 |
| NGSI-014 | `EntityFactory` - Device实体创建验证 | `ACT/core/ngsi_ld/entity_factory.py` | 高 | 待测试 |
| NGSI-015 | `EntityFactory` - Alarm实体创建验证 | `ACT/core/ngsi_ld/entity_factory.py` | 高 | 待测试 |
| NGSI-016 | `EntityFactory` - Prediction实体创建验证 | `ACT/core/ngsi_ld/entity_factory.py` | 高 | 待测试 |
| NGSI-017 | `EntityFactory` - DeviceStatus实体创建验证 | `ACT/core/ngsi_ld/entity_factory.py` | 高 | 待测试 |
| NGSI-018 | `EntityFactory` - 自动模型类型识别验证 | `ACT/core/ngsi_ld/entity_factory.py` | 中 | 待测试 |
| NGSI-019 | `NGSI_LD_Converter` - 集成新实体模型验证 | `ACT/core/ngsi_ld/converter.py` | 高 | 待测试 |
| NGSI-020 | NGSI-LD实体JSON格式完整性验证 | `ACT/core/ngsi_ld/*.py` | 高 | 待测试 |
| NGSI-021 | 设备间耦合关系语义化表达验证（interferesWith/dependsOn） | `ACT/core/ngsi_ld/device_entity.py` | 高 | 待测试 |
| NGSI-022 | 耦合关系实际设备ID参数验证 | `ACT/core/ngsi_ld/entity_factory.py` | 高 | 待测试 |

---

## 六、知识图谱模块

### 6.1 设备知识图谱

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| KG-001 | `DeviceKnowledgeGraph` - 设备节点添加验证 | `ACT/core/knowledge_graph/device_graph.py` | 高 | 待测试 |
| KG-002 | `DeviceKnowledgeGraph` - 机场节点添加验证 | `ACT/core/knowledge_graph/device_graph.py` | 高 | 待测试 |
| KG-003 | `DeviceKnowledgeGraph` - 关系添加验证（interferes/dependsOn/locatedAt） | `ACT/core/knowledge_graph/device_graph.py` | 高 | 待测试 |
| KG-004 | `DeviceKnowledgeGraph` - 从NGSI实体构建图谱验证 | `ACT/core/knowledge_graph/device_graph.py` | 高 | 待测试 |
| KG-005 | `DeviceKnowledgeGraph` - 耦合关系图构建验证 | `ACT/core/knowledge_graph/device_graph.py` | 高 | 待测试 |
| KG-006 | `DeviceKnowledgeGraph` - 干扰路径查找验证 | `ACT/core/knowledge_graph/device_graph.py` | 高 | 待测试 |
| KG-007 | `DeviceKnowledgeGraph` - 设备依赖查找验证 | `ACT/core/knowledge_graph/device_graph.py` | 高 | 待测试 |
| KG-008 | `DeviceKnowledgeGraph` - 干扰设备查找验证 | `ACT/core/knowledge_graph/device_graph.py` | 高 | 待测试 |
| KG-009 | `DeviceKnowledgeGraph` - 图谱统计信息验证 | `ACT/core/knowledge_graph/device_graph.py` | 中 | 待测试 |
| KG-010 | `DeviceKnowledgeGraph` - Cypher语句生成验证 | `ACT/core/knowledge_graph/device_graph.py` | 中 | 待测试 |

### 6.2 图服务增强

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| KG-011 | `build_coupling_graph` - 耦合图谱构建验证 | `ACT/monitor/graph_service.py` | 高 | 待测试 |
| KG-012 | `build_device_knowledge_graph` - 设备图谱构建验证 | `ACT/monitor/graph_service.py` | 高 | 待测试 |
| KG-013 | `find_interference_path` - 干扰路径API验证 | `ACT/monitor/graph_service.py` | 高 | 待测试 |
| KG-014 | `get_device_dependencies` - 设备依赖API验证 | `ACT/monitor/graph_service.py` | 高 | 待测试 |
| KG-015 | `sync_coupling_graph` - Neo4j同步验证 | `ACT/monitor/graph_service.py` | 中 | 待测试 |

### 6.3 知识图谱API

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| KG-016 | `knowledge_graph_coupling` - 耦合图谱API验证 | `ACT/monitor/views.py` | 高 | 待测试 |
| KG-017 | `knowledge_graph_devices` - 设备图谱API验证 | `ACT/monitor/views.py` | 高 | 待测试 |
| KG-018 | `knowledge_graph_path` - 干扰路径API验证 | `ACT/monitor/views.py` | 高 | 待测试 |
| KG-019 | `knowledge_graph_dependencies` - 设备依赖API验证 | `ACT/monitor/views.py` | 高 | 待测试 |
| KG-020 | `knowledge_graph_sync` - Neo4j同步API验证 | `ACT/monitor/views.py` | 中 | 待测试 |

### 6.4 Docker部署

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| KG-021 | docker-compose.yml - FIWARE Orion启动验证 | `docker-compose.yml` | 高 | 待测试 |
| KG-022 | docker-compose.yml - MongoDB连接验证 | `docker-compose.yml` | 高 | 待测试 |
| KG-023 | docker-compose.yml - Django后端连接验证 | `ACT/Dockerfile` | 高 | 待测试 |
| KG-024 | docker-compose.yml - Neo4j图数据库连接验证 | `docker-compose.yml` | 中 | 待测试 |

---

## 七、系统级耦合模拟模块

### 7.1 耦合矩阵

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| SIM-001 | `DeviceCouplingMatrix` - 默认耦合初始化验证 | `ACT/core/simulation/coupling_matrix.py` | 高 | 待测试 |
| SIM-002 | `DeviceCouplingMatrix` - 添加耦合关系验证 | `ACT/core/simulation/coupling_matrix.py` | 高 | 待测试 |
| SIM-003 | `DeviceCouplingMatrix` - 获取耦合影响验证 | `ACT/core/simulation/coupling_matrix.py` | 高 | 待测试 |
| SIM-004 | `DeviceCouplingMatrix` - 计算系统级影响验证 | `ACT/core/simulation/coupling_matrix.py` | 高 | 待测试 |

### 7.2 事件驱动生成

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| SIM-005 | `EventDrivenGenerator` - 初始化设备状态验证 | `ACT/core/simulation/event_driven_generator.py` | 高 | 待测试 |
| SIM-006 | `EventDrivenGenerator` - 正常事件处理验证 | `ACT/core/simulation/event_driven_generator.py` | 高 | 待测试 |
| SIM-007 | `EventDrivenGenerator` - 天气事件处理验证 | `ACT/core/simulation/event_driven_generator.py` | 高 | 待测试 |
| SIM-008 | `EventDrivenGenerator` - 故障事件处理验证 | `ACT/core/simulation/event_driven_generator.py` | 高 | 待测试 |
| SIM-009 | `EventDrivenGenerator` - 级联事件传播验证 | `ACT/core/simulation/event_driven_generator.py` | 高 | 待测试 |
| SIM-010 | `EventDrivenGenerator` - 故障恢复验证 | `ACT/core/simulation/event_driven_generator.py` | 高 | 待测试 |

### 7.3 空间GIS建模

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| SIM-011 | `SpatialQueryEngine` - 地理距离计算验证 | `ACT/core/simulation/spatial_model.py` | 高 | 待测试 |
| SIM-012 | `SpatialQueryEngine` - 半径范围设备查询验证 | `ACT/core/simulation/spatial_model.py` | 高 | 待测试 |
| SIM-013 | `SpatialQueryEngine` - 区域环境状态验证 | `ACT/core/simulation/spatial_model.py` | 高 | 待测试 |
| SIM-014 | `SpatialQueryEngine` - 空间可视化数据验证 | `ACT/core/simulation/spatial_model.py` | 高 | 待测试 |

### 7.4 趋势预测

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| SIM-015 | `TrendBasedPredictor` - 时间序列分解验证 | `ACT/core/simulation/trend_predictor.py` | 高 | 待测试 |
| SIM-016 | `TrendBasedPredictor` - 趋势外推验证 | `ACT/core/simulation/trend_predictor.py` | 高 | 待测试 |
| SIM-017 | `TrendBasedPredictor` - 置信区间计算验证 | `ACT/core/simulation/trend_predictor.py` | 高 | 待测试 |
| SIM-018 | `TrendBasedPredictor` - 异常概率计算验证 | `ACT/core/simulation/trend_predictor.py` | 高 | 待测试 |

### 7.5 数据分层架构

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| SIM-019 | `RealtimeDataLayer` - 实时状态推送验证 | `ACT/core/simulation/data_layers.py` | 高 | 待测试 |
| SIM-020 | `TimeSeriesDataLayer` - 时序数据存储验证 | `ACT/core/simulation/data_layers.py` | 高 | 待测试 |
| SIM-021 | `InsightDataLayer` - 洞察数据生成验证 | `ACT/core/simulation/data_layers.py` | 高 | 待测试 |
| SIM-022 | `DataLayerManager` - 三层数据流转验证 | `ACT/core/simulation/data_layers.py` | 高 | 待测试 |

### 7.6 数据质量系统

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| SIM-023 | `DataQualityEngine` - 完整性检测验证 | `ACT/core/simulation/data_quality.py` | 高 | 待测试 |
| SIM-024 | `DataQualityEngine` - 一致性检测验证 | `ACT/core/simulation/data_quality.py` | 高 | 待测试 |
| SIM-025 | `DataQualityEngine` - 时效性检测验证 | `ACT/core/simulation/data_quality.py` | 高 | 待测试 |
| SIM-026 | `DataQualityEngine` - 准确性检测验证 | `ACT/core/simulation/data_quality.py` | 高 | 待测试 |
| SIM-027 | `DataQualityEngine` - 总体质量评分验证 | `ACT/core/simulation/data_quality.py` | 高 | 待测试 |

### 7.7 级联告警传播

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| SIM-028 | `CascadeAlarmEngine` - L1设备告警触发验证 | `ACT/core/simulation/cascade_alarm.py` | 高 | 待测试 |
| SIM-029 | `CascadeAlarmEngine` - L2链路告警触发验证 | `ACT/core/simulation/cascade_alarm.py` | 高 | 待测试 |
| SIM-030 | `CascadeAlarmEngine` - L3系统告警触发验证 | `ACT/core/simulation/cascade_alarm.py` | 高 | 待测试 |
| SIM-031 | `CascadeAlarmEngine` - 告警传播链验证 | `ACT/core/simulation/cascade_alarm.py` | 高 | 待测试 |
| SIM-032 | `CascadeAlarmEngine` - 告警关联矩阵验证 | `ACT/core/simulation/cascade_alarm.py` | 高 | 待测试 |

---

## 八、数据生成API接口测试

### 8.1 数据生成接口

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| API-001 | `data_generation_devices` - 设备数据生成API验证 | `ACT/monitor/views.py` | 高 | 待测试 |
| API-002 | `data_generation_coupled_data` - 耦合数据查询API验证 | `ACT/monitor/views.py` | 高 | 待测试 |
| API-003 | `data_generation_events_trigger` - 事件触发API验证 | `ACT/monitor/views.py` | 高 | 待测试 |
| API-004 | `data_generation_spatial_regions` - 空间区域API验证 | `ACT/monitor/views.py` | 高 | 待测试 |
| API-005 | `data_generation_quality_report` - 质量报告API验证 | `ACT/monitor/views.py` | 高 | 待测试 |

### 8.2 预测数据接口

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| API-006 | `predictions_trend_analysis` - 趋势分析API验证 | `ACT/monitor/views.py` | 高 | 待测试 |

### 8.3 级联告警接口

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| API-007 | `alarm_cascade_propagation_chain` - 告警传播链API验证 | `ACT/monitor/views.py` | 高 | 待测试 |

---

## 九、异常处理策略测试

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| EXC-001 | `DeviceCouplingMatrix` - 耦合计算异常降级为单设备模式验证 | `ACT/core/simulation/coupling_matrix.py` | 高 | 待测试 |
| EXC-002 | `EventDrivenGenerator` - 事件队列溢出丢弃低优先级事件验证 | `ACT/core/simulation/event_driven_generator.py` | 高 | 待测试 |
| EXC-003 | `SpatialQueryEngine` - GIS坐标计算失败使用默认坐标验证 | `ACT/core/simulation/spatial_model.py` | 高 | 待测试 |
| EXC-004 | `TrendBasedPredictor` - 预测置信度不足标记样本不足验证 | `ACT/core/simulation/trend_predictor.py` | 高 | 待测试 |
| EXC-005 | `DataQualityEngine` - 数据质量评分过低阻断入库验证 | `ACT/core/simulation/data_quality.py` | 高 | 待测试 |
| EXC-006 | `CascadeAlarmEngine` - 级联告警传播深度上限（≤3层）验证 | `ACT/core/simulation/cascade_alarm.py` | 高 | 待测试 |
| EXC-007 | `ExceptionHandler` - 统一异常处理和错误日志验证 | `ACT/core/simulation/exception_handler.py` | 高 | 待测试 |

---

## 十、数字孪生引擎测试

| 任务ID | 任务描述 | 关联模块 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| TWIN-001 | `DigitalTwinEngine` - 数字孪生引擎主循环验证 | `ACT/monitor/data_generation/digital_twin_engine.py` | 高 | ✅ 已通过 |
| TWIN-002 | `EnvironmentState` - 环境状态日周期变化验证 | `ACT/monitor/data_generation/environment_state.py` | 高 | ✅ 已通过 |
| TWIN-003 | `DeviceSimulator` - 设备模拟器受环境影响验证 | `ACT/monitor/data_generation/device_simulator.py` | 高 | ✅ 已通过 |
| TWIN-004 | `EventBus` - 事件总线发布/订阅验证 | `ACT/monitor/data_generation/event_bus.py` | 高 | ✅ 已通过 |
| TWIN-005 | `SpatialUtils` - 空间距离计算和邻居查询验证 | `ACT/monitor/data_generation/spatial_utils.py` | 高 | ✅ 已通过 |
| TWIN-006 | `PredictionModel` - 时间序列预测验证 | `ACT/monitor/data_generation/predictor.py` | 高 | ✅ 已通过 |
| TWIN-007 | `EarlyWarningModel` - 预警模型多维度检测验证 | `ACT/monitor/data_generation/early_warning.py` | 高 | ✅ 已通过 |
| TWIN-008 | `NetworkEffects` - 设备间故障扩散验证 | `ACT/monitor/data_generation/network_effects.py` | 高 | ✅ 已通过 |

---

## 十一、测试环境准备

### 11.1 数据准备

| 任务ID | 任务描述 | 关联文件 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| ENV-001 | 运行数据生成脚本创建测试数据 | `ACT/data/data_resources/generate_data.py` | 高 | 待执行 |
| ENV-002 | 触发混合预测模型训练流水线 | `ACT/core/ai/trainer.py` | 高 | 待执行 |

### 6.2 依赖检查

| 任务ID | 任务描述 | 关联文件 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| ENV-003 | xgboost 库安装验证 | `ACT/requirements.txt` | 高 | 待确认 |
| ENV-004 | 所有 AI 相关依赖完整性检查 | `ACT/requirements.txt` | 高 | 待确认 |

---

## 七、测试执行计划

### 阶段一：单元测试

1. 验证各模块独立功能正确性
2. 执行时间：优化实施完成后立即进行

### 阶段二：集成测试

1. 验证模块间数据流转正确性
2. 执行时间：所有优化代码合并后进行

### 阶段三：端到端测试

1. 验证从数据采集 → 模型训练 → 推理预测 → 前端展示完整链路
2. 执行时间：部署到测试环境后进行

---

## 八、验收标准

### 8.1 功能验收

- [ ] 混合预测模型能够正确输出物理基础值、AI修正值和置信区间
- [ ] 推理引擎能够实时处理设备指标数据流
- [ ] 训练流水线能够自动构建样本并训练XGBoost模型
- [ ] 耦合模型输出符合NGSI-LD标准，可对接FIWARE Context Broker
- [ ] WebSocket实时预测流能够正常推送单设备/多设备/故障传播预测
- [ ] 多设备联合预测能够正确处理VHF→ILS耦合影响
- [ ] 故障传播预测能够正确计算级联故障概率
- [ ] NGSI-LD语义化实体模型能够正确表达Property/Relationship/GeoProperty
- [ ] 设备耦合关系能够通过interferesWith/dependsOn语义化表达
- [ ] EntityFactory能够从Django模型自动创建NGSI-LD实体
- [ ] 系统级耦合模拟能够正确计算设备间耦合影响
- [ ] 事件驱动模拟能够触发正常波动、天气变化、故障和级联事件
- [ ] 空间GIS建模能够计算地理距离和区域环境状态
- [ ] 趋势预测能够进行时间序列分解和置信区间计算
- [ ] 数据分层架构（L1/L2/L3）能够正常数据流转
- [ ] 数据质量引擎能够进行四维质量检测
- [ ] 级联告警引擎能够正确传播L1→L2→L3告警

### 8.2 性能验收

- [ ] 单设备推理延迟 < 100ms
- [ ] 批量训练5000样本时间 < 60秒
- [ ] 100设备并发推理稳定运行
- [ ] WebSocket连接保持稳定，支持100+客户端并发

### 8.3 可视化验收

- [ ] 预测趋势图正确显示置信区间
- [ ] 健康度评分动态更新
- [ ] 故障预警信息准确展示
- [ ] 系统级数字孪生网络拓扑可视化