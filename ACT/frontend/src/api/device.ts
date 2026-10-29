import request from './request'

// 获取设备列表
export function getDevices(params?: any) {
  return request({
    url: '/api/devices/',
    method: 'get',
    params
  })
}

// 获取特定设备详情
export function getDevice(id: string) {
  return request({
    url: `/api/devices/${id}/`,
    method: 'get'
  })
}

// 更新设备信息
export function updateDevice(id: string, data: any) {
  return request({
    url: `/api/devices/${id}/`,
    method: 'put',
    data
  })
}

// 删除设备
export function deleteDevice(id: string) {
  return request({
    url: `/api/devices/${id}/`,
    method: 'delete'
  })
}

export function createDevice(data: any) {
  return request({
    url: '/api/devices/',
    method: 'post',
    data
  })
}

export function batchCreateDevices(data: any[]) {
  return request({
    url: '/api/devices/batch-create/',
    method: 'post',
    data: { data }
  })
}

// 获取设备状态日志
export function getStatusLogs(params?: any) {
  return request({
    url: '/api/status_logs/',
    method: 'get',
    params
  })
}

export function batchCreateEnvironmentData(data: any[]) {
  return request({
    url: '/api/environment_data/batch-create/',
    method: 'post',
    data: { data }
  })
}

// ---------------------------
// 告警相关API
// ---------------------------
export function getAlarms(params?: any) {
  return request({
    url: '/api/alarms/',
    method: 'get',
    params
  })
}

export function getAlarm(id: string | number) {
  return request({
    url: `/api/alarms/${id}/`,
    method: 'get'
  })
}

export function acknowledgeAlarm(id: string | number) {
  return request({
    url: `/api/alarms/${id}/ack/`,
    method: 'post'
  })
}

export function clearAlarm(id: string | number) {
  return request({
    url: `/api/alarms/${id}/clear/`,
    method: 'post'
  })
}

// ---------------------------
// 趋势预测相关API
// ---------------------------

// 获取设备趋势数据
export function getDeviceTrend(deviceId: string, metric: string = 'device_temperature', days: number = 7) {
  return request({
    url: '/api/predictions/device-trend/',
    method: 'get',
    params: { device_id: deviceId, metric, days }
  })
}

// 执行预测
export function executePrediction(deviceId: string, metric: string = 'device_temperature', horizon: number = 60) {
  return request({
    url: '/api/predictions/predict/',
    method: 'post',
    data: { device_id: deviceId, metric, horizon }
  })
}

// 异常检测
export function detectAnomaly(deviceId: string, metric: string = 'device_temperature') {
  return request({
    url: '/api/predictions/anomaly-detection/',
    method: 'get',
    params: { device_id: deviceId, metric }
  })
}

// 获取预测汇总
export function getPredictionsSummary() {
  return request({
    url: '/api/predictions/predictions-summary/',
    method: 'get'
  })
}

export function getHealthSummary() {
  return request({
    url: '/api/predictions/health-summary/',
    method: 'get'
  })
}

export function getHealthDetail(deviceId: string) {
  return request({
    url: '/api/predictions/health-detail/',
    method: 'get',
    params: { device_id: deviceId }
  })
}

export function recalculatePredictions(deviceId?: string) {
  return request({
    url: '/api/predictions/recalculate/',
    method: 'post',
    data: deviceId ? { device_id: deviceId } : {}
  })
}

// ---------------------------
// NGSI-LD 相关API
// ---------------------------

// 获取设备 NGSI-LD 格式数据
export function getDeviceNGSI(deviceId: string) {
  return request({
    url: `/api/ngsi/devices/${deviceId}/`,
    method: 'get',
    headers: { 'Accept': 'application/ld+json' }
  })
}

// 获取设备状态 NGSI-LD 格式
export function getDeviceStatusNGSI(deviceId: string) {
  return request({
    url: `/api/ngsi/devices/${deviceId}/status/`,
    method: 'get',
    headers: { 'Accept': 'application/ld+json' }
  })
}

// 获取设备告警 NGSI-LD 格式
export function getDeviceAlarmsNGSI(deviceId: string) {
  return request({
    url: `/api/ngsi/alarms/`,
    method: 'get',
    params: { device_id: deviceId },
    headers: { 'Accept': 'application/ld+json' }
  })
}

// 获取设备预测 NGSI-LD 格式
export function getDevicePredictionsNGSI(deviceId: string) {
  return request({
    url: `/api/ngsi/predictions/${deviceId}/`,
    method: 'get',
    headers: { 'Accept': 'application/ld+json' }
  })
}

// 统一 NGSI-LD 查询
export function queryNGSI(data: any) {
  return request({
    url: '/api/ngsi/query/',
    method: 'post',
    data,
    headers: { 'Content-Type': 'application/ld+json' }
  })
}

// ---------------------------
// 数据库可视化API
// ---------------------------
export function getDatabaseStats() {
  return request({
    url: '/api/database/stats/',
    method: 'get'
  })
}

export function getDatabaseSchema() {
  return request({
    url: '/api/database/schema/',
    method: 'get'
  })
}

export function getRootCauseGraph(alarmId: string | number) {
  return request({
    url: '/api/root-cause/graph/',
    method: 'get',
    params: { alarm_id: alarmId }
  })
}

export function getRootCausePath(deviceId: string) {
  return request({
    url: '/api/root-cause/path/',
    method: 'get',
    params: { device_id: deviceId }
  })
}

export function syncRootCauseGraph() {
  return request({
    url: '/api/root-cause/sync/',
    method: 'post'
  })
}
