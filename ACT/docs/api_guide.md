# API 联调指南 (API Guide)

本指南旨在为前端与后端的 API 联调提供参考。

## ⚙️ 接口标准

- **接口前缀**: `/api/`
- **认证方式 (预留)**: 暂未启用鉴权，可在开发环境中直接访问。生产环境将启用 JWT (Authorization: Bearer <token>)。
- **响应格式**: JSON
- **分页模式**: Django REST Framework (DRF) 默认分页。

## 📋 核心 API 接口

### 1. 设备管理
- `GET /api/devices/`: 获取设备列表。
- `GET /api/devices/{device_id}/`: 获取设备详情。
- `POST /api/devices/`: 创建新设备。
- `PUT /api/devices/{device_id}/`: 更新设备信息。

### 2. 状态日志
- `GET /api/status_logs/`: 获取设备状态记录。
- `POST /api/status_logs/`: 上报设备状态数据（**触发告警的核心接口**）。
  - **参数**: `device` (device_id), `online_status`, `collect_time`, `power_voltage`, `device_temperature` 等。

### 3. 告警管理
- `GET /api/alarms/`: 获取告警记录列表。
- `POST /api/alarms/{id}/operate/`: 告警操作（确认/清除）。
  - **请求体**: `{"action": "ACK"}` 或 `{"action": "CLEAR"}`。
- `GET /api/alarm_rules/`: 获取告警规则列表。

### 4. 环境数据管理
- `GET /api/environment_data/`: 获取环境数据列表。
- `POST /api/environment_data/collect/`: 采集单条环境数据。
- `POST /api/environment_data/collect-batch/`: 批量采集环境数据。
- `GET /api/environment_data/statistics/`: 获取环境数据统计信息。

### 5. 预测结果管理
- `GET /api/predictions/`: 获取预测结果列表。
- `POST /api/predictions/create-prediction/`: 创建预测结果。
- `GET /api/predictions/latest/`: 获取最新预测结果。

### 6. 算法计算接口
- `POST /api/algorithms/sliding-window/`: 滑动窗口计算。
- `POST /api/algorithms/trend-calculation/`: 趋势计算。
- `POST /api/algorithms/prediction/`: 预测计算。
- `POST /api/algorithms/anomaly-detection/`: 异常检测。
- `POST /api/algorithms/threshold-comparison/`: 阈值对比。
- `GET /api/algorithms/device-analysis/`: 设备综合分析。

### 7. NGSI-LD 接口
- `GET /api/ngsi/devices/{device_id}/`: 以 NGSI-LD 格式获取设备实体。
- `GET /api/ngsi/alarms/`: 以 NGSI-LD 格式获取告警实体列表。

## ⚠️ 错误处理约定

当接口返回非 2xx 状态码时，响应格式通常为：
```json
{
    "detail": "错误信息描述",
    "errors": {
        "field_name": ["字段校验错误描述"]
    }
}
```

## 🔌 WebSocket 实时通知
- **连接地址**: `ws://127.0.0.1:8000/ws/notifications/`
- **消息格式**:
```json
{
    "type": "ALARM_TRIGGERED",
    "alarm_id": "ALARM_DEV001_...",
    "device_id": "DEV001",
    "metric": "device_temperature",
    "value": 70,
    "severity": "ERROR",
    "title": "温度过高告警",
    "time": "2026-03-18T..."
}
```
前端收到此类消息后，应立即通过 `ElNotification` 弹出提示。

---

## 📖 环境数据接口详解

### 7.1 环境数据采集接口

**接口地址**: `POST /api/environment_data/collect/`

**请求参数**:
```json
{
    "device_id": "DEV001",
    "ambient_temperature": 25.5,
    "humidity": 60.0,
    "atmospheric_pressure": 1013.25,
    "wind_speed": 5.0,
    "wind_direction": 180.0,
    "rain_intensity": 0.0,
    "visibility": 10.0,
    "collect_time": "2026-05-04T10:00:00Z"
}
```

**响应示例**:
```json
{
    "id": 1,
    "device": 1,
    "device_id": "DEV001",
    "ambient_temperature": 25.5,
    "humidity": 60.0,
    "atmospheric_pressure": 1013.25,
    "wind_speed": 5.0,
    "wind_direction": 180.0,
    "rain_intensity": 0.0,
    "visibility": 10.0,
    "collect_time": "2026-05-04T10:00:00Z",
    "created_at": "2026-05-04T10:00:01Z",
    "updated_at": "2026-05-04T10:00:01Z"
}
```

