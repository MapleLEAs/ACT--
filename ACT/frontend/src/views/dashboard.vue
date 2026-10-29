<template>
  <div class="dashboard-container">
    <main class="content">
      <!-- 顶部数据概览卡片 -->
      <div class="stat-cards">
        <el-card class="stat-card" shadow="hover">
          <div class="card-content">
            <div class="icon blue">
              <el-icon><AppIcon name="device" /></el-icon>
            </div>
            <div class="text">
              <div class="label">设备总数</div>
              <div class="value">{{ stats.totalDevices }} 台</div>
            </div>
          </div>
        </el-card>

        <el-card class="stat-card" shadow="hover">
          <div class="card-content">
            <div class="icon green">
              <el-icon><AppIcon name="check" /></el-icon>
            </div>
            <div class="text">
              <div class="label">在线设备</div>
              <div class="value">{{ stats.onlineDevices }} 台</div>
            </div>
          </div>
        </el-card>

        <el-card class="stat-card" shadow="hover">
          <div class="card-content">
            <div class="icon orange">
              <el-icon><AppIcon name="data-analysis" /></el-icon>
            </div>
            <div class="text">
              <div class="label">系统运行率</div>
              <div class="value">{{ stats.operationRate }}%</div>
            </div>
          </div>
        </el-card>

        <el-card class="stat-card" shadow="hover">
          <div class="card-content">
            <div class="icon red">
              <el-icon><AppIcon name="warning" /></el-icon>
            </div>
            <div class="text">
              <div class="label">今日告警</div>
              <div class="value">{{ stats.todayAlerts }} 次</div>
            </div>
          </div>
        </el-card>
      </div>

      <el-row :gutter="20">
        <!-- 左侧图表区域 -->
        <el-col :span="16">
          <el-card class="chart-card main-chart" shadow="never">
            <template #header>
              <div class="card-header">
                <span>设备运行趋势 (24h)</span>
                <el-radio-group v-model="trendMetric" size="small" @change="loadDeviceTrendData">
                  <el-radio-button label="device_temperature">温度</el-radio-button>
                  <el-radio-button label="signal_strength">信号</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            <div id="trendChart" class="chart"></div>
          </el-card>

          <el-card class="recent-alarms-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>最近告警事件</span>
                <el-button link type="primary" @click="$router.push('/alarm-center')">查看全部</el-button>
              </div>
            </template>
            <el-table :data="recentAlarms" size="small" style="width: 100%">
              <el-table-column prop="raised_at" label="时间" width="160">
                <template #default="{ row }">
                  {{ formatTime(row.raised_at) }}
                </template>
              </el-table-column>
              <el-table-column prop="device_name" label="设备" width="120" />
              <el-table-column prop="title" label="告警项" />
              <el-table-column prop="level" label="级别" width="100">
                <template #default="{ row }">
                  <el-tag :type="getSeverityTag(row.level)" size="small">
                    {{ getSeverityText(row.level) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusTag(row.status)" effect="plain" size="small">
                    {{ getStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <!-- 右侧分布统计 -->
        <el-col :span="8">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>告警级别分布</span>
              </div>
            </template>
            <div id="alarmDistributionChart" class="chart-small"></div>
          </el-card>

          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>设备类型占比</span>
              </div>
            </template>
            <div id="deviceTypeChart" class="chart-small"></div>
          </el-card>
        </el-col>
      </el-row>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { ElLoading, ElMessage } from 'element-plus'
import request from '../api/request'
import { useDataSyncStore } from '@/store/dataSync'

const dataSyncStore = useDataSyncStore()

// 响应式数据
const stats = ref({
  totalDevices: 0,
  onlineDevices: 0,
  operationRate: 0,
  todayAlerts: 0
})
const recentAlarms = ref([])
const trendMetric = ref('device_temperature')
let loading: any = null

// 图表实例
let trendChart: echarts.ECharts | null = null
let alarmDistChart: echarts.ECharts | null = null
let deviceTypeChart: echarts.ECharts | null = null
let refreshTimer: number | null = null

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', { 
    month: '2-digit', day: '2-digit', 
    hour: '2-digit', minute: '2-digit' 
  })
}

// 严重程度标签映射
const getSeverityTag = (level: string) => {
  const map: any = {
    'CRITICAL': 'danger',
    'ERROR': 'danger',
    'WARN': 'warning',
    'INFO': 'info'
  }
  return map[level] || 'info'
}

const getSeverityText = (level: string) => {
  const map: any = {
    'CRITICAL': '紧急',
    'ERROR': '重要',
    'WARN': '次要',
    'INFO': '提醒'
  }
  return map[level] || level
}

// 状态标签映射
const getStatusTag = (status: string) => {
  const map: any = {
    'OPEN': 'danger',
    'ACK': 'warning',
    'CLEARED': 'success'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: any = {
    'OPEN': '待处理',
    'ACK': '已确认',
    'CLEARED': '已恢复'
  }
  return map[status] || status
}

// 加载仪表盘数据
const loadDashboardData = async () => {
  loading = ElLoading.service({ target: '.content', text: '同步实时数据...' })
  try {
    const response = await request({
      url: '/api/dashboard/overview/',
      method: 'get'
    })
    // 此时 response 已经是 res.data 了
    const { stats: apiStats, severity_distribution, device_type_distribution, recent_alarms } = response
    
    // 1. 更新顶部卡片
    stats.value = {
      totalDevices: apiStats.total_devices || 0,
      onlineDevices: apiStats.online_devices || 0,
      operationRate: apiStats.operation_rate || 0,
      todayAlerts: apiStats.today_alarm_count || 0
    }
    
    // 2. 更新最近告警
    recentAlarms.value = recent_alarms || []
    
    // 3. 更新图表
    updateAlarmDistChart(severity_distribution)
    updateDeviceTypeChart(device_type_distribution)
    await loadDeviceTrendData()
    
  } catch (err: any) {
    ElMessage.error('数据加载失败：' + (err.message || '网络连接异常'))
  } finally {
    loading.close()
  }
}

// 加载趋势图数据
const loadDeviceTrendData = async () => {
  try {
    const response = await request({
      url: '/api/trend-analysis/',
      method: 'get',
      params: { metric: trendMetric.value }
    })
    const trendData = response.data || response
    
    if (!trendChart) return
    
    const labels = (trendData.labels || []).slice(-24)
    const values = (trendData.values || []).slice(-24)
    
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { 
        type: 'category', 
        data: labels.map(l => l.split(' ')[1]), // 只显示时间部分
        axisLabel: { fontSize: 10 }
      },
      yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [{
        name: trendMetric.value === 'device_temperature' ? '温度' : '信号强度',
        type: 'line',
        data: values,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#1890ff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0)' }
          ])
        }
      }]
    }, true)
  } catch (err: any) {
    console.error('趋势数据加载失败', err)
  }
}

