<template>
  <div class="data-analysis-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>预测性维护中心</h1>
      <p class="subtitle">设备健康度评估、风险预测与环境数据管理</p>
    </div>

    <!-- 设备健康总览 -->
    <div class="health-overview" v-loading="healthLoading">
      <div class="health-summary-cards">
        <div class="health-card">
          <div class="health-value">{{ healthSummary.avg_health_score || 0 }}</div>
          <div class="health-label">平均健康度</div>
        </div>
        <div class="health-card healthy">
          <div class="health-value">{{ healthSummary.level_counts?.['健康'] || 0 }}</div>
          <div class="health-label">健康设备</div>
        </div>
        <div class="health-card warning">
          <div class="health-value">{{ (healthSummary.level_counts?.['关注'] || 0) + (healthSummary.level_counts?.['预警'] || 0) }}</div>
          <div class="health-label">需关注</div>
        </div>
        <div class="health-card danger">
          <div class="health-value">{{ healthSummary.level_counts?.['高危'] || 0 }}</div>
          <div class="health-label">高危设备</div>
        </div>
      </div>

      <div class="analysis-card high-risk-card">
        <div class="card-header">
          <div class="card-title"><h3>高风险设备排行</h3></div>
          <el-button size="small" @click="fetchHealthSummary"><AppIcon name="refresh" /> 刷新健康度</el-button>
        </div>
        <div class="card-content">
          <el-table :data="healthSummary.high_risk_devices || []" size="small" border>
            <el-table-column prop="device_id" label="设备" width="120" />
            <el-table-column prop="device_type" label="类型" width="100" />
            <el-table-column prop="health_score" label="健康度" width="90" />
            <el-table-column prop="health_level" label="等级" width="90">
              <template #default="{ row }">
                <el-tag :type="healthLevelType(row.health_level)" size="small">{{ row.health_level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="maintenance_suggestion" label="维护建议" min-width="200" />
          </el-table>
        </div>
      </div>
    </div>

    <!-- 单设备健康详情 -->
    <div v-if="healthDetail" class="analysis-card health-detail-card">
      <div class="card-header">
        <div class="card-title"><h3>当前设备健康详情</h3></div>
        <el-tag>{{ healthDetail.health_level }} · {{ healthDetail.health_score }} 分</el-tag>
      </div>
      <div class="card-content health-detail-body">
        <p><strong>维护建议：</strong>{{ healthDetail.maintenance_suggestion }}</p>
        <p v-if="healthDetail.prediction_window_hours">
          <strong>预警窗口：</strong>未来 {{ healthDetail.prediction_window_hours }} 小时内需关注
        </p>
        <ul v-if="healthDetail.top_risks?.length">
          <li v-for="(risk, idx) in healthDetail.top_risks" :key="idx">{{ risk }}</li>
        </ul>
        <el-alert v-if="!healthDetail.sample_sufficient" type="info" show-icon :closable="false" title="样本不足，预测结果仅供参考" />
      </div>
    </div>

    <!-- 控制面板 -->
    <div class="control-panel">
      <div class="control-group">
        <label>选择设备</label>
        <el-select v-model="selectedDevice" placeholder="请选择设备" @change="handleDeviceChange">
          <el-option v-for="device in devices" :key="device.device_id" :label="device.device_id + ' - ' + device.device_type" :value="device.device_id" />
        </el-select>
      </div>
      <div class="control-group">
        <label>选择指标</label>
        <el-select v-model="selectedMetric" placeholder="请选择指标">
          <el-option label="设备温度" value="device_temperature" />
          <el-option label="设备湿度" value="device_humidity" />
          <el-option label="信号强度" value="signal_strength" />
          <el-option label="运行时间" value="running_time" />
        </el-select>
      </div>
      <div class="control-group">
        <label>时间跨度</label>
        <el-select v-model="timeRange" placeholder="请选择时间跨度">
          <el-option label="近3天" :value="3" />
          <el-option label="近7天" :value="7" />
          <el-option label="近14天" :value="14" />
        </el-select>
      </div>
      <div class="control-actions">
        <el-button type="primary" @click="fetchTrendData"><AppIcon name="trend" /> 获取趋势</el-button>
        <el-button type="success" @click="executePrediction"><AppIcon name="data-analysis" /> 执行预测</el-button>
        <el-button type="warning" @click="detectAnomaly"><AppIcon name="warning" /> 异常检测</el-button>
      </div>
    </div>

    <!-- 核心分析区域 -->
    <div class="analysis-content">
      <!-- 左侧：趋势图表 -->
      <div class="main-chart-section">
        <div class="analysis-card trend-card">
          <div class="card-header">
            <div class="card-title">
              <svg class="card-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 13H5V21H3V13ZM10 8H12V21H10V8ZM17 3H19V21H17V3Z" fill="#165DFF"/>
              </svg>
              <h3>趋势分析图表</h3>
            </div>
            <div class="card-status">
              <span :class="['status-badge', trendDirectionClass]">{{ trendDirectionText }}</span>
            </div>
          </div>
          <div class="card-content">
            <div ref="trendChartRef" class="chart-container"></div>
            <div class="chart-legend">
              <div class="legend-item">
                <div class="legend-color" style="background-color: #165DFF;"></div>
                <span>历史数据</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background-color: #4CAF50;"></div>
                <span>移动平均</span>
              </div>
              <div class="legend-item">
                <div class="legend-color" style="background-color: #FF7D00;"></div>
                <span>预测数据</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：统计信息 -->
      <div class="stats-section">
        <!-- 统计卡片 -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon temp-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C14.21 2 16 3.79 16 6C16 8.21 14.21 10 12 10C9.79 10 8 8.21 8 6C8 3.79 9.79 2 12 2ZM4 14.5C4 13.12 5.12 12 6.5 12S9 13.12 9 14.5V20C9 20.55 8.55 21 8 21H4C3.45 21 3 20.55 3 20V14.5C3 14.22 3.22 14 3.5 14C3.78 14 4 14.22 4 14.5ZM18 14.5C18 13.12 19.12 12 20.5 12S23 13.12 23 14.5V20C23 20.55 22.55 21 22 21H18C17.45 21 17 20.55 17 20V14.5C17 14.22 17.22 14 17.5 14C17.78 14 18 14.22 18 14.5Z" fill="#FF7D00"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.avg.toFixed(2) }}</div>
              <div class="stat-label">平均值</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon trend-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 18L5 6V18H19Z" fill="#4CAF50"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.slope.toFixed(4) }}</div>
              <div class="stat-label">趋势斜率</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon confidence-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#165DFF"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.confidence.toFixed(1) }}%</div>
              <div class="stat-label">置信度</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon anomaly-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" fill="#D9001B"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ anomalyCount }}</div>
              <div class="stat-label">异常数量</div>
            </div>
          </div>
        </div>

        <!-- 预测结果卡片 -->
        <div class="analysis-card">
          <div class="card-header">
            <div class="card-title">
              <svg class="card-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" fill="#9C27B0"/>
              </svg>
              <h3>预测结果</h3>
            </div>
          </div>
          <div class="card-content">
            <div v-if="predictionResult" class="prediction-result">
              <div class="prediction-header">
                <span class="prediction-metric">{{ selectedMetricLabel }}</span>
                <span class="prediction-horizon">预测 {{ predictionResult.prediction_horizon }} 分钟后</span>
              </div>
              <div class="prediction-values">
                <div v-for="(pred, index) in predictionResult.predictions" :key="index" class="prediction-item">
                  <span class="prediction-time">{{ (index + 1) * 15 }}分钟后</span>
                  <span class="prediction-value">{{ pred.predicted_value.toFixed(2) }}</span>
                  <span class="prediction-confidence">置信度: {{ pred.confidence_score.toFixed(0) }}%</span>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" fill="#ccc"/>
              </svg>
              <p>点击"执行预测"按钮获取预测结果</p>
            </div>
          </div>
        </div>

        <!-- 异常检测结果 -->
        <div class="analysis-card">
          <div class="card-header">
            <div class="card-title">
              <svg class="card-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" fill="#D9001B"/>
              </svg>
              <h3>异常检测</h3>
            </div>
          </div>
          <div class="card-content">
            <div v-if="anomalyResult" class="anomaly-result">
              <!-- 告警规则信息 -->
              <div v-if="anomalyResult.threshold_info" class="threshold-info">
                <h4>当前告警规则</h4>
                <div class="threshold-details">
                  <div class="threshold-item">
                    <span class="threshold-label">规则名称:</span>
                    <span class="threshold-value">{{ anomalyResult.threshold_info.rule_name }}</span>
                  </div>
                  <div class="threshold-item">
                    <span class="threshold-label">阈值:</span>
                    <span class="threshold-value">{{ anomalyResult.threshold_info.metric }} {{ anomalyResult.threshold_info.operator }} {{ anomalyResult.threshold_info.threshold }}</span>
                  </div>
                  <div class="threshold-item">
                    <span class="threshold-label">严重程度:</span>
                    <span :class="['threshold-value', 'severity-' + anomalyResult.threshold_info.severity.toLowerCase()]">{{ anomalyResult.threshold_info.severity }}</span>
                  </div>
                </div>
              </div>
              
              <div class="anomaly-summary">
                <div class="anomaly-stat">
                  <span class="anomaly-count-value">{{ anomalyResult.anomaly_count }}</span>
                  <span class="anomaly-count-label">IQR异常</span>
                </div>
                <div class="anomaly-stat">
                  <span class="anomaly-count-value alarm-trigger">{{ anomalyResult.alarm_triggered_count || 0 }}</span>
                  <span class="anomaly-count-label">超阈值告警</span>
                </div>
                <div class="anomaly-stat">
                  <span class="anomaly-rate-value">{{ anomalyResult.anomaly_rate }}%</span>
                  <span class="anomaly-rate-label">异常率</span>
                </div>
                <div class="anomaly-stat">
                  <span class="anomaly-rate-value alarm-rate">{{ anomalyResult.alarm_rate || 0 }}%</span>
                  <span class="anomaly-rate-label">告警率</span>
                </div>
              </div>
              <div v-if="anomalyResult.anomalies && anomalyResult.anomalies.length > 0" class="anomaly-list">
                <h4>异常详情</h4>
                <div v-for="(anomaly, index) in anomalyResult.anomalies.slice(0, 5)" :key="index" class="anomaly-item">
                  <span class="anomaly-time">{{ formatTime(anomaly.time) }}</span>
                  <span class="anomaly-value">值: {{ anomaly.value.toFixed(2) }}</span>
                  <span class="anomaly-score" :class="{ 'high-score': anomaly.score > 0.8 }">
                    评分: {{ anomaly.score.toFixed(2) }}
                  </span>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" fill="#ccc"/>
              </svg>
              <p>点击"异常检测"按钮进行检测</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 环境数据批量导入 -->
    <div class="analysis-card env-import-card">
      <div class="card-header">
        <div class="card-title"><h3>环境数据批量导入</h3></div>
      </div>
      <div class="card-content">
        <p class="env-tip">导入后将自动刷新趋势图与健康度评分</p>
        <el-input
          v-model="envBatchJson"
          type="textarea"
          :rows="6"
          placeholder='[{"device_id":"VHF001","ambient_temperature":28.5,"humidity":65,"collect_time":"2026-06-17T10:00:00Z"}]'
        />
        <div class="env-actions">
          <el-button @click="fillEnvTemplate"><AppIcon name="edit" /> 填充模板</el-button>
          <el-button type="primary" :loading="envSubmitting" @click="handleEnvBatchImport"><AppIcon name="import" /> 提交导入</el-button>
        </div>
        <el-alert
          v-if="envBatchResult"
          :title="`环境数据：成功 ${envBatchResult.created_count} 条，失败 ${envBatchResult.failed_count || 0} 条`"
          :type="envBatchResult.failed_count ? 'warning' : 'success'"
          show-icon
          :closable="false"
          class="env-result"
        />
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="analysis-card data-table-card">
      <div class="card-header">
        <div class="card-title">
          <svg class="card-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z" fill="#5C6E8D"/>
          </svg>
          <h3>历史数据记录</h3>
        </div>
      </div>
      <div class="card-content">
        <el-table :data="historicalData" border :height="250">
          <el-table-column prop="time" label="时间" width="180" />
          <el-table-column prop="value" label="值" width="120">
            <template #default="scope">
              {{ scope.row.value.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="isAnomaly" label="是否异常" width="100">
            <template #default="scope">
              <span v-if="scope.row.isAnomaly" class="anomaly-badge">是</span>
              <span v-else class="normal-badge">否</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { ElSelect, ElOption, ElButton, ElTable, ElTableColumn, ElMessage } from 'element-plus'
import {
  getDevices,
  getDeviceTrend,
  executePrediction as apiExecutePrediction,
  detectAnomaly as apiDetectAnomaly,
  getHealthSummary,
  getHealthDetail,
  batchCreateEnvironmentData,
  recalculatePredictions,
} from '@/api/device'
import { useDataSyncStore } from '@/store/dataSync'

const dataSyncStore = useDataSyncStore()

// --- 状态定义 ---
const devices = ref([])
const selectedDevice = ref('')
const selectedMetric = ref('device_temperature')
const timeRange = ref(7)

const trendData = ref([])
const movingAverageData = ref([])
const predictionData = ref([])
const predictionResult = ref(null)
const anomalyResult = ref(null)
const anomalyCount = ref(0)

const statistics = ref({
  avg: 0,
  min: 0,
  max: 0,
  slope: 0,
  confidence: 0
})

const trendChartRef = ref(null)
let trendChartInstance = null

const healthLoading = ref(false)
const healthSummary = ref({ avg_health_score: 0, level_counts: {}, high_risk_devices: [] })
const healthDetail = ref(null)
const envBatchJson = ref('')
const envSubmitting = ref(false)
const envBatchResult = ref(null)

const healthLevelType = (level) => {
  const map = { '健康': 'success', '关注': 'info', '预警': 'warning', '高危': 'danger' }
  return map[level] || 'info'
}

const fetchHealthSummary = async () => {
  healthLoading.value = true
  try {
    const res = await getHealthSummary()
    healthSummary.value = res.data || res
  } catch (error) {
    console.error('获取健康度汇总失败:', error)
  } finally {
    healthLoading.value = false
  }
}

const fetchHealthDetail = async () => {
  if (!selectedDevice.value) return
  try {
    const res = await getHealthDetail(selectedDevice.value)
    healthDetail.value = res.data || res
  } catch (error) {
    console.error('获取健康详情失败:', error)
  }
}

const fillEnvTemplate = () => {
  const deviceId = selectedDevice.value || 'VHF001'
  envBatchJson.value = JSON.stringify([
    {
      device_id: deviceId,
      ambient_temperature: 28.5,
      humidity: 65,
      atmospheric_pressure: 1013,
      wind_speed: 3.2,
      collect_time: new Date().toISOString(),
    },
  ], null, 2)
}

const handleEnvBatchImport = async () => {
  envSubmitting.value = true
  envBatchResult.value = null
  try {
    const parsed = JSON.parse(envBatchJson.value || '[]')
    if (!Array.isArray(parsed) || !parsed.length) {
      ElMessage.warning('请提供有效的 JSON 数组')
      return
    }
    const res = await batchCreateEnvironmentData(parsed)
    envBatchResult.value = res.data || res
    dataSyncStore.notifyEnvironmentChanged()
    await Promise.all([fetchHealthSummary(), fetchHealthDetail(), fetchTrendData()])
    await recalculatePredictions(selectedDevice.value || undefined)
    ElMessage.success(`环境数据导入完成：成功 ${envBatchResult.value.created_count} 条`)
  } catch {
    ElMessage.error('环境数据导入失败')
  } finally {
    envSubmitting.value = false
  }
}

// --- 计算属性 ---
const selectedMetricLabel = computed(() => {
  const labels = {
    'device_temperature': '设备温度',
    'device_humidity': '设备湿度',
    'signal_strength': '信号强度',
    'running_time': '运行时间'
  }
  return labels[selectedMetric.value] || selectedMetric.value
})

const trendDirectionText = computed(() => {
  if (statistics.value.slope > 0.01) return '上升趋势'
  if (statistics.value.slope < -0.01) return '下降趋势'
  return '稳定'
})

const trendDirectionClass = computed(() => {
  if (statistics.value.slope > 0.01) return 'trend-up'
  if (statistics.value.slope < -0.01) return 'trend-down'
  return 'trend-stable'
})

const historicalData = computed(() => {
  return trendData.value.map(item => ({
    time: formatTime(item.time),
    value: item.value,
    isAnomaly: false
  }))
})

// --- 工具函数 ---
function formatTime(timeStr) {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// --- 数据获取 ---
const fetchDevices = async () => {
  try {
    const response = await getDevices()
    devices.value = response.results || response
    if (devices.value.length > 0) {
      selectedDevice.value = devices.value[0].device_id
    }
  } catch (error) {
    console.error('获取设备列表失败:', error)
  }
}

const fetchTrendData = async () => {
  if (!selectedDevice.value) {
    ElMessage.warning('请先选择设备')
    return
  }

  try {
    const response = await getDeviceTrend(selectedDevice.value, selectedMetric.value, timeRange.value)
    
    if (response && response.data) {
      trendData.value = response.data
      movingAverageData.value = response.moving_average || []
      
      // 更新统计数据
      statistics.value = {
        avg: response.statistics?.avg || 0,
        min: response.statistics?.min || 0,
        max: response.statistics?.max || 0,
        slope: response.trend?.slope || 0,
        confidence: response.trend?.confidence || 0
      }
      
      predictionData.value = []
      predictionResult.value = null
      
      nextTick(() => {
        updateTrendChart()
      })
    }
  } catch (error) {
    console.error('获取趋势数据失败:', error)
    ElMessage.error('获取趋势数据失败')
  }
}

const executePrediction = async () => {
  if (!selectedDevice.value) {
    ElMessage.warning('请先选择设备')
    return
  }

  try {
    const response = await apiExecutePrediction(selectedDevice.value, selectedMetric.value, 60)
    
    if (response) {
      predictionResult.value = response
      
      // 更新预测数据用于图表
      if (response.predictions) {
        predictionData.value = response.predictions.map((p, index) => ({
          time: `预测+${(index + 1) * 15}分钟`,
          value: p.predicted_value
        }))
      }
      
      nextTick(() => {
        updateTrendChart()
      })
      
      ElMessage.success('预测完成')
    }
  } catch (error) {
    console.error('执行预测失败:', error)
    ElMessage.error('执行预测失败')
  }
}

const detectAnomaly = async () => {
  if (!selectedDevice.value) {
    ElMessage.warning('请先选择设备')
    return
  }

  try {
    const response = await apiDetectAnomaly(selectedDevice.value, selectedMetric.value)
    
    if (response) {
      anomalyResult.value = response
      anomalyCount.value = response.anomaly_count || 0
      
      // 更新历史数据的异常标记
      if (response.anomalies) {
        const anomalyIndices = new Set(response.anomalies.map(a => a.index))
        trendData.value.forEach((item, index) => {
          item.isAnomaly = anomalyIndices.has(index)
        })
      }
      
      ElMessage.success(`检测完成，发现 ${anomalyCount.value} 个异常`)
    }
  } catch (error) {
    console.error('异常检测失败:', error)
    ElMessage.error('异常检测失败')
  }
}

// --- 图表相关 ---
const updateTrendChart = () => {
  if (!trendChartRef.value) return
  
  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChartRef.value)
  }
  
  const xData = trendData.value.map(item => {
    const time = new Date(item.time)
    return `${time.getMonth() + 1}/${time.getDate()} ${time.getHours()}:${String(time.getMinutes()).padStart(2, '0')}`
  })
  
  const yData = trendData.value.map(item => item.value)
  const maXData = movingAverageData.value.length > 0 
    ? xData.slice(-movingAverageData.value.length) 
    : []
  const maYData = movingAverageData.value.map(item => item.value)
  
  // 预测数据的X轴标签
  const predXData = predictionData.value.map(item => item.time)
  const predYData = predictionData.value.map(item => item.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      padding: [8, 12],
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e8e8e8',
      borderWidth: 1,
      textStyle: { color: '#333' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: [...xData, ...predXData],
      axisLine: { lineStyle: { color: '#e8e8e8' } },
      axisLabel: { 
        color: '#666',
        rotate: 45,
        fontSize: 10
      },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: selectedMetricLabel.value,
      axisLine: { lineStyle: { color: '#e8e8e8' } },
      axisLabel: { color: '#666' },
      splitLine: { lineStyle: { color: '#f0f0f0' } }
    },
    series: [
      {
        name: '历史数据',
        type: 'line',
        data: yData,
        smooth: true,
        itemStyle: { color: '#165DFF' },
        lineStyle: { width: 2 },
        symbol: 'circle',
        symbolSize: 4
      },
      {
        name: '移动平均',
        type: 'line',
        data: [...Array(xData.length - maXData.length).fill(null), ...maYData],
        smooth: true,
        itemStyle: { color: '#4CAF50' },
        lineStyle: { width: 2, type: 'dashed' },
        symbol: 'none'
      },
      {
        name: '预测数据',
        type: 'line',
        data: [...Array(xData.length).fill(null), ...predYData],
        smooth: true,
        itemStyle: { color: '#FF7D00' },
        lineStyle: { width: 2, type: 'dashed' },
        symbol: 'diamond',
        symbolSize: 6,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 125, 0, 0.3)' },
            { offset: 1, color: 'rgba(255, 125, 0, 0.05)' }
          ])
        }
      }
    ]
  }
  
  trendChartInstance.setOption(option)
}

