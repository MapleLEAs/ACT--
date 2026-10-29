<template>
  <div class="alarm-center-container">
    <!-- 顶部标题栏 -->
    <div class="page-header">
      <div class="header-left">
        <h1>告警中心</h1>
        <el-tag type="danger" effect="dark" size="small" class="alarm-count-tag">
          {{ overview.active_count }} 个待处理
        </el-tag>
      </div>
      <div class="header-right">
        <el-button @click="fetchData" :loading="loading"><AppIcon name="refresh" />刷新</el-button>
      </div>
    </div>

    <!-- 概览卡片 -->
    <div class="overview-cards">
      <div class="stat-card critical">
        <div class="stat-icon"><AppIcon name="warning" /></div>
        <div class="stat-content">
          <div class="stat-value">{{ overview.critical_count }}</div>
          <div class="stat-label">严重故障</div>
        </div>
      </div>
      <div class="stat-card error">
        <div class="stat-icon"><AppIcon name="close" /></div>
        <div class="stat-content">
          <div class="stat-value">{{ overview.error_count }}</div>
          <div class="stat-label">重要故障</div>
        </div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon"><AppIcon name="warning" /></div>
        <div class="stat-content">
          <div class="stat-value">{{ overview.warning_count }}</div>
          <div class="stat-label">次要告警</div>
        </div>
      </div>
      <div class="stat-card info">
        <div class="stat-icon"><AppIcon name="info" /></div>
        <div class="stat-content">
          <div class="stat-value">{{ overview.resolved_today }}</div>
          <div class="stat-label">今日已解决</div>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-select v-model="filters.status" placeholder="告警状态" size="default" clearable style="width: 140px">
          <el-option label="全部" :value="null" />
          <el-option label="待处理" value="OPEN" />
          <el-option label="已确认" value="ACK" />
          <el-option label="已处理" value="CLEAR" />
        </el-select>
        <el-select v-model="filters.severity" placeholder="严重级别" size="default" clearable style="width: 140px">
          <el-option label="全部" :value="null" />
          <el-option label="严重" value="CRITICAL" />
          <el-option label="重要" value="ERROR" />
          <el-option label="次要" value="WARN" />
          <el-option label="一般" value="INFO" />
        </el-select>
        <el-select v-model="filters.device_id" placeholder="所属设备" size="default" clearable style="width: 200px">
          <el-option label="全部设备" :value="null" />
          <el-option v-for="dev in devices" :key="dev.device_id" :label="dev.name" :value="dev.device_id" />
        </el-select>
      </div>
      <div class="filter-right">
        <el-button type="primary" @click="handleBatchAck"><AppIcon name="check" /> 批量确认</el-button>
      </div>
    </div>

    <!-- 告警列表 -->
    <div class="table-wrapper">
      <el-table 
        :data="filteredAlarms" 
        v-loading="loading" 
        stripe
        row-key="id"
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="trigger_time" label="触发时间" width="180" sortable>
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.trigger_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="device" label="设备名称" width="160">
          <template #default="{ row }">
            <el-link type="primary" :underline="false">
              <AppIcon name="device" style="margin-right:5px" />
              {{ row.device?.name || '未知设备' }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" effect="dark" size="small">
              {{ getSeverityText(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rule" label="告警规则" min-width="200">
          <template #default="{ row }">
            <span class="rule-text">
              {{ row.rule?.name || '自定义规则' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="告警内容" min-width="240" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'OPEN'" 
              type="primary" 
              size="small" 
              link
              @click="handleAck(row)"
            >
              <AppIcon name="check" /> 确认
            </el-button>
            <el-button 
              v-if="['OPEN', 'ACK'].includes(row.status)" 
              type="success" 
              size="small" 
              link
              @click="handleClear(row)"
            >
              <AppIcon name="check" /> 处理
            </el-button>
            <el-button type="info" size="small" link @click="handleDetail(row)">
              <AppIcon name="document" /> 详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="alarms.length"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>
    </div>

    <!-- 告警详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="告警详情"
      width="700px"
    >
      <div v-if="currentAlarm" class="alarm-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="告警ID">{{ currentAlarm.id }}</el-descriptions-item>
          <el-descriptions-item label="触发时间">{{ formatTime(currentAlarm.trigger_time) }}</el-descriptions-item>
          <el-descriptions-item label="设备">{{ currentAlarm.device?.name }}</el-descriptions-item>
          <el-descriptions-item label="告警规则">{{ currentAlarm.rule?.name }}</el-descriptions-item>
          <el-descriptions-item label="严重级别">
            <el-tag :type="getSeverityType(currentAlarm.severity)" effect="dark">{{ getSeverityText(currentAlarm.severity) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="getStatusType(currentAlarm.status)">{{ getStatusText(currentAlarm.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="告警描述" :span="2">{{ currentAlarm.message }}</el-descriptions-item>
          <el-descriptions-item label="备注信息" :span="2">{{ currentAlarm.remark || '无' }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDevices, getAlarms, acknowledgeAlarm, clearAlarm } from '@/api/device'

// 状态
const loading = ref(false)
const devices = ref<any[]>([])
const alarms = ref<any[]>([])
const selectedRows = ref<any[]>([])
const currentAlarm = ref<any>(null)
const detailVisible = ref(false)

// 筛选
const filters = ref({
  status: null as string | null,
  severity: null as string | null,
  device_id: null as string | null,
})

// 分页
const pagination = ref({
  page: 1,
  size: 20
})

// 概览数据
const overview = ref({
  critical_count: 0,
  error_count: 0,
  warning_count: 0,
  active_count: 0,
  resolved_today: 0
})

// 计算属性：筛选后的告警
const filteredAlarms = computed(() => {
  let result = [...alarms.value]
  
  if (filters.value.status) {
    result = result.filter(a => a.status === filters.value.status)
  }
  
  if (filters.value.severity) {
    result = result.filter(a => a.severity === filters.value.severity)
  }
  
  if (filters.value.device_id) {
    result = result.filter(a => a.device?.device_id === filters.value.device_id)
  }
  
  // 分页模拟
  const start = (pagination.value.page - 1) * pagination.value.size
  const end = start + pagination.value.size
  return result.slice(start, end)
})

// 工具函数
const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

const getSeverityType = (s: string) => {
  const map: any = { CRITICAL: 'danger', ERROR: 'danger', WARN: 'warning', INFO: 'info' }
  return map[s] || 'info'
}

const getSeverityText = (s: string) => {
  const map: any = { CRITICAL: '严重', ERROR: '重要', WARN: '次要', INFO: '一般' }
  return map[s] || s
}

const getStatusType = (s: string) => {
  const map: any = { OPEN: 'danger', ACK: 'warning', CLEAR: 'success' }
  return map[s] || 'info'
}

const getStatusText = (s: string) => {
  const map: any = { OPEN: '待处理', ACK: '已确认', CLEAR: '已处理' }
  return map[s] || s
}

// 数据获取
const fetchData = async () => {
  loading.value = true
  try {
    const [devRes, alarmRes] = await Promise.all([getDevices(), getAlarms()])
    devices.value = (devRes as any).results || devRes
    alarms.value = ((alarmRes as any).results || alarmRes).sort((a: any, b: any) => 
      new Date(b.trigger_time).getTime() - new Date(a.trigger_time).getTime()
    )
    
    // 计算概览数据
    overview.value = {
      critical_count: alarms.value.filter(a => a.severity === 'CRITICAL' && a.status !== 'CLEAR').length,
      error_count: alarms.value.filter(a => a.severity === 'ERROR' && a.status !== 'CLEAR').length,
      warning_count: alarms.value.filter(a => a.severity === 'WARN' && a.status !== 'CLEAR').length,
      active_count: alarms.value.filter(a => a.status !== 'CLEAR').length,
      resolved_today: alarms.value.filter(a => {
        const today = new Date().toDateString()
        return a.status === 'CLEAR' && new Date(a.trigger_time).toDateString() === today
      }).length
    }
  } catch (e) {
    ElMessage.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

// 操作函数
const handleSelectionChange = (rows: any[]) => {
  selectedRows.value = rows
}

const handleAck = async (row: any) => {
  try {
    await acknowledgeAlarm(row.id)
    ElMessage.success('告警已确认')
    fetchData()
  } catch (e) {
    ElMessage.error('确认失败')
  }
}

const handleClear = async (row: any) => {
  try {
    await ElMessageBox.confirm('确认该告警已处理完毕？', '处理告警', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await clearAlarm(row.id)
    ElMessage.success('告警已处理')
    fetchData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('处理失败')
  }
}

const handleBatchAck = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要确认的告警')
    return
  }
  try {
    await Promise.all(selectedRows.value.map(r => acknowledgeAlarm(r.id)))
    ElMessage.success(`已确认 ${selectedRows.value.length} 条告警`)
    fetchData()
  } catch (e) {
    ElMessage.error('批量确认失败')
  }
}

const handleDetail = (row: any) => {
  currentAlarm.value = row
  detailVisible.value = true
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.alarm-center-container {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #1f2937;
}

.alarm-count-tag {
  font-weight: bold;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border-left: 4px solid;
}

.stat-card.critical { border-left-color: #f5222d; }
.stat-card.error { border-left-color: #faad14; }
.stat-card.warning { border-left-color: #1890ff; }
.stat-card.info { border-left-color: #52c41a; }

.stat-icon {
  font-size: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-card.critical .stat-icon { color: #f5222d; }
.stat-card.error .stat-icon { color: #faad14; }
.stat-card.warning .stat-icon { color: #1890ff; }
.stat-card.info .stat-icon { color: #52c41a; }

.stat-content { flex: 1; }
.stat-value { font-size: 28px; font-weight: bold; color: #1f2937; }
.stat-label { font-size: 14px; color: #6b7280; margin-top: 4px; }

.filter-bar {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.table-wrapper {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.time-text { color: #6b7280; font-family: 'Monaco', 'Consolas', monospace; }
.rule-text { color: #4b5563; }

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.alarm-detail {
  padding: 10px 0;
}
</style>