### 7.2 批量环境数据采集接口

**接口地址**: `POST /api/environment_data/collect-batch/`

**请求参数**:
```json
{
    "data": [
        {
            "device_id": "DEV001",
            "ambient_temperature": 25.5,
            "humidity": 60.0,
            "collect_time": "2026-05-04T10:00:00Z"
        },
        {
            "device_id": "DEV001",
            "ambient_temperature": 26.0,
            "humidity": 62.0,
            "collect_time": "2026-05-04T10:05:00Z"
        }
    ]
}
```

**响应示例**:
```json
{
    "created_count": 2,
    "created_ids": [1, 2],
    "errors": []
}
```

### 7.3 环境数据统计接口

**接口地址**: `GET /api/environment_data/statistics/?device_id=DEV001`

**响应示例**:
```json
{
    "device_id": "DEV001",
    "data_count": 100,
    "statistics": {
        "temperature": {
            "count": 100,
            "avg": 25.5,
            "min": 20.0,
            "max": 30.0,
            "std": 2.5
        },
        "humidity": {
            "count": 100,
            "avg": 60.0,
            "min": 50.0,
            "max": 70.0,
            "std": 5.0
        },
        "atmospheric_pressure": {
            "count": 100,
            "avg": 1013.25,
            "min": 1000.0,
            "max": 1020.0,
            "std": 5.0
        }
    }
}
```

---

## 📖 预测结果接口详解

### 8.1 创建预测结果接口

**接口地址**: `POST /api/predictions/create-prediction/`

**请求参数**:
```json
{
    "device_id": "DEV001",
    "metric": "signal_strength",
    "predicted_value": -45.5,
    "prediction_time": "2026-05-04T11:00:00Z",
    "prediction_horizon": 30,
    "confidence_score": 0.85,
    "error_margin": 2.5,
    "threshold_value": -50.0,
    "is_above_threshold": true,
    "severity": "WARN"
}
```

**响应示例**:
```json
{
    "id": 1,
    "device": 1,
    "device_id": "DEV001",
    "metric": "signal_strength",
    "metric_display": "signal_strength",
    "predicted_value": -45.5,
    "prediction_time": "2026-05-04T11:00:00Z",
    "prediction_horizon": 30,
    "confidence_score": 0.85,
    "error_margin": 2.5,
    "threshold_value": -50.0,
    "is_above_threshold": true,
    "severity": "WARN",
    "severity_display": "警告",
    "status": "PREDICTED",
    "created_at": "2026-05-04T10:30:00Z",
    "updated_at": "2026-05-04T10:30:00Z"
}
```

---

## 📖 算法计算接口详解

### 9.1 滑动窗口计算接口

**接口地址**: `POST /api/algorithms/sliding-window/`

**请求参数**:
```json
{
    "values": [1.0, 2.0, 3.0, 4.0, 5.0],
    "window_size": 3,
    "add_value": 6.0,
    "use_optimized": false
}
```

**响应示例**:
```json
{
    "window_size": 3,
    "current_count": 3,
    "is_full": true,
    "fill_rate": 1.0,
    "statistics": {
        "count": 3,
        "average": 4.0,
        "std": 1.0,
        "min": 3.0,
        "max": 5.0,
        "median": 4.0,
        "range": 2.0,
        "variance": 1.0,
        "fill_rate": 1.0,
        "is_full": true
    },
    "data": [4.0, 5.0, 6.0]
}
```

### 9.2 趋势计算接口

**接口地址**: `POST /api/algorithms/trend-calculation/`

**请求参数**:
```json
{
    "values": [1.0, 2.0, 3.0, 4.0, 5.0],
    "window_size": 10
}
```

**响应示例**:
```json
{
    "trend": {
        "trend_score": 102.0,
        "trend_direction": "increasing",
        "slope": 1.0,
        "r_squared": 1.0,
        "correlation": 1.0
    },
    "values_count": 5,
    "moving_average": [],
    "ema": [1.0, 1.7, 2.49, 3.443, 4.4101]
}
```

### 9.3 预测计算接口

**接口地址**: `POST /api/algorithms/prediction/`

