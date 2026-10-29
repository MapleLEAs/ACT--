<template>
  <div class="monitor-container">
    <!-- 顶部导航栏 -->
    <header class="monitor-header">
      <div class="header-left">
        <el-button type="text" @click="goBack" class="back-btn">
          <AppIcon name="back" />
          <span>返回首页</span>
        </el-button>
        <div class="divider"></div>
        <span class="page-title">实时监控分析中心</span>
      </div>
      <div class="header-right">
        <div class="status-indicator">
          <span class="pulse-dot" :class="{ active: isWsConnected }"></span>
          <span class="status-text">{{ isWsConnected ? '实时同步中' : '离线模式' }}</span>
        </div>
        <span class="current-time">{{ currentTime }}</span>
      </div>
    </header>

    <!-- 主要内容区 -->
    <main class="monitor-layout">
      <!-- 左侧：设备状态列表 -->
      <aside class="side-panel left-panel">
        <div class="panel-header">
          <span class="panel-title">设备在线状态</span>
          <el-badge :value="onlineCount" type="success" class="online-badge">
              <el-button circle size="small" @click="refreshDeviceList">
                <AppIcon name="refresh" />
              </el-button>
          </el-badge>
        </div>
        
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索设备..."
            size="small"
            clearable
          >
            <template #prefix>
              <el-icon><AppIcon name="search" /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="device-list custom-scrollbar">
          <el-empty v-if="filteredDevices.length === 0" :image-size="60" description="未发现匹配设备" />
          <div 
            v-else
            v-for="device in filteredDevices" 
            :key="device.id" 
            class="device-item"
            :class="{ active: selectedDeviceId === device.deviceId, 'has-alarm': device.status === 'error' }"
            @click="focusDevice(device)"
          >
            <div class="device-status-icon">
              <span class="status-dot" :style="{ backgroundColor: device.statusDot.color }"></span>
            </div>
            <div class="device-info">
              <div class="device-name-row">
                <span class="device-name">{{ device.name }}</span>
                <el-tag v-if="device.status === 'error'" size="small" type="danger" effect="dark">告警</el-tag>
              </div>
              <div class="device-meta">
                <span class="device-location">{{ device.location }}</span>
                <span class="device-type">{{ device.device_type }}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 中间：Three.js 3D 场景区域 -->
      <section class="scene-panel">
        <div class="scene-controls">
          <el-button-group>
            <el-tooltip content="重置视角" placement="bottom">
              <el-button size="small" @click="resetCamera"><el-icon><Aim /></el-icon></el-button>
            </el-tooltip>
            <el-tooltip content="显示网格" placement="bottom">
              <el-button size="small" :type="showGrid ? 'primary' : 'default'" @click="toggleGrid">
                <el-icon><Grid /></el-icon>
              </el-button>
            </el-tooltip>
          </el-button-group>
          
          <div class="scene-stats" v-if="hoveredDevice">
            <span class="label">当前指向:</span>
            <span class="value">{{ hoveredDevice.name }}</span>
          </div>
        </div>

        <div 
          ref="sceneRef" 
          class="three-scene-container"
          @click="onSceneClick"
          @contextmenu.prevent="openContextMenu"
        ></div>

        <div class="scene-overlay">
          <div class="legend">
            <div class="legend-item"><span class="dot green"></span> 在线</div>
            <div class="legend-item"><span class="dot orange"></span> 离线</div>
            <div class="legend-item"><span class="dot red"></span> 异常</div>
          </div>
        </div>
      </section>

      <!-- 右侧：虚拟设备库与属性 -->
      <aside class="side-panel right-panel">
        <div class="panel-header">
          <span class="panel-title">资产库</span>
        </div>
        
        <div class="library-grid">
          <div 
            v-for="type in availableDeviceTypes"
            :key="type.code"
            class="library-item" 
            :class="{ active: selectedDeviceType === type.code }"
            @click="selectDeviceType(type.code)"
          >
            <div class="model-preview">
              <el-icon size="24"><component :is="type.icon" /></el-icon>
            </div>
            <div class="model-name">{{ type.name }}</div>
          </div>
        </div>

        <div class="placement-tip" v-if="selectedDeviceType">
          <div class="tip-content">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>点击场景放置设备</span>
          </div>
          <el-button link type="primary" size="small" @click="cancelSelection">取消</el-button>
        </div>

        <div v-if="currentDeviceInfo" class="device-details-panel">
          <div class="panel-divider"></div>
          <div class="panel-header">
            <span class="panel-title">设备属性</span>
          </div>
          <div class="details-content">
            <div class="detail-row">
              <span class="label">资产编号</span>
              <span class="value">{{ currentDeviceInfo.deviceId }}</span>
            </div>
            <div class="detail-row">
              <span class="label">安装位置</span>
              <span class="value">{{ currentDeviceInfo.location }}</span>
            </div>
            <div class="detail-row">
              <span class="label">运行状态</span>
              <el-tag :type="getStatusType(currentDeviceInfo.status)" size="small">
                {{ currentDeviceInfo.statusText }}
              </el-tag>
            </div>
            <div class="detail-actions">
              <el-button type="primary" plain size="small" @click="viewHistory">历史趋势</el-button>
              <el-button type="danger" plain size="small" @click="deleteDevice">移除设备</el-button>
            </div>
          </div>
        </div>
      </aside>
    </main>

    <!-- 右键删除菜单 -->
    <div
      v-if="contextMenuVisible"
      class="context-menu"
      :style="{ left: contextX + 'px', top: contextY + 'px' }"
    >
      <div class="context-item" @click="deleteDevice">删除设备</div>
    </div>

    <!-- 新建设备配置弹窗 -->
    <el-dialog
      v-model="deviceConfigVisible"
      title="新建设备配置"
      width="600px"
      :close-on-click-modal="false"
      :before-close="handleConfigClose"
    >
      <el-form
        ref="configFormRef"
        :model="deviceConfigForm"
        :rules="configFormRules"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="设备名称 *" prop="name">
          <el-input
            v-model="deviceConfigForm.name"
            placeholder="请输入设备名称"
            maxlength="50"
            show-word-limit
            @blur="checkDeviceNameUnique"
          >
            <template #prefix>
              <el-icon><AppIcon name="document" /></el-icon>
            </template>
          </el-input>
          <div v-if="nameExistsError" class="error-tip">{{ nameExistsError }}</div>
        </el-form-item>

        <el-form-item label="设备型号 *" prop="device_model">
          <el-select
            v-model="deviceConfigForm.device_model"
            placeholder="请选择设备型号"
            style="width: 100%"
          >
            <el-option
              v-for="model in deviceModels"
              :key="model.value"
              :label="model.label"
              :value="model.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="设备位置 *" prop="location">
          <el-input
            v-model="deviceConfigForm.location"
            placeholder="请输入设备安装位置"
            maxlength="100"
          >
            <template #prefix>
              <AppIcon name="location" />
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="3D 坐标">
          <el-input
            :model-value="positionText"
            disabled
            placeholder="自动获取"
          >
            <template #prefix>
              <el-icon><Coordinate /></el-icon>
            </template>
          </el-input>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleConfigClose">取消</el-button>
          <el-button type="primary" @click="submitDeviceConfig" :loading="isSubmitting">
            {{ isSubmitting ? '保存中...' : '保存' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 取消配置确认弹窗 -->
    <el-dialog
      v-model="cancelConfirmVisible"
      title="提示"
      width="400px"
      :close-on-click-modal="false"
    >
      <p>设备未配置，是否删除？</p>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleCancelConfirm(false)">保留</el-button>
          <el-button type="danger" @click="handleCancelConfirm(true)">删除</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElLoading, ElMessage, ElEmpty, ElDialog, ElForm, ElInput, ElSelect, ElOption, ElTag, ElBadge, ElTooltip, ElButtonGroup, ElButton } from 'element-plus'
import { Document, Coordinate, Aim, Grid, Loading } from '@element-plus/icons-vue'
import { getDevices } from '@/api/device'
import request from '@/api/request'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js'
import { useWebSocketStore } from '@/store/websocket'

const router = useRouter()
const wsStore = useWebSocketStore()

const currentTime = ref('')
const deviceList = ref<any[]>([])
const sceneRef = ref<HTMLDivElement | null>(null)
const searchQuery = ref('')
const selectedDeviceId = ref('')
const showGrid = ref(true)
const hoveredDevice = ref<any>(null)
const isWsConnected = computed(() => wsStore.isConnected)

const currentDeviceInfo = ref<any>(null)

// 右键菜单
const contextMenuVisible = ref(false)
const contextX = ref(0)
const contextY = ref(0)
const rightClickDeviceId = ref('')

// 设备配置相关
const selectedDeviceType = ref('')
const deviceConfigVisible = ref(false)
const configFormRef = ref<any>(null)
const isSubmitting = ref(false)
const nameExistsError = ref('')
const cancelConfirmVisible = ref(false)
const tempDeviceData = ref<any>(null)

// 设备型号选项
const deviceModels = ref([
  { value: 'VHF-Model-X', label: 'VHF 通信设备 X 型' },
  { value: 'VHF-Model-Y', label: 'VHF 通信设备 Y 型' },
  { value: 'ILS-Model-A', label: 'ILS 仪表着陆系统 A 型' },
  { value: 'ILS-Model-B', label: 'ILS 仪表着陆系统 B 型' },
])

// 设备配置表单
const deviceConfigForm = ref({
  name: '',
  device_model: '',
  location: '',
  position_x: 0,
  position_y: 0,
  position_z: 0,
})

// 表单验证规则
const configFormRules = ref({
  name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  device_model: [
    { required: true, message: '请选择设备型号', trigger: 'change' },
  ],
  location: [
    { required: true, message: '请输入设备位置', trigger: 'blur' },
  ],
})

// 3D 坐标文本
const positionText = computed(() => {
  const { position_x, position_y, position_z } = deviceConfigForm.value
  return `X: ${position_x.toFixed(2)}, Y: ${position_y.toFixed(2)}, Z: ${position_z.toFixed(2)}`
})

// 设备类型定义
const availableDeviceTypes = [
  { code: 'VHF', name: 'VHF 通信站', icon: 'Connection' },
  { code: 'ILS', name: 'ILS 导航台', icon: 'Aim' },
  { code: 'VOR', name: 'VOR 信标台', icon: 'Monitor' },
]

// 过滤后的设备列表
const filteredDevices = computed(() => {
  if (!searchQuery.value) return deviceList.value
  const q = searchQuery.value.toLowerCase()
  return deviceList.value.filter(d => 
    d.name.toLowerCase().includes(q) || 
    d.deviceId.toLowerCase().includes(q) ||
    d.location.toLowerCase().includes(q)
  )
})

const onlineCount = computed(() => deviceList.value.filter(d => d.status === 'online').length)

// 状态类型映射
const getStatusType = (status: string) => {
  const map: any = { 'online': 'success', 'error': 'danger', 'offline': 'info' }
  return map[status] || 'info'
}

// 聚焦设备
const focusDevice = (device: any) => {
  selectedDeviceId.value = device.deviceId
  currentDeviceInfo.value = {
    ...device,
    statusText: mapStatus(device.status).text
  }
  
  // 在 3D 场景中聚焦
  const mesh = deviceMeshes.get(device.deviceId)
  if (mesh && controls) {
    const pos = mesh.position
    controls.target.set(pos.x, pos.y, pos.z)
    camera?.position.set(pos.x + 10, pos.y + 10, pos.z + 10)
    controls.update()
  }
}

const toggleGrid = () => {
  showGrid.value = !showGrid.value
  if (gridHelper) gridHelper.visible = showGrid.value
}

const resetCamera = () => {
  if (controls && camera) {
    controls.target.set(0, 0, 0)
    camera.position.set(20, 20, 20)
    controls.update()
  }
}

const viewHistory = () => {
  if (currentDeviceInfo.value) {
    ElMessage.info(`正在查看 ${currentDeviceInfo.value.name} 的历史数据...`)
  }
}

// WebSocket 事件监听
const initWebSocket = () => {
  wsStore.init()
  wsStore.onMessage((data) => {
    if (data.type === 'STATUS_UPDATED') {
      updateDeviceInList(data.data)
    } else if (data.type === 'ALARM_TRIGGERED') {
      handleRealtimeAlarm(data.data)
    }
  })
}

const updateDeviceInList = (eventData: any) => {
  const metadata = eventData.metadata || {}
  const device = deviceList.value.find(d => d.deviceId === metadata.device_id)
  if (device) {
    device.status = metadata.online_status ? 'online' : 'offline'
    if (metadata.alarm_flag) device.status = 'error'
    device.statusDot = mapStatus(device.status)
    updateMeshStatus(metadata.device_id, device.status)
  }
}

const handleRealtimeAlarm = (eventData: any) => {
  const metadata = eventData.metadata || {}
  const device = deviceList.value.find(d => d.deviceId === metadata.device_id)
  if (device) {
    device.status = 'error'
    device.statusDot = mapStatus('error')
    updateMeshStatus(metadata.device_id, 'error')
    showAlarmRing(metadata.device_id)
  }
}

const updateMeshStatus = (deviceId: string, status: string) => {
  const mesh = deviceMeshes.get(deviceId)
  if (mesh) {
    const color = mapStatus(status).color
    mesh.material.color.set(color)
  }
}

let gridHelper: THREE.GridHelper | null = null
let loading: any = null
let timer: number | null = null

let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let renderer: THREE.WebGLRenderer | null = null
let controls: OrbitControls | null = null
let labelRenderer: CSS2DRenderer | null = null
let animateId: number | null = null

const deviceMeshes: Map<string, any> = new Map()
const alarmRings: Map<string, THREE.Mesh> = new Map()
const pendingDevice = ref<any>(null)

let deviceIndex = 1

type DeviceStateType = 'initial-normal' | 'initial-error' | 'pending-config' | 'configured'

const goBack = () => {
  router.push('/').catch(err => {
    ElMessage.error('返回首页失败：' + err.message)
  })
}

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  }).replace(/\//g, '-')
}

