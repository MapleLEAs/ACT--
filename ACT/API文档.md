# ATC Monitor API 接口文档

## 项目信息

- **项目名称**: ATC Monitor (空中交通管制监控系统)
- **版本**: 1.0.0
- **基础URL**: `http://127.0.0.1:8002`
- **认证方式**: JWT Token
- **数据格式**: JSON / JSON-LD (NGSI-LD接口)

---

## 目录

1. [认证接口](#认证接口)
2. [设备管理接口](#设备管理接口)
3. [设备状态日志接口](#设备状态日志接口)
4. [告警规则接口](#告警规则接口)
5. [告警接口](#告警接口)
6. [预测接口](#预测接口)
7. [环境数据接口](#环境数据接口)
8. [仪表盘接口](#仪表盘接口)
9. [3D可视化接口](#3d可视化接口)
10. [人员管理接口](#人员管理接口)
11. [工单管理接口](#工单管理接口)
12. [维护计划接口](#维护计划接口)
13. [NGSI-LD数据交换接口](#ngsi-ld数据交换接口)

---

## 认证接口

### 1. 获取JWT令牌

**接口地址**: `POST /api/token/`

**请求参数**:
```json
{
  "username": "admin",
  "password": "password"
}
```

**响应示例**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**说明**:
- `access`: 访问令牌，有效期较短（通常2小时）
- `refresh`: 刷新令牌，有效期较长（通常7天）

---

### 2. 刷新JWT令牌

**接口地址**: `POST /api/token/refresh/`

**请求参数**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**响应示例**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## 设备管理接口

### 1. 获取设备列表

**接口地址**: `GET /api/devices/`

**权限**: 无需认证

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认10）

**响应示例**:
```json
{
  "count": 100,
  "next": "http://127.0.0.1:8002/api/devices/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "device_id": "VHF001",
      "device_type": "VHF",
      "device_model": "VHF-2000",
      "name": "VHF-2000",
      "location": "塔台A区",
      "manufacturer": "华为",
      "install_time": "2023-01-15T00:00:00Z",
      "owner": 1,
      "position_x": 10.5,
      "position_y": 20.3,
      "position_z": 15.0,
      "created_at": "2023-01-15T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z",
      "latest_status": "NORMAL",
      "latest_status_time": "2024-01-15T10:30:00Z",
      "online_status": true,
      "alarm_level": "none"
    }
  ]
}
```

**字段说明**:
- `latest_status`: 设备最新状态（NORMAL/ALARM/OFFLINE）
- `latest_status_time`: 最新状态时间
- `online_status`: 在线状态（true/false）
- `alarm_level`: 告警级别（none/low/medium/high/critical）

---

### 2. 创建设备

**接口地址**: `POST /api/devices/`

**权限**: 需要认证

**请求参数**:
```json
{
  "device_id": "VHF002",
  "device_type": "VHF",
  "device_model": "VHF-2000",
  "location": "塔台B区",
  "manufacturer": "华为",
  "install_time": "2023-02-01T00:00:00Z",
  "position_x": 15.0,
  "position_y": 25.0,
  "position_z": 18.0
}
```

**响应示例**:
```json
{
  "id": 2,
  "device_id": "VHF002",
  "device_type": "VHF",
  "device_model": "VHF-2000",
  "name": "VHF-2000",
  "location": "塔台B区",
  "manufacturer": "华为",
  "install_time": "2023-02-01T00:00:00Z",
  "owner": 1,
  "position_x": 15.0,
  "position_y": 25.0,
  "position_z": 18.0,
  "created_at": "2024-01-16T00:00:00Z",
  "updated_at": "2024-01-16T00:00:00Z",
  "latest_status": "NORMAL",
  "latest_status_time": null,
  "online_status": true,
  "alarm_level": "none"
}
```

---

### 3. 获取设备详情

**接口地址**: `GET /api/devices/{id}/`

**权限**: 需要认证

**路径参数**:
- `id`: 设备ID（数字）

**响应示例**: 同创建设备响应

---

### 4. 更新设备

**接口地址**: `PUT /api/devices/{id}/`

**权限**: 需要认证

**请求参数**: 同创建设备

**响应示例**: 同创建设备响应

---

### 5. 删除设备

**接口地址**: `DELETE /api/devices/{id}/`

**权限**: 需要认证

**响应示例**:
```json
{
  "detail": "设备已删除"
}
```

---

### 6. 变更设备状态

**接口地址**: `POST /api/devices/{device_id}/change-status/`

**权限**: 需要认证

**路径参数**:
- `device_id`: 设备ID（字符串，如"VHF001"）

**请求参数**:
```json
{
  "status": "online"
}
```

**状态选项**:
- `online`: 在线
- `offline`: 离线
- `error`: 错误

**响应示例**:
```json
{
  "message": "状态变更成功",
  "device_id": "VHF001",
  "old_status": "offline",
  "new_status": "online"
}
```

---

### 7. 关联告警规则

**接口地址**: `POST /api/devices/{device_id}/link-alarm/`

**权限**: 需要认证

**路径参数**:
- `device_id`: 设备ID（数字）

**请求参数**:
```json
{
  "alarm_rule_ids": [1, 2, 3]
}
```

**响应示例**:
```json
{
  "message": "关联成功"
}
```

---

## 设备状态日志接口

### 1. 获取状态日志列表

**接口地址**: `GET /api/status_logs/`

**权限**: 无需认证

**查询参数**:
- `page`: 页码
- `page_size`: 每页数量
- `device_id`: 设备ID筛选

**响应示例**:
```json
{
  "count": 1000,
  "next": "http://127.0.0.1:8002/api/status_logs/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "device": 1,
      "online_status": true,
      "device_status": "NORMAL",
      "alarm_flag": false,
      "device_temperature": 45.5,
      "device_humidity": 60.2,
      "collect_time": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 2. 创建状态日志

**接口地址**: `POST /api/status_logs/`

**权限**: 无需认证

**请求参数**:
```json
{
  "device": 1,
  "online_status": true,
  "device_status": "NORMAL",
  "alarm_flag": false,
  "device_temperature": 45.5,
  "device_humidity": 60.2,
  "collect_time": "2024-01-15T10:30:00Z"
}
```

**响应示例**: 同获取状态日志响应

---

## 告警规则接口

### 1. 获取告警规则列表

**接口地址**: `GET /api/alarm_rules/`

**权限**: 无需认证

**响应示例**:
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "温度过高告警",
      "metric": "device_temperature",
      "operator": ">",
      "threshold_value": 80.0,
      "severity": "HIGH",
      "enabled": true,
      "cooldown_seconds": 300,
      "recovery_operator": "<",
      "recovery_threshold_value": 70.0,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

---

### 2. 创建告警规则

**接口地址**: `POST /api/alarm_rules/`

**权限**: 无需认证

**请求参数**:
```json
{
  "name": "温度过高告警",
  "metric": "device_temperature",
  "operator": ">",
  "threshold_value": 80.0,
  "severity": "HIGH",
  "enabled": true,
  "cooldown_seconds": 300,
  "recovery_operator": "<",
  "recovery_threshold_value": 70.0
}
```

**响应示例**: 同获取告警规则响应

---

### 3. 更新告警规则

**接口地址**: `PUT /api/alarm_rules/{id}/`

**权限**: 无需认证

**请求参数**: 同创建告警规则

**响应示例**: 同获取告警规则响应

---

### 4. 删除告警规则

**接口地址**: `DELETE /api/alarm_rules/{id}/`

**权限**: 无需认证

**响应示例**:
```json
{
  "detail": "告警规则已删除"
}
```

---

## 告警接口

### 1. 获取告警列表

**接口地址**: `GET /api/alarms/`

**权限**: 无需认证

**查询参数**:
- `status`: 状态筛选（OPEN/ACK/CLOSED）
- `severity`: 严重程度筛选（LOW/MEDIUM/HIGH/CRITICAL）
- `device_id`: 设备ID筛选

**响应示例**:
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "device": {
        "device_id": "VHF001",
        "device_type": "VHF",
        "name": "VHF-2000"
      },
      "device_name": "VHF001",
      "device_id": "VHF001",
      "device_type": "VHF",
      "rule": {
        "id": 1,
        "name": "温度过高告警"
      },
      "title": "温度过高告警",
      "description": "device_temperature: 85.5",
      "message": "device_temperature > 85.5",
      "level": "HIGH",
      "severity": "HIGH",
      "status": "OPEN",
      "raised_at": "2024-01-15T10:30:00Z",
      "acknowledged_at": null,
      "handler_name": null,
      "confirmed_by": null,
      "confirmed_by_name": null,
      "metric": "device_temperature",
      "value": 85.5,
      "value_str": "85.5",
      "recover_value": null,
      "recover_value_str": null,
      "alarm_id": "ALM-20240115-001",
      "trigger_time": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 2. 创建告警

**接口地址**: `POST /api/alarms/`

**权限**: 无需认证

**请求参数**:
```json
{
  "device": 1,
  "rule": 1,
  "metric": "device_temperature",
  "value": 85.5,
  "value_str": "85.5",
  "severity": "HIGH",
  "status": "OPEN",
  "alarm_id": "ALM-20240115-001"
}
```

**响应示例**: 同获取告警响应

---

### 3. 更新告警

**接口地址**: `PUT /api/alarms/{id}/`

**权限**: 无需认证

**请求参数**: 同创建告警

**响应示例**: 同获取告警响应

---

### 4. 删除告警

**接口地址**: `DELETE /api/alarms/{id}/`

**权限**: 无需认证

**响应示例**:
```json
{
  "detail": "告警已删除"
}
```

---

## 预测接口

### 1. 获取预测结果列表

**接口地址**: `GET /api/predictions/`

**权限**: 无需认证

**响应示例**:
```json
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "device": 1,
      "device_id": "VHF001",
      "device_type": "VHF",
      "metric": "device_temperature",
      "predicted_value": 82.5,
      "prediction_time": "2024-01-15T11:00:00Z",
      "prediction_horizon": 30,
      "confidence_score": 0.85,
      "error_margin": 5.0,
      "threshold_value": 80.0,
      "is_above_threshold": true,
      "severity": "HIGH",
      "status": "ACTIVE",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 2. 创建预测结果

**接口地址**: `POST /api/predictions/`

**权限**: 无需认证

**请求参数**:
```json
{
  "device": 1,
  "metric": "device_temperature",
  "predicted_value": 82.5,
  "prediction_horizon": 30,
  "confidence_score": 0.85,
  "error_margin": 5.0,
  "threshold_value": 80.0,
  "is_above_threshold": true,
  "severity": "HIGH",
  "status": "ACTIVE"
}
```

**响应示例**: 同获取预测结果响应

---

## 环境数据接口

### 1. 获取环境数据列表

**接口地址**: `GET /api/environment_data/`

**权限**: 无需认证

**响应示例**:
```json
{
  "count": 1000,
  "results": [
    {
      "id": 1,
      "device": 1,
      "device_id": "VHF001",
      "ambient_temperature": 25.5,
      "humidity": 65.2,
      "atmospheric_pressure": 1013.25,
      "wind_speed": 5.5,
      "wind_direction": 180,
      "rain_intensity": 0,
      "visibility": 10000,
      "collect_time": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 2. 创建环境数据

**接口地址**: `POST /api/environment_data/`

**权限**: 无需认证

**请求参数**:
```json
{
  "device": 1,
  "ambient_temperature": 25.5,
  "humidity": 65.2,
  "atmospheric_pressure": 1013.25,
  "wind_speed": 5.5,
  "wind_direction": 180,
  "rain_intensity": 0,
  "visibility": 10000,
  "collect_time": "2024-01-15T10:30:00Z"
}
```

**响应示例**: 同获取环境数据响应

---

## 仪表盘接口

### 1. 仪表盘概览

**接口地址**: `GET /api/dashboard/overview/`

**权限**: 无需认证

**响应示例**:
```json
{
  "stats": {
    "total_devices": 100,
    "online_devices": 95,
    "operation_rate": 95.0,
    "today_alarm_count": 10
  },
  "severity_distribution": [
    {
      "severity": "HIGH",
      "count": 5
    },
    {
      "severity": "MEDIUM",
      "count": 3
    },
    {
      "severity": "LOW",
      "count": 2
    }
  ],
  "device_type_distribution": [
    {
      "device_type": "VHF",
      "count": 30
    },
    {
      "device_type": "ILS",
      "count": 25
    },
    {
      "device_type": "DME",
      "count": 20
    },
    {
      "device_type": "RADAR",
      "count": 25
    }
  ],
  "recent_alarms": [
    {
      "id": 1,
      "device": {
        "device_id": "VHF001",
        "device_type": "VHF",
        "name": "VHF-2000"
      },
      "device_name": "VHF001",
      "device_id": "VHF001",
      "device_type": "VHF",
      "rule": {
        "id": 1,
        "name": "温度过高告警"
      },
      "title": "温度过高告警",
      "description": "device_temperature: 85.5",
      "message": "device_temperature > 85.5",
      "level": "HIGH",
      "severity": "HIGH",
      "status": "OPEN",
      "raised_at": "2024-01-15T10:30:00Z",
      "acknowledged_at": null,
      "handler_name": null,
      "confirmed_by": null,
      "confirmed_by_name": null,
      "metric": "device_temperature",
      "value": 85.5,
      "value_str": "85.5",
      "recover_value": null,
      "recover_value_str": null,
      "alarm_id": "ALM-20240115-001",
      "trigger_time": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 2. 趋势分析

**接口地址**: `GET /api/trend-analysis/`

**权限**: 无需认证

**查询参数**:
- `metric`: 指标名称（默认：device_temperature）

**响应示例**:
```json
{
  "labels": [
    "2024-01-08 00:00",
    "2024-01-08 01:00",
    "2024-01-08 02:00"
  ],
  "values": [
    45.5,
    46.2,
    47.8
  ]
}
```

**说明**:
- 返回最近7天的趋势数据
- 每小时一个数据点

---

### 3. 环境数据统计

**接口地址**: `GET /api/environment-data/`

**权限**: 无需认证

**响应示例**:
```json
{
  "statistics": {
    "avg": 45.5,
    "max": 85.5,
    "min": 25.0
  },
  "data": [
    {
      "collect_time": "2024-01-15T10:30:00Z",
      "device_temperature": 45.5
    }
  ]
}
```

**说明**:
- 返回最近24小时的环境数据
- 包含平均值、最大值、最小值统计

---

## 3D可视化接口

### 1. 获取3D场景数据

**接口地址**: `GET /api/threejs/scene/`

**权限**: 无需认证

**查询参数**:
- `force`: 是否强制刷新（true/false）

**响应示例**:
```json
{
  "devices": [
    {
      "id": 1,
      "device_id": "VHF001",
      "device_type": "VHF",
      "name": "VHF-2000",
      "position": {
        "x": 10.5,
        "y": 20.3,
        "z": 15.0
      },
      "status": "NORMAL",
      "online": true
    }
  ],
  "connections": [],
  "metadata": {
    "total_devices": 100,
    "last_updated": "2024-01-15T10:30:00Z"
  }
}
```

---

### 2. 获取设备历史数据

**接口地址**: `GET /api/threejs/device/{device_id}/history/`

**权限**: 无需认证

**路径参数**:
- `device_id`: 设备ID（字符串）

**查询参数**:
- `hours`: 历史数据小时数（默认24）

**响应示例**:
```json
{
  "device_id": "VHF001",
  "data": [
    {
      "collect_time": "2024-01-15T10:30:00Z",
      "device_temperature": 45.5,
      "device_humidity": 60.2,
      "online_status": true,
      "device_status": "NORMAL"
    }
  ],
  "data_points": 24
}
```

---

## 人员管理接口

### 1. 获取人员列表

**接口地址**: `GET /api/personnel/`

**权限**: 需要认证

**响应示例**:
```json
[
  {
    "id": 1,
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com"
    },
    "real_name": "管理员",
    "email": "admin@example.com",
    "phone": "13800138000",
    "department": "运维部",
    "position": "系统管理员",
    "role_ids": [1, 2],
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2024-01-15T00:00:00Z"
  }
]
```

---

### 2. 创建人员

**接口地址**: `POST /api/personnel/`

**权限**: 需要认证

**请求参数**:
```json
{
  "user": {
    "username": "user001",
    "email": "user001@example.com"
  },
  "real_name": "张三",
  "email": "user001@example.com",
  "phone": "13800138001",
  "department": "运维部",
  "position": "运维工程师",
  "role_ids": [1]
}
```

**响应示例**: 同获取人员响应

---

### 3. 更新权限

**接口地址**: `PUT /api/personnel/{user_id}/permissions/`

**权限**: 需要认证

**路径参数**:
- `user_id`: 用户ID（数字）

**请求参数**:
```json
{
  "permission_ids": [1, 2, 3]
}
```

**响应示例**:
```json
{
  "message": "权限更新成功"
}
```

---

### 4. 分配角色

**接口地址**: `PUT /api/personnel/{user_id}/roles/`

**权限**: 需要认证

**路径参数**:
- `user_id`: 用户ID（数字）

**请求参数**:
```json
{
  "role_ids": [1, 2]
}
```

**响应示例**:
```json
{
  "message": "角色分配成功"
}
```

---

## 工单管理接口

### 1. 创建工单

**接口地址**: `POST /api/work-orders/`

**权限**: 需要认证

**请求参数**:
```json
{
  "title": "VHF001设备故障维修",
  "work_type": "repair",
  "priority": "high",
  "device": 1,
  "description": "设备温度过高，需要检查散热系统",
  "scheduled_time": "2024-01-16T09:00:00Z",
  "estimated_duration": 120
}
```

**响应示例**:
```json
{
  "id": 1,
  "title": "VHF001设备故障维修",
  "work_type": "repair",
  "priority": "high",
  "device": 1,
  "description": "设备温度过高，需要检查散热系统",
  "scheduled_time": "2024-01-16T09:00:00Z",
  "estimated_duration": 120,
  "assignee": null,
  "status": "pending",
  "progress_percent": 0,
  "attachments": [],
  "claim_time": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### 2. 认领工单

**接口地址**: `POST /api/work-orders/{order_id}/claim/`

**权限**: 需要认证

**路径参数**:
- `order_id`: 工单ID（数字）

**响应示例**:
```json
{
  "id": 1,
  "title": "VHF001设备故障维修",
  "work_type": "repair",
  "priority": "high",
  "device": 1,
  "description": "设备温度过高，需要检查散热系统",
  "scheduled_time": "2024-01-16T09:00:00Z",
  "estimated_duration": 120,
  "assignee": 1,
  "status": "claimed",
  "progress_percent": 0,
  "attachments": [],
  "claim_time": "2024-01-15T10:35:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

---

### 3. 获取工单列表

**接口地址**: `GET /api/work-orders/list/`

**权限**: 需要认证

**查询参数**:
- `status`: 状态筛选（pending/claimed/processing/completed/canceled）

**响应示例**:
```json
[
  {
    "id": 1,
    "title": "VHF001设备故障维修",
    "work_type": "repair",
    "priority": "high",
    "device": 1,
    "description": "设备温度过高，需要检查散热系统",
    "scheduled_time": "2024-01-16T09:00:00Z",
    "estimated_duration": 120,
    "assignee": 1,
    "status": "claimed",
    "progress_percent": 0,
    "attachments": [],
    "claim_time": "2024-01-15T10:35:00Z",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
  }
]
```

---

## 维护计划接口

### 1. 获取维护计划列表

**接口地址**: `GET /api/maintenance-plans/list/`

**权限**: 需要认证

**响应示例**:
```json
[
  {
    "id": 1,
    "name": "VHF设备月度巡检",
    "plan_type": "inspection",
    "device_ids": ["VHF001", "VHF002", "VHF003"],
    "cycle_type": "monthly",
    "cycle_value": 1,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2024-01-15T00:00:00Z"
  }
]
```

---

### 2. 创建维护计划

**接口地址**: `POST /api/maintenance-plans/list/`

**权限**: 需要认证

**请求参数**:
```json
{
  "name": "VHF设备月度巡检",
  "plan_type": "inspection",
  "device_ids": ["VHF001", "VHF002", "VHF003"],
  "cycle_type": "monthly",
  "cycle_value": 1
}
```

**响应示例**: 同获取维护计划响应

---

## NGSI-LD数据交换接口

### 1. NGSI-LD根路径

**接口地址**: `GET /api/ngsi/`

**权限**: 无需认证

**响应示例**:
```json
{
  "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
  "description": "ATC Monitor NGSI-LD Exchange Layer",
  "version": "1.0.0",
  "available_endpoints": {
    "entities": {
      "method": "GET",
      "url": "/api/ngsi/entities/",
      "description": "获取实体列表，支持按类型筛选",
      "params": {
        "type": "Device/DeviceStatus/Alarm/PredictionResult",
        "limit": "返回数量（默认50）",
        "offset": "偏移量（默认0）"
      }
    },
    "entity": {
      "method": "GET",
      "url": "/api/ngsi/entity/?id={urn}",
      "description": "根据URN获取单个实体"
    },
    "query": {
      "method": "POST",
      "url": "/api/ngsi/query/",
      "description": "标准查询接口，支持条件过滤"
    },
    "export": {
      "method": "GET",
      "url": "/api/ngsi/export/",
      "description": "导出实体数据交换包"
    },
    "device": {
      "method": "GET",
      "url": "/api/ngsi/devices/{device_id}/",
      "description": "获取指定设备的NGSI-LD实体"
    },
    "device_status": {
      "method": "GET",
      "url": "/api/ngsi/devices/{device_id}/status/",
      "description": "获取指定设备的最新状态"
    },
    "device_alarms": {
      "method": "GET",
      "url": "/api/ngsi/devices/{device_id}/alarms/",
      "description": "获取指定设备的告警列表"
    },
    "alarms": {
      "method": "GET",
      "url": "/api/ngsi/alarms/",
      "description": "获取所有告警的NGSI-LD实体"
    },
    "predictions": {
      "method": "GET",
      "url": "/api/ngsi/predictions/{device_id}/",
      "description": "获取指定设备的预测结果"
    }
  },
  "supported_entity_types": ["Device", "DeviceStatus", "Alarm", "PredictionResult"],
  "content_type": "application/ld+json"
}
```

---

### 2. 获取实体列表

**接口地址**: `GET /api/ngsi/entities/`

**权限**: 无需认证

**查询参数**:
- `type`: 实体类型（Device/DeviceStatus/Alarm/PredictionResult）
- `limit`: 返回数量（默认50）
- `offset`: 偏移量（默认0）

**响应示例**:
```json
[
  {
    "id": "urn:ngsi-ld:Device:VHF001",
    "type": "Device",
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "deviceId": {
      "type": "Property",
      "value": "VHF001"
    },
    "deviceType": {
      "type": "Property",
      "value": "VHF"
    },
    "deviceModel": {
      "type": "Property",
      "value": "VHF-2000"
    },
    "location": {
      "type": "Property",
      "value": "塔台A区"
    },
    "manufacturer": {
      "type": "Property",
      "value": "华为"
    },
    "installTime": {
      "type": "Property",
      "value": "2023-01-15T00:00:00Z"
    },
    "position": {
      "type": "GeoProperty",
      "value": {
        "type": "Point",
        "coordinates": [10.5, 20.3, 15.0]
      }
    },
    "status": {
      "type": "Property",
      "value": "NORMAL"
    },
    "onlineStatus": {
      "type": "Property",
      "value": true
    }
  }
]
```

---

### 3. 根据URN获取实体

**接口地址**: `GET /api/ngsi/entity/?id={urn}`

**权限**: 无需认证

**查询参数**:
- `id`: 实体URN（如：urn:ngsi-ld:Device:VHF001）

**响应示例**: 同获取实体列表响应

---

### 4. 标准查询接口

**接口地址**: `POST /api/ngsi/query/`

**权限**: 无需认证

**请求参数**:
```json
{
  "type": "Device",
  "q": "deviceType=='VHF'",
  "attrs": ["deviceId", "deviceType", "status"],
  "limit": 50,
  "offset": 0
}
```

**响应示例**:
```json
[
  {
    "id": "urn:ngsi-ld:Device:VHF001",
    "type": "Device",
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "deviceId": {
      "type": "Property",
      "value": "VHF001"
    },
    "deviceType": {
      "type": "Property",
      "value": "VHF"
    },
    "status": {
      "type": "Property",
      "value": "NORMAL"
    }
  }
]
```

---

### 5. 导出实体数据

**接口地址**: `GET /api/ngsi/export/`

**权限**: 无需认证

**查询参数**:
- `type`: 实体类型（可选）

**响应示例**:
```json
{
  "@context": [
    "/static/ngsi-ld/ngsi-ld-core-context.jsonld",
    "/static/ngsi-ld/atc-monitor-context.jsonld"
  ],
  "type": "NGSI-LD-ExportPackage",
  "entities": [
    {
      "id": "urn:ngsi-ld:Device:VHF001",
      "type": "Device",
      "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
      "deviceId": {
        "type": "Property",
        "value": "VHF001"
      }
    }
  ]
}
```

---

### 6. 获取设备实体

**接口地址**: `GET /api/ngsi/devices/{device_id}/`

**权限**: 无需认证

**路径参数**:
- `device_id`: 设备ID（字符串）

**响应示例**: 同获取实体列表响应

---

### 7. 获取设备状态

**接口地址**: `GET /api/ngsi/devices/{device_id}/status/`

**权限**: 无需认证

**路径参数**:
- `device_id`: 设备ID（字符串）

**响应示例**:
```json
{
  "id": "urn:ngsi-ld:DeviceStatus:VHF001-20240115103000",
  "type": "DeviceStatus",
  "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
  "refDevice": {
    "type": "Relationship",
    "object": "urn:ngsi-ld:Device:VHF001"
  },
  "onlineStatus": {
    "type": "Property",
    "value": true
  },
  "deviceStatus": {
    "type": "Property",
    "value": "NORMAL"
  },
  "alarmFlag": {
    "type": "Property",
    "value": false
  },
  "deviceTemperature": {
    "type": "Property",
    "value": 45.5
  },
  "deviceHumidity": {
    "type": "Property",
    "value": 60.2
  },
  "collectTime": {
    "type": "Property",
    "value": "2024-01-15T10:30:00Z"
  }
}
```

---

### 8. 获取设备告警

**接口地址**: `GET /api/ngsi/devices/{device_id}/alarms/`

**权限**: 无需认证

**路径参数**:
- `device_id`: 设备ID（字符串）

**响应示例**:
```json
[
  {
    "id": "urn:ngsi-ld:Alarm:ALM-20240115-001",
    "type": "Alarm",
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "refDevice": {
      "type": "Relationship",
      "object": "urn:ngsi-ld:Device:VHF001"
    },
    "alarmId": {
      "type": "Property",
      "value": "ALM-20240115-001"
    },
    "severity": {
      "type": "Property",
      "value": "HIGH"
    },
    "status": {
      "type": "Property",
      "value": "OPEN"
    },
    "metric": {
      "type": "Property",
      "value": "device_temperature"
    },
    "value": {
      "type": "Property",
      "value": 85.5
    },
    "triggerTime": {
      "type": "Property",
      "value": "2024-01-15T10:30:00Z"
    }
  }
]
```

---

### 9. 获取告警列表

**接口地址**: `GET /api/ngsi/alarms/`

**权限**: 无需认证

**查询参数**:
- `status`: 状态筛选（OPEN/ACK/CLOSED）
- `device_id`: 设备ID筛选

**响应示例**: 同获取设备告警响应

---

### 10. 获取预测结果

**接口地址**: `GET /api/ngsi/predictions/{device_id}/`

**权限**: 无需认证

**路径参数**:
- `device_id`: 设备ID（字符串）

**响应示例**:
```json
[
  {
    "id": "urn:ngsi-ld:PredictionResult:1",
    "type": "PredictionResult",
    "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    "refDevice": {
      "type": "Relationship",
      "object": "urn:ngsi-ld:Device:VHF001"
    },
    "metric": {
      "type": "Property",
      "value": "device_temperature"
    },
    "predictedValue": {
      "type": "Property",
      "value": 82.5
    },
    "predictionTime": {
      "type": "Property",
      "value": "2024-01-15T11:00:00Z"
    },
    "predictionHorizon": {
      "type": "Property",
      "value": 30
    },
    "confidenceScore": {
      "type": "Property",
      "value": 0.85
    },
    "errorMargin": {
      "type": "Property",
      "value": 5.0
    },
    "thresholdValue": {
      "type": "Property",
      "value": 80.0
    },
    "isAboveThreshold": {
      "type": "Property",
      "value": true
    },
    "severity": {
      "type": "Property",
      "value": "HIGH"
    },
    "status": {
      "type": "Property",
      "value": "ACTIVE"
    }
  }
]
```

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 认证说明

### JWT Token使用

1. 获取Token：
   ```bash
   curl -X POST http://127.0.0.1:8002/api/token/ \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"password"}'
   ```

2. 使用Token访问受保护接口：
   ```bash
   curl -X GET http://127.0.0.1:8002/api/personnel/ \
     -H "Authorization: Bearer <access_token>"
   ```

3. 刷新Token：
   ```bash
   curl -X POST http://127.0.0.1:8002/api/token/refresh/ \
     -H "Content-Type: application/json" \
     -d '{"refresh":"<refresh_token>"}'
   ```

---

## 注意事项

1. **时间格式**: 所有时间字段使用ISO 8601格式（如：`2024-01-15T10:30:00Z`）

2. **分页**: 列表接口支持分页，默认每页10条记录

3. **权限**: 部分接口需要JWT Token认证，请在请求头中添加：
   ```
   Authorization: Bearer <access_token>
   ```

4. **NGSI-LD格式**: NGSI-LD接口返回的数据格式符合ETSI NGSI-LD规范，使用`application/ld+json`作为Content-Type

5. **数据隔离**: 设备数据支持按用户隔离，普通用户只能看到自己创建的设备

6. **性能优化**: 设备列表接口已优化，避免N+1查询问题

---

## 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 包含完整的设备管理、告警管理、预测分析等功能
- 支持NGSI-LD数据交换标准
- 提供3D可视化数据接口

---

## 联系方式

如有问题或建议，请联系项目维护团队。

---

**文档生成时间**: 2024-01-15
**文档版本**: 1.0.0