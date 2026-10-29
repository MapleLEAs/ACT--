<!-- src/views/AlarmCenter/AlarmCenter.vue -->
<template>
  <div class="alarm-center">
    <!-- 告警中心的公共部分，比如标签页导航 -->
    <div class="alarm-tabs">
      <router-link to="/alarm-center/list" class="tab-link">告警列表</router-link>
      <router-link to="/alarm-center/confirmation" class="tab-link">告警确认</router-link>
      
    </div>
    
    <!-- 子路由出口 -->
    <router-view />
  </div>
</template>

<script setup>
// 告警中心主容器逻辑
</script>

<style scoped>
.alarm-center {
  padding: 20px;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.alarm-tabs {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e8e8e8;
}

.tab-link {
  padding: 8px 16px;
  color: #5C6E8D;
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.3s;
}

.tab-link:hover {
  background-color: #f0f2f5;
  color: #165dff;
}

.tab-link.router-link-active {
  background-color: #5C6E8D;
  color: #fff;
}
</style>