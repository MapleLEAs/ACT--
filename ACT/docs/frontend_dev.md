# 前端开发指南 (Frontend Development)

本指南旨在为前端开发人员提供有关 ATC Monitor 系统前端基础框架的详细说明。

## 🏗️ 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite 6.0.0+
- **状态管理**: Pinia 3.0.4+
- **路由**: Vue Router 5.0.3+
- **UI 组件库**: Element Plus 2.13.3+
- **网络请求**: Axios 1.13.6+
- **类型系统**: TypeScript 5.9.3+

## 📁 目录结构

- `src/api`: Axios 封装和业务 API 请求（如 `device.ts`, `request.ts`）。
- `src/layout`: 全局布局组件（如 `MainLayout.vue`）。
- `src/views`: 页面视图（如 `DeviceList.vue`, `HomeView.vue`）。
- `src/router`: 路由定义和导航守卫。
- `src/store`: Pinia 状态库定义。
- `src/api/websocket.ts`: WebSocket 连接逻辑封装。

## ⚙️ 关键配置

### 1. Vite 代理 (vite.config.ts)
- 已配置 `/api` 代理到后端 `http://127.0.0.1:8000/api/`。
- 已配置 `/ws` 代理到后端 `ws://127.0.0.1:8000/ws/`，并启用了 `ws: true`。

### 2. WebSocket 实时通知
- 系统会在 `MainLayout.vue` 中自动启动 WebSocket 连接。
- 当监听到 `ALARM_TRIGGERED` 消息时，使用 `ElNotification` 弹出右下角提醒。

### 3. TypeScript 别名
- 使用 `@` 指向 `src` 目录，例如 `import '@/api/request'`。

## 🚀 启动与构建

1. 安装依赖: `npm install`
2. 启动开发服务器: `npm run dev`
3. 生产环境构建: `npm run build`

## 💡 页面开发建议

- **设备管理**: 参照 `DeviceList.vue` 的实现，它集成了数据加载、加载动画和 Element Plus 表格。
- **样式冲突**: 所有的全局样式定义在 `src/style.css` 中，已清理了 Vite 默认模板中可能导致布局错乱的居中样式。
- **图标**: 已全局注册 `@element-plus/icons-vue`，可直接在模板中使用 `<Odometer />` 等图标组件。
