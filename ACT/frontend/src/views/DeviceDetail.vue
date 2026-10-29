<template>
  <div class="device-detail">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备详情 - {{ deviceId }}</span>
          <el-button type="primary" @click="refreshAll">
            <el-icon><AppIcon name="refresh" /></el-icon>
            刷新数据
          </el-button>
        </div>
      </template>

      <!-- Tab 切换 -->
      <el-tabs v-model="activeTab" type="card" @tab-change="handleTabChange">
        <!-- 基础信息 -->
        <el-tab-pane label="基础信息" name="basic">
          <div v-if="deviceData" class="info-grid">
            <div class="info-item">
              <span class="label">设备ID</span>
              <span class="value">{{ deviceData.device_id }}</span>
            </div>
            <div class="info-item">
              <span class="label">设备类型</span>
              <span class="value">{{ deviceData.device_type }}</span>
            </div>
            <div class="info-item">
              <span class="label">设备型号</span>
              <span class="value">{{ deviceData.device_model }}</span>
            </div>
            <div class="info-item">
              <span class="label">安装位置</span>
              <span class="value">{{ deviceData.location }}</span>
            </div>
            <div class="info-item">
              <span class="label">制造商</span>
              <span class="value">{{ deviceData.manufacturer }}</span>
            </div>
            <div class="info-item">
              <span class="label">安装时间</span>
              <span class="value">{{ formatTime(deviceData.install_time) }}</span>
            </div>
            <div class="info-item">
              <span class="label">在线状态</span>
              <el-tag :type="getStatusType(deviceData.status)">{{ deviceData.status || 'ONLINE' }}</el-tag>
            </div>
            <div class="info-item">
              <span class="label">告警级别</span>
              <el-tag :type="getAlarmLevelType(deviceData.alarm_level)">{{ getAlarmLevelText(deviceData.alarm_level) }}</el-tag>
            </div>
          </div>
          <div v-else class="empty-state">
            <el-empty description="暂无数据" />
          </div>
        </el-tab-pane>

        <!-- 实时状态 -->
        <el-tab-pane label="实时状态" name="status">
          <div v-if="statusData" class="status-grid">
            <div class="status-card">
              <div class="status-icon online">
                <AppIcon name="realtime-monitor" />
              </div>
              <div class="status-info">
                <div class="status-label">在线状态</div>
                <div class="status-value" :class="statusData.online_status ? 'online' : 'offline'">
                  {{ statusData.online_status ? '在线' : '离线' }}
                </div>
              </div>
            </div>
            <div class="status-card">
              <div class="status-icon temp">
                <AppIcon name="thermometer" />
              </div>
              <div class="status-info">
                <div class="status-label">设备温度</div>
                <div class="status-value">{{ statusData.device_temperature }}°C</div>
              </div>
            </div>
            <div class="status-card">
              <div class="status-icon signal">
                <AppIcon name="wifi" />
              </div>
              <div class="status-info">
                <div class="status-label">信号强度</div>
                <div class="status-value">{{ statusData.signal_strength }} dBm</div>
              </div>
            </div>
            <div class="status-card">
              <div class="status-icon power">
                <AppIcon name="power" />
              </div>
              <div class="status-info">
                <div class="status-label">电源电压</div>
                <div class="status-value">{{ statusData.power_voltage }} V</div>
              </div>
            </div>
            <div class="status-card">
              <div class="status-icon link">
                <AppIcon name="link" />
              </div>
              <div class="status-info">
                <div class="status-label">链路状态</div>
                <div class="status-value">{{ statusData.link_status ? '正常' : '异常' }}</div>
              </div>
            </div>
            <div class="status-card">
              <div class="status-icon error">
                <AppIcon name="warning" />
              </div>
              <div class="status-info">
                <div class="status-label">误码率</div>
                <div class="status-value">{{ statusData.bit_error_rate }}</div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <el-empty description="暂无状态数据" />
          </div>
        </el-tab-pane>

        <!-- 告警记录 -->
        <el-tab-pane label="告警记录" name="alarms">
          <el-table :data="alarmList" v-loading="loading" style="width: 100%">
            <el-table-column prop="alarm_id" label="告警ID" width="200" />
            <el-table-column prop="metric" label="监控指标" width="150" />
            <el-table-column prop="value" label="当前值" width="120" />
            <el-table-column prop="severity" label="严重程度" width="120">
              <template #default="scope">
                <el-tag :type="getAlarmLevelType(scope.row.severity)">{{ scope.row.severity }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column prop="trigger_time" label="触发时间" width="200" />
          </el-table>
        </el-tab-pane>

        <!-- NGSI-LD标准数据 -->
        <el-tab-pane label="NGSI-LD标准数据" name="ngsi">
          <el-card>
            <template #header>
              <div class="ngsi-header">
                <span>NGSI-LD 数据预览</span>
                <el-select v-model="ngsiDataType" @change="loadNGSIData">
                  <el-option label="设备实体" value="device" />
                  <el-option label="状态实体" value="status" />
                  <el-option label="告警实体" value="alarms" />
                  <el-option label="预测实体" value="predictions" />
                </el-select>
              </div>
            </template>
            <div v-if="ngsiData" class="ngsi-content">
              <pre class="json-pre">{{ formattedNGSI }}</pre>
            </div>
            <div v-else class="empty-state">
              <el-empty description="点击上方下拉框选择数据类型" />
            </div>
          </el-card>

          <!-- 查询示例 -->
          <el-card style="margin-top: 20px;">
            <template #header>
              <span>统一查询接口示例</span>
            </template>
            <div class="query-example">
              <div class="query-input">
                <span>查询类型:</span>
                <el-select v-model="queryType" style="width: 150px;">
                  <el-option label="Device" value="Device" />
                  <el-option label="Alarm" value="Alarm" />
                  <el-option label="DeviceStatus" value="DeviceStatus" />
                  <el-option label="PredictionResult" value="PredictionResult" />
                </el-select>
              </div>
              <div class="query-input">
                <span>查询条件:</span>
                <el-input v-model="queryCondition" placeholder="deviceType=='VHF'" style="width: 250px;" />
              </div>
              <div class="query-input">
                <span>数量限制:</span>
                <el-input-number v-model="queryLimit" :min="1" :max="50" style="width: 100px;" />
              </div>
              <el-button type="primary" @click="executeQuery">
                <el-icon><AppIcon name="search" /></el-icon>
                执行查询
              </el-button>
            </div>
            <div v-if="queryResult" class="query-result">
              <pre class="json-pre">{{ formattedQueryResult }}</pre>
            </div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getDevice, getStatusLogs, getDeviceNGSI, getDeviceStatusNGSI, getDeviceAlarmsNGSI, getDevicePredictionsNGSI, queryNGSI } from '@/api/device'

