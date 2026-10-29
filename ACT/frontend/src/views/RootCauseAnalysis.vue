<template>
  <div class="root-cause-container">
    <div class="page-header">
      <div>
        <h1>根因分析</h1>
        <p class="subtitle">基于知识图谱的告警溯源与路径分析</p>
      </div>
      <div class="header-actions">
        <el-button :loading="syncing" @click="handleSync"><AppIcon name="sync" /> 同步图谱</el-button>
        <el-button type="primary" :loading="loading" @click="loadGraph"><AppIcon name="refresh" /> 刷新</el-button>
      </div>
    </div>

    <div class="control-panel">
      <div class="control-group">
        <label>查询模式</label>
        <el-radio-group v-model="queryMode">
          <el-radio-button value="alarm">按告警</el-radio-button>
          <el-radio-button value="device">按设备</el-radio-button>
        </el-radio-group>
      </div>
      <div class="control-group" v-if="queryMode === 'alarm'">
        <label>选择告警</label>
        <el-select v-model="selectedAlarmId" placeholder="请选择告警" filterable style="width: 320px">
          <el-option
            v-for="alarm in alarms"
            :key="alarm.id"
            :label="`${alarm.alarm_id} - ${alarm.device_id}`"
            :value="alarm.id"
          />
        </el-select>
      </div>
      <div class="control-group" v-else>
        <label>选择设备</label>
        <el-select v-model="selectedDeviceId" placeholder="请选择设备" filterable style="width: 320px">
          <el-option
            v-for="device in devices"
            :key="device.device_id"
            :label="`${device.device_id} - ${device.device_type}`"
            :value="device.device_id"
          />
        </el-select>
      </div>
      <div class="control-group">
        <label><AppIcon name="filter" /> 严重级别</label>
        <el-select v-model="severityFilter" clearable placeholder="全部" style="width: 140px">
          <el-option label="CRITICAL" value="CRITICAL" />
          <el-option label="ERROR" value="ERROR" />
          <el-option label="WARN" value="WARN" />
          <el-option label="INFO" value="INFO" />
        </el-select>
      </div>
      <el-button type="primary" @click="loadGraph"><AppIcon name="search" /> 分析</el-button>
    </div>

    <el-alert
      v-if="graphData?.degraded"
      type="warning"
      show-icon
      :closable="false"
      title="Neo4j 未连接，当前展示关系型数据库降级图谱"
      class="degraded-alert"
    />

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="never" class="graph-card">
          <template #header>
            <span>知识图谱</span>
            <el-tag size="small" type="info">{{ graphData?.provider || '-' }}</el-tag>
          </template>
          <div ref="graphChartRef" class="graph-chart" v-loading="loading"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="side-card">
          <template #header>根因候选</template>
          <div v-if="graphData?.root_candidates?.length" class="candidate-list">
            <div
              v-for="(item, index) in graphData.root_candidates"
              :key="item.node_id"
              class="candidate-item"
              @click="highlightNode(item.node_id)"
            >
              <div class="candidate-rank">#{{ index + 1 }}</div>
              <div class="candidate-body">
                <div class="candidate-name">{{ item.name }}</div>
                <div class="candidate-score">置信度 {{ (item.score * 100).toFixed(0) }}%</div>
                <div class="candidate-reason">{{ item.reason }}</div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无根因候选" />
        </el-card>

        <el-card shadow="never" class="side-card">
          <template #header>路径说明</template>
          <ul v-if="graphData?.path_explanations?.length" class="path-list">
            <li v-for="(text, index) in graphData.path_explanations" :key="index">{{ text }}</li>
          </ul>
          <el-empty v-else description="暂无路径说明" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { ElMessage } from 'element-plus'
import { getAlarms, getDevices, getRootCauseGraph, getRootCausePath, syncRootCauseGraph } from '@/api/device'

type GraphNode = { id: string; name: string; category: string; severity?: string; symbolSize?: number }
type GraphEdge = { source: string; target: string; value: string }
type GraphData = {
  nodes: GraphNode[]
  edges: GraphEdge[]
  root_candidates: Array<{ node_id: string; name: string; score: number; reason: string }>
  path_explanations: string[]
  provider: string
  degraded?: boolean
}

const CATEGORY_COLORS: Record<string, string> = {
  device: '#409eff',
  alarm: '#f56c6c',
  rule: '#e6a23c',
  status: '#67c23a',
  prediction: '#9c27b0',
  workorder: '#909399',
  event: '#00bcd4',
}