const mapStatus = (status: string) => {
  switch (status) {
    case 'online': return { color: '#4CAF50', text: '在线' }
    case 'error': return { color: '#F44336', text: '异常' }
    case 'offline': return { color: '#faad14', text: '离线' }
    default: return { color: '#909399', text: '未知' }
  }
}

const loadDeviceList = async () => {
  loading = ElLoading.service({ target: '.monitor-layout', text: '加载设备状态...' })
  try {
    const response = await getDevices()
    const res = response.data || response
    const data = res.results || res
    if (data && Array.isArray(data)) {
      deviceList.value = data.map((item: any) => {
        let deviceName = item.name || item.device_model || item.device_id
        return {
          id: item.id || item.device_id,
          deviceId: item.device_id,
          name: deviceName,
          location: item.location || '未知位置',
          status: item.status || 'online',
          statusDot: mapStatus(item.status || 'online'),
          updatedAt: currentTime.value,
          position_x: item.position_x,
          position_y: item.position_y,
          position_z: item.position_z,
          device_type: item.device_type
        }
      })
      renderDevicesInScene(data)
    } else {
      deviceList.value = []
    }
  } catch (err: any) {
    ElMessage.error('设备数据加载失败')
    deviceList.value = []
  } finally {
    loading.close()
  }
}

