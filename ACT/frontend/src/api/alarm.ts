// @ts-ignore
import request from '@/utils/request';

// 获取告警中心仪表盘统计数据
export function getAlarmDashboardStats() {
  return request({
    url: '/api/ngsi/alarms/dashboard-stats/',  // 修改这里
    method: 'get',
  });
}

// 获取告警统计信息
export function getAlarmStats() {
  return request({
    url: '/api/ngsi/alarms/stats/',  // 修改这里
    method: 'get',
  });
}

// 获取告警级别分布数据
export function getAlarmLevelDistribution() {
  return request({
    url: '/api/ngsi/alarms/level-distribution/',  // 修改这里
    method: 'get',
  });
}

// 获取告警列表
export function getAlarmList(params: any) {
  // 清理空参数
  const cleanParams: Record<string, any> = {};
  for (const key in params) {
    if (params[key] !== '' && params[key] !== null && params[key] !== undefined) {
      cleanParams[key] = params[key];
    }
  }

  // 状态映射：前端 -> 后端
  const statusMap: Record<string, string> = {
    'NEW': 'OPEN',
    'ACK': 'ACK',
    'CLEAR': 'CLEARED',
    'RESOLVED': 'CLEARED'
  };
  
  if (cleanParams.status && statusMap[cleanParams.status]) {
    cleanParams.status = statusMap[cleanParams.status];
  }

  // 级别映射
  const levelMap: Record<string, string> = {
    'CRITICAL': 'CRITICAL',
    'WARNING': 'ERROR', // 后端是ERROR, WARN等
    'INFO': 'WARN'
  };
  if (cleanParams.level && levelMap[cleanParams.level]) {
    cleanParams.level = levelMap[cleanParams.level];
  }

  return request({
    url: '/api/alarms/',  // 修改为标准接口
    method: 'get',
    params: cleanParams, // 包含'page'，'pageSize'，'keyword'等参数
  });
}

// 获取当前登录用户
const getCurrentUser = () => {
  return localStorage.getItem('username') || 'system';
};

// 确认告警(ACK)
export function ackAlarm(id: string | number) {
  return request({
    url: `/api/alarms/${id}/operate/`,  // 修改这里
    method: 'post',
    data: { 
      'action': 'ACK',
      'operator': getCurrentUser()
    },
  });
}

// 清除告警
export function clearAlarm(id: string | number) {
  return request({
    url: `/api/alarms/${id}/operate/`,  // 修改这里
    method: 'post',
    data: { 
      'action': 'CLEAR',
      'operator': getCurrentUser()
    },
  });
}

// 添加告警备注
export function addAlarmComment(id: string | number, comment: string) {
  return request({
    url: `/api/ngsi/alarms/${id}/comment/`,  // 修改这里
    method: 'post',
    data: { comment },
  });
}

// 获取告警详情
export function getAlarmDetail(id: string | number) {
  return request({
    url: `/api/ngsi/alarms/${id}/`,  // 修改这里
    method: 'get',
  });
}

// 转派告警
export function reassignAlarm(id: string | number, assignee: string) {
  return request({
    url: `/api/ngsi/alarms/${id}/reassign/`,  // 修改这里
    method: 'post',
    data: { assignee },
  });
}


//conformation

// 获取待确认告警列表（支持分页和筛选）
export function getPendingAlarms(params: any) {
  // 清除空值，避免后端解析错误
  const cleanParams: Record<string, any> = {};
  for (const key in params) {
    if (params[key] !== '' && params[key] !== null && params[key] !== undefined) {
      cleanParams[key] = params[key];
    }
  }
  
  // 状态映射：前端 -> 后端
  const statusMap: Record<string, string> = {
    'NEW': 'OPEN',
    'ACK': 'ACK',
    'PROCESSING': 'ACK', // 或者根据需要调整
    'RESOLVED': 'CLEARED'
  };
  
  if (cleanParams.status && statusMap[cleanParams.status]) {
    cleanParams.status = statusMap[cleanParams.status];
  }

  // 级别映射
  const levelMap = {
    'CRITICAL': 'CRITICAL',
    'WARNING': 'ERROR', // 后端是ERROR, WARN等
    'INFO': 'WARN'
  };
  if (cleanParams.level && levelMap[cleanParams.level as keyof typeof levelMap]) {
    cleanParams.level = levelMap[cleanParams.level as keyof typeof levelMap];
  }



  return request({
    url: '/api/alarms/', // 不要只请求 pending，应该请求全部告警列表然后前端通过 status 过滤，或者后端放开 pending 的限制
    method: 'get',
    params: cleanParams, // 包含 page, pageSize, device_type 等参数
  });
}

// 批量确认告警
export function batchConfirmAlarms(alarmIds: (string | number)[], data: any) {
  return request({
    url: '/api/alarms/batch-confirm/',
    method: 'post',
    data: {
      alarm_ids: alarmIds,
      ...data
    },
  });
}

// 获取确认统计信息
export function getConfirmationStats(params: any = {}) {
  return request({
    url: '/api/alarms/confirmation-stats/',
    method: 'get',
    params,
  });
}

// 导出确认列表
export function exportConfirmationList(params: any) {
  return request({
    url: '/api/alarms/export-confirmation/',
    method: 'get',
    params,
    responseType: 'blob', // 用于文件下载
  });
}

// 获取设备类型统计
export function getDeviceTypeStats() {
  return request({
    url: '/api/alarms/device-type-stats/',
    method: 'get',
  });
}