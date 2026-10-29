# 数据生成工具

## 功能说明

本工具用于生成项目前期可以使用的测试数据，包括：

- **设备基础信息**：VHF和ILS设备的基本信息
- **状态时序数据**：设备的运行状态数据，包含告警触发
- **数据导出**：将设备信息导出为JSON文件

## 数据设计参考

本工具根据《最小闭环.md》文档设计，满足以下要求：

### 1. 设备类型
- **VHF设备**：2台（VHF-001、VHF-002）
- **ILS设备**：2台（ILS-001、ILS-002）

### 2. 状态字段

#### VHF设备核心字段
- signal_strength（信号强度）
- link_status（链路状态）
- bit_error_rate（误码率）
- device_temperature（运行温度）
- power_voltage（电源电压）
- online_status（在线状态）

#### ILS设备核心字段
- loc_guidance_deviation（LOC引导偏差）
- gs_guidance_deviation（GS下滑偏差）
- signal_power（信号功率）
- device_temperature（运行温度）
- power_voltage（电源电压）
- antenna_swr（天线驻波比）
- online_status（在线状态）

### 3. 告警规则
- **VHF**：信号强度 < -85dBm、链路断开、温度 > 65℃
- **ILS**：引导偏差 > 1.5°、信号功率 < 10dBm、设备离线

## 使用方法

### 1. 进入项目目录

```powershell
cd "c:\Users\fengjunhao\Desktop\covid-19-django-master\项目后端框架"
```

### 2. 运行数据生成脚本

```powershell
python "..\data_resources\generate_data.py"
```

### 3. 脚本执行流程

1. **清空现有数据**：删除数据库中的设备和状态数据
2. **创建设备**：创建4台测试设备
3. **生成状态数据**：生成过去7天的状态数据，每5分钟一次
4. **导出设备信息**：将设备信息导出为JSON文件

### 4. 查看生成结果

- **设备信息**：在数据库中查看或通过API访问 `/api/devices/`
- **状态数据**：通过API访问 `/api/status_logs/`
- **设备信息JSON**：`data_resources/device_info.json`

## 数据验证

### 1. 设备识别验证
- 访问 `/api/devices/`，确认返回4台设备
- 检查设备字段是否完整

### 2. 状态采集验证
- 访问 `/api/status_logs/`，确认返回状态数据
- 检查数据字段是否完整

### 3. 状态判断验证
- 检查 `device_status` 字段，确认状态判断正确
- 检查 `alarm_flag` 字段，确认告警触发正确

### 4. 状态展示验证
- 运行 `generate_visual_report.py` 生成可视化报告
- 检查报告中的告警标记是否正确

## 数据特点

- **模拟真实环境**：数据分布符合真实设备运行状态
- **覆盖完整闭环**：包含设备识别、状态采集、状态判断、告警触发、状态展示
- **高效生成**：批量插入数据，提高生成速度
- **可扩展性**：支持添加更多设备和状态字段

## 注意事项

1. 运行脚本前确保Django服务已启动
2. 首次运行会清空现有数据，请谨慎操作
3. 生成的数据量较大（约2000条状态记录），可能需要几分钟时间
