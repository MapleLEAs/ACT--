<template>
  <div class="predictive-maintenance">
    <div class="page-header">
      <div>
        <h1>预测性维护 2.0</h1>
        <p class="subtitle">基于健康度评分和趋势预测的智能运维决策</p>
      </div>
      <el-button type="primary" :loading="loading" @click="fetchHealthSummary">
        <AppIcon name="refresh" /> 重新计算
      </el-button>
    </div>

    <el-row :gutter="20" class="overview-cards">
      <el-col :span="6">
        <el-card class="stat-card health-excellent">
          <div class="stat-icon">
            <AppIcon name="check" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ healthSummary?.excellent || 0 }}</div>
            <div class="stat-label">健康设备</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card health-monitor">
          <div class="stat-icon">
            <AppIcon name="view" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ healthSummary?.attention || 0 }}</div>
            <div class="stat-label">需关注</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card health-warning">
          <div class="stat-icon">
            <AppIcon name="warning" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ healthSummary?.warning || 0 }}</div>
            <div class="stat-label">预警设备</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card health-critical">
          <div class="stat-icon">
            <AppIcon name="close" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ healthSummary?.critical || 0 }}</div>
            <div class="stat-label">高危设备</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>设备健康度分布</span>
              <el-radio-group v-model="healthViewType" size="small">
                <el-radio-button value="list">列表</el-radio-button>
                <el-radio-button value="chart">图表</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          
          <div v-if="healthViewType === 'chart'" ref="healthChartRef" class="health-chart"></div>
          
          <div v-else class="health-list">
            <el-table :data="healthDevices" stripe>
              <el-table-column prop="device_id" label="设备ID" width="140"></el-table-column>
              <el-table-column prop="device_type" label="设备类型" width="100">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.device_type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="health_score" label="健康度" width="140">
                <template #default="{ row }">
                  <el-progress 
                    :percentage="row.health_score" 
                    :color="getHealthColor(row.health_score)"
                    :stroke-width="8"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="health_level" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getHealthTagType(row.health_level)" size="small">
                    {{ row.health_level }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="risk_factors" label="风险因素" min-width="200">
                <template #default="{ row }">
                  <span class="risk-tags">
                    <el-tag v-for="(rf, idx) in (row.risk_factors || []).slice(0, 3)" 
                      :key="idx" size="small" type="danger">
                      {{ rf }}
                    </el-tag>
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="showDeviceDetail(row.device_id)">
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
          <el-card class="high-risk-card">
            <template #header>
              <span>重点关注设备（需维护）</span>
            </template>
          <div class="risk-list">
            <div v-for="device in highRiskDevices" :key="device.device_id" class="risk-item">
              <div class="risk-header">
                <span class="risk-id">{{ device.device_id }}</span>
                <el-tag type="danger" size="small">高风险</el-tag>
              </div>
              <div class="risk-info">
                <div class="risk-stat">
                  <span class="stat-label">健康度</span>
                  <span class="stat-value">{{ device.health_score }}%</span>
                </div>
                <div class="risk-stat">
                  <span class="stat-label">预测故障时间</span>
                  <span class="stat-value">{{ device.predict_failure_days || '--' }}天后</span>
                </div>
              </div>
              <div class="risk-actions">
                <el-button size="small" type="primary" @click="handleCreateWorkOrder(device.device_id)">创建维护工单</el-button>
                <el-button size="small" @click="showDeviceDetail(device.device_id)">查看详情</el-button>
              </div>
            </div>
            
            <el-empty v-if="!highRiskDevices.length" description="暂无高风险设备" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="detail-card" v-if="selectedDevice">
      <template #header>
        <div class="card-header">
          <span>{{ selectedDevice }} - 健康度详情</span>
          <el-button link @click="selectedDevice = null">关闭</el-button>
        </div>
      </template>
      
      <el-row :gutter="20" v-if="deviceHealthDetail">
        <el-col :span="8">
          <div class="health-score-circle">
            <el-progress 
              type="circle" 
              :percentage="deviceHealthDetail.health_score" 
              :color="getHealthColor(deviceHealthDetail.health_score)"
              :width="150"
            />
            <div class="score-label">健康度</div>
          </div>
        </el-col>
        
        <el-col :span="16">
          <div class="detail-metrics">
            <div class="detail-item">
              <span class="label">健康等级</span>
              <el-tag :type="getHealthTagType(deviceHealthDetail.health_level)">
                {{ deviceHealthDetail.health_level }}
              </el-tag>
            </div>
            <div class="detail-item">
              <span class="label">上次评估时间</span>
              <span>{{ deviceHealthDetail.last_evaluated || '—' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">预测窗口</span>
              <span class="highlight">{{ deviceHealthDetail.prediction_window_hours != null ? deviceHealthDetail.prediction_window_hours + ' 小时' : '—' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">维护建议</span>
              <span>{{ deviceHealthDetail.maintenance_suggestion || '—' }}</span>
            </div>

            <div class="risk-factors-section">
              <div class="section-title">主要风险因素</div>
              <div class="risk-factor-list">
                <div v-for="(rf, idx) in (deviceHealthDetail.risk_factors || deviceHealthDetail.top_risks || [])" :key="idx" class="risk-factor-item">
                  <el-icon><AppIcon name="warning" /></el-icon>
                  <span>{{ rf }}</span>
                </div>
                <div v-if="!(deviceHealthDetail.risk_factors || deviceHealthDetail.top_risks || []).length" class="risk-factor-item" style="background:#f6ffed;border-color:#b7eb8f;color:#52c41a">
                  <span>暂无显著风险</span>
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { getHealthSummary, getHealthDetail } from '@/api/device'

const loading = ref(false)
const healthSummary = ref<any>(null)
const healthViewType = ref<'list' | 'chart'>('list')
const selectedDevice = ref<string | null>(null)
const deviceHealthDetail = ref<any>(null)
const healthChartRef = ref<HTMLElement | null>(null)
let healthChart: ECharts | null = null

const healthDevices = computed(() => {
  return healthSummary.value?.devices || []
})

const highRiskDevices = computed(() => {
  return (healthDevices.value || [])
    .filter((d: any) => d.health_level !== '健康')
    .sort((a: any, b: any) => (a.health_score ?? 100) - (b.health_score ?? 100))
    .slice(0, 5)
})

const getHealthColor = (score: number) => {
  if (score >= 85) return '#52c41a'
  if (score >= 70) return '#faad14'
  if (score >= 50) return '#fa8c16'
  return '#f5222d'
}

const getHealthTagType = (level: string) => {
  const map: Record<string, any> = {
    '健康': 'success',
    '关注': 'warning',
    '预警': 'warning',
    '高危': 'danger'
  }
  return map[level] || 'info'
}

const getScoreClass = (score: number) => {
  if (score >= 80) return 'score-good'
  if (score >= 60) return 'score-medium'
  return 'score-poor'
}

const fetchHealthSummary = async () => {
  loading.value = true
  try {
    const res: any = await getHealthSummary()
    healthSummary.value = res.data || res
    if (healthViewType.value === 'chart') {
      await nextTick()
      renderHealthChart()
    }
  } catch {
    ElMessage.error('获取健康度汇总失败')
  } finally {
    loading.value = false
  }
}

const showDeviceDetail = async (deviceId: string) => {
  try {
    const res: any = await getHealthDetail(deviceId)
    deviceHealthDetail.value = res.data || res
    selectedDevice.value = deviceId
  } catch {
    ElMessage.error('获取设备健康详情失败')
  }
}

// 演示用：生成维护工单（仅前端提示，不落库，避免改动演示数据）
const handleCreateWorkOrder = (deviceId: string) => {
  ElMessage.success(`已为 ${deviceId} 生成维护工单（演示）`)
}

const renderHealthChart = () => {
  if (!healthChartRef.value) return
  
  if (!healthChart) {
    healthChart = echarts.init(healthChartRef.value)
  }
  
  const levelData = [
    { name: '健康', value: healthSummary.value?.excellent || 0, itemStyle: { color: '#52c41a' } },
    { name: '关注', value: healthSummary.value?.attention || 0, itemStyle: { color: '#faad14' } },
    { name: '预警', value: healthSummary.value?.warning || 0, itemStyle: { color: '#fa8c16' } },
    { name: '高危', value: healthSummary.value?.critical || 0, itemStyle: { color: '#f5222d' } }
  ]
  
  healthChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '45%'],
      data: levelData,
      label: { formatter: '{b}: {c}台' }
    }]
  })
}