**请求参数**:
```json
{
    "historical_data": [1.0, 2.0, 3.0, 4.0, 5.0],
    "horizon": 5,
    "include_environmental": true,
    "environmental_data": [
        {"ambient_temperature": 25.0, "humidity": 60.0},
        {"ambient_temperature": 26.0, "humidity": 62.0},
        {"ambient_temperature": 27.0, "humidity": 65.0},
        {"ambient_temperature": 28.0, "humidity": 68.0},
        {"ambient_temperature": 29.0, "humidity": 70.0}
    ]
}
```

**响应示例**:
```json
{
    "predictions": [5.5, 6.0, 6.5, 7.0, 7.5],
    "raw_predictions": [5.5, 6.0, 6.5, 7.0, 7.5],
    "trend": {
        "slope": 1.0,
        "direction": "increasing",
        "score": 102.0
    },
    "confidence": 0.8,
    "environmental_impact": {
        "temperature_impact": 0.26,
        "humidity_impact": 0.06,
        "total_impact": 0.32,
        "reliability": 0.75
    },
    "model_parameters": {
        "window_size": 5,
        "alpha": 0.3,
        "threshold": 3.5,
        "volatility": 0.4714045207910317,
        "trend_direction": "increasing"
    }
}
```

### 9.4 异常检测接口

**接口地址**: `POST /api/algorithms/anomaly-detection/`

**请求参数**:
```json
{
    "value": 10.0,
    "mean": 5.0,
    "std": 1.0,
    "threshold": 3.0
}
```

**响应示例**:
```json
{
    "is_anomaly": true,
    "anomaly_score": 5.0,
    "z_score": 5.0
}
```

### 9.5 阈值对比接口

**接口地址**: `POST /api/algorithms/threshold-comparison/`

**请求参数**:
```json
{
    "value": 5.0,
    "threshold": 3.0,
    "operator": ">"
}
```

**响应示例**:
```json
{
    "value": 5.0,
    "threshold": 3.0,
    "operator": ">",
    "compare_result": true,
    "severity": "WARN",
    "deviation": {
        "deviation": 2.0,
        "deviation_ratio": 0.6666666666666666,
        "is_exceeded": true
    }
}
```

### 9.6 设备综合分析接口

**接口地址**: `GET /api/algorithms/device-analysis/?device_id=DEV001&metric=signal_strength&window_size=20`

**响应示例**:
```json
{
    "device_id": "DEV001",
    "metric": "signal_strength",
    "data_count": 20,
    "sliding_window_stats": {
        "count": 20,
        "average": -45.5,
        "std": 3.2,
        "min": -50.0,
        "max": -40.0,
        "median": -45.0,
        "range": 10.0,
        "variance": 10.24,
        "fill_rate": 1.0,
        "is_full": true
    },
    "trend_analysis": {
        "trend_score": 15.5,
        "trend_direction": "decreasing",
        "slope": -0.5,
        "r_squared": 0.85,
        "correlation": -0.92
    },
    "predictions": {
        "basic": {
            "predictions": [-46.0, -46.5, -47.0, -47.5, -48.0],
            "trend": {...},
            "confidence": 0.75
        },
        "with_environmental_factors": {
            "predictions": [-45.8, -46.3, -46.8, -47.3, -47.8],
            "environmental_impact": {...}
        }
    },
    "environmental_data_count": 20
}
```

### 9.7 指数平滑预测接口

**接口地址**: `POST /api/algorithms/exponential-smoothing/`

**请求参数**:
```json
{
    "data": [1.0, 2.0, 3.0, 4.0, 5.0],
    "horizon": 5,
    "method": "auto",
    "alpha": 0.3,
    "beta": 0.1
}
```

**响应示例**:
```json
{
    "predictions": [5.5, 6.0, 6.5, 7.0, 7.5],
    "smoothed_value": 4.5,
    "method": "ses",
    "alpha": 0.3
}
```

### 9.8 模型融合预测接口

**接口地址**: `POST /api/algorithms/model-fusion/`

**请求参数**:
```json
{
    "data": [1.0, 2.0, 3.0, 4.0, 5.0],
    "horizon": 5,
    "weights": {"ma": 0.3, "lr": 0.3, "ses": 0.4}
}
```

**响应示例**:
```json
{
    "predictions": [5.2, 5.8, 6.4, 7.0, 7.6],
    "component_predictions": {
        "moving_average": [4.0, 4.0, 4.0, 4.0, 4.0],
        "linear_regression": [5.2, 5.8, 6.4, 7.0, 7.6],
        "exponential_smoothing": [5.0, 5.5, 6.0, 6.5, 7.0]
    },
    "weights": {"ma": 0.3, "lr": 0.3, "ses": 0.4},
    "method": "fusion"
}
```

