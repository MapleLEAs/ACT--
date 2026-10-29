import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import MainLayout from "@/layout/MainLayout.vue";

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      title: '系统登录',
    },
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      // 仪表盘
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard.vue'),
        meta: {
          title: '仪表盘',
          icon: 'dashboard',
        },
      },
      {
        path: 'realtime-monitor',
        name: 'RealtimeMonitor',
        component: () => import('@/views/RealtimeMonitor.vue'),
        meta: {
          title: '实时监控 (3D)',
          icon: 'video-camera',
        },
      },
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('@/views/DeviceList.vue'),
        meta: {
          title: '设备列表',
          icon: 'device',
        },
      },
      {
        path: 'device-detail/:id',
        name: 'DeviceDetail',
        component: () => import('@/views/DeviceDetail.vue'),
        meta: {
          title: '设备详情',
          icon: 'device',
        },
      },
      {
        path: 'alarm-center',
        name: 'AlarmCenter',
        component: () => import('@/views/AlarmCenter/AlarmCenter.vue'),
        redirect: '/alarm-center/list',
        meta: {
          title: '告警中心',
          icon: 'alarm',
        },
        children: [
          {
            path: 'list',
            name: 'AlarmList',
            component: () => import('@/views/AlarmCenter/AlarmList.vue'),
            meta: {
              title: '告警列表',
              keepAlive: true,
            },
          },
          {
            path: 'handling',
            name: 'AlarmHandling',
            component: () => import('@/views/AlarmCenter/AlarmHandling.vue'),
            meta: {
              title: '告警处理',
              keepAlive: true,
            },
          },
          {
            path: 'confirmation',
            name: 'AlarmConfirmation',
            component: () => import('@/views/AlarmCenter/AlarmConfirmation.vue'),
            meta: {
              title: '告警确认',
              keepAlive: true,
            },
          },
        ],
      },
      {
        path: 'data-analysis',
        name: 'DataAnalysis',
        component: () => import('@/views/DataAnalysis.vue'),
        meta: {
          title: '数据分析',
          icon: 'chart',
        },
      },
      {
        path: 'operation-management',
        name: 'OperationManagement',
        component: () => import('@/views/OperationCenter.vue'),
        meta: {
          title: '运维管理',
          icon: 'operation',
        },
      },
      {
        path: 'root-cause-analysis',
        name: 'RootCauseAnalysis',
        component: () => import('@/views/RootCauseAnalysis.vue'),
        meta: {
          title: '根因分析',
          icon: 'share',
        },
      },
      {
        path: 'ngsi-exchange',
        name: 'NgsiExchange',
        component: () => import('@/views/NgsiExchange.vue'),
        meta: {
          title: 'NGSI‑LD 数据交换',
          icon: 'exchange',
        },
      },
      {
        path: 'database',
        name: 'DatabaseVisualization',
        component: () => import('@/views/DatabaseVisualization.vue'),
        meta: {
          title: '数据库可视化',
          icon: 'database',
        },
      },
      {
        path: 'predictive-maintenance',
        name: 'PredictiveMaintenance',
        component: () => import('@/views/PredictiveMaintenance.vue'),
        meta: {
          title: '预测性维护 2.0',
          icon: 'predictive',
        },
      },
      // ===文档资源管理===
      {
        path: 'doc-manage',
        name: 'DocManage',
        component: () => import('@/views/doc-manage.vue'),
        meta: {
          title: '文档资源管理',
          icon: 'Document',
        },
      },
      // 旧路径重定向，修复侧边栏 /file-classify 警告
      {
        path: 'file-classify',
        redirect: '/doc-manage'
      }
    ],
  },
]

// Cookie读取工具函数
function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null
  return null
}

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 登录守卫
router.beforeEach((to, _from) => {
  if (to.meta.title) {
    document.title = `空管设备数据集中分析系统的设计与实现 - ${to.meta.title}`
  } else {
    document.title = '空管设备数据集中分析系统的设计与实现'
  }

  if (!to.path.includes('/login')) {
    const cookieToken = getCookie('access_token')
    const sessionToken = sessionStorage.getItem('access_token')
    if (!cookieToken && !sessionToken) {
      return '/login'
    }
  }
  return true
})

export default router