const renderDevicesInScene = (devices: any[]) => {
  if (!scene) return
  deviceMeshes.forEach((mesh, id) => {
    if (!mesh.userData.isTemporary) {
      scene?.remove(mesh)
      deviceMeshes.delete(id)
    }
  })
  devices.forEach((device, index) => {
    const deviceId = device.device_id
    if (!deviceId) return
    let position: THREE.Vector3
    const hasPosition = device.position_x !== undefined && device.position_x !== null && parseFloat(device.position_x) !== 0
    if (hasPosition) {
      position = new THREE.Vector3(parseFloat(device.position_x), parseFloat(device.position_y) || 0, parseFloat(device.position_z))
    } else {
      const angle = (index * 120) * Math.PI / 180
      const radius = 4 + Math.floor(index / 3) * 4
      position = new THREE.Vector3(Math.cos(angle) * radius, 0, Math.sin(angle) * radius)
    }
    const latestStatus = device.latest_status || 'NORMAL'
    const state: DeviceStateType = latestStatus === 'ALARM' ? 'initial-error' : 'configured'
    createRealDeviceModel(deviceId, device.name || deviceId, position, state, false)
  })
}

const refreshDeviceList = () => {
  loadDeviceList()
  ElMessage.success('设备列表已刷新')
}

const selectDeviceType = (type: string) => {
  if (selectedDeviceType.value === type) {
    cancelSelection()
  } else {
    selectedDeviceType.value = type
    ElMessage.info('请在 3D 场景中点击放置位置')
  }
}

const cancelSelection = () => {
  selectedDeviceType.value = ''
  pendingDevice.value = null
}

const onSceneClick = (e: MouseEvent) => {
  if (!selectedDeviceType.value || !scene || !camera) return
  const rect = sceneRef.value!.getBoundingClientRect()
  const x = ((e.clientX - rect.left) / rect.width) * 2 - 1
  const y = -((e.clientY - rect.top) / rect.height) * 2 + 1
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(new THREE.Vector2(x, y), camera)
  const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0)
  const intersectPoint = new THREE.Vector3()
  raycaster.ray.intersectPlane(plane, intersectPoint)
  const tempId = `${selectedDeviceType.value}_TEMP_${Date.now()}`
  createRealDeviceModel(tempId, '未配置设备', intersectPoint, 'pending-config', true)
  pendingDevice.value = { tempId, type: selectedDeviceType.value, position: intersectPoint }
  openDeviceConfig(intersectPoint)
  cancelSelection()
}

const openDeviceConfig = (position: THREE.Vector3) => {
  tempDeviceData.value = { device_type: selectedDeviceType.value }
  deviceConfigForm.value = {
    name: `${selectedDeviceType.value}_${String(deviceIndex).padStart(2, '0')}`,
    device_model: selectedDeviceType.value === 'VHF' ? 'VHF-Model-X' : 'ILS-Model-A',
    location: '',
    position_x: parseFloat(position.x.toFixed(2)),
    position_y: parseFloat(position.y.toFixed(2)),
    position_z: parseFloat(position.z.toFixed(2)),
  }
  nameExistsError.value = ''
  deviceConfigVisible.value = true
}

