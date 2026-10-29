<template>
  <el-container class="layout-container">
    <el-aside width="200px">
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><AppIcon name="dashboard" /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/realtime-monitor">
          <el-icon><AppIcon name="realtime-monitor" /></el-icon>
          <span>实时监控 (3D)</span>
        </el-menu-item>
        <el-menu-item index="/devices">
          <el-icon><AppIcon name="device" /></el-icon>
          <span>设备管理</span>
        </el-menu-item>
        <el-sub-menu index="/alarm-center">
          <template #title>
            <el-icon><AppIcon name="alarm" /></el-icon>
            <span>告警中心</span>
          </template>

          <el-menu-item index="/alarm-center/list">
            <span>告警列表</span>
          </el-menu-item>
          <el-menu-item index="/alarm-center/handling">
            <span>告警处理</span>
          </el-menu-item>
          <el-menu-item index="/alarm-center/confirmation">
            <span>告警确认</span>
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/operation-management">
          <el-icon><AppIcon name="ops" /></el-icon>
          <span>运维管理</span>
        </el-menu-item>
        <el-menu-item index="/data-analysis">
          <el-icon><AppIcon name="data-analysis" /></el-icon>
          <span>数据分析</span>
        </el-menu-item>
        <el-menu-item index="/root-cause-analysis">
          <el-icon><AppIcon name="root-cause" /></el-icon>
          <span>根因分析</span>
        </el-menu-item>
        <el-menu-item index="/ngsi-exchange">
          <el-icon><AppIcon name="ngsi-exchange" /></el-icon>
          <span>NGSI-LD 数据交换</span>
        </el-menu-item>
        <el-menu-item index="/database">
          <el-icon><AppIcon name="database" /></el-icon>
          <span>数据库可视化</span>
        </el-menu-item>
        <!-- 新增文档资源管理菜单 -->
        <el-menu-item index="/file-classify">
          <el-icon><AppIcon name="document" /></el-icon>
          <span>文档资源管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <div class="header-content">
          <span>空管设备数据集中分析系统的设计与实现（ATC Monitor）</span>
        </div>
      </el-header>
      <el-main class="main-content-wrapper">
        <router-view v-slot="{ Component }">
          <!-- 优化：增加 keep-alive 缓存，避免频繁切换导致页面重绘和数据丢失 -->
          <keep-alive>
            <component :is="Component" v-if="$route.meta.keepAlive" />
          </keep-alive>
          <component :is="Component" v-if="!$route.meta.keepAlive" />
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()

const activeMenu = computed(() => {
  return route.path
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background-color: #f0f2f5;
}

.el-aside {
  background-color: #304156;
  color: #fff;
  overflow-y: auto;
}

.el-menu {
  border-right: none;
  background-color: transparent;
}

:deep(.el-menu-item) {
  color: #bfcbd9;
}

:deep(.el-menu-item.is-active) {
  color: var(--atc-primary);
  background-color: #263445;
}

:deep(.el-sub-menu__title) {
  color: #bfcbd9;
}

:deep(.el-sub-menu__title:hover) {
  background-color: #263445;
}

.el-header {
  background-color: #ffffff;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  z-index: 10;
}

.header-content {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.main-content-wrapper {
  padding: 20px;
  background-color: #f0f2f5;
  height: calc(100vh - 60px);
  overflow-y: auto;
  box-sizing: border-box;
}

@media screen and (max-width: 768px) {
  .layout-container {
    flex-direction: column;
  }

  .el-aside {
    width: 100% !important;
    height: auto !important;
    position: static !important;
  }

  .el-menu {
    display: flex;
    overflow-x: auto;
    white-space: nowrap;
  }

  :deep(.el-menu-item),
  :deep(.el-sub-menu__title) {
    padding: 0 12px !important;
  }

  .main-content-wrapper {
    width: 100% !important;
    padding: 12px !important;
    height: auto;
    min-height: calc(100vh - 60px);
    overflow-x: hidden;
  }
}
</style>