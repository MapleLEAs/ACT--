<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>欢迎使用</span>
            </div>
          </template>
          <div class="welcome-content">
            <h1>空管设备数据集中分析系统的设计与实现（ATC Monitor）</h1>
            <p>这是为您搭建的前端基础框架，已集成了以下技术栈：</p>
            <ul>
              <li>Vite (构建工具)</li>
              <li>Vue 3 (Composition API)</li>
              <li>TypeScript (类型安全)</li>
              <li>Vue Router (路由管理)</li>
              <li>Pinia (状态管理)</li>
              <li>Element Plus (UI 组件库)</li>
              <li>Axios (网络请求)</li>
              <li>Three.js (3D 可视化)</li>
              <li>WebSocket (实时同步)</li>
            </ul>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>3D 实时状态演示 (Three.js + WebSocket)</span>
            </div>
          </template>
          <ThreeVisualizer />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import ThreeVisualizer from './ThreeVisualizer.vue';
</script>

<style scoped>
.home {
  padding: 20px;
}
.welcome-content {
  line-height: 1.8;
}
ul {
  margin-top: 20px;
}
li {
  margin-bottom: 10px;
}
</style>
