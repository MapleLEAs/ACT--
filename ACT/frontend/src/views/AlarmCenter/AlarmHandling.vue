<template>
  <div class="alarm-handling">
    <!-- 顶部导航 -->
    <div class="page-header">
      <h2>告警处理</h2>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="goBack">
          <AppIcon name="back" /> 返回
        </button>
      </div>
    </div>

    <!-- 告警信息卡片 -->
    <div class="alarm-card" v-if="alarm">
      <div class="card-title">告警详情</div>
      
      <div class="alarm-info">
        <div class="info-row">
          <label>告警编号：</label>
          <span>{{ alarm.id }}</span>
        </div>
        <div class="info-row">
          <label>设备名称：</label>
          <span>{{ alarm.device_name }}</span>
        </div>
        <div class="info-row">
          <label>设备类型：</label>
          <span>{{ alarm.device_type }}</span>
        </div>
        <div class="info-row">
          <label>告警信息：</label>
          <span>{{ alarm.message }}</span>
        </div>
        <div class="info-row">
          <label>告警级别：</label>
          <span :class="'level-' + alarm.level.toLowerCase()">{{ getLevelText(alarm.level) }}</span>
        </div>
        <div class="info-row">
          <label>触发时间：</label>
          <span>{{ formatDateTime(alarm.created_at) }}</span>
        </div>
        <div class="info-row">
          <label>当前状态：</label>
          <span :class="'status-' + alarm.status.toLowerCase()">{{ getStatusText(alarm.status) }}</span>
        </div>
      </div>
    </div>

    <!-- 处理表单 -->
    <div class="handling-form">
      <div class="card-title">处理信息</div>
      
      <el-form :model="form" label-width="120px">
        <el-form-item label="处理方式">
          <el-input v-model="form.handle_type" disabled style="width: 200px"/>
        </el-form-item>
        
        <el-form-item label="处理人">
          <el-select v-model="form.handler" placeholder="请选择处理人">
            <el-option label="张三" value="张三"/>
            <el-option label="李四" value="李四"/>
            <el-option label="王五" value="王五"/>
            <el-option label="赵六" value="赵六"/>
          </el-select>
        </el-form-item>
        
        <el-form-item label="处理结果">
          <el-select v-model="form.result" placeholder="请选择处理结果">
            <el-option label="已解决" value="resolved"/>
            <el-option label="待跟进" value="pending"/>
          </el-select>
        </el-form-item>
        
        <el-form-item label="处理备注">
          <el-textarea 
            v-model="form.remark" 
            :rows="4" 
            placeholder="请输入处理备注..."
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :disabled="loading">
            {{ loading ? '处理中...' : '提交处理' }}
          </el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAlarmDetail, ackAlarm, clearAlarm, addAlarmComment } from '@/api/alarm'

const router = useRouter()
const route = useRoute()

const alarm = ref(null)
const loading = ref(false)
const form = ref({
  handle_type: '现场排查',
  handler: '',
  result: '',
  remark: ''
})

const getLevelText = (level) => {
  const map = {
    'CRITICAL': '严重',
    'MAJOR': '重要',
    'MINOR': '次要',
    'WARNING': '警告',
    'INFO': '信息'
  }
  return map[level] || level
}

const getStatusText = (status) => {
  const map = {
    'OPEN': '待确认',
    'ACK': '已确认',
    'CLEARED': '已清除',
    'CLOSED': '已关闭',
    'NEW': '待确认',
    'PROCESSING': '处理中',
    'RESOLVED': '已解决'
  }
  return map[status] || status
}

const formatDateTime = (date) => {
  if (!date) return '--'
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const fetchAlarmDetail = async () => {
  const alarmId = route.query.alarmId
  if (!alarmId) {
    ElMessage.warning('未指定告警ID')
    return
  }
  
  loading.value = true
  try {
    const response = await getAlarmDetail(alarmId)
    alarm.value = response.data || response
  } catch (error) {
    console.error('获取告警详情失败:', error)
    ElMessage.error('获取告警详情失败')
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!form.value.handle_type) {
    ElMessage.warning('请选择处理方式')
    return
  }
  if (!form.value.handler) {
    ElMessage.warning('请选择处理人')
    return
  }
  if (!form.value.result) {
    ElMessage.warning('请选择处理结果')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要提交处理结果吗？', '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
  } catch (e) {
    return
  }
  
  loading.value = true
  try {
    const alarmId = route.query.alarmId
    
    // 先确认告警
    await ackAlarm(alarmId)
    
    // 如果处理结果是已解决，清除告警
    if (form.value.result === 'resolved') {
      await clearAlarm(alarmId)
    }
    
    // 如果有备注，添加备注
    if (form.value.remark) {
      await addAlarmComment(alarmId, form.value.remark)
    }
    
    ElMessage.success('处理成功')
    router.push('/alarm-center/confirmation')
  } catch (error) {
    console.error('处理告警失败:', error)
    ElMessage.error('处理失败，请重试')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/alarm-center/confirmation')
}

onMounted(() => {
  fetchAlarmDetail()
})
</script>

<style scoped>
.alarm-handling {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.alarm-card, .handling-form {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.alarm-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.info-row {
  display: flex;
  align-items: center;
}

.info-row label {
  font-weight: 500;
  color: #666;
  margin-right: 10px;
  min-width: 100px;
}

.info-row span {
  color: #333;
}

.level-critical {
  color: #f56c6c;
  font-weight: 500;
}

.level-major {
  color: #e6a23c;
  font-weight: 500;
}

.level-minor, .level-warning {
  color: #f5a623;
  font-weight: 500;
}

.level-info {
  color: #67c23a;
  font-weight: 500;
}

.status-open, .status-new {
  color: #f56c6c;
  font-weight: 500;
}

.status-ack {
  color: #e6a23c;
  font-weight: 500;
}

.status-cleared, .status-closed, .status-resolved {
  color: #67c23a;
  font-weight: 500;
}

.btn {
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary {
  background: #f5f7fa;
  color: #606266;
}

.btn-secondary:hover {
  background: #e4e7ed;
}
</style>