// 更新告警分布图
const updateAlarmDistChart = (data: any[]) => {
  if (!alarmDistChart) return
  
  const severityMap: any = {
    'CRITICAL': { name: '紧急', color: '#f5222d' },
    'ERROR': { name: '重要', color: '#fa541c' },
    'WARN': { name: '次要', color: '#faad14' },
    'INFO': { name: '提醒', color: '#1890ff' }
  }
  
  const chartData = data.map(item => ({
    name: severityMap[item.severity]?.name || item.severity,
    value: item.count,
    itemStyle: { color: severityMap[item.severity]?.color }
  }))
  
  alarmDistChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['50%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false, position: 'center' },
      emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
      data: chartData
    }]
  })
}

// 更新设备类型图
const updateDeviceTypeChart = (data: any[]) => {
  if (!deviceTypeChart) return
  
  const chartData = data.map(item => ({
    name: item.device_type,
    value: item.count
  }))
  
  deviceTypeChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: '0%', left: 'center', icon: 'circle', itemWidth: 10 },
    series: [{
      type: 'pie',
      radius: '60%',
      center: ['50%', '45%'],
      data: chartData,
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
      }
    }]
  })
}

// 初始化所有图表
const initCharts = () => {
  const trendDom = document.getElementById('trendChart')
  const alarmDom = document.getElementById('alarmDistributionChart')
  const typeDom = document.getElementById('deviceTypeChart')
  
  if (trendDom) trendChart = echarts.init(trendDom)
  if (alarmDom) alarmDistChart = echarts.init(alarmDom)
  if (typeDom) deviceTypeChart = echarts.init(typeDom)
  
  window.addEventListener('resize', () => {
    trendChart?.resize()
    alarmDistChart?.resize()
    deviceTypeChart?.resize()
  })
}

onMounted(async () => {
  await nextTick()
  initCharts()
  await loadDashboardData()
  
  refreshTimer = window.setInterval(loadDashboardData, 60000) // 每分钟刷新一次
})

watch(() => dataSyncStore.devicesVersion, () => {
  loadDashboardData()
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  trendChart?.dispose()
  alarmDistChart?.dispose()
  deviceTypeChart?.dispose()
})
</script>

<style scoped>
.dashboard-container {
  height: 100%;
  background-color: #f5f7fa;
}

.content {
  padding: 20px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  border: none;
  border-radius: 12px;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.card-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
}

.icon.blue { background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%); }
.icon.green { background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%); }
.icon.orange { background: linear-gradient(135deg, #fa8c16 0%, #d46b08 100%); }
.icon.red { background: linear-gradient(135deg, #f5222d 0%, #cf1322 100%); }

.text .label {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.text .value {
  font-size: 24px;
  font-weight: 700;
  color: #262626;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.chart-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: none;
}

.main-chart {
  height: 400px;
}

.chart {
  height: 320px;
}

.chart-small {
  height: 240px;
}

.recent-alarms-card {
  border-radius: 12px;
  border: none;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 15px 20px;
}

:deep(.el-table) {
  --el-table-header-bg-color: #fafafa;
}
</style>