const handleResize = () => {
  healthChart?.resize()
}

onMounted(() => {
  fetchHealthSummary()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  healthChart?.dispose()
})
</script>

<style scoped>
.predictive-maintenance {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
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
  color: #1d2129;
}

.subtitle {
  margin: 0;
  color: #86909c;
}

.overview-cards {
  margin-bottom: 20px;
}

.stat-card {
  border: none;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.stat-card .el-card__body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.health-excellent .stat-icon { background: #e6f7e6; color: #52c41a; }
.health-monitor .stat-icon { background: #fff7e6; color: #faad14; }
.health-warning .stat-icon { background: #fff1e6; color: #fa8c16; }
.health-critical .stat-icon { background: #fff1f0; color: #f5222d; }

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1d2129;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #86909c;
  margin-top: 4px;
}

.charts-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.health-chart {
  height: 400px;
}

.high-risk-card {
  height: 100%;
}

.risk-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.risk-item {
  padding: 16px;
  background: #fff1f0;
  border: 1px solid #ffa39e;
  border-radius: 8px;
}

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.risk-id {
  font-weight: 600;
  color: #1d2129;
}

.risk-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.risk-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.risk-stat .stat-label {
  font-size: 12px;
  color: #86909c;
}

.risk-stat .stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #f5222d;
}

.risk-actions {
  display: flex;
  gap: 8px;
}

.detail-card {
  margin-bottom: 20px;
}

.health-score-circle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
}

.score-label {
  margin-top: 16px;
  font-size: 16px;
  color: #86909c;
}

.detail-metrics {
  padding: 20px 0;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f2f3f5;
}

.detail-item .label {
  color: #86909c;
}

.detail-item .highlight {
  font-weight: 600;
  color: #1890ff;
}

.risk-factors-section {
  margin-top: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
}

.risk-factor-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-factor-item {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 12px;
  background: #fff1f0;
  border-radius: 4px;
  color: #f5222d;
  font-size: 14px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 20px;
}

.metric-card {
  padding: 16px;
  background: #f7f8fa;
  border-radius: 8px;
  text-align: center;
}

.metric-name {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 8px;
}

.metric-score {
  font-size: 20px;
  font-weight: 700;
}

.score-good { color: #52c41a; }
.score-medium { color: #faad14; }
.score-poor { color: #f5222d; }
</style>