const checkDeviceNameUnique = async () => {
  if (!deviceConfigForm.value.name) return
  try {
    const response = await request({
      url: '/api/devices/check-name/',
      method: 'get',
      params: { name: deviceConfigForm.value.name }
    })
    const res = response.data || response
    nameExistsError.value = !res.available ? '该设备名称已存在' : ''
  } catch (err) {}
}

const handleConfigClose = () => {
  if (pendingDevice.value) cancelConfirmVisible.value = true
  else deviceConfigVisible.value = false
}

const handleCancelConfirm = (del: boolean) => {
  cancelConfirmVisible.value = false
  if (del && pendingDevice.value) removeDeviceModel(pendingDevice.value.tempId)
  pendingDevice.value = null
  deviceConfigVisible.value = false
}

const submitDeviceConfig = async () => {
  if (!configFormRef.value) return
  await configFormRef.value.validate(async (valid: boolean) => {
    if (!valid || nameExistsError.value) return
    isSubmitting.value = true
    try {
      const payload = {
        device_id: `${deviceConfigForm.value.device_model}_${Date.now()}`,
        device_type: tempDeviceData.value.device_type,
        device_model: deviceConfigForm.value.device_model,
        name: deviceConfigForm.value.name,
        location: deviceConfigForm.value.location,
        position_x: deviceConfigForm.value.position_x,
        position_y: deviceConfigForm.value.position_y,
        position_z: deviceConfigForm.value.position_z,
      }
      const response = await request({ url: '/api/devices/', method: 'post', data: payload })
      ElMessage.success('设备创建成功')
      deviceConfigVisible.value = false
      if (pendingDevice.value) {
        updateDeviceModel(pendingDevice.value.tempId, { deviceId: (response as any).device_id, name: payload.name, state: 'configured' })
      }
      await loadDeviceList()
      pendingDevice.value = null
      deviceIndex++
    } catch (err) {
      ElMessage.error('保存失败')
    } finally {
      isSubmitting.value = false
    }
  })
}

