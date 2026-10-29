<template>
  <div class="ngsi-exchange">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <AppIcon name="ngsi-exchange" class="icon-lg" />
        </div>
        <div class="header-text">
          <h1>NGSI-LD 数据交换中心</h1>
          <p class="description">标准化数据交换层 - 统一实体查询与导出</p>
        </div>
      </div>
      <div class="header-badge">
        <el-tag type="info" size="small">ETSI标准兼容</el-tag>
      </div>
    </div>

    <!-- 查询区域 -->
    <div class="query-section">
      <el-card class="query-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <AppIcon name="search" class="card-icon" />
            <span>实体查询</span>
          </div>
        </template>
        
        <div class="query-form">
          <div class="form-row">
            <div class="form-group">
              <label>实体类型</label>
              <el-select 
                v-model="queryForm.entityType" 
                placeholder="选择实体类型"
                class="select-input"
                size="large"
              >
                <el-option label="全部实体" value="" />
                <el-option label="设备 (Device)" value="Device" />
                <el-option label="设备状态 (DeviceStatus)" value="DeviceStatus" />
                <el-option label="告警 (Alarm)" value="Alarm" />
              </el-select>
            </div>

            <div class="form-group">
              <label>数量限制</label>
              <el-input 
                v-model.number="queryForm.limit" 
                type="number" 
                placeholder="数量"
                class="limit-input"
                size="large"
              />
            </div>

            <div class="form-actions">
              <el-button 
                type="primary" 
                @click="queryEntities"
                :loading="loading"
                size="large"
              >
                <AppIcon name="search" />
                查询
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 结果展示区域 -->
    <div class="result-section">
      <el-card class="result-card" shadow="hover">
        <template #header>
          <div class="result-header">
            <div class="header-left">
              <AppIcon name="ngsi-exchange" class="card-icon" />
              <span>查询结果</span>
            </div>
            <div class="result-actions">
              <span class="count">共 {{ ngsiData.length }} 条</span>
              <el-button 
                type="text" 
                @click="copyJson"
                :disabled="!ngsiData.length"
                size="small"
              >
                <el-icon><AppIcon name="copy" /></el-icon>
                复制
              </el-button>
              <el-button 
                type="text" 
                @click="downloadJson"
                :disabled="!ngsiData.length"
                size="small"
              >
                <el-icon><AppIcon name="export" /></el-icon>
                下载
              </el-button>
            </div>
          </div>
        </template>

        <div v-if="ngsiData.length">
          <pre class="json-output">{{ formattedJson }}</pre>
        </div>
        <div class="empty-state" v-else>
          <el-empty description="暂无数据，请先查询" :image-size="100" />
        </div>
      </el-card>
    </div>

    <!-- 接口文档区域 -->
    <div class="docs-section">
      <el-card class="docs-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <AppIcon name="document" class="card-icon" />
            <span>接口文档</span>
          </div>
        </template>
        
        <div class="api-docs">
          <div class="api-category">
            <h4>基础接口</h4>
            <div class="api-item">
              <span class="method get">GET</span>
              <code>/api/ngsi/</code>
              <span class="desc">API根路径，返回可用接口列表</span>
            </div>
            <div class="api-item">
              <span class="method get">GET</span>
              <code>/api/ngsi/entities/</code>
              <span class="desc">获取实体列表，支持 type/limit/offset 参数</span>
            </div>
          </div>
          
          <div class="api-category">
            <h4>设备接口</h4>
            <div class="api-item">
              <span class="method get">GET</span>
              <code>/api/ngsi/devices/{id}/</code>
              <span class="desc">获取指定设备的NGSI-LD实体</span>
            </div>
            <div class="api-item">
              <span class="method get">GET</span>
              <code>/api/ngsi/devices/{id}/status/</code>
              <span class="desc">获取设备实时状态</span>
            </div>
          </div>
          
          <div class="api-category">
            <h4>其他接口</h4>
            <div class="api-item">
              <span class="method get">GET</span>
              <code>/api/ngsi/alarms/</code>
              <span class="desc">获取所有告警的NGSI-LD实体</span>
            </div>
            <div class="api-item">
              <span class="method post">POST</span>
              <code>/api/ngsi/query/</code>
              <span class="desc">高级查询接口</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { getNgsiEntities, copyJsonToClipboard, downloadJsonFile } from '@/api/ngsi'

// 查询表单
const queryForm = ref({
  entityType: '',
  limit: 10
})

// 状态
const loading = ref(false)
const ngsiData = ref<any[]>([])

// 格式化JSON
const formattedJson = computed(() => {
  return JSON.stringify(ngsiData.value, null, 2)
})

// 查询实体
async function queryEntities() {
  loading.value = true
  try {
    ngsiData.value = await getNgsiEntities(queryForm.value.entityType || undefined, queryForm.value.limit, 0)
  } catch (error) {
    console.error('查询失败:', error)
    ngsiData.value = []
  } finally {
    loading.value = false
  }
}

// 复制JSON
async function copyJson() {
  try {
    await copyJsonToClipboard(ngsiData.value)
    alert('复制成功!')
  } catch (error) {
    console.error('复制失败:', error)
  }
}

// 下载JSON
function downloadJson() {
  downloadJsonFile(ngsiData.value, `ngsi-entities-${Date.now()}`)
}
</script>

<style scoped>
.ngsi-exchange {
  padding: 24px;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
  border-radius: 16px;
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon {
  width: 64px;
  height: 64px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-lg {
  font-size: 32px;
  color: #fff;
}

.header-text h1 {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px 0;
}

.header-text .description {
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  font-size: 14px;
}

.header-badge {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

/* 通用卡片 */
.query-card, .result-card, .docs-card {
  border-radius: 12px;
  border: none;
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.card-icon {
  color: #3b82f6;
}

/* 查询表单 */
.query-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: flex;
  gap: 20px;
  align-items: flex-end;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
}

.select-input {
  min-width: 200px;
}

.limit-input {
  width: 120px;
}

.form-actions {
  display: flex;
  gap: 12px;
}

/* 结果区域 */
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.count {
  color: #6b7280;
  font-size: 14px;
}

/* JSON输出 */
.json-output {
  background: #0f172a;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
  max-height: 500px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 空状态 */
.empty-state {
  padding: 40px;
}

/* 接口文档 */
.api-docs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.api-category h4 {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e5e7eb;
}

.api-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 8px;
}

.method {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  align-self: flex-start;
}

.method.get {
  background: #dcfce7;
  color: #16a34a;
}

.method.post {
  background: #dbeafe;
  color: #2563eb;
}

.api-item code {
  font-family: 'Monaco', monospace;
  font-size: 13px;
  color: #1e293b;
  font-weight: 500;
}

.api-item .desc {
  font-size: 12px;
  color: #64748b;
}
</style>
