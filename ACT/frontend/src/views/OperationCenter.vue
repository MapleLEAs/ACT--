<template>
  <div class="operation-center-container">
    <!-- 顶部概览 -->
    <div class="page-header">
      <div class="header-left">
        <h1>运维中心</h1>
        <div class="header-stats">
          <el-tag type="primary" effect="plain" class="stat-tag">
            <AppIcon name="tools" />
            {{ stats.pending_orders }} 待处理工单
          </el-tag>
          <el-tag type="success" effect="plain" class="stat-tag">
            <el-icon><AppIcon name="calendar" /></el-icon>
            {{ stats.upcoming_plans }} 即将到期计划
          </el-tag>
        </div>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreateOrder"><AppIcon name="add" />创建工单</el-button>
        <el-button @click="fetchData"><AppIcon name="refresh" />刷新</el-button>
      </div>
    </div>

    <!-- 内容区域 -->
    <el-row :gutter="20" class="content-row">
      <!-- 左侧：工单管理 -->
      <el-col :span="14">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="card-header-flex">
              <span class="card-title"><el-icon><AppIcon name="document" /></el-icon> 工单管理</span>
              <el-radio-group v-model="orderTab" size="small">
                <el-radio-button label="pending">待处理</el-radio-button>
                <el-radio-button label="processing">处理中</el-radio-button>
                <el-radio-button label="completed">已完成</el-radio-button>
                <el-radio-button label="all">全部</el-radio-button>
              </el-radio-group>
            </div>
          </template>

          <el-table :data="currentOrders" stripe style="width: 100%">
            <el-table-column prop="id" label="工单号" width="120">
              <template #default="{ row }">
                <span class="order-id">#{{ row.id }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="device" label="关联设备" width="140">
              <template #default="{ row }">
                {{ row.device_name || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="100">
              <template #default="{ row }">
                <el-tag :type="getPriorityType(row.priority)" size="small">
                  {{ row.priority_text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getOrderStatusType(row.status)" size="small">
                  {{ row.status_text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="handleViewOrder(row)">查看</el-button>
                <el-button type="info" size="small" link @click="handleProcessOrder(row)" v-if="row.status !== 'completed'">处理</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination-wrapper">
            <el-pagination small layout="prev, pager, next" :total="orders.length" />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：维护计划 -->
      <el-col :span="10">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="card-header-flex">
              <span class="card-title"><el-icon><AppIcon name="clock" /></el-icon> 维护计划</span>
              <el-button type="primary" size="small" link><AppIcon name="add" />新增</el-button>
            </div>
          </template>

          <el-timeline>
            <el-timeline-item
              v-for="(plan, index) in maintenancePlans"
              :key="index"
              :timestamp="formatTime(plan.scheduled_time)"
              placement="top"
              :type="plan.type"
              :color="getPlanColor(plan.status)"
            >
              <div class="plan-item">
                <div class="plan-header">
                  <span class="plan-name">{{ plan.name }}</span>
                  <el-tag :type="getPlanTagType(plan.status)" size="small">{{ plan.status_text }}</el-tag>
                </div>
                <p class="plan-desc">{{ plan.description }}</p>
                <div class="plan-meta">
                  <span class="plan-device">设备: {{ plan.device_name }}</span>
                  <span class="plan-type">类型: {{ plan.type_text }}</span>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
          
          <div v-if="maintenancePlans.length === 0" class="empty-state">
            <el-empty description="暂无维护计划" />
          </div>
        </el-card>

        <!-- 今日巡检 -->
        <el-card shadow="never" class="section-card mt-20">
          <template #header>
            <span class="card-title"><AppIcon name="box" /> 今日巡检任务</span>
          </template>

          <el-steps :active="inspectionProgress" finish-status="success" direction="vertical">
            <el-step
              v-for="(task, idx) in todayInspections"
              :key="idx"
              :title="task.title"
              :description="task.location"
            />
          </el-steps>
          
          <div class="inspection-actions">
            <el-button 
              type="primary" 
              style="width: 100%; margin-top: 10px" 
              :disabled="isInspecting"
              @click="startInspection"
            >
              {{ isInspecting ? '巡检中...' : '开始巡检' }}
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建工单弹窗 -->
    <el-dialog
      v-model="createOrderVisible"
      title="创建运维工单"
      width="600px"
    >
      <el-form :model="orderForm" label-width="100px">
        <el-form-item label="工单标题">
          <el-input v-model="orderForm.title" placeholder="请输入工单标题" />
        </el-form-item>
        <el-form-item label="关联设备">
          <el-select v-model="orderForm.device_id" placeholder="选择设备" style="width: 100%">
            <el-option v-for="dev in devices" :key="dev.device_id" :label="dev.name" :value="dev.device_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="orderForm.priority" style="width: 100%">
            <el-option label="紧急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题描述">
          <el-input type="textarea" v-model="orderForm.description" :rows="4" placeholder="请详细描述问题..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createOrderVisible = false">取消</el-button>
        <el-button type="primary" @click="submitOrder">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getDevices } from '@/api/device'
import { useDataSyncStore } from '@/store/dataSync'

const dataSyncStore = useDataSyncStore()

// 状态
const loading = ref(false)
const devices = ref<any[]>([])
const orders = ref<any[]>([])
const orderTab = ref('pending')
const createOrderVisible = ref(false)

// 工单表单
const orderForm = ref({
  title: '',
  device_id: '',
  priority: 'medium',
  description: ''
})

// 模拟数据 - 概览
const stats = ref({
  pending_orders: 3,
  upcoming_plans: 2
})

// 模拟数据 - 维护计划
const maintenancePlans = ref([
  {
    id: 1,
    name: 'VHF-01 季度校准',
    description: '按照民航局标准进行频率校准测试',
    device_name: 'VHF-西塔台',
    type: 'primary',
    status: 'scheduled',
    status_text: '待执行',
    type_text: '校准',
    scheduled_time: new Date(Date.now() + 3600000 * 4).toISOString()
  },
  {
    id: 2,
    name: 'ILS-02 天线检查',
    description: '检查下滑道天线阵列',
    device_name: 'ILS-02L',
    type: 'warning',
    status: 'in_progress',
    status_text: '进行中',
    type_text: '巡检',
    scheduled_time: new Date(Date.now() - 3600000 * 2).toISOString()
  }
])

// 模拟数据 - 今日巡检
const todayInspections = ref([
  { title: '东塔台 VHF 组巡检', location: '东塔台 3F', completed: true },
  { title: '主跑道 ILS 巡检', location: '01L 跑道头', completed: false },
  { title: '气象雷达站检查', location: '气象雷达楼', completed: false }
])

const inspectionProgress = computed(() => {
  return todayInspections.value.filter(t => t.completed).length
})

// 巡检状态
const isInspecting = ref(false)

// 巡检操作
const startInspection = async () => {
  const currentIndex = inspectionProgress.value
  if (currentIndex >= todayInspections.value.length) {
    ElMessage.success('今日巡检任务已全部完成！')
    return
  }
  
  isInspecting.value = true
  ElMessage.info(`开始巡检: ${todayInspections.value[currentIndex].title}`)
  
  // 模拟巡检过程
  for (let i = currentIndex; i < todayInspections.value.length; i++) {
    // 模拟每个巡检点耗时2秒
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 标记当前任务完成
    todayInspections.value[i].completed = true
    
    // 显示巡检结果
    ElMessage.success(`✓ ${todayInspections.value[i].title} - 检查完成`)
  }
  
  isInspecting.value = false
  ElMessage.success('🎉 今日巡检任务全部完成！')
}

// 计算属性
const currentOrders = computed(() => {
  // 模拟数据
  const mockOrders = [
    {
      id: 'WO-2025001',
      title: 'VHF-03 信号衰减严重',
      device_name: 'VHF-03',
      priority: 'high',
      priority_text: '高',
      status: 'pending',
      status_text: '待处理',
      created_at: new Date(Date.now() - 7200000).toISOString(),
      description: '值班员报告信号强度波动明显'
    },
    {
      id: 'WO-2025002',
      title: 'DME-01 测距误差偏大',
      device_name: 'DME-01',
      priority: 'urgent',
      priority_text: '紧急',
      status: 'processing',
      status_text: '处理中',
      created_at: new Date(Date.now() - 10800000).toISOString(),
      description: '误差已超过 0.1 海里'
    },
    {
      id: 'WO-2024120',
      title: '例行设备清洁',
      device_name: 'VHF-组',
      priority: 'low',
      priority_text: '低',
      status: 'completed',
      status_text: '已完成',
      created_at: new Date(Date.now() - 86400000).toISOString(),
      description: '每日例行'
    }
  ]
  
  if (orderTab.value === 'all') return mockOrders
  return mockOrders.filter(o => o.status === orderTab.value)
})

// 工具函数
const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

const getPriorityType = (p: string) => {
  const map: any = { urgent: 'danger', high: 'warning', medium: 'info', low: '' }
  return map[p] || ''
}

const getOrderStatusType = (s: string) => {
  const map: any = { pending: 'danger', processing: 'warning', completed: 'success' }
  return map[s] || ''
}

const getPlanColor = (s: string) => {
  const map: any = { scheduled: '#409eff', in_progress: '#e6a23c', completed: '#67c23a' }
  return map[s] || '#909399'
}

const getPlanTagType = (s: string) => {
  const map: any = { scheduled: 'info', in_progress: 'warning', completed: 'success' }
  return map[s] || 'info'
}

// 数据获取
const fetchData = async () => {
  loading.value = true
  try {
    const res = await getDevices()
    devices.value = res.results || res
  } catch (e) {
    ElMessage.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

// 操作函数
const handleCreateOrder = () => {
  createOrderVisible.value = true
}

const handleViewOrder = (row: any) => {
  ElMessage.info(`查看工单: ${row.title}`)
}

const handleProcessOrder = (row: any) => {
  ElMessage.info(`处理工单: ${row.title}`)
}

const submitOrder = () => {
  ElMessage.success('工单创建成功')
  createOrderVisible.value = false
  orderForm.value = { title: '', device_id: '', priority: 'medium', description: '' }
}

onMounted(() => {
  fetchData()
})

watch(() => dataSyncStore.devicesVersion, () => {
  fetchData()
})
</script>

<style scoped>
.operation-center-container {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  color: #1f2937;
}

.header-stats {
  display: flex;
  gap: 12px;
}

.stat-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

.content-row {
  margin-top: 0;
}

.section-card {
  margin-bottom: 20px;
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: bold;
  color: #1f2937;
}

.order-id {
  font-family: 'Monaco', 'Consolas', monospace;
  color: #1890ff;
  font-weight: bold;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.plan-item {
  padding: 4px 0;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.plan-name {
  font-weight: 500;
  color: #1f2937;
}

.plan-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 4px 0;
}

.plan-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #9ca3af;
}

.empty-state {
  padding: 20px 0;
}

.mt-20 {
  margin-top: 20px;
}
</style>
