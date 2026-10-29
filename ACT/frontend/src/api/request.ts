import axios from 'axios'
import type { InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: '', // 使用Vite代理，路径由代理配置处理
  timeout: 30000,
  withCredentials: true // 允许携带 Cookie
})

// 从 Cookie 中获取 Token 的辅助函数
function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null
  return null
}

// 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getCookie('access_token') || sessionStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

service.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    
    if (res && typeof res === 'object' && 'access' in res && 'refresh' in res) {
      return res
    }
    
    if (res && typeof res === 'object' && 'code' in res && 'data' in res) {
      if (res.code === 200 || res.code === 201) {
        return res.data
      } else {
        ElMessage.error(res.msg || '请求错误')
        return Promise.reject(new Error(res.msg || 'Error'))
      }
    }
    
    return res
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      sessionStorage.removeItem('access_token')
      document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
      document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
      
      if (!window.location.pathname.includes('/login')) {
        ElMessage.warning('登录已过期，请重新登录')
        setTimeout(() => {
          window.location.href = '/login'
        }, 1500)
      }
    } else {
      const errorMsg = error.response?.data?.msg || error.response?.data?.detail || error.message || '请求失败'
      ElMessage.error(errorMsg)
    }
    return Promise.reject(error)
  }
)

export default service