// Three.js 核心逻辑
const initScene = () => {
  if (!sceneRef.value) return
  const width = sceneRef.value.clientWidth
  const height = sceneRef.value.clientHeight
  scene = new THREE.Scene()
  scene.background = new THREE.Color('#1a1a1a')
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.position.set(20, 20, 20)
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  sceneRef.value.appendChild(renderer.domElement)
  labelRenderer = new CSS2DRenderer()
  labelRenderer.setSize(width, height)
  labelRenderer.domElement.style.position = 'absolute'
  labelRenderer.domElement.style.top = '0'
  labelRenderer.domElement.style.pointerEvents = 'none'
  sceneRef.value.appendChild(labelRenderer.domElement)
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8)
  dirLight.position.set(10, 20, 10)
  scene.add(dirLight)
  gridHelper = new THREE.GridHelper(100, 100, 0x444444, 0x222222)
  scene.add(gridHelper)
  animate()
}

const animate = () => {
  animateId = requestAnimationFrame(animate)
  controls?.update()
  renderer?.render(scene!, camera!)
  labelRenderer?.render(scene!, camera!)
  alarmRings.forEach(ring => {
    ring.scale.x += 0.05
    ring.scale.y += 0.05
    const material = ring.material as THREE.MeshBasicMaterial
    material.opacity -= 0.02
    if (material.opacity <= 0) {
      material.opacity = 1
      ring.scale.set(1, 1, 1)
    }
  })
}

const createRealDeviceModel = (id: string, name: string, pos: THREE.Vector3, state: DeviceStateType, isTemp: boolean) => {
  if (!scene) return
  const geometry = new THREE.BoxGeometry(1, 1, 1)
  const color = state === 'initial-error' ? '#F44336' : (state === 'pending-config' ? '#FFEB3B' : '#4CAF50')
  const material = new THREE.MeshPhongMaterial({ color })
  const mesh = new THREE.Mesh(geometry, material)
  mesh.position.copy(pos)
  mesh.userData = { id, name, isTemporary: isTemp }
  scene.add(mesh)
  deviceMeshes.set(id, mesh)
  const labelDiv = document.createElement('div')
  labelDiv.className = 'device-label'
  labelDiv.textContent = name
  const label = new CSS2DObject(labelDiv)
  label.position.set(0, 1, 0)
  mesh.add(label)
}

const removeDeviceModel = (id: string) => {
  const mesh = deviceMeshes.get(id)
  if (mesh) {
    scene?.remove(mesh)
    deviceMeshes.delete(id)
  }
}

const updateDeviceModel = (id: string, data: any) => {
  const mesh = deviceMeshes.get(id)
  if (mesh) {
    mesh.userData.id = data.deviceId
    mesh.userData.name = data.name
    mesh.userData.isTemporary = false
    const material = mesh.material as THREE.MeshPhongMaterial
    material.color.set('#4CAF50')
  }
}

const showAlarmRing = (id: string) => {
  const mesh = deviceMeshes.get(id)
  if (!mesh || !scene) return
  const geometry = new THREE.RingGeometry(0.8, 1, 32)
  const material = new THREE.MeshBasicMaterial({ color: 0xff0000, side: THREE.DoubleSide, transparent: true })
  const ring = new THREE.Mesh(geometry, material)
  ring.position.copy(mesh.position)
  ring.rotation.x = Math.PI / 2
  scene.add(ring)
  alarmRings.set(id, ring)
}

const openContextMenu = (e: MouseEvent) => {
  const rect = sceneRef.value!.getBoundingClientRect()
  const x = ((e.clientX - rect.left) / rect.width) * 2 - 1
  const y = -((e.clientY - rect.top) / rect.height) * 2 + 1
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(new THREE.Vector2(x, y), camera!)
  const intersects = raycaster.intersectObjects(Array.from(deviceMeshes.values()))
  if (intersects.length > 0) {
    contextMenuVisible.value = true
    contextX.value = e.clientX
    contextY.value = e.clientY
    const firstIntersect = intersects[0]
    if (firstIntersect && firstIntersect.object && firstIntersect.object.userData) {
      rightClickDeviceId.value = firstIntersect.object.userData.id || ''
    }
  }
}

const deleteDevice = async () => {
  const id = rightClickDeviceId.value || currentDeviceInfo.value?.device_id
  if (!id) return
  try {
    await request({ url: `/api/devices/${id}/`, method: 'delete' })
    ElMessage.success('设备已移除')
    removeDeviceModel(id)
    loadDeviceList()
  } catch (err) {
    ElMessage.error('移除失败')
  } finally {
    contextMenuVisible.value = false
  }
}

