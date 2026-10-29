/*
atc_monitor 空管设备数据系统数据库初始化脚本

Date: 2026-02-09
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for devices
-- 设备基础信息表
-- ----------------------------
DROP TABLE IF EXISTS `devices`;
CREATE TABLE `devices` (
  `id` INT(11) PRIMARY KEY AUTO_INCREMENT,
  `device_id` VARCHAR(50) UNIQUE NOT NULL COMMENT '设备唯一标识 (如 VHF-001)',
  `device_type` VARCHAR(20) NOT NULL COMMENT '设备类型 (VHF/ILS)',
  `device_model` VARCHAR(50) DEFAULT NULL COMMENT '设备型号',
  `location` VARCHAR(100) DEFAULT NULL COMMENT '安装位置',
  `manufacturer` VARCHAR(100) DEFAULT NULL COMMENT '生产厂家',
  `install_time` DATETIME DEFAULT NULL COMMENT '投用时间',
  `protocol_version` VARCHAR(20) DEFAULT NULL COMMENT '通信协议版本',
  `status` INT(11) DEFAULT 1 COMMENT '设备状态',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备基础信息表';

-- ----------------------------
-- Table structure for device_status_logs
-- 设备状态时序数据表
-- ----------------------------
DROP TABLE IF EXISTS `device_status_logs`;
CREATE TABLE `device_status_logs` (
  `id` BIGINT(20) PRIMARY KEY AUTO_INCREMENT,
  `device_id` VARCHAR(50) NOT NULL COMMENT '关联设备ID',
  
  -- 通用状态字段
  `online_status` BOOLEAN DEFAULT FALSE COMMENT '在线状态',
  `device_status` VARCHAR(20) DEFAULT 'OFFLINE' COMMENT '综合状态 (NORMAL/ALARM/OFFLINE)',
  `alarm_flag` BOOLEAN DEFAULT FALSE COMMENT '告警标识',
  `power_voltage` FLOAT DEFAULT NULL COMMENT '电源电压 (v)',
  `device_temperature` FLOAT DEFAULT NULL COMMENT '运行温度 (℃)',
  
  -- VHF 专属字段
  `signal_strength` FLOAT DEFAULT NULL COMMENT '信号强度 (dBm)',
  `link_status` VARCHAR(20) DEFAULT NULL COMMENT '链路状态 (CONNECTED/DISCONNECTED)',
  `bit_error_rate` FLOAT DEFAULT NULL COMMENT '误码率 (%)',
  
  -- ILS 专属字段
  `loc_guidance_deviation` FLOAT DEFAULT NULL COMMENT 'LOC引导偏差 (°)',
  `gs_guidance_deviation` FLOAT DEFAULT NULL COMMENT 'GS下滑偏差 (°)',
  `signal_power` FLOAT DEFAULT NULL COMMENT '信号功率 (dBm)',
  `antenna_swr` FLOAT DEFAULT NULL COMMENT '天线驻波比',
  
  `collect_time` DATETIME NOT NULL COMMENT '数据采集时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  INDEX `idx_device_time` (`device_id`, `collect_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备状态时序数据表';

-- ----------------------------
-- Table structure for users
-- 用户表 (可选)
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` INT(11) PRIMARY KEY AUTO_INCREMENT,
  `username` VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
  `password` VARCHAR(100) NOT NULL COMMENT '密码',
  `name` VARCHAR(50) DEFAULT NULL COMMENT '姓名',
  `role` VARCHAR(20) DEFAULT 'user' COMMENT '角色 (admin/user)',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ----------------------------
-- Insert sample data
-- 插入示例数据
-- ----------------------------
-- 插入设备数据
INSERT INTO `devices` (`device_id`, `device_type`, `device_model`, `location`, `manufacturer`) VALUES
('VHF-001', 'VHF', 'TR-8000', '塔台', '罗克韦尔柯林斯'),
('VHF-002', 'VHF', 'TTR-4100', '导航台', '泰雷兹'),
('ILS-001', 'ILS', '4200B', '跑道18L', '霍尼韦尔'),
('ILS-002', 'ILS', 'ILS 720', '跑道36R', '英德拉');

-- 插入用户数据
INSERT INTO `users` (`username`, `password`, `name`, `role`) VALUES
('admin', 'pbkdf2_sha256$390000$zK9v4E4F1r6t7u8i9o0p1a2s3d4f5g6h7j8k9l0', '管理员', 'admin'),
('user', 'pbkdf2_sha256$390000$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8', '普通用户', 'user');

SET FOREIGN_KEY_CHECKS=1;