### 9.9 IQR异常检测接口

**接口地址**: `POST /api/algorithms/iqr-anomaly-detection/`

**请求参数**:
```json
{
    "data": [1.0, 2.0, 3.0, 4.0, 5.0, 100.0],
    "k": 1.5
}
```

**响应示例**:
```json
{
    "detections": [
        {"value": 1.0, "is_anomaly": false, "anomaly_score": 0, "reason": "normal"},
        ...
        {"value": 100.0, "is_anomaly": true, "anomaly_score": 2.5, "reason": "above_upper_bound"}
    ],
    "adaptive_thresholds": {
        "lower_threshold": 1.5,
        "upper_threshold": 8.5,
        "q1": 2.5,
        "q3": 5.0,
        "iqr": 2.5,
        "confidence_level": 0.95
    },
    "k": 1.5
}
```

### 9.10 缺失数据处理接口

**接口地址**: `POST /api/algorithms/missing-data-handling/`

**请求参数**:
```json
{
    "data": [1.0, null, 3.0, null, 5.0],
    "method": "linear",
    "degree": 2,
    "k": 3
}
```

**响应示例**:
```json
{
    "data": [1.0, 2.0, 3.0, 4.0, 5.0],
    "method": "linear",
    "missing_count": 2,
    "data_quality_score": 0.6
}
```

### 9.11 自适应窗口调整接口

**接口地址**: `POST /api/algorithms/adaptive-window/`

**请求参数**:
```json
{
    "data": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
    "min_window": 5,
    "max_window": 50
}
```

**响应示例**:
```json
{
    "optimal_window": 20,
    "min_window": 5,
    "max_window": 50,
    "volatility": {
        "volatility": 0.15,
        "cv": 0.18,
        "range_ratio": 0.82
    },
    "recommended_for": "stable"
}
```

### 9.12 多变量预测接口

**接口地址**: `POST /api/algorithms/multi-variable-prediction/`

**请求参数**:
```json
{
    "target_data": [1.0, 2.0, 3.0, 4.0, 5.0],
    "related_data": {
        "device_temperature": [25.0, 26.0, 27.0, 28.0, 29.0],
        "humidity": [60.0, 62.0, 65.0, 68.0, 70.0]
    },
    "horizon": 5
}
```

**响应示例**:
```json
{
    "predictions": [5.5, 6.0, 6.5, 7.0, 7.5],
    "raw_predictions": [5.2, 5.8, 6.4, 7.0, 7.6],
    "trend": {"slope": 1.0, "direction": "increasing", "score": 102.0},
    "confidence": 0.78,
    "method": "multi_variable",
    "related_metrics_contribution": 0.15,
    "influential_metrics": ["device_temperature", "humidity"]
}
```

### 9.13 风险评估接口

**接口地址**: `POST /api/algorithms/risk-assessment/`

**请求参数**:
```json
{
    "prediction": 5.5,
    "current_value": 5.0,
    "threshold": 6.0,
    "trend": {"slope": 0.5, "trend_direction": "increasing"},
    "confidence": 0.85,
    "environmental_factors": {"temperature": 30.0, "humidity": 75.0}
}
```

**响应示例**:
```json
{
    "risk_score": 0.65,
    "severity": "ERROR",
    "priority": 25,
    "components": {
        "prediction_risk": 0.3,
        "trend_risk": 0.5,
        "confidence_risk": 0.15,
        "environmental_risk": 0.2
    },
    "prediction": 5.5,
    "threshold": 6.0,
    "deviation_ratio": 0.083,
    "time_to_threshold": 2.0,
    "warning_level": "URGENT"
}
```

### 9.14 批量风险评估接口

**接口地址**: `POST /api/algorithms/batch-risk-assessment/`

**请求参数**:
```json
{
    "predictions": [5.0, 5.5, 6.0, 6.5, 7.0],
    "current_value": 5.0,
    "threshold": 6.0,
    "trend": {"slope": 0.5, "trend_direction": "increasing"},
    "confidence": 0.85
}
```

**响应示例**:
```json
{
    "assessments": [
        {"horizon_step": 1, "risk_score": 0.3, "severity": "WARN", ...},
        {"horizon_step": 2, "risk_score": 0.65, "severity": "ERROR", ...},
        ...
    ],
    "summary": {
        "max_risk_score": 0.95,
        "max_risk_severity": "CRITICAL",
        "max_risk_horizon": 5,
        "warning_level": "IMMEDIATE"
    }
}
```

