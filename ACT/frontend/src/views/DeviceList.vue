<template>
  <div class="device-list-container">
    <el-card class="main-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="title">设备管理中心</span>
            <el-tag type="info" size="small" effect="plain" class="count-tag">
              共 {{ devices.length }} 台设备
            </el-tag>
          </div>
          <div class="header-right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索设备 ID 或位置..."
              size="default"
              clearable
              style="width: 240px; margin-right: 15px"
            >
              <template #prefix>
                <el-icon><AppIcon name="search" /></el-icon>
              </template>
            </el-input>
            <el-button type="success" @click="openCreateDialog">
              <el-icon><AppIcon name="add" /></el-icon>
              新增设备
            </el-button>
            <el-button type="warning" @click="batchDialogVisible = true">
              <el-icon><AppIcon name="import" /></el-icon>
              批量导入
            </el-button>
            <el-button type="primary" @click="exportDevices">
              <el-icon><AppIcon name="export" /></el-icon>
              导出
            </el-button>
            <el-button type="primary" @click="fetchDevices" :loading="loading">
              <el-icon><AppIcon name="refresh" :spin="loading" /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table 
        :data="filteredDevices" 
        v-loading="loading" 
        style="width: 100%"
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
      >
        <el-table-column prop="device_id" label="资产编号" width="160" sortable />
        <el-table-column prop="device_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="light">{{ row.device_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="device_model" label="型号" min-width="150" />
        <el-table-column prop="location" label="安装位置" min-width="150">
          <template #default="{ row }">
            <div class="location-cell">
              <el-icon><AppIcon name="location" /></el-icon>
              <span>{{ row.location }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="健康度" width="130">
          <template #default="scope">
            <el-tag :type="getAlarmLevelType(scope.row.alarm_level)" size="small" effect="dark">
              {{ getAlarmLevelText(scope.row.alarm_level) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="在线状态" width="120">
          <template #default="scope">
            <div class="status-cell">
              <span class="status-indicator" :class="scope.row.online_status ? 'online' : 'offline'"></span>
              <span>{{ scope.row.online_status ? '在线' : '离线' }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="handleEdit(scope.row)">
              <el-icon><AppIcon name="edit" /></el-icon>
              编辑
            </el-button>
            <el-button link type="danger" @click="handleDelete(scope.row)">
              <el-icon><AppIcon name="delete" /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="设备属性配置"
      width="550px"
      destroy-on-close
      class="custom-dialog"
    >
      <el-form :model="editForm" ref="editFormRef" :rules="formRules" label-width="100px" label-position="left">
        <el-form-item label="资产编号">
          <el-input v-model="editForm.device_id" disabled />
        </el-form-item>
        
        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="editForm.device_type" placeholder="请选择设备类型" style="width: 100%">
            <el-option label="甚高频通信设备 (VHF)" value="VHF" />
            <el-option label="仪表着陆系统 (ILS)" value="ILS" />
            <el-option label="全向信标 (VOR)" value="VOR" />
            <el-option label="测距仪 (DME)" value="DME" />
            <el-option label="短波通信设备 (HF)" value="HF" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="设备型号" prop="device_model">
          <el-input v-model="editForm.device_model" placeholder="请输入设备型号" />
        </el-form-item>
        
        <el-form-item label="安装位置" prop="location">
          <el-input v-model="editForm.location" placeholder="请输入安装位置" />
        </el-form-item>
        
        <el-form-item label="制造商" prop="manufacturer">
          <el-input v-model="editForm.manufacturer" placeholder="请输入制造商名称" />
        </el-form-item>
        
        <el-form-item label="安装时间" prop="install_time">
          <el-date-picker 
            v-model="editForm.install_time" 
            type="datetime" 
            placeholder="选择安装日期时间"
            format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSave" :loading="saving">
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 新增设备弹窗 -->
    <el-dialog v-model="createDialogVisible" title="新增设备" width="550px" destroy-on-close>
      <el-form :model="createForm" ref="createFormRef" :rules="createRules" label-width="100px">
        <el-form-item label="资产编号" prop="device_id">
          <el-input v-model="createForm.device_id" placeholder="如 VOR001" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="createForm.device_type" placeholder="请选择" style="width: 100%">
            <el-option label="甚高频通信设备 (VHF)" value="VHF" />
            <el-option label="仪表着陆系统 (ILS)" value="ILS" />
            <el-option label="全向信标 (VOR)" value="VOR" />
            <el-option label="测距仪 (DME)" value="DME" />
            <el-option label="短波通信设备 (HF)" value="HF" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备型号" prop="device_model">
          <el-input v-model="createForm.device_model" />
        </el-form-item>
        <el-form-item label="安装位置" prop="location">
          <el-input v-model="createForm.location" />
        </el-form-item>
        <el-form-item label="制造商">
          <el-input v-model="createForm.manufacturer" />
        </el-form-item>
        <el-form-item label="安装时间">
          <el-date-picker v-model="createForm.install_time" type="datetime" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="batchDialogVisible" title="批量导入设备" width="720px" destroy-on-close>
      <p class="batch-tip">粘贴 JSON 数组，或按模板填写后提交。支持部分成功。</p>
      <el-input
        v-model="batchJson"
        type="textarea"
        :rows="12"
        placeholder='[{"device_id":"VOR001","device_type":"VOR","device_model":"Model-A","location":"A站","manufacturer":"厂商A","install_time":"2026-06-17T10:00:00Z"}]'
      />
      <div class="batch-actions">
        <el-button @click="fillBatchTemplate">填充模板</el-button>
        <el-button type="primary" :loading="batchSubmitting" @click="handleBatchImport">提交导入</el-button>
      </div>
      <div v-if="batchResult" class="batch-result">
        <el-alert
          :title="`成功 ${batchResult.created_count} 条，失败 ${batchResult.failed_count} 条`"
          :type="batchResult.failed_count ? 'warning' : 'success'"
          show-icon
          :closable="false"
        />
        <ul v-if="batchResult.errors?.length">
          <li v-for="(err, idx) in batchResult.errors" :key="idx">
            第 {{ err.index + 1 }} 行 [{{ err.device_id || '-' }}]: {{ formatError(err.message) }}
          </li>
        </ul>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { getDevices, updateDevice, deleteDevice, createDevice, batchCreateDevices } from '@/api/device'
import { useDataSyncStore } from '@/store/dataSync'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'

const dataSyncStore = useDataSyncStore()

const devices = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const searchQuery = ref('')
const editFormRef = ref<FormInstance>()
const createFormRef = ref<FormInstance>()
const createDialogVisible = ref(false)
const batchDialogVisible = ref(false)
const creating = ref(false)
const batchSubmitting = ref(false)
const batchJson = ref('')
const batchResult = ref<any>(null)

const createForm = ref({
  device_id: '',
  device_type: '',
  device_model: '',
  location: '',
  manufacturer: '',
  install_time: null as Date | string | null,
})

const createRules = {
  device_id: [{ required: true, message: '请输入资产编号', trigger: 'blur' }],
  device_type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  device_model: [{ required: true, message: '请输入设备型号', trigger: 'blur' }],
  location: [{ required: true, message: '请输入安装位置', trigger: 'blur' }],
}

const editForm = ref({
  device_id: '',
  device_type: '',
  device_model: '',
  location: '',
  manufacturer: '',
  install_time: null as Date | string | null,
  status: 'online'
})

const formRules = {
  device_type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  device_model: [{ required: true, message: '请输入设备型号', trigger: 'blur' }],
  location: [{ required: true, message: '请输入安装位置', trigger: 'blur' }]
}

const filteredDevices = computed(() => {
  if (!searchQuery.value) return devices.value
  const q = searchQuery.value.toLowerCase()
  return devices.value.filter(d => 
    d.device_id.toLowerCase().includes(q) || 
    d.location?.toLowerCase().includes(q) ||
    d.device_model?.toLowerCase().includes(q)
  )
})

const fetchDevices = async () => {
  loading.value = true
  try {
    const res: any = await getDevices()
    devices.value = res.data || res.results || res
  } catch (error) {
    ElMessage.error('获取设备列表失败')
  } finally {
    loading.value = false
  }
}

// 导出当前（过滤后）设备列表为 JSON 文件
const exportDevices = () => {
  const data = filteredDevices.value
  if (!data.length) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `devices_export_${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success(`已导出 ${data.length} 台设备`)
}

const getAlarmLevelType = (level: string) => {
  const map: Record<string, string> = {
    'critical': 'danger',
    'error': 'danger',
    'warning': 'warning',
    'info': 'info',
    'none': 'success',
  }
  return map[level?.toLowerCase()] || 'success'
}

const getAlarmLevelText = (level: string) => {
  const map: Record<string, string> = {
    'critical': '严重故障',
    'error': '重要故障',
    'warning': '次要故障',
    'info': '一般提醒',
    'none': '运行良好',
  }
  return map[level?.toLowerCase()] || '运行良好'
}

const handleEdit = (row: any) => {
  editForm.value = {
    device_id: row.device_id || '',
    device_type: row.device_type || '',
    device_model: row.device_model || '',
    location: row.location || '',
    manufacturer: row.manufacturer || '',
    install_time: row.install_time ? new Date(row.install_time) : null,
    status: row.status || 'online'
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    saving.value = true
    try {
      const payload = {
        device_type: editForm.value.device_type,
        device_model: editForm.value.device_model,
        location: editForm.value.location,
        manufacturer: editForm.value.manufacturer,
        install_time: editForm.value.install_time instanceof Date 
          ? editForm.value.install_time.toISOString() 
          : editForm.value.install_time
      }
      
      await updateDevice(editForm.value.device_id, payload)
      ElMessage.success('配置已更新')
      dialogVisible.value = false
      fetchDevices()
    } catch (error) {
      ElMessage.error('保存失败')
    } finally {
      saving.value = false
    }
  })
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确定要永久删除资产 ${row.device_id} 吗？此操作不可撤销。`,
    '安全确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await deleteDevice(row.device_id)
      ElMessage.success('设备已移除')
      fetchDevices()
      dataSyncStore.notifyDevicesChanged()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const openCreateDialog = () => {
  createForm.value = {
    device_id: '',
    device_type: '',
    device_model: '',
    location: '',
    manufacturer: '',
    install_time: null,
  }
  createDialogVisible.value = true
}

const handleCreate = async () => {
  if (!createFormRef.value) return
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return
    creating.value = true
    try {
      const payload = {
        ...createForm.value,
        install_time: createForm.value.install_time instanceof Date
          ? createForm.value.install_time.toISOString()
          : createForm.value.install_time,
      }
      await createDevice(payload)
      ElMessage.success('设备创建成功')
      createDialogVisible.value = false
      fetchDevices()
      dataSyncStore.notifyDevicesChanged()
    } catch {
      ElMessage.error('创建设备失败')
    } finally {
      creating.value = false
    }
  })
}

const fillBatchTemplate = () => {
  batchJson.value = JSON.stringify([
    {
      device_id: 'VOR001',
      device_type: 'VOR',
      device_model: 'Model-A',
      location: 'A站',
      manufacturer: '厂商A',
      install_time: new Date().toISOString(),
    },
  ], null, 2)
}

const formatError = (message: any) => {
  if (typeof message === 'string') return message
  return JSON.stringify(message)
}

const handleBatchImport = async () => {
  batchSubmitting.value = true
  batchResult.value = null
  try {
    const parsed = JSON.parse(batchJson.value || '[]')
    if (!Array.isArray(parsed) || !parsed.length) {
      ElMessage.warning('请提供有效的 JSON 数组')
      return
    }
    const res: any = await batchCreateDevices(parsed)
    batchResult.value = res.data || res
    if (batchResult.value.created_count > 0) {
      fetchDevices()
      dataSyncStore.notifyDevicesChanged()
    }
    ElMessage.success(`导入完成：成功 ${batchResult.value.created_count} 条`)
  } catch {
    ElMessage.error('批量导入失败，请检查 JSON 格式')
  } finally {
    batchSubmitting.value = false
  }
}

watch(() => dataSyncStore.devicesVersion, () => {
  fetchDevices()
})

onMounted(() => {
  fetchDevices()
})
</script>

<style scoped>
.device-list-container {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 60px);
}

.main-card {
  border-radius: 8px;
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.count-tag {
  font-weight: normal;
}

.header-right {
  display: flex;
  align-items: center;
}

.location-cell {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #909399;
}

.status-indicator.online {
  background-color: #52c41a;
  box-shadow: 0 0 5px #52c41a;
}

.status-indicator.offline {
  background-color: #f5222d;
}

.custom-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #f0f0f0;
  margin-right: 0;
  padding-bottom: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.batch-tip {
  margin: 0 0 12px;
  color: #909399;
  font-size: 13px;
}

.batch-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 12px;
}

.batch-result {
  margin-top: 16px;
}

.batch-result ul {
  margin: 12px 0 0;
  padding-left: 18px;
  color: #f56c6c;
  font-size: 13px;
}
</style>
