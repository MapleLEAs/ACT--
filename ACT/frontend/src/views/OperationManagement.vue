<template>
  <div class="operation-management-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>运维管理</h1>
    </div>

    <!-- 四个核心功能模块卡片 -->
    <div class="function-cards">
      <!-- 设备管理 -->
      <div class="function-card" :class="{ active: activeModule === 'device' }" @click="handleCardClick('device')">
        <div class="card-header">
          <AppIcon name="device" class="card-icon" />
          <span class="card-title">设备管理</span>
        </div>
        <div class="card-actions">
          <button class="action-btn" @click.stop="showEditInfo = true">
            <el-icon><AppIcon name="edit" /></el-icon> 编辑信息
          </button>
          <button class="action-btn" @click.stop="showLinkAlarm = true">
            <AppIcon name="bell" /> 关联告警
          </button>
        </div>
      </div>

      <!-- 人员管理 -->
      <div class="function-card" :class="{ active: activeModule === 'personnel' }" @click="handleCardClick('personnel')">
        <div class="card-header">
          <el-icon class="card-icon"><AppIcon name="user" /></el-icon>
          <span class="card-title">人员管理</span>
        </div>
        <div class="card-actions">
          <button class="action-btn" @click.stop="showModifyPermission = true">
            <el-icon><AppIcon name="key" /></el-icon> 修改权限
          </button>
          <button class="action-btn" @click.stop="showAssignRole = true">
            <el-icon><AppIcon name="user" /></el-icon> 分派角色
          </button>
          <button class="action-btn btn-add" @click.stop="showAddPersonnel = true">
            <AppIcon name="add" /> 新增人员
          </button>
        </div>
      </div>

      <!-- 工单管理 -->
      <div class="function-card" :class="{ active: activeModule === 'workOrder' }" @click="handleCardClick('workOrder')">
        <div class="card-header">
          <el-icon class="card-icon"><AppIcon name="document" /></el-icon>
          <span class="card-title">工单管理</span>
        </div>
        <div class="card-actions">
          <button class="action-btn" @click.stop="showCreateOrder = true">
            <AppIcon name="add" /> 新建工单
          </button>
          <button class="action-btn" @click.stop="showClaimOrder = true">
            <el-icon><AppIcon name="list" /></el-icon> 认领工单
          </button>
          <button class="action-btn" @click.stop="showProcessOrder = true">
            <el-icon><AppIcon name="wrench" /></el-icon> 处理工单
          </button>
        </div>
      </div>

      <!-- 维护计划 -->
      <div class="function-card" :class="{ active: activeModule === 'maintenance' }" @click="handleCardClick('maintenance')">
        <div class="card-header">
          <el-icon class="card-icon"><AppIcon name="settings" /></el-icon>
          <span class="card-title">维护计划</span>
        </div>
        <div class="card-actions">
          <button class="action-btn" @click.stop="showAddPlan = true">
            <el-icon><AppIcon name="add" /></el-icon> 新增计划
          </button>
          <button class="action-btn" @click.stop="showExecuteInspection = true">
            <el-icon><AppIcon name="search" /></el-icon> 执行巡检
          </button>
          <button class="action-btn" @click.stop="showMarkComplete = true">
            <el-icon><AppIcon name="check" /></el-icon> 标记完成
          </button>
        </div>
      </div>
    </div>

    <!-- 右侧工作区 -->
    <div class="work-area">
      <div v-if="activeModule === 'device'" class="module-content">
        <h3>设备管理</h3>
        <div class="device-panel">
          <el-card class="device-info-card">
            <template #header>
              <span>设备列表</span>
              <el-button size="small" @click="showEditInfo = true" class="add-btn">
                <el-icon><AppIcon name="add" /></el-icon> 添加设备
              </el-button>
            </template>
            <el-table :data="deviceList" border style="width: 100%">
              <el-table-column prop="name" label="设备名称" />
              <el-table-column prop="type" label="设备类型" />
              <el-table-column prop="status" label="状态">
                <template #default="scope">
                  <el-tag :type="scope.row.status === '正常' ? 'success' : 'warning'">
                    {{ scope.row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="location" label="位置" />
              <el-table-column label="操作">
                <template #default="scope">
                  <el-button size="mini" @click="editDevice(scope.row)">编辑</el-button>
                  <el-button size="mini" type="danger">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </div>

      <div v-if="activeModule === 'personnel'" class="module-content">
        <h3>人员管理</h3>
        <div class="personnel-panel">
          <el-card class="personnel-info-card">
            <template #header>
              <span>人员列表</span>
              <el-button size="small" @click="showAddPersonnel = true" class="add-btn">
                <AppIcon name="add" /> 新增人员
              </el-button>
            </template>
            <el-table :data="personnelList" border style="width: 100%">
              <el-table-column prop="name" label="姓名" />
              <el-table-column prop="role" label="角色" />
              <el-table-column prop="department" label="部门" />
              <el-table-column prop="status" label="状态">
                <template #default="scope">
                  <el-tag :type="scope.row.status === '在职' ? 'success' : 'info'">
                    {{ scope.row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作">
                <template #default="scope">
                  <el-button size="mini" @click="modifyPersonnelPermission(scope.row)">权限</el-button>
                  <el-button size="mini">编辑</el-button>
                  <el-button size="mini" type="danger">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </div>

      <div v-if="activeModule === 'workOrder'" class="module-content">
        <h3>工单管理</h3>
        <div class="workorder-panel">
          <el-card class="workorder-info-card">
            <template #header>
              <span>工单列表</span>
              <el-button size="small" @click="showCreateOrder = true" class="add-btn">
                <AppIcon name="add" /> 新建工单
              </el-button>
            </template>
            <el-table :data="workOrderList" border style="width: 100%">
              <el-table-column prop="id" label="工单编号" />
              <el-table-column prop="title" label="工单标题" />
              <el-table-column prop="priority" label="优先级">
                <template #default="scope">
                  <el-tag :type="getPriorityType(scope.row.priority)">
                    {{ scope.row.priority }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" />
              <el-table-column prop="createTime" label="创建时间" />
              <el-table-column label="操作">
                <template #default="scope">
                  <el-button size="mini" @click="claimOrder(scope.row)">认领</el-button>
                  <el-button size="mini" @click="processOrder(scope.row)">处理</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </div>

      <div v-if="activeModule === 'maintenance'" class="module-content">
        <h3>维护计划</h3>
        <div class="maintenance-panel">
          <el-card class="maintenance-info-card">
            <template #header>
              <span>维护计划列表</span>
              <el-button size="small" @click="showAddPlan = true" class="add-btn">
                <el-icon><AppIcon name="add" /></el-icon> 新增计划
              </el-button>
            </template>
            <el-table :data="maintenanceList" border style="width: 100%">
              <el-table-column prop="name" label="计划名称" />
              <el-table-column prop="type" label="维护类型" />
              <el-table-column prop="frequency" label="频率" />
              <el-table-column prop="status" label="状态">
                <template #default="scope">
                  <el-tag :type="getStatusType(scope.row.status)">
                    {{ scope.row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="nextExecute" label="下次执行" />
              <el-table-column label="操作">
                <template #default="scope">
                  <el-button size="mini" @click="executeInspection(scope.row)">巡检</el-button>
                  <el-button size="mini" @click="markPlanComplete(scope.row)">完成</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </div>

      <div v-if="!activeModule" class="placeholder">
        <AppIcon name="layout" class="placeholder-icon" />
        <p>请从上方选择一个功能模块开始操作</p>
      </div>
    </div>

    <!-- 编辑设备信息弹窗 -->
    <el-dialog title="编辑设备信息" v-model="showEditInfo" width="500px">
      <el-form :model="deviceForm" label-width="80px">
        <el-form-item label="设备名称">
          <el-input v-model="deviceForm.name" />
        </el-form-item>
        <el-form-item label="设备类型">
          <el-select v-model="deviceForm.type">
            <el-option label="传感器" value="传感器" />
            <el-option label="控制器" value="控制器" />
            <el-option label="网关" value="网关" />
          </el-select>
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="deviceForm.location" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="deviceForm.status">
            <el-option label="正常" value="正常" />
            <el-option label="故障" value="故障" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditInfo = false">取消</el-button>
        <el-button type="primary" @click="saveDeviceInfo">保存</el-button>
      </template>
    </el-dialog>

    <!-- 关联告警弹窗 -->
    <el-dialog title="关联告警" v-model="showLinkAlarm" width="600px">
      <el-form :model="linkAlarmForm" label-width="80px">
        <el-form-item label="选择设备">
          <el-select v-model="linkAlarmForm.deviceId">
            <el-option v-for="device in deviceList" :key="device.id" :label="device.name" :value="device.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="告警规则">
          <el-select multiple v-model="linkAlarmForm.alarmRules">
            <el-option label="温度过高" value="temp_high" />
            <el-option label="湿度异常" value="humidity_abnormal" />
            <el-option label="连接断开" value="disconnect" />
            <el-option label="电量不足" value="low_battery" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLinkAlarm = false">取消</el-button>
        <el-button type="primary" @click="saveLinkAlarm">保存</el-button>
      </template>
    </el-dialog>

    <!-- 修改权限弹窗 -->
    <el-dialog title="修改权限" v-model="showModifyPermission" width="500px">
      <el-form :model="permissionForm" label-width="100px">
        <el-form-item label="选择人员">
          <el-select v-model="permissionForm.personnelId">
            <el-option v-for="person in personnelList" :key="person.id" :label="person.name" :value="person.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="权限设置">
          <el-checkbox-group v-model="permissionForm.permissions">
            <el-checkbox label="设备管理" value="device_manage" />
            <el-checkbox label="人员管理" value="personnel_manage" />
            <el-checkbox label="工单管理" value="workorder_manage" />
            <el-checkbox label="告警处理" value="alarm_handle" />
            <el-checkbox label="数据查看" value="data_view" />
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showModifyPermission = false">取消</el-button>
        <el-button type="primary" @click="savePermission">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分派角色弹窗 -->
    <el-dialog title="分派角色" v-model="showAssignRole" width="500px">
      <el-form :model="roleForm" label-width="80px">
        <el-form-item label="选择人员">
          <el-select v-model="roleForm.personnelId">
            <el-option v-for="person in personnelList" :key="person.id" :label="person.name" :value="person.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择角色">
          <el-select v-model="roleForm.role">
            <el-option label="管理员" value="admin" />
            <el-option label="运维人员" value="operator" />
            <el-option label="巡检员" value="inspector" />
            <el-option label="查看员" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssignRole = false">取消</el-button>
        <el-button type="primary" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新增人员弹窗 -->
    <el-dialog title="新增人员" v-model="showAddPersonnel" width="500px">
      <el-form :model="personnelForm" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="personnelForm.name" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="personnelForm.department" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="personnelForm.role">
            <el-option label="管理员" value="admin" />
            <el-option label="运维人员" value="operator" />
            <el-option label="巡检员" value="inspector" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="personnelForm.status">
            <el-option label="在职" value="在职" />
            <el-option label="离职" value="离职" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddPersonnel = false">取消</el-button>
        <el-button type="primary" @click="savePersonnel">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新建工单弹窗 -->
    <el-dialog title="新建工单" v-model="showCreateOrder" width="500px">
      <el-form :model="workOrderForm" label-width="80px">
        <el-form-item label="工单标题">
          <el-input v-model="workOrderForm.title" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="workOrderForm.priority">
            <el-option label="紧急" value="紧急" />
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="工单类型">
          <el-select v-model="workOrderForm.type">
            <el-option label="故障维修" value="repair" />
            <el-option label="日常维护" value="maintenance" />
            <el-option label="设备安装" value="installation" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input type="textarea" v-model="workOrderForm.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateOrder = false">取消</el-button>
        <el-button type="primary" @click="saveWorkOrder">保存</el-button>
      </template>
    </el-dialog>

    <!-- 认领工单弹窗 -->
    <el-dialog title="认领工单" v-model="showClaimOrder" width="600px">
      <el-table :data="unclaimedOrders" border style="width: 100%">
        <el-table-column prop="id" label="工单编号" />
        <el-table-column prop="title" label="工单标题" />
        <el-table-column prop="priority" label="优先级">
          <template #default="scope">
            <el-tag :type="getPriorityType(scope.row.priority)">
              {{ scope.row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button size="mini" type="primary" @click="confirmClaim(scope.row)">认领</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showClaimOrder = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 处理工单弹窗 -->
    <el-dialog title="处理工单" v-model="showProcessOrder" width="500px">
      <el-form :model="processForm" label-width="80px">
        <el-form-item label="选择工单">
          <el-select v-model="processForm.orderId">
            <el-option v-for="order in workOrderList" :key="order.id" :label="order.title" :value="order.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理状态">
          <el-select v-model="processForm.status">
            <el-option label="处理中" value="处理中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已关闭" value="已关闭" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理备注">
          <el-input type="textarea" v-model="processForm.note" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProcessOrder = false">取消</el-button>
        <el-button type="primary" @click="saveProcess">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新增计划弹窗 -->
    <el-dialog title="新增维护计划" v-model="showAddPlan" width="500px">
      <el-form :model="planForm" label-width="80px">
        <el-form-item label="计划名称">
          <el-input v-model="planForm.name" />
        </el-form-item>
        <el-form-item label="维护类型">
          <el-select v-model="planForm.type">
            <el-option label="日常巡检" value="daily" />
            <el-option label="月度维护" value="monthly" />
            <el-option label="季度检修" value="quarterly" />
          </el-select>
        </el-form-item>
        <el-form-item label="频率">
          <el-select v-model="planForm.frequency">
            <el-option label="每日" value="每日" />
            <el-option label="每周" value="每周" />
            <el-option label="每月" value="每月" />
            <el-option label="每季度" value="每季度" />
          </el-select>
        </el-form-item>
        <el-form-item label="下次执行时间">
          <el-date-picker v-model="planForm.nextExecute" type="date" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddPlan = false">取消</el-button>
        <el-button type="primary" @click="savePlan">保存</el-button>
      </template>
    </el-dialog>

    <!-- 执行巡检弹窗 -->
    <el-dialog title="执行巡检" v-model="showExecuteInspection" width="600px">
      <div class="inspection-content">
        <el-form :model="inspectionForm" label-width="100px">
          <el-form-item label="选择计划">
            <el-select v-model="inspectionForm.planId">
              <el-option v-for="plan in maintenanceList" :key="plan.id" :label="plan.name" :value="plan.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="巡检项目">
            <el-checkbox-group v-model="inspectionForm.items">
              <el-checkbox label="设备外观检查" value="appearance" />
              <el-checkbox label="运行状态检查" value="status" />
              <el-checkbox label="参数校准" value="calibration" />
              <el-checkbox label="清洁维护" value="cleaning" />
            </el-checkbox-group>
          </el-form-item>
          <el-form-item label="巡检结果">
            <el-select v-model="inspectionForm.result">
              <el-option label="正常" value="正常" />
              <el-option label="异常" value="异常" />
            </el-select>
          </el-form-item>
          <el-form-item label="巡检备注">
            <el-input type="textarea" v-model="inspectionForm.note" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showExecuteInspection = false">取消</el-button>
        <el-button type="primary" @click="saveInspection">保存</el-button>
      </template>
    </el-dialog>

    <!-- 标记完成弹窗 -->
    <el-dialog title="标记完成" v-model="showMarkComplete" width="600px">
      <el-table :data="pendingPlans" border style="width: 100%">
        <el-table-column prop="name" label="计划名称" />
        <el-table-column prop="type" label="维护类型" />
        <el-table-column prop="nextExecute" label="计划时间" />
        <el-table-column label="操作">
          <template #default="scope">
            <el-button size="mini" type="success" @click="confirmComplete(scope.row)">标记完成</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showMarkComplete = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

// 当前激活的功能模块
const activeModule = ref(null)

// 弹窗控制
const showEditInfo = ref(false)
const showLinkAlarm = ref(false)
const showModifyPermission = ref(false)
const showAssignRole = ref(false)
const showAddPersonnel = ref(false)
const showCreateOrder = ref(false)
const showClaimOrder = ref(false)
const showProcessOrder = ref(false)
const showAddPlan = ref(false)
const showExecuteInspection = ref(false)
const showMarkComplete = ref(false)

// 表单数据
const deviceForm = reactive({
  name: '',
  type: '',
  location: '',
  status: '正常'
})

const linkAlarmForm = reactive({
  deviceId: '',
  alarmRules: []
})

const permissionForm = reactive({
  personnelId: '',
  permissions: []
})

const roleForm = reactive({
  personnelId: '',
  role: ''
})

const personnelForm = reactive({
  name: '',
  department: '',
  role: '',
  status: '在职'
})

const workOrderForm = reactive({
  title: '',
  priority: '中',
  type: '',
  description: ''
})

const processForm = reactive({
  orderId: '',
  status: '',
  note: ''
})

const planForm = reactive({
  name: '',
  type: '',
  frequency: '',
  nextExecute: ''
})

const inspectionForm = reactive({
  planId: '',
  items: [],
  result: '',
  note: ''
})

// 模拟数据
const deviceList = ref([
  { id: 1, name: '温度传感器-001', type: '传感器', status: '正常', location: 'A区-1号机房' },
  { id: 2, name: '湿度传感器-002', type: '传感器', status: '正常', location: 'A区-1号机房' },
  { id: 3, name: '控制器-001', type: '控制器', status: '故障', location: 'B区-2号机房' },
  { id: 4, name: '网关-001', type: '网关', status: '正常', location: 'C区-3号机房' }
])

const personnelList = ref([
  { id: 1, name: '张三', role: '管理员', department: '运维部', status: '在职' },
  { id: 2, name: '李四', role: '运维人员', department: '运维部', status: '在职' },
  { id: 3, name: '王五', role: '巡检员', department: '运维部', status: '在职' },
  { id: 4, name: '赵六', role: '查看员', department: '技术部', status: '在职' }
])

const workOrderList = ref([
  { id: 'WO-2024-001', title: '修复温度传感器故障', priority: '紧急', status: '待处理', createTime: '2024-01-15 09:00' },
  { id: 'WO-2024-002', title: '定期设备维护', priority: '中', status: '待处理', createTime: '2024-01-14 14:30' },
  { id: 'WO-2024-003', title: '更换控制器', priority: '高', status: '已认领', createTime: '2024-01-13 10:00' },
  { id: 'WO-2024-004', title: '网关升级', priority: '低', status: '待处理', createTime: '2024-01-12 16:00' }
])

const maintenanceList = ref([
  { id: 1, name: '每日设备巡检', type: '日常巡检', frequency: '每日', status: '执行中', nextExecute: '2024-01-16' },
  { id: 2, name: '月度设备维护', type: '月度维护', frequency: '每月', status: '待执行', nextExecute: '2024-02-01' },
  { id: 3, name: '季度设备检修', type: '季度检修', frequency: '每季度', status: '待执行', nextExecute: '2024-04-01' },
  { id: 4, name: '空调系统维护', type: '月度维护', frequency: '每月', status: '已完成', nextExecute: '2024-02-15' }
])

// 计算属性
const unclaimedOrders = computed(() => workOrderList.value.filter(order => order.status === '待处理'))
const pendingPlans = computed(() => maintenanceList.value.filter(plan => plan.status !== '已完成'))

// 卡片点击事件
const handleCardClick = (module) => {
  activeModule.value = module
}

// 设备管理相关操作
const editDevice = (device) => {
  deviceForm.name = device.name
  deviceForm.type = device.type
  deviceForm.location = device.location
  deviceForm.status = device.status
  showEditInfo.value = true
}

const saveDeviceInfo = () => {
  showEditInfo.value = false
  ElMessage.success('设备信息保存成功')
}

const saveLinkAlarm = () => {
  showLinkAlarm.value = false
  ElMessage.success('告警关联成功')
}

// 人员管理相关操作
const modifyPersonnelPermission = (personnel) => {
  permissionForm.personnelId = personnel.id
  showModifyPermission.value = true
}

const savePermission = () => {
  showModifyPermission.value = false
  ElMessage.success('权限修改成功')
}

const saveRole = () => {
  showAssignRole.value = false
  ElMessage.success('角色分派成功')
}

const savePersonnel = () => {
  showAddPersonnel.value = false
  ElMessage.success('人员新增成功')
}

// 工单管理相关操作
const saveWorkOrder = () => {
  showCreateOrder.value = false
  ElMessage.success('工单创建成功')
}

const claimOrder = (order) => {
  showClaimOrder.value = true
}

const confirmClaim = (order) => {
  ElMessage.success(`工单 ${order.id} 认领成功`)
}

const processOrder = (order) => {
  processForm.orderId = order.id
  showProcessOrder.value = true
}

const saveProcess = () => {
  showProcessOrder.value = false
  ElMessage.success('工单处理成功')
}

// 维护计划相关操作
const savePlan = () => {
  showAddPlan.value = false
  ElMessage.success('维护计划新增成功')
}

const executeInspection = (plan) => {
  inspectionForm.planId = plan.id
  showExecuteInspection.value = true
}

const saveInspection = () => {
  showExecuteInspection.value = false
  ElMessage.success('巡检记录保存成功')
}

const markPlanComplete = (plan) => {
  showMarkComplete.value = true
}

const confirmComplete = (plan) => {
  ElMessage.success(`计划 ${plan.name} 已标记完成`)
}

// 辅助函数
const getPriorityType = (priority) => {
  const types = {
    '紧急': 'danger',
    '高': 'warning',
    '中': 'info',
    '低': 'success'
  }
  return types[priority] || 'info'
}

const getStatusType = (status) => {
  const types = {
    '执行中': 'warning',
    '待执行': 'info',
    '已完成': 'success'
  }
  return types[status] || 'info'
}
</script>

<style scoped>
.operation-management-container {
  padding: 20px;
  font-family: 'Inter', sans-serif;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 30px;
}

/* 功能卡片区域 */
.function-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.function-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 2px solid #e8e8e8;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 180px;
  display: flex;
  flex-direction: column;
}

.function-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(92, 110, 141, 0.15);
  border-color: #5c6e8d;
}

.function-card.active {
  border-color: #5c6e8d;
  background-color: #f8fafc;
}

.card-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid;
  border-image: linear-gradient(to right, 
    rgba(101, 184, 248, 0.7), 
    rgba(101, 184, 248, 0.15)
  ) 1;
  border-image-slice: 1;
  display: flex;
  align-items: center;
}

.card-icon {
  color: #5c6e8d;
  font-size: 20px;
  margin-right: 10px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #5c6e8d;
}

.card-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  justify-content: flex-end;
}

/* 操作按钮样式 */
.action-btn {
  padding: 10px 14px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  color: #606266;
  font-size: 14px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn:hover {
  background-color: #f5f7fa;
  border-color: #c0c4cc;
  color: #5c6e8d;
}

.btn-add {
  background-color: #e8f4ff;
  border-color: #5c6e8d;
  color: #5c6e8d;
  font-weight: 500;
}

.btn-add:hover {
  background-color: #5c6e8d;
  color: white;
}

/* 右侧工作区 */
.work-area {
  background: #fff;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e8e8e8;
  min-height: 500px;
}

.module-content h3 {
  color: #333;
  margin-bottom: 20px;
  font-size: 20px;
  font-weight: 600;
}

.module-content p {
  color: #666;
  line-height: 1.6;
}

.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #999;
  font-size: 16px;
}

.placeholder-icon {
  font-size: 64px;
  color: #ddd;
  margin-bottom: 20px;
}

/* 面板样式 */
.device-panel, .personnel-panel, .workorder-panel, .maintenance-panel {
  margin-top: 20px;
}

.add-btn {
  float: right;
}

.el-table {
  margin-top: 15px;
}

.el-form-item {
  margin-bottom: 20px;
}

.inspection-content {
  max-height: 400px;
  overflow-y: auto;
}
</style>