const queryMode = ref<'alarm' | 'device'>('alarm')
const selectedAlarmId = ref<number | null>(null)
const selectedDeviceId = ref('')
const severityFilter = ref('')
const loading = ref(false)
const syncing = ref(false)
const alarms = ref<any[]>([])
const devices = ref<any[]>([])
const graphData = ref<GraphData | null>(null)
const graphChartRef = ref<HTMLElement | null>(null)
let chartInstance: ECharts | null = null

const fetchMeta = async () => {
  const [alarmRes, deviceRes] = await Promise.all([
    getAlarms({ page_size: 100 }),
    getDevices(),
  ]) as [any, any]
  alarms.value = alarmRes.results || alarmRes.data || alarmRes || []
  devices.value = deviceRes.results || deviceRes.data || deviceRes || []
  if (alarms.value.length && !selectedAlarmId.value) {
    selectedAlarmId.value = alarms.value[0].id
  }
  if (devices.value.length && !selectedDeviceId.value) {
    selectedDeviceId.value = devices.value[0].device_id
  }
}

const filterNodes = (nodes: GraphNode[]) => {
  if (!severityFilter.value) return nodes
  return nodes.filter(node => {
    if (node.category !== 'alarm') return true
    return node.severity === severityFilter.value
  })
}

const renderGraph = async () => {
  if (!graphData.value || !graphChartRef.value) return
  await nextTick()

  if (!chartInstance) {
    chartInstance = echarts.init(graphChartRef.value)
  }

  const nodes = filterNodes(graphData.value.nodes).map(node => ({
    ...node,
    symbolSize: node.category === 'device' ? 50 : node.category === 'alarm' ? 40 : 32,
    itemStyle: { color: CATEGORY_COLORS[node.category] || '#5c6e8d' },
  }))
  const nodeIds = new Set(nodes.map(node => node.id))
  const edges = graphData.value.edges.filter(
    edge => nodeIds.has(edge.source) && nodeIds.has(edge.target)
  )
  const categories = [...new Set(nodes.map(node => node.category))].map(name => ({ name }))

  chartInstance.setOption({
    tooltip: { formatter: (params: any) => params.data?.name || '' },
    legend: [{ data: categories.map(item => item.name) }],
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      categories,
      data: nodes,
      links: edges.map(edge => ({
        ...edge,
        label: { show: true, formatter: edge.value, fontSize: 10 },
      })),
      force: { repulsion: 280, edgeLength: [80, 160] },
      lineStyle: { color: '#aaa', curveness: 0.2 },
      emphasis: { focus: 'adjacency' },
    }],
  }, true)
}

const loadGraph = async () => {
  loading.value = true
  try {
    let res: any
    if (queryMode.value === 'alarm') {
      if (!selectedAlarmId.value) {
        ElMessage.warning('请选择告警')
        return
      }
      res = await getRootCauseGraph(selectedAlarmId.value)
    } else {
      if (!selectedDeviceId.value) {
        ElMessage.warning('请选择设备')
        return
      }
      res = await getRootCausePath(selectedDeviceId.value)
    }
    graphData.value = res.data || res
    await renderGraph()
  } catch {
    ElMessage.error('根因图谱加载失败')
  } finally {
    loading.value = false
  }
}

const handleSync = async () => {
  syncing.value = true
  try {
    const res: any = await syncRootCauseGraph()
    const payload = res.data || res
    ElMessage.success(payload.message || '同步完成')
    await loadGraph()
  } catch {
    ElMessage.error('图谱同步失败')
  } finally {
    syncing.value = false
  }
}

const highlightNode = (nodeId: string) => {
  if (!chartInstance || !graphData.value) return
  chartInstance.dispatchAction({ type: 'highlight', seriesIndex: 0, name: nodeId })
}

const handleResize = () => chartInstance?.resize()

watch([queryMode, severityFilter], () => {
  if (graphData.value) renderGraph()
})

onMounted(async () => {
  await fetchMeta()
  await loadGraph()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.root-cause-container {
  padding: 4px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.control-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 16px;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-group label {
  font-size: 13px;
  color: #606266;
}

.degraded-alert {
  margin-bottom: 16px;
}

.graph-card,
.side-card {
  margin-bottom: 16px;
}

.graph-chart {
  height: 520px;
}

.candidate-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.candidate-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.candidate-item:hover {
  border-color: #409eff;
}

.candidate-rank {
  font-weight: bold;
  color: #409eff;
}

.candidate-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.candidate-score {
  font-size: 12px;
  color: #67c23a;
  margin-bottom: 4px;
}

.candidate-reason {
  font-size: 13px;
  color: #606266;
}

.path-list {
  margin: 0;
  padding-left: 18px;
  color: #606266;
  line-height: 1.8;
}
</style>
