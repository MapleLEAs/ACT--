# 后端开发指南 (Backend Development)

本指南旨在为后端开发人员提供有关 ATC Monitor 系统架构和关键逻辑的深入了解。

## ⚙️ 环境配置

- **Python**: 3.10+
- **Django**: 4.1.5 / 6.0.3 (当前更新至 6.0.3 以支持 Channels)
- **数据库**: MySQL 8.0+
- **消息层 (可选)**: Redis (生产环境建议)

### 数据库连接设置
数据库连接在 `atc_monitor/settings.py` 中定义。请确保字符集使用 `utf8mb4`。

## 🏗️ 核心逻辑

### 1. 告警引擎 (Alarm Engine)
系统不再硬编码告警阈值，而是通过 `AlarmRule` 模型动态管理。
- **触发点**: 位于 `monitor/views.py` 的 `DeviceStatusLogViewSet.perform_create` 方法中。
- **匹配流程**: 采集数据进入 -> 筛选当前设备适用的规则 -> 运算比较 -> 触发 `Alarm`。
- **性能优化**: 启用了 `cache.get('alarm_rules_cache')` 以减少数据库查询。

### 2. NGSI-LD 转换 (NGSI-LD Converter)
`core/ngsi_ld.py` 是将 Django 模型转换为标准 NGSI-LD 格式的核心类。
- **支持实体**: `Device`, `Alarm`, `DeviceStatus`。
- **关联模型**: 通过 `Relationship` 类型定义实体间的引用关系。

### 3. WebSocket 实时推送
使用 Django Channels 框架实现。
- **ASGI**: `atc_monitor/asgi.py` 负责分发 HTTP 和 WebSocket 请求。
- **Consumer**: `monitor/consumers.py` 处理 `notifications` 组的广播。

## 🧪 接口测试
项目根目录下包含 `test_api.py` (如果有) 或可通过 Django Admin 直接录入测试数据。
推荐使用 Postman 导入 `api_guide.md` 中的示例进行联调。
