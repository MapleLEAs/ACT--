import axios, { type AxiosInstance, type AxiosResponse } from 'axios';
import { ElMessage } from 'element-plus';
import router from '@/router';

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: '', // 使用Vite代理，路径由代理配置处理
  timeout: 10000,
  withCredentials: true // 允许携带 Cookie
});

// 从 Cookie 中获取 Token 的辅助函数
function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null
  return null
}

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 从 Cookie 中读取 Token，而不是从 localStorage
    const token = getCookie('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data;
    
    // 如果后端使用了 CustomJSONRenderer，响应格式为 { code, msg, data }
    if (res && typeof res === 'object' && 'code' in res && 'data' in res) {
      if (res.code >= 200 && res.code < 300) {
        return res.data;
      } else {
        ElMessage.error(res.msg || '请求错误');
        return Promise.reject(new Error(res.msg || 'Error'));
      }
    }
    
    return res;
  },
  (error) => {
    console.error('Response Error:', error.response);

    if (error.response) {
      const { status, data } = error.response;
      const errorMsg = data?.detail || data?.error || `请求错误 (${status})`;

      switch (status) {
        case 400:
          ElMessage.error(`参数错误: ${errorMsg}`);
          break;
        case 401:
          ElMessage.warning('登录已过期，请重新登录');
          // 清除 Cookie
          document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
          document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
          router.push('/login');
          break;
        case 403:
          ElMessage.error('权限不足，无法访问');
          break;
        case 404:
          ElMessage.error('请求的资源不存在');
          break;
        case 500:
          ElMessage.error('服务器内部错误，请稍后重试');
          break;
        default:
          ElMessage.error(errorMsg);
      }
    } else {
      ElMessage.error('网络连接失败，请检查网络设置');
    }
    return Promise.reject(error);
  }
);

export default service;