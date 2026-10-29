import axios from 'axios'

/**
 * NGSI-LD 数据交换 API
 * 提供标准化数据交换能力
 */

export interface NgsiEntity {
  id: string
  type: string
  '@context': string[]
  [key: string]: any
}

export interface QueryParams {
  type: string
  q?: string
  attrs?: string[]
  limit?: number
  offset?: number
}

export interface ExportPackage {
  '@context': string[]
  type: string
  entities: NgsiEntity[]
}

/**
 * 获取实体列表
 * @param type 实体类型（可选）
 * @param limit 返回数量
 * @param offset 偏移量
 */
export function getNgsiEntities(type?: string, limit = 50, offset = 0): Promise<NgsiEntity[]> {
  const params: Record<string, any> = { limit, offset }
  if (type) {
    params.type = type
  }
  return axios.get('/api/ngsi/entities/', { params }).then(res => res.data)
}

/**
 * 根据URN获取单个实体
 * @param urn 实体URN
 */
export function getNgsiEntityByUrn(urn: string): Promise<NgsiEntity> {
  return axios.get('/api/ngsi/entity/', { params: { id: urn } }).then(res => res.data)
}

/**
 * 标准查询接口
 * @param data 查询参数
 */
export function queryNgsi(data: QueryParams): Promise<NgsiEntity[]> {
  return axios.post('/api/ngsi/query/', data).then(res => res.data)
}

/**
 * 导出数据交换包
 * @param type 实体类型（可选，为空则导出全部）
 */
export function exportNgsiPackage(type?: string): Promise<ExportPackage> {
  const params: Record<string, any> = {}
  if (type) {
    params.type = type
  }
  return axios.get('/api/ngsi/export/', { params }).then(res => res.data)
}

/**
 * 获取设备的NGSI-LD数据
 * @param deviceId 设备ID
 */
export function getNgsiDevice(deviceId: string): Promise<NgsiEntity> {
  return axios.get(`/api/ngsi/devices/${deviceId}/`).then(res => res.data)
}

/**
 * 获取设备最新状态的NGSI-LD格式
 * @param deviceId 设备ID
 */
export function getNgsiDeviceStatus(deviceId: string): Promise<NgsiEntity> {
  return axios.get(`/api/ngsi/devices/${deviceId}/status/`).then(res => res.data)
}

/**
 * 获取设备告警的NGSI-LD格式
 * @param deviceId 设备ID
 */
export function getNgsiDeviceAlarms(deviceId: string): Promise<NgsiEntity[]> {
  return axios.get(`/api/ngsi/devices/${deviceId}/alarms/`).then(res => res.data)
}

/**
 * 获取设备预测结果的NGSI-LD格式
 * @param deviceId 设备ID
 */
export function getNgsiPredictions(deviceId: string): Promise<NgsiEntity[]> {
  return axios.get(`/api/ngsi/predictions/${deviceId}/`).then(res => res.data)
}

/**
 * 获取告警列表的NGSI-LD格式
 * @param status 告警状态筛选（可选）
 * @param deviceId 设备ID筛选（可选）
 */
export function getNgsiAlarms(status?: string, deviceId?: string): Promise<NgsiEntity[]> {
  const params: Record<string, any> = {}
  if (status) {
    params.status = status
  }
  if (deviceId) {
    params.device_id = deviceId
  }
  return axios.get('/api/ngsi/alarms/', { params }).then(res => res.data)
}

/**
 * 复制JSON到剪贴板
 * @param data JSON数据
 */
export async function copyJsonToClipboard(data: any): Promise<void> {
  const jsonStr = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
  await navigator.clipboard.writeText(jsonStr)
}

/**
 * 下载JSON文件
 * @param data JSON数据
 * @param filename 文件名
 */
export function downloadJsonFile(data: any, filename: string): void {
  const jsonStr = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/ld+json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