// --- 事件处理 ---
const handleDeviceChange = () => {
  predictionData.value = []
  predictionResult.value = null
  anomalyResult.value = null
  anomalyCount.value = 0
  fetchHealthDetail()
}

const handleResize = () => {
  if (trendChartInstance) {
    trendChartInstance.resize()
  }
}

// --- 生命周期 ---
onMounted(async () => {
  await fetchDevices()
  await fetchHealthSummary()
  if (selectedDevice.value) {
    await fetchHealthDetail()
  }

  window.addEventListener('resize', handleResize)
})

watch(() => dataSyncStore.devicesVersion, async () => {
  await fetchDevices()
  await fetchHealthSummary()
})

watch(() => dataSyncStore.environmentVersion, async () => {
  await fetchHealthSummary()
  await fetchHealthDetail()
  await fetchTrendData()
})

onBeforeUnmount(() => {
  if (trendChartInstance) {
    trendChartInstance.dispose()
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.data-analysis-container {
  padding: 24px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.page-header .subtitle {
  font-size: 14px;
  color: #888;
  margin: 0;
}

/* 控制面板 */
.control-panel {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-group label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.control-group :deep(.el-select) {
  width: 180px;
}

.control-actions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

/* 分析内容区域 */
.analysis-content {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 20px;
  margin-bottom: 20px;
}

/* 主图表区域 */
.main-chart-section {
  display: flex;
  flex-direction: column;
}

.trend-card {
  flex: 1;
}

.trend-card .card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 统计区域 */
.stats-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 20px;
  height: 20px;
}

.temp-icon {
  background: linear-gradient(135deg, #fff3e0, #ffe0b2);
}

.trend-icon {
  background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
}

.confidence-icon {
  background: linear-gradient(135deg, #e3f2fd, #bbdefb);
}

.anomaly-icon {
  background: linear-gradient(135deg, #ffebee, #ffcdd2);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.stat-label {
  font-size: 12px;
  color: #888;
}

/* 卡片通用样式 */
.analysis-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  overflow: hidden;
}

.analysis-card .card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-title h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.card-icon {
  width: 18px;
  height: 18px;
}

.card-status {
  display: flex;
  gap: 8px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.trend-up {
  background: #e8f5e9;
  color: #2e7d32;
}

.trend-down {
  background: #ffebee;
  color: #c62828;
}

.trend-stable {
  background: #e3f2fd;
  color: #1565c0;
}

.analysis-card .card-content {
  padding: 20px;
}

/* 图表容器 */
.chart-container {
  width: 100%;
  height: 350px;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
}

.legend-color {
  width: 12px;
  height: 3px;
  border-radius: 2px;
}

/* 预测结果 */
.prediction-result {
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.prediction-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #e0e0e0;
}

.prediction-metric {
  font-weight: 600;
  color: #333;
}

.prediction-horizon {
  font-size: 12px;
  color: #888;
}

.prediction-values {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prediction-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #fff;
  border-radius: 4px;
}

.prediction-time {
  font-size: 12px;
  color: #666;
}

.prediction-value {
  font-size: 16px;
  font-weight: 600;
  color: #165DFF;
}

.prediction-confidence {
  font-size: 11px;
  color: #888;
}

/* 异常检测结果 */
.anomaly-result {
  padding: 12px;
}

.anomaly-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #e0e0e0;
}

.anomaly-stat {
  flex: 1;
  text-align: center;
}

.anomaly-count-value,
.anomaly-rate-value {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: #d9001b;
}

.anomaly-count-label,
.anomaly-rate-label {
  font-size: 12px;
  color: #888;
}

.anomaly-list h4 {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin: 0 0 10px 0;
}

.anomaly-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 10px;
  background: #fff5f5;
  border-radius: 4px;
  margin-bottom: 6px;
  font-size: 12px;
}

.anomaly-time {
  color: #666;
}

.anomaly-value {
  color: #d9001b;
  font-weight: 500;
}

.anomaly-score {
  color: #888;
}

.anomaly-score.high-score {
  color: #d9001b;
  font-weight: 600;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  color: #999;
}

.empty-state svg {
  width: 40px;
  height: 40px;
  margin-bottom: 12px;
}

.empty-state p {
  margin: 0;
  font-size: 13px;
}

/* 数据表格卡片 */
.data-table-card {
  margin-top: 20px;
}

.data-table-card :deep(.el-table) {
  font-size: 13px;
}

.data-table-card :deep(.el-table th) {
  background: #fafafa;
  font-weight: 600;
  color: #333;
}

.anomaly-badge {
  display: inline-block;
  padding: 2px 8px;
  background: #ffebee;
  color: #d9001b;
  border-radius: 4px;
  font-size: 11px;
}

.normal-badge {
  display: inline-block;
  padding: 2px 8px;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 4px;
  font-size: 11px;
}

.health-overview {
  margin-bottom: 24px;
}

.health-summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.health-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.health-card .health-value {
  font-size: 28px;
  font-weight: 700;
  color: #165dff;
}

.health-card.healthy .health-value { color: #4caf50; }
.health-card.warning .health-value { color: #ff7d00; }
.health-card.danger .health-value { color: #d9001b; }

.health-card .health-label {
  margin-top: 8px;
  color: #86909c;
  font-size: 13px;
}

.high-risk-card,
.health-detail-card,
.env-import-card {
  margin-bottom: 24px;
}

.health-detail-body p,
.health-detail-body ul {
  margin: 8px 0;
  color: #4e5969;
}

.env-tip {
  margin: 0 0 12px;
  color: #86909c;
  font-size: 13px;
}

.env-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 12px;
}

.env-result {
  margin-top: 12px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .analysis-content {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .control-panel {
    flex-direction: column;
    align-items: stretch;
  }
  
  .control-group :deep(.el-select) {
    width: 100%;
  }
  
  .control-actions {
    margin-left: 0;
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .chart-container {
    height: 250px;
  }
}
</style>