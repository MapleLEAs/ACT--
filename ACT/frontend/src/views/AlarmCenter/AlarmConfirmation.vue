<template>
  <div class="alarm-handling-container">
    <!-- 顶部标题 -->
    <div class="page-header">
      <div class="header-left">
        <h1>告警处理中心</h1>
        <div class="stats-bar">
          <div class="stat-item">
            <span class="stat-label">今日告警</span>
            <span class="stat-value">{{ stats.today_total }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-label">待处理</span>
            <span class="stat-value highlight">{{ stats.pending }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-label">已处理</span>
            <span class="stat-value">{{ stats.cleared_today }}</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <el-button @click="fetchData" :loading="loading" circle><AppIcon name="refresh" /></el-button>
      </div>
    </div>

    <!-- 标签页 -->
    <div class="tabs-container">
      <div 
        v-for="tab in tabs" 
        :key="tab.key"
        class="tab-item"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
        <span v-if="stats[tab.countKey]" class="tab-count">{{ stats[tab.countKey] }}</span>
      </div>
    </div>

    <!-- 筛选与操作 -->
    <div class="filter-container">
      <div class="filter-left">
        <el-select 
          v-model="filters.severity" 
          placeholder="告警级别" 
          clearable 
          class="filter-select"
        >
          <el-option label="全部级别" :value="null" />
          <el-option label="严重" value="CRITICAL" />
          <el-option label="重要" value="ERROR" />
          <el-option label="次要" value="WARN" />
          <el-option label="一般" value="INFO" />
        </el-select>
        <el-select 
          v-model="filters.device_type" 
          placeholder="设备类型" 
          clearable 
          class="filter-select"
        >
          <el-option label="全部设备" :value="null" />
          <el-option label="VHF" value="VHF" />
          <el-option label="ILS" value="ILS" />
          <el-option label="VOR" value="VOR" />
          <el-option label="DME" value="DME" />
          <el-option label="HF" value="HF" />
        </el-select>
        <el-input
          v-model="filters.keyword"
          placeholder="搜索设备或规则"
          clearable
          class="filter-search"
        >
          <template #prefix>
            <el-icon><AppIcon name="search" /></el-icon>
          </template>
        </el-input>
      </div>
      <div class="filter-right">
        <el-button 
          v-if="activeTab === 'OPEN'"
          type="primary" 
          size="small"
          @click="handleBatchAck"
          :disabled="selectedAlarms.length === 0"
        >
          <AppIcon name="check" /> 批量确认
        </el-button>
        <el-button 
          v-if="activeTab === 'ACK'"
          type="primary" 
          size="small"
          @click="handleBatchClear"
          :disabled="selectedAlarms.length === 0"
        >
          <AppIcon name="check" /> 批量处理
        </el-button>
      </div>
    </div>

    <!-- 告警列表 -->
    <div class="table-container">
      <el-table
        :data="currentAlarms"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        :row-class-name="getRowClassName"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column label="时间" width="130">
          <template #default="{ row }">
            <div class="time-cell">
              <span class="time-main">{{ formatShortTime(row.trigger_time) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="设备与告警" min-width="260">
          <template #default="{ row }">
            <div class="device-alarm-cell">
              <div class="device-line">
                <span class="device-type">{{ row.device?.device_type || '-' }}</span>
                <span class="device-name">{{ row.device?.name || '未知设备' }}</span>
              </div>
              <div class="alarm-line">{{ row.rule?.name || '自定义规则' }}{{ row.message ? ': ' + row.message : '' }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="级别" width="90">
          <template #default="{ row }">
            <span :class="['severity-dot', row.severity?.toLowerCase()]"></span>
            <span class="severity-text">{{ getSeverityText(row.severity) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="85">
          <template #default="{ row }">
            <span :class="['status-tag', row.status?.toLowerCase()]">{{ getStatusText(row.status) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="响应" width="80">
          <template #default="{ row }">
            <span v-if="row.ack_time" class="duration-text">{{ getResponseDuration(row) }}</span>
            <span v-else class="text-gray">--</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button 
                v-if="row.status === 'OPEN'"
                type="primary" 
                size="small" 
                link
                @click="openHandleDialog(row, 'ack')"
              >
                确认
              </el-button>
              <el-button 
                v-if="row.status === 'ACK'"
                type="success" 
                size="small" 
                link
                @click="openHandleDialog(row, 'clear')"
              >
                处理
              </el-button>
              <el-button 
                type="default" 
                size="small" 
                link
                @click="openDetailDialog(row)"
              >
                详情
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50]"
          :total="alarms.length"
          layout="total, prev, pager, next"
          size="small"
        />
      </div>
    </div>

    <!-- 处理操作弹窗 -->
    <el-dialog
      v-model="handleDialogVisible"
      :title="handleDialogType === 'ack' ? '确认告警' : '处理告警'"
      width="500px"
      class="simple-dialog"
    >
      <div v-if="currentAlarm" class="handle-content">
        <div class="alarm-info-row">
          <span class="label">设备:</span>
          <span class="value">{{ currentAlarm.device?.name }}</span>
        </div>
        <div class="alarm-info-row">
          <span class="label">规则:</span>
          <span class="value">{{ currentAlarm.rule?.name }}</span>
        </div>
        <div class="alarm-info-row">
          <span class="label">状态:</span>
          <span :class="['status-tag', currentAlarm.status?.toLowerCase()]">{{ getStatusText(currentAlarm.status) }}</span>
        </div>
        
        <el-form :model="handleForm" label-width="0" style="margin-top: 20px">
          <el-form-item>
            <el-input
              v-model="handleForm.remark"
              type="textarea"
              :rows="3"
              :placeholder="handleDialogType === 'ack' ? '备注（可选）' : '请描述处理措施'"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="handleDialogVisible = false" size="small">取消</el-button>
        <el-button 
          type="primary" 
          size="small"
          :loading="handleLoading"
          @click="submitHandle"
        >
          {{ handleDialogType === 'ack' ? '确认' : '完成' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="告警详情"
      width="700px"
      class="simple-dialog"
    >
      <div v-if="currentAlarm" class="detail-content">
        <el-row :gutter="24">
          <el-col :span="12">
            <div class="detail-section">
              <div class="section-title">基本信息</div>
              <div class="detail-item">
                <span class="label">告警ID</span>
                <span class="value">{{ currentAlarm.alarm_id }}</span>
              </div>
              <div class="detail-item">
                <span class="label">设备名称</span>
                <span class="value">{{ currentAlarm.device?.name }}</span>
              </div>
              <div class="detail-item">
                <span class="label">设备类型</span>
                <span class="value">{{ currentAlarm.device?.device_type }}</span>
              </div>
              <div class="detail-item">
                <span class="label">严重级别</span>
                <span class="value">
                  <span :class="['severity-dot', currentAlarm.severity?.toLowerCase()]"></span>
                  {{ getSeverityText(currentAlarm.severity) }}
                </span>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="detail-section">
              <div class="section-title">时间线</div>
              <div class="timeline-simple">
                <div class="timeline-item">
                  <div class="dot danger"></div>
                  <div class="tl-content">
                    <div class="tl-title">告警触发</div>
                    <div class="tl-time">{{ formatTime(currentAlarm.trigger_time) }}</div>
                  </div>
                </div>
                <div v-if="currentAlarm.ack_time" class="timeline-item">
                  <div class="dot warning"></div>
                  <div class="tl-content">
                    <div class="tl-title">已确认</div>
                    <div class="tl-time">{{ formatTime(currentAlarm.ack_time) }}</div>
                  </div>
                </div>
                <div v-if="currentAlarm.clear_time" class="timeline-item">
                  <div class="dot success"></div>
                  <div class="tl-content">
                    <div class="tl-title">已处理</div>
                    <div class="tl-time">{{ formatTime(currentAlarm.clear_time) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false" size="small">关闭</el-button>
        <template v-if="currentAlarm">
          <el-button v-if="currentAlarm.status === 'OPEN'" type="primary" size="small" @click="openHandleDialog(currentAlarm, 'ack')">
            确认
          </el-button>
          <el-button v-if="currentAlarm.status === 'ACK'" type="primary" size="small" @click="openHandleDialog(currentAlarm, 'clear')">
            处理
          </el-button>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAlarms, acknowledgeAlarm, clearAlarm } from '@/api/device'

const loading = ref(false)
const activeTab = ref('OPEN')
const alarms = ref<any[]>([])
const selectedAlarms = ref<any[]>([])
const currentAlarm = ref<any>(null)
const detailVisible = ref(false)
const handleDialogVisible = ref(false)
const handleDialogType = ref<'ack' | 'clear'>('ack')
const handleLoading = ref(false)

const filters = ref({
  severity: null as string | null,
  device_type: null as string | null,
  keyword: ''
})

const pagination = ref({
  page: 1,
  size: 20
})

const handleForm = ref({
  remark: ''
})

const tabs = [
  { key: 'OPEN', label: '待确认', countKey: 'pending' },
  { key: 'ACK', label: '已确认', countKey: 'acknowledged' },
  { key: 'CLEARED', label: '已处理', countKey: 'cleared' },
  { key: 'ALL', label: '全部', countKey: 'total' }
]

interface Stats {
  today_total: number
  pending: number
  acknowledged: number
  cleared: number
  cleared_today: number
  total: number
  [key: string]: number
}

const stats = ref<Stats>({
  today_total: 0,
  pending: 0,
  acknowledged: 0,
  cleared: 0,
  cleared_today: 0,
  total: 0
})

const currentAlarms = computed(() => {
  let result = [...alarms.value]
  
  if (activeTab.value !== 'ALL') {
    result = result.filter(a => a.status === activeTab.value)
  }
  
  if (filters.value.severity) {
    result = result.filter(a => a.severity === filters.value.severity)
  }
  
  if (filters.value.device_type) {
    result = result.filter(a => a.device?.device_type === filters.value.device_type)
  }
  
  if (filters.value.keyword) {
    const kw = filters.value.keyword.toLowerCase()
    result = result.filter(a => 
      a.device?.name?.toLowerCase().includes(kw) || 
      a.rule?.name?.toLowerCase().includes(kw)
    )
  }
  
  return result
})

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

const formatShortTime = (timeStr: string) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

const getSeverityText = (s: string) => {
  const map: any = { CRITICAL: '严重', ERROR: '重要', WARN: '次要', INFO: '一般' }
  return map[s] || s
}

const getStatusText = (s: string) => {
  const map: any = { OPEN: '待确认', ACK: '已确认', CLEARED: '已处理' }
  return map[s] || s
}

const getRowClassName = ({ row }: any) => {
  if (row.severity === 'CRITICAL' && row.status === 'OPEN') return 'row-critical'
  return ''
}

const getResponseDuration = (row: any) => {
  if (!row.trigger_time || !row.ack_time) return '--'
  const trigger = new Date(row.trigger_time).getTime()
  const ack = new Date(row.ack_time).getTime()
  const diffMin = Math.round((ack - trigger) / 60000)
  if (diffMin < 60) return `${diffMin}m`
  const hours = Math.floor(diffMin / 60)
  return `${hours}h`
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getAlarms()
    const data = (res as any).results || res
    alarms.value = data.sort((a: any, b: any) => 
      new Date(b.trigger_time).getTime() - new Date(a.trigger_time).getTime()
    )
    
    const today = new Date().toDateString()
    stats.value = {
      total: alarms.value.length,
      pending: alarms.value.filter(a => a.status === 'OPEN').length,
      acknowledged: alarms.value.filter(a => a.status === 'ACK').length,
      cleared: alarms.value.filter(a => a.status === 'CLEARED').length,
      today_total: alarms.value.filter(a => new Date(a.trigger_time).toDateString() === today).length,
      cleared_today: alarms.value.filter(a => 
        a.status === 'CLEARED' && a.clear_time && new Date(a.clear_time).toDateString() === today
      ).length
    }
  } catch (e) {
    ElMessage.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

const switchTab = (tab: string) => {
  activeTab.value = tab
  pagination.value.page = 1
}

const handleSelectionChange = (rows: any[]) => {
  selectedAlarms.value = rows
}

const openHandleDialog = (row: any, type: 'ack' | 'clear') => {
  currentAlarm.value = row
  handleDialogType.value = type
  handleForm.value = { remark: '' }
  handleDialogVisible.value = true
}

const openDetailDialog = (row: any) => {
  currentAlarm.value = row
  detailVisible.value = true
}

const submitHandle = async () => {
  if (!currentAlarm.value) return
  
  handleLoading.value = true
  try {
    if (handleDialogType.value === 'ack') {
      await acknowledgeAlarm(currentAlarm.value.id)
      ElMessage.success('已确认')
    } else {
      await clearAlarm(currentAlarm.value.id)
      ElMessage.success('已处理')
    }
    handleDialogVisible.value = false
    fetchData()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    handleLoading.value = false
  }
}

const handleBatchAck = async () => {
  try {
    await Promise.all(selectedAlarms.value.map(r => acknowledgeAlarm(r.id)))
    ElMessage.success(`已确认 ${selectedAlarms.value.length} 条`)
    fetchData()
  } catch (e) {
    ElMessage.error('批量操作失败')
  }
}

const handleBatchClear = async () => {
  try {
    await Promise.all(selectedAlarms.value.map(r => clearAlarm(r.id)))
    ElMessage.success(`已处理 ${selectedAlarms.value.length} 条`)
    fetchData()
  } catch (e) {
    ElMessage.error('批量操作失败')
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.alarm-handling-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left h1 {
  margin: 0 0 12px 0;
  font-size: 22px;
  font-weight: 600;
  color: #1d2129;
}

.stats-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: #86909c;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
}

.stat-value.highlight {
  color: #f53f3f;
}

.stat-divider {
  width: 1px;
  height: 28px;
  background-color: #e5e6eb;
}

.tabs-container {
  display: flex;
  gap: 32px;
  margin-bottom: 20px;
}

.tab-item {
  font-size: 14px;
  color: #86909c;
  cursor: pointer;
  position: relative;
  padding: 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.tab-item:hover {
  color: #4e5969;
}

.tab-item.active {
  color: #1677ff;
  font-weight: 500;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background-color: #1677ff;
}

.tab-count {
  font-size: 12px;
  background: #f2f3f5;
  color: #4e5969;
  padding: 0 6px;
  border-radius: 8px;
  line-height: 18px;
}

.filter-container {
  background: white;
  padding: 16px 20px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.filter-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-select {
  width: 120px;
}

.filter-search {
  width: 240px;
}

.table-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.time-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.time-main {
  font-size: 13px;
  color: #1d2129;
  font-family: 'Monaco', 'Consolas', monospace;
}

.device-alarm-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.device-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-type {
  font-size: 12px;
  color: #86909c;
  background: #f7f8fa;
  padding: 0 6px;
  border-radius: 3px;
}

.device-name {
  font-size: 14px;
  color: #1d2129;
}

.alarm-line {
  font-size: 13px;
  color: #4e5969;
}

.severity-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

.severity-dot.critical { background: #f53f3f; }
.severity-dot.error { background: #ff7d00; }
.severity-dot.warn { background: #ff7d00; }
.severity-dot.info { background: #1677ff; }

.severity-text {
  font-size: 13px;
  color: #4e5969;
}

.status-tag {
  display: inline-block;
  padding: 2px 8px;
  font-size: 12px;
  border-radius: 3px;
}

.status-tag.open {
  color: #f53f3f;
  background: #fff1f0;
}

.status-tag.ack {
  color: #ff7d00;
  background: #fff7e8;
}

.status-tag.cleared {
  color: #00b42a;
  background: #f2fff4;
}

.duration-text {
  font-size: 13px;
  color: #4e5969;
  font-family: 'Monaco', 'Consolas', monospace;
}

.text-gray {
  color: #c9cdd4;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.row-critical {
  background: #fffbfb !important;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.simple-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #e5e6eb;
  padding-bottom: 16px;
}

.handle-content {
  padding: 10px 0;
}

.alarm-info-row {
  display: flex;
  margin-bottom: 12px;
  align-items: center;
}

.alarm-info-row .label {
  width: 60px;
  color: #86909c;
  font-size: 13px;
}

.alarm-info-row .value {
  flex: 1;
  color: #1d2129;
  font-size: 14px;
}

.detail-content {
  padding: 10px 0;
}

.detail-section {
  padding: 4px 0;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f2f3f5;
}

.detail-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.detail-item .label {
  font-size: 13px;
  color: #86909c;
}

.detail-item .value {
  font-size: 13px;
  color: #1d2129;
}

.timeline-simple {
  padding-left: 8px;
}

.timeline-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  position: relative;
}

.timeline-item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 3px;
  top: 16px;
  width: 1px;
  height: calc(100% + 8px);
  background: #e5e6eb;
}

.timeline-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.timeline-item .dot.danger { background: #f53f3f; }
.timeline-item .dot.warning { background: #ff7d00; }
.timeline-item .dot.success { background: #00b42a; }

.tl-content {
  flex: 1;
}

.tl-title {
  font-size: 13px;
  color: #1d2129;
  margin-bottom: 2px;
}

.tl-time {
  font-size: 12px;
  color: #86909c;
}
</style>
