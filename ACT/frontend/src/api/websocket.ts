import { ElNotification } from 'element-plus'

// 定义回调函数的类型
type MessageCallback = (data: any) => void;

export function useWebSocket() {
  let socket: WebSocket | null = null
  const callbacks = new Set<MessageCallback>();

  const connect = () => {
    // 根据当前协议选择 ws 或 wss
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/notifications/`

    socket = new WebSocket(wsUrl)

    socket.onopen = () => {
      console.log('WebSocket connected')
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      // 触发所有订阅的回调
      callbacks.forEach(callback => callback(data));

      // 根据消息类型处理通知
      switch (data.type) {
        case 'ALARM_TRIGGERED':
          showAlarmNotification(data.data)
          break
        case 'ANOMALY_DETECTED':
          showAnomalyNotification(data.data)
          break
        case 'STATUS_UPDATED':
          // 状态更新通常不弹窗，但在控制台记录
          console.log('Device status updated:', data.data)
          break
      }
    }

    socket.onclose = () => {
      console.log('WebSocket disconnected, retrying in 5s...')
      setTimeout(connect, 5000)
    }

    socket.onerror = (error) => {
      console.error('WebSocket error:', error)
      socket?.close()
    }
  }

  // 发送消息的方法
  const send = (data: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  }

  // 订阅消息的方法
  const subscribe = (callback: MessageCallback) => {
    callbacks.add(callback);
    return () => callbacks.delete(callback); // 返回取消订阅的函数
  }

  const showAlarmNotification = (eventData: any) => {
    const metadata = eventData.metadata || {}
    const typeMap: Record<string, string> = {
      'CRITICAL': 'error',
      'ERROR': 'error',
      'WARN': 'warning',
      'INFO': 'info'
    }

    ElNotification({
      title: `新告警: ${metadata.message || '指标异常'}`,
      message: `设备 ${metadata.device_id} 的 ${metadata.metric} 触发告警！当前值: ${metadata.value}`,
      type: (typeMap[metadata.severity] || 'info') as any,
      duration: 0,
      position: 'bottom-right'
    })
  }

  const showAnomalyNotification = (eventData: any) => {
    const metadata = eventData.metadata || {}
    ElNotification({
      title: `异常检测: 发现疑似异常`,
      message: `设备 ${metadata.device_id} 出现异常偏离 (分数: ${metadata.anomaly_score?.toFixed(2)})`,
      type: 'warning',
      duration: 8000,
      position: 'bottom-right'
    })
  }

  return {
    connect,
    send,
    subscribe
  }
}