onMounted(() => {
  updateTime()
  timer = window.setInterval(updateTime, 1000)
  initScene()
  loadDeviceList()
  initWebSocket()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (animateId) cancelAnimationFrame(animateId)
  renderer?.dispose()
})
</script>

<style scoped>
.monitor-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  color: #333333;
  overflow: hidden;
}

.monitor-header {
  height: 60px;
  background: rgba(245, 245, 245, 0.9);
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid #e8e8e8;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.divider {
  width: 1px;
  height: 20px;
  background: rgba(255, 255, 255, 0.2);
}

.page-title {
  font-size: 18px;
  font-weight: bold;
  letter-spacing: 1px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #8c8c8c;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #ff4d4f;
  border-radius: 50%;
}

.pulse-dot.active {
  background: #52c41a;
  box-shadow: 0 0 8px #52c41a;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(82, 196, 26, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(82, 196, 26, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(82, 196, 26, 0); }
}

.monitor-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr 280px;
  gap: 1px;
  background: #e8e8e8;
}

.side-panel {
  background: #ffffff;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
}

.panel-title {
  font-size: 14px;
  font-weight: bold;
  color: #666666;
  text-transform: uppercase;
}

.search-bar {
  padding: 10px 15px;
}

.device-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.device-item {
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  display: flex;
  gap: 12px;
  transition: all 0.3s;
  background: #fafafa;
  border: 1px solid #f0f0f0;
}

.device-item:hover { background: #f5f5f5; border-color: #e8e8e8; }
.device-item.active { background: rgba(24, 144, 255, 0.08); border: 1px solid rgba(24, 144, 255, 0.4); }
.device-item.has-alarm { background: rgba(245, 34, 45, 0.08); border: 1px solid rgba(245, 34, 45, 0.4); }

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 4px;
}

.device-info { flex: 1; }
.device-name-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.device-name { font-weight: 500; font-size: 14px; color: #333; }
.device-meta { display: flex; justify-content: space-between; font-size: 12px; color: #8c8c8c; }

.scene-panel {
  position: relative;
  background: #fafafa;
}

.scene-controls {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 10;
  display: flex;
  gap: 15px;
  align-items: center;
}

.scene-stats {
  background: rgba(255, 255, 255, 0.9);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  backdrop-filter: blur(4px);
  border: 1px solid #e8e8e8;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.scene-stats .label { color: #8c8c8c; margin-right: 6px; }

.three-scene-container { width: 100%; height: 100%; }

.scene-overlay {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 10;
}

.legend {
  background: rgba(255, 255, 255, 0.95);
  padding: 10px 15px;
  border-radius: 8px;
  backdrop-filter: blur(4px);
  border: 1px solid #e8e8e8;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-item { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #333; }
.legend-item .dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.green { background: #52c41a; }
.dot.orange { background: #faad14; }
.dot.red { background: #f5222d; }

.library-grid {
  padding: 15px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.library-item {
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 15px 10px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.library-item:hover { background: #f0f0f0; }
.library-item.active { border-color: #1890ff; background: rgba(24, 144, 255, 0.08); }

.model-preview { margin-bottom: 8px; color: #1890ff; }
.model-name { font-size: 12px; color: #666666; }

.placement-tip {
  margin: 10px 15px;
  padding: 10px;
  background: rgba(24, 144, 255, 0.08);
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid rgba(24, 144, 255, 0.2);
}

.tip-content { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #1890ff; }

.device-details-panel { padding: 0 15px; }
.panel-divider { height: 1px; background: #f0f0f0; margin: 15px 0; }
.details-content { padding: 10px 0; }
.detail-row { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 13px; }
.detail-row .label { color: #8c8c8c; }
.detail-row .value { color: #333; }
.detail-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px; }

.context-menu {
  position: fixed;
  z-index: 1000;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 4px 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.context-item {
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
  color: #333;
}

.context-item:hover { background: #f5222d; color: white; }

:deep(.device-label) {
  color: #333333;
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  border: 1px solid #e8e8e8;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 2px; }
</style>
