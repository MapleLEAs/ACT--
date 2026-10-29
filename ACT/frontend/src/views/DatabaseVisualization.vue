<template>
  <div class="database-visualization">
    <div class="page-header">
      <div>
        <h1>数据库可视化</h1>
        <p class="subtitle">统一查看设备、告警、日志和表结构分布</p>
      </div>
      <el-button @click="fetchData" :loading="loading">
        <el-icon><AppIcon name="refresh" /></el-icon>
        刷新数据
      </el-button>
    </div>

    <div v-if="stats" class="stats-overview">
      <div class="stat-card">
        <div class="stat-value">{{ stats.devices?.total || 0 }}</div>
        <div class="stat-label">设备总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.alarms?.total || 0 }}</div>
        <div class="stat-label">告警总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.logs?.total || 0 }}</div>
        <div class="stat-label">状态日志</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.rules?.total || 0 }}</div>
        <div class="stat-label">规则总数</div>
      </div>
    </div>

    <div class="charts-container">
      <div class="chart-card">
        <div class="chart-title">设备类型分布</div>
        <div ref="deviceTypeChartRef" class="chart"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">告警状态分布</div>
        <div ref="alarmStatusChartRef" class="chart"></div>
      </div>
      <div class="chart-card full-width">
        <div class="chart-title">数据增长趋势（最近 30 天）</div>
        <div ref="growthChartRef" class="chart"></div>
      </div>
      <div class="chart-card full-width">
        <div class="chart-title">数据库表结构</div>
        <div class="table-schema">
          <div
            v-for="table in schema?.tables || []"
            :key="table.name"
            class="table-card"
          >
            <div class="table-header">
              <span class="table-name">{{ table.verbose_name }}</span>
              <el-tag size="small" type="info">{{ table.count }} 条</el-tag>
            </div>
            <div class="table-fields">
              <div v-for="field in table.fields" :key="field.name" class="field-item">
                <span class="field-name">{{ field.verbose_name }}</span>
                <div class="field-meta">
                  <span class="field-type">{{ field.type }}</span>
                  <span v-if="field.primary_key" class="field-pk">PK</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { getDatabaseSchema, getDatabaseStats } from '@/api/device'

type DatabaseStats = {
  devices?: {
    total: number
    by_type: Array<{ device_type: string; count: number }>
  }
  alarms?: {
    total: number
    open: number
    ack: number
    cleared: number
  }
  logs?: { total: number }
  rules?: { total: number }
  growth_trend?: Array<{ date: string; devices: number; alarms: number; logs: number }>
}

const loading = ref(false)
const stats = ref<DatabaseStats | null>(null)
const schema = ref<{ tables: Array<any> } | null>(null)
const deviceTypeChartRef = ref<HTMLElement | null>(null)
const alarmStatusChartRef = ref<HTMLElement | null>(null)
const growthChartRef = ref<HTMLElement | null>(null)

let deviceTypeChart: ECharts | null = null
let alarmStatusChart: ECharts | null = null
let growthChart: ECharts | null = null

const resizeCharts = () => {
  deviceTypeChart?.resize()
  alarmStatusChart?.resize()
  growthChart?.resize()
}

const disposeCharts = () => {
  deviceTypeChart?.dispose()
  alarmStatusChart?.dispose()
  growthChart?.dispose()
  deviceTypeChart = null
  alarmStatusChart = null
  growthChart = null
}

const renderCharts = () => {
  if (!stats.value) return

  if (deviceTypeChartRef.value) {
    deviceTypeChart ??= echarts.init(deviceTypeChartRef.value)
    deviceTypeChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [
        {
          name: '设备类型',
          type: 'pie',
          radius: ['42%', '70%'],
          avoidLabelOverlap: true,
          label: { formatter: '{b}: {c}' },
          data: (stats.value.devices?.by_type || []).map((item) => ({
            name: item.device_type,
            value: item.count,
          })),
        },
      ],
    })
  }

  if (alarmStatusChartRef.value) {
    alarmStatusChart ??= echarts.init(alarmStatusChartRef.value)
    alarmStatusChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 36, right: 16, top: 24, bottom: 24 },
      xAxis: {
        type: 'category',
        data: ['待确认', '已确认', '已处理'],
        axisTick: { show: false },
      },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef1f5' } } },
      series: [
        {
          type: 'bar',
          barWidth: 36,
          itemStyle: {
            borderRadius: [8, 8, 0, 0],
            color: (params: any) => ['#ef4444', '#f59e0b', '#22c55e'][params.dataIndex],
          },
          data: [
            stats.value.alarms?.open || 0,
            stats.value.alarms?.ack || 0,
            stats.value.alarms?.cleared || 0,
          ],
        },
      ],
    })
  }

  if (growthChartRef.value) {
    growthChart ??= echarts.init(growthChartRef.value)
    growthChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { top: 0, data: ['设备', '告警', '日志'] },
      grid: { left: 36, right: 16, top: 44, bottom: 24 },
      xAxis: {
        type: 'category',
        data: (stats.value.growth_trend || []).map((item) => item.date),
      },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef1f5' } } },
      series: [
        {
          name: '设备',
          type: 'line',
          smooth: true,
          data: (stats.value.growth_trend || []).map((item) => item.devices),
        },
        {
          name: '告警',
          type: 'line',
          smooth: true,
          data: (stats.value.growth_trend || []).map((item) => item.alarms),
        },
        {
          name: '日志',
          type: 'line',
          smooth: true,
          data: (stats.value.growth_trend || []).map((item) => item.logs),
        },
      ],
    })
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const [statsRes, schemaRes] = await Promise.all([getDatabaseStats(), getDatabaseSchema()]) as [any, any]
    stats.value = statsRes
    schema.value = schemaRes
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
})
</script>

<style scoped>
.database-visualization {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1d2129;
}

.subtitle {
  margin: 6px 0 0;
  color: #86909c;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  padding: 24px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: #1890ff;
}

.stat-label {
  font-size: 14px;
  color: #86909c;
  margin-top: 8px;
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.chart-card.full-width {
  grid-column: span 2;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 16px;
}

.chart {
  width: 100%;
  height: 300px;
}

.table-schema {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.table-card {
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f7f8fa;
  border-bottom: 1px solid #e5e6eb;
}

.table-name {
  font-weight: 600;
  color: #1d2129;
}

.table-fields {
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.field-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f2f3f5;
}

.field-item:last-child {
  border-bottom: none;
}

.field-name {
  color: #1d2129;
  font-size: 13px;
}

.field-type {
  font-size: 12px;
  color: #86909c;
  background: #f2f3f5;
  padding: 2px 8px;
  border-radius: 4px;
}

.field-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.field-pk {
  font-size: 11px;
  color: #1890ff;
  background: #e6f7ff;
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid #91d5ff;
}
</style>