const deviceId = ref('VHF001')
const activeTab = ref('basic')
const loading = ref(false)

// 数据
const deviceData = ref<any>(null)
const statusData = ref<any>(null)
const alarmList = ref<any[]>([])
const ngsiDataType = ref('device')
const ngsiData = ref<any>(null)

// 查询相关
const queryType = ref('Device')
const queryCondition = ref("deviceType=='VHF'")
const queryLimit = ref(10)
const queryResult = ref<any>(null)

// 获取设备基础信息
const fetchDevice = async () => {
  try {
    const res: any = await getDevice(deviceId.value)
    deviceData.value = res.data || res
  } catch (error) {
    console.error('获取设备信息失败:', error)
  }
}

// 获取设备状态
const fetchStatus = async () => {
  try {
    const res: any = await getStatusLogs({ device_id: deviceId.value, limit: 1 })
    const logs = res.data || res.results || res
    if (logs.length > 0) {
      statusData.value = logs[0]
    }
  } catch (error) {
    console.error('获取设备状态失败:', error)
  }
}

// 获取告警记录
const fetchAlarms = async () => {
  loading.value = true
  try {
    const res: any = await getDeviceAlarmsNGSI(deviceId.value)
    alarmList.value = res.data || res
  } catch (error) {
    console.error('获取告警记录失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载 NGSI-LD 数据
const loadNGSIData = async () => {
  try {
    switch (ngsiDataType.value) {
      case 'device':
        ngsiData.value = await getDeviceNGSI(deviceId.value)
        break
      case 'status':
        ngsiData.value = await getDeviceStatusNGSI(deviceId.value)
        break
      case 'alarms':
        ngsiData.value = await getDeviceAlarmsNGSI(deviceId.value)
        break
      case 'predictions':
        ngsiData.value = await getDevicePredictionsNGSI(deviceId.value)
        break
    }
  } catch (error) {
    console.error('获取NGSI-LD数据失败:', error)
    ElMessage.error('获取NGSI-LD数据失败')
  }
}

// 格式化 JSON
const formattedNGSI = computed(() => {
  if (!ngsiData.value) return ''
  return JSON.stringify(ngsiData.value, null, 2)
})

// 格式化查询结果
const formattedQueryResult = computed(() => {
  if (!queryResult.value) return ''
  return JSON.stringify(queryResult.value, null, 2)
})

// 执行查询
const executeQuery = async () => {
  try {
    const res = await queryNGSI({
      type: queryType.value,
      q: queryCondition.value,
      limit: queryLimit.value
    })
    queryResult.value = res.data || res
    ElMessage.success('查询成功')
  } catch (error) {
    console.error('查询失败:', error)
    ElMessage.error('查询失败')
  }
}

// 刷新所有数据
const refreshAll = async () => {
  await Promise.all([fetchDevice(), fetchStatus(), fetchAlarms()])
  ElMessage.success('数据刷新成功')
}

// Tab切换处理
const handleTabChange = (tab: string) => {
  if (tab === 'ngsi') {
    loadNGSIData()
  }
}

// 时间格式化
const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 状态类型映射
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    'online': 'success',
    'offline': 'danger',
    'warning': 'warning',
    'error': 'danger'
  }
  return map[status?.toLowerCase()] || 'success'
}

// 告警级别映射
const getAlarmLevelType = (level: string) => {
  const map: Record<string, string> = {
    'critical': 'danger',
    'error': 'danger',
    'warning': 'warning',
    'info': 'info',
    'none': 'success'
  }
  return map[level?.toLowerCase()] || 'success'
}

const getAlarmLevelText = (level: string) => {
  const map: Record<string, string> = {
    'critical': '严重告警',
    'error': '错误告警',
    'warning': '警告告警',
    'info': '一般告警',
    'none': '无告警'
  }
  return map[level?.toLowerCase()] || '无告警'
}

// 监听设备ID变化
watch(deviceId, () => {
  refreshAll()
})

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.device-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  padding: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}

.info-item .label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.info-item .value {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  padding: 20px;
}

.status-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 12px;
}

.status-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
}

.status-icon.online {
  background: #e8f5e9;
  color: #4caf50;
}

.status-icon.temp {
  background: #fff3e0;
  color: #ff9800;
}

.status-icon.signal {
  background: #e3f2fd;
  color: #2196f3;
}

.status-icon.power {
  background: #f3e5f5;
  color: #9c27b0;
}

.status-icon.link {
  background: #e8eaf6;
  color: #3f51b5;
}

.status-icon.error {
  background: #ffebee;
  color: #f44336;
}

.status-info {
  display: flex;
  flex-direction: column;
}

.status-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.status-value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.status-value.online {
  color: #4caf50;
}

.status-value.offline {
  color: #f44336;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

.ngsi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ngsi-content {
  padding: 20px;
}

.json-pre {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 20px;
  border-radius: 8px;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.6;
}

.query-example {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  flex-wrap: wrap;
}

.query-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.query-result {
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding-top: 20px;
}

@media (max-width: 1200px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .status-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
  .status-grid {
    grid-template-columns: 1fr;
  }
}
</style>
