# ATC Monitor 共用框架整体说明

## 1. 项目概述

ATC Monitor 共用框架是一个基于 Django + DRF 的空管设备监控系统框架，专为 VHF（甚高频通信）和 ILS（仪表着陆系统）设备的状态监控而设计。

### 核心目标
- **最小闭环验证**：实现设备识别 → 状态采集 → 状态判断 → 告警触发 → 状态展示的完整闭环
- **快速搭建**：提供开箱即用的项目结构和数据模型
- **可扩展性**：支持后续功能扩展和其他设备类型的接入

### 适用场景
- 项目前期开发和验证
- 设备监控系统原型搭建
- 空管设备状态分析
- 告警系统测试

## 2. 技术架构

### 2.1 技术栈
| 分类 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 后端框架 | Django | 4.1.5 | Web框架，提供管理界面和路由 |
| API框架 | Django REST Framework | 3.15.1 | RESTful API开发 |
| 数据库 | SQLite | 内置 | 开发环境数据库 |
| 数据库 | MySQL | 8.0+ | 生产环境数据库 |
| 前端可视化 | Chart.js | 3.9.1 | 设备状态图表展示 |
| 依赖管理 | pip | 最新版 | 包管理 |

### 2.2 架构图

```
┌─────────────────────┐
│    前端应用层       │
│  (Vue.js + ECharts) │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│    API接口层        │
│  (Django REST)      │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│    业务逻辑层        │
│  (Device + Status)  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│    数据存储层        │
│  (SQLite/MySQL)     │
└─────────────────────┘
```

## 3. 核心功能

### 3.1 设备管理
- **设备识别**：支持VHF和ILS设备的自动识别
- **设备信息管理**：存储设备基本信息，包括型号、位置、厂家等
- **设备分类**：根据设备类型（VHF/ILS）进行分类管理

### 3.2 状态监控
- **实时状态采集**：采集设备运行状态数据
- **状态判断**：根据设备类型自动判断综合状态
- **告警触发**：根据阈值条件自动触发告警
- **历史数据存储**：存储设备状态历史数据

### 3.3 告警系统
- **VHF告警**：信号强度、链路状态、温度等指标告警
- **ILS告警**：引导偏差、信号功率、设备离线等告警
- **告警标记**：在状态数据中标记告警状态
- **告警阈值配置**：可配置的告警阈值

### 3.4 数据可视化
- **状态趋势图**：设备状态变化趋势图表
- **告警展示**：红色线段标记告警触发点
- **系统概览**：设备数量、数据点、告警次数统计

### 3.5 API接口
- **设备管理API**：设备的增删改查
- **状态日志API**：状态数据的采集和查询
- **系统状态API**：框架运行状态和接口导航
- **Django Admin**：图形化管理界面

## 4. 目录结构

```
atc_monitor_framework/
├── 项目后端框架/                  # Django项目根目录
│   ├── atc_monitor/              # 项目配置目录
│   │   ├── settings.py           # 项目设置
│   │   ├── urls.py               # URL路由
│   │   └── wsgi.py               # WSGI配置
│   │
│   ├── core/                     # 核心模块
│   │   ├── models.py             # 抽象模型基类
│   │   └── views.py              # 核心视图
│   │
│   ├── monitor/                  # 监控应用
│   │   ├── models.py             # 设备和状态模型
│   │   ├── views.py              # API视图
│   │   ├── serializers.py        # 数据序列化
│   │   └── urls.py               # 应用路由
│   │
│   ├── manage.py                 # 项目管理脚本
│   ├── requirements.txt          # 依赖包配置
│   ├── generate_visual_report.py # 可视化报告生成
│   └── atc_monitor.sql           # 数据库脚本
│
├── data_resources/               # 数据资源目录
│   ├── generate_data.py          # 数据生成脚本
│   ├── README.md                 # 使用说明
│   ├── device_info.json          # 设备信息示例
│   └── FRAMEWORK_OVERVIEW.md     # 框架整体说明
│
└── 项目文件夹/                    # 项目文档目录
    ├── 技术选型.md               # 技术栈选型文档
    └── 最小闭环.md               # 最小闭环验证文档
```

## 5. 数据模型

### 5.1 设备模型 (Device)
| 字段名 | 类型 | 说明 |
|-------|------|------|
| device_id | string | 设备唯一标识 |
| device_type | string | 设备类型（VHF/ILS） |
| device_model | string | 设备型号 |
| location | string | 安装位置 |
| manufacturer | string | 生产厂家 |
| install_time | datetime | 投用时间 |
| protocol_version | string | 通信协议版本 |

### 5.2 状态日志模型 (DeviceStatusLog)

#### 通用字段
| 字段名 | 类型 | 说明 |
|-------|------|------|
| device | ForeignKey | 关联设备 |
| online_status | boolean | 在线状态 |
| device_status | string | 综合状态（NORMAL/ALARM/OFFLINE） |
| alarm_flag | boolean | 告警标识 |
| collect_time | datetime | 数据采集时间 |
| power_voltage | float | 电源电压 |
| device_temperature | float | 运行温度 |

#### VHF专属字段
| 字段名 | 类型 | 说明 | 单位 |
|-------|------|------|------|
| signal_strength | float | 信号强度 | dBm |
| link_status | string | 链路状态 | CONNECTED/DISCONNECTED |
| bit_error_rate | float | 误码率 | % |

#### ILS专属字段
| 字段名 | 类型 | 说明 | 单位 |
|-------|------|------|------|
| loc_guidance_deviation | float | LOC航向引导偏差 | ° |
| gs_guidance_deviation | float | GS下滑引导偏差 | ° |
| signal_power | float | 信号功率 | dBm |
| antenna_swr | float | 天线驻波比 | - |

### 5.3 告警阈值
| 设备类型 | 指标 | 阈值 | 单位 |
|---------|------|------|------|
| VHF | 信号强度 | < -85 | dBm |
| VHF | 温度 | > 65 | ℃ |
| VHF | 链路状态 | DISCONNECTED | - |
| ILS | 引导偏差 | > 1.5 | ° |
| ILS | 信号功率 | < 10 | dBm |
| 通用 | 在线状态 | false | - |

## 6. API接口

### 6.1 系统状态
- **URL**：`/`
- **方法**：GET
- **功能**：返回系统状态和API端点导航
- **返回格式**：JSON，包含项目信息和可用接口

### 6.2 设备管理
- **URL**：`/api/devices/`
- **方法**：GET, POST
- **功能**：获取设备列表，创建设备
- **返回格式**：JSON设备列表

- **URL**：`/api/devices/{device_id}/`
- **方法**：GET, PUT, DELETE
- **功能**：获取设备详情，更新设备信息，删除设备
- **返回格式**：JSON设备详情

### 6.3 状态日志
- **URL**：`/api/status_logs/`
- **方法**：GET, POST
- **功能**：获取状态日志列表，提交状态数据
- **返回格式**：JSON状态日志列表

- **URL**：`/api/status_logs/{id}/`
- **方法**：GET, PUT, DELETE
- **功能**：获取状态日志详情，更新状态数据，删除状态日志
- **返回格式**：JSON状态日志详情

### 6.4 管理界面
- **URL**：`/admin/`
- **功能**：Django管理后台，提供图形化管理界面
- **访问方式**：浏览器访问，需要超级用户登录

## 7. 使用方法

### 7.1 环境搭建

1. **安装依赖**
   ```powershell
   cd "项目后端框架"
   python -m pip install -r requirements.txt
   ```

2. **数据库迁移**
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **创建超级用户**（可选）
   ```powershell
   python manage.py createsuperuser
   ```

4. **启动服务**
   ```powershell
   python manage.py runserver
   ```

### 7.2 数据生成

1. **生成测试数据**
   ```powershell
   python "..\data_resources\generate_data.py"
   ```

2. **验证数据**
   - 访问 `http://127.0.0.1:8000/api/devices/` 查看设备
   - 访问 `http://127.0.0.1:8000/api/status_logs/` 查看状态数据

### 7.3 可视化报告

1. **生成可视化报告**
   ```powershell
   python generate_visual_report.py
   ```

2. **查看报告**
   - 打开 `闭环验证可视化/closed_loop_report.html`
   - 查看设备状态趋势和告警标记

### 7.4 闭环验证

1. **设备识别验证**
   - 访问 `/api/devices/` 确认设备列表返回
   - 测试设备创建功能

2. **状态采集验证**
   - 发送状态数据到 `/api/status_logs/`
   - 验证数据提交成功

3. **状态判断验证**
   - 检查 `device_status` 字段是否正确
   - 验证状态判断逻辑

4. **告警触发验证**
   - 发送超过阈值的数据
   - 验证 `alarm_flag` 是否为 true

5. **状态展示验证**
   - 查看可视化报告
   - 确认告警标记正确显示

## 8. 部署说明

### 8.1 开发环境
- **系统**：Windows 10/11
- **Python**：3.8+
- **数据库**：SQLite（内置）
- **服务启动**：`python manage.py runserver`

### 8.2 生产环境

1. **系统准备**
   - Linux服务器（Ubuntu 20.04+）
   - Python 3.8+
   - MySQL 8.0+

2. **配置修改**
   - 修改 `atc_monitor/settings.py` 中的数据库配置
   - 设置 `DEBUG = False`
   - 配置 `ALLOWED_HOSTS`

3. **部署方式**
   - **Nginx + Gunicorn**：推荐生产环境部署
   - **Docker**：容器化部署

4. **定时任务**
   - 配置定时任务采集设备状态
   - 设置告警通知机制

## 9. 扩展开发

### 9.1 新增设备类型
1. 在 `monitor/models.py` 中创建新的设备模型
2. 添加对应的状态字段和阈值
3. 在API视图中添加新设备类型的处理逻辑

### 9.2 新增状态字段
1. 在 `DeviceStatusLog` 模型中添加新字段
2. 更新序列化器和视图
3. 修改状态判断逻辑

### 9.3 自定义告警规则
1. 在 `monitor/views.py` 中修改告警判断逻辑
2. 更新阈值常量
3. 测试告警触发效果

### 9.4 集成其他系统
1. 通过API接口集成第三方系统
2. 配置Webhook接收告警通知
3. 开发数据导出功能

## 10. 常见问题

### 10.1 服务启动失败
- **问题**：`ModuleNotFoundError`
- **解决**：运行 `python -m pip install -r requirements.txt` 安装依赖

### 10.2 数据库迁移失败
- **问题**：`django.db.utils.OperationalError`
- **解决**：检查数据库连接配置，确保数据库服务正常

### 10.3 API访问返回404
- **问题**：接口路径错误
- **解决**：检查URL路径是否正确，确保服务运行中

### 10.4 告警不触发
- **问题**：告警规则未生效
- **解决**：检查阈值设置，验证状态数据是否超过阈值

### 10.5 可视化报告无数据
- **问题**：报告生成失败
- **解决**：确保已生成测试数据，检查报告生成脚本路径

## 11. 维护与支持

### 11.1 版本管理
- 代码版本：使用Git进行版本控制
- 依赖版本：在requirements.txt中固定版本

### 11.2 日志管理
- Django日志：记录系统运行状态
- 应用日志：记录业务操作和错误

### 11.3 性能优化
- 数据库索引：为常用查询字段添加索引
- 缓存策略：使用缓存减少数据库查询
- 批量操作：使用bulk_create减少数据库写入次数

### 11.4 安全考虑
- CSRF防护：Django内置CSRF防护
- 权限控制：使用Django的权限系统
- 输入验证：对API输入进行严格验证

## 12. 总结

ATC Monitor 共用框架提供了一个完整的空管设备监控系统基础，包含了设备管理、状态监控、告警触发和数据可视化等核心功能。通过这个框架，开发团队可以快速搭建项目原型，验证系统功能，并为后续的扩展开发奠定基础。

框架的设计遵循了最小闭环原则，确保了系统能够完成从设备识别到状态展示的完整流程，同时保持了良好的可扩展性，支持后续功能的持续迭代和优化。

---

**文档版本**：v1.0
**更新时间**：2026-02-24
**适用框架**：ATC Monitor v1.0