### 9.15 批量预测处理接口

**接口地址**: `POST /api/algorithms/batch-prediction/`

**请求参数**:
```json
{
    "device_data": [
        {
            "device_id": "device001",
            "metric": "signal_strength",
            "values": [1.0, 2.0, 3.0, 4.0, 5.0],
            "environmental_data": [{"ambient_temperature": 25.0, "humidity": 60.0}]
        },
        {
            "device_id": "device002",
            "metric": "temperature",
            "values": [20.0, 21.0, 22.0, 23.0, 24.0]
        }
    ],
    "horizon": 5,
    "methods": ["trend", "exponential_smoothing"],
    "use_cache": true
}
```

**响应示例**:
```json
{
    "results": [
        {
            "device_id": "device001",
            "metric": "signal_strength",
            "predictions": {
                "trend": {"predictions": [...], "from_cache": false},
                "exponential_smoothing": {"predictions": [...], "from_cache": false}
            }
        }
    ],
    "summary": {
        "total_devices": 2,
        "methods_used": ["trend", "exponential_smoothing"],
        "cache_hits": 0,
        "cache_misses": 4,
        "cache_hit_rate": 0.0
    },
    "timestamp": "2026-05-04T12:00:00"
}
```

### 9.16 增量预测接口

**接口地址**: `POST /api/algorithms/incremental-prediction/`

**请求参数**:
```json
{
    "device_id": "device001",
    "metric": "signal_strength",
    "new_value": 6.0,
    "historical_values": [1.0, 2.0, 3.0, 4.0, 5.0],
    "horizon": 5
}
```

**响应示例**:
```json
{
    "device_id": "device001",
    "metric": "signal_strength",
    "new_value": 6.0,
    "prediction": {
        "predictions": [5.5, 6.0, 6.5, 7.0, 7.5],
        "trend": {...},
        "confidence": 0.8
    },
    "incremental": true,
    "cache_invalidated": true
}
```

### 9.17 设备批量预测接口

**接口地址**: `GET /api/algorithms/batch-prediction-device/?device_id=xxx&metrics=signal_strength,temperature&data.signal_strength=1.0,2.0,3.0&data.temperature=20.0,21.0,22.0&horizon=5`

**响应示例**:
```json
{
    "device_id": "device001",
    "predictions": [...],
    "summary": {
        "total_devices": 1,
        "methods_used": ["trend", "exponential_smoothing"],
        "cache_hits": 0,
        "cache_misses": 2,
        "cache_hit_rate": 0.0
    }
}
```

### 9.18 预测缓存统计接口

**接口地址**: `GET /api/algorithms/prediction-cache-stats/`

**响应示例**:
```json
{
    "cache_enabled": true,
    "total_entries": 10,
    "expired_entries": 2,
    "valid_entries": 8,
    "max_size": 1000,
    "ttl_seconds": 300,
    "utilization": 0.01
}
```

### 9.19 预测缓存清除接口

**接口地址**: `POST /api/algorithms/prediction-cache-clear/`

**请求参数**:
```json
{
    "device_id": "device001",
    "metric": "signal_strength"
}
```

**响应示例**:
```json
{
    "cleared_count": 1,
    "device_id": "device001",
    "metric": "signal_strength"
}
```

---

## 📖 数据模型详解

### EnvironmentData（环境数据模型）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键 |
| device | ForeignKey | 关联设备 |
| ambient_temperature | Float | 环境温度（℃） |
| humidity | Float | 湿度（%） |
| atmospheric_pressure | Float | 大气压力（hPa） |
| wind_speed | Float | 风速（m/s） |
| wind_direction | Float | 风向（度） |
| rain_intensity | Float | 降雨强度（mm/h） |
| visibility | Float | 能见度（km） |
| collect_time | DateTime | 数据采集时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### PredictionResult（预测结果模型）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键 |
| device | ForeignKey | 关联设备 |
| metric | CharField | 预测指标 |
| predicted_value | Float | 预测值 |
| prediction_time | DateTime | 预测时间 |
| prediction_horizon | Integer | 预测时间跨度（分钟） |
| confidence_score | Float | 置信度（0-1） |
| error_margin | Float | 误差范围 |
| threshold_value | Float | 阈值 |
| is_above_threshold | Boolean | 是否超过阈值 |
| severity | CharField | 严重程度 |
| status | CharField | 预测状态 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |
