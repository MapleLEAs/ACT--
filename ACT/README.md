# 空管设备数据集中分析系统的设计与实现（ATC Monitor）

本项目是一个基于 Django + Vue 3 的空管设备数据集中分析系统的设计与实现（ATC Monitor），支持设备状态实时采集、动态告警触发、NGSI-LD 标准数据输出以及 WebSocket 实时通知。

## 📁 目录结构

- `/atc_monitor`: Django 项目核心配置文件
- `/monitor`: 业务逻辑模块（设备管理、告警引擎、状态日志）
- `/core`: 通用核心功能（抽象模型、NGSI-LD 转换器、渲染器）
- `/frontend`: 基于 Vite + Vue 3 + TypeScript 的前端基础框架
- `/static/ngsi-ld`: NGSI-LD 上下文定义文件

## 🚀 核心功能

1. **设备管理**: 支持多种设备类型（VHF, ILS），管理基础资产信息。
2. **实时监控**: 记录设备状态时序数据，追踪电源、温度、信号等物理量。
3. **高级告警引擎**: 
   - 动态规则：支持通过后台配置阈值和逻辑运算符（>, <, abs> 等）。
   - 状态追踪：告警全生命周期记录（触发、确认、清除）。
   - 实时通知：集成 WebSocket，告警产生时前端即时弹出提醒。
4. **NGSI-LD 集成**: 完全符合 ETSI 标准的 JSON-LD 数据输出，支持跨系统互操作。
5. **数据库支持**: 已优化为 MySQL 数据库，支持大规模数据存储。

## 🛠️ 快速开始

### 后端 (Django)
1. 安装依赖：`pip install -r requirements.txt`
2. 创建 MySQL 数据库：`atc_monitor_db`
3. 修改 `atc_monitor/settings.py` 中的数据库密码。
4. 执行迁移：`python manage.py migrate`
5. 启动服务：`python manage.py runserver`

### 前端 (Vue 3)
1. 进入目录：`cd frontend`
2. 安装依赖：`npm install`
3. 启动开发服务器：`npm run dev`

## 📄 文档说明

更多详细文档请参考：
- [后端开发指南](./docs/backend_dev.md)
- [前端开发指南](./docs/frontend_dev.md)
- [API 联调说明](./docs/api_guide.md)
