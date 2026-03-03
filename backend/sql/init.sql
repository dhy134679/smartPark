-- ============================================
-- 智能停车场系统 —— 数据库初始化脚本
-- 数据库：MySQL 8.0
-- 字符集：utf8mb4
-- ============================================
-- 创建数据库
CREATE DATABASE IF NOT EXISTS smart_parking DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;
USE smart_parking;
-- ============================================
-- 1. 用户表
-- ============================================
DROP TABLE IF EXISTS spot_status_logs;
DROP TABLE IF EXISTS parking_records;
DROP TABLE IF EXISTS fee_rules;
DROP TABLE IF EXISTS parking_spots;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    phone VARCHAR(20) NOT NULL UNIQUE COMMENT '手机号',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    password_hash VARCHAR(128) NOT NULL COMMENT '密码哈希(bcrypt)',
    role VARCHAR(20) NOT NULL DEFAULT 'resident' COMMENT '角色：resident/admin',
    is_resident TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否小区业主',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_phone (phone),
    INDEX idx_role (role)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '用户表';
-- ============================================
-- 2. 车辆表
-- ============================================
CREATE TABLE vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '车辆ID',
    plate_number VARCHAR(20) NOT NULL UNIQUE COMMENT '车牌号码',
    owner_id INT NULL COMMENT '车主ID',
    brand VARCHAR(50) NULL COMMENT '车辆品牌',
    color VARCHAR(20) NULL COMMENT '车辆颜色',
    vehicle_type VARCHAR(20) NOT NULL DEFAULT 'car' COMMENT '车辆类型：car/suv/truck',
    is_resident TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否小区车辆',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE
    SET NULL,
        INDEX idx_plate (plate_number),
        INDEX idx_owner (owner_id),
        INDEX idx_resident (is_resident)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '车辆表';
-- ============================================
-- 3. 车位表
-- ============================================
CREATE TABLE parking_spots (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '车位ID',
    spot_number VARCHAR(10) NOT NULL UNIQUE COMMENT '车位编号(如A-01)',
    zone CHAR(1) NOT NULL COMMENT '区域：A/B/C',
    status VARCHAR(20) NOT NULL DEFAULT 'free' COMMENT '状态：free/occupied/reserved',
    owner_id INT NULL COMMENT '车位所有者',
    is_shared TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否共享',
    shared_start DATETIME NULL COMMENT '共享开始时间',
    shared_end DATETIME NULL COMMENT '共享结束时间',
    x_pos FLOAT NOT NULL DEFAULT 0 COMMENT 'X坐标(导航)',
    y_pos FLOAT NOT NULL DEFAULT 0 COMMENT 'Y坐标(导航)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE
    SET NULL,
        INDEX idx_zone (zone),
        INDEX idx_status (status),
        INDEX idx_owner (owner_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '车位表';
-- ============================================
-- 4. 停车记录表
-- ============================================
CREATE TABLE parking_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    vehicle_id INT NOT NULL COMMENT '车辆ID',
    spot_id INT NULL COMMENT '车位ID',
    plate_number VARCHAR(20) NOT NULL COMMENT '车牌号码',
    entry_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入场时间',
    exit_time DATETIME NULL COMMENT '出场时间',
    duration_minutes INT NULL COMMENT '停车时长(分钟)',
    fee DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '停车费用(元)',
    owner_income DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '车主收益(元)',
    platform_income DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '平台收益(元)',
    is_resident TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否小区车辆',
    is_paid TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已支付',
    payment_time DATETIME NULL COMMENT '支付时间',
    status VARCHAR(20) NOT NULL DEFAULT 'parked' COMMENT '状态：parked/exited/paid',
    entry_image VARCHAR(255) NULL COMMENT '入场图片路径',
    exit_image VARCHAR(255) NULL COMMENT '出场图片路径',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (spot_id) REFERENCES parking_spots(id) ON DELETE
    SET NULL,
        INDEX idx_plate (plate_number),
        INDEX idx_entry_time (entry_time),
        INDEX idx_status (status),
        INDEX idx_vehicle (vehicle_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '停车记录表';
-- ============================================
-- 5. 收费规则表
-- ============================================
CREATE TABLE fee_rules (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '规则ID',
    name VARCHAR(50) NOT NULL COMMENT '规则名称',
    free_minutes INT NOT NULL DEFAULT 30 COMMENT '免费时长(分钟)',
    rate_per_hour DECIMAL(10, 2) NOT NULL DEFAULT 5.00 COMMENT '每小时收费(元)',
    max_daily DECIMAL(10, 2) NOT NULL DEFAULT 50.00 COMMENT '每日封顶(元)',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '收费规则表';
-- ============================================
-- 6. 车位状态日志表（LSTM预测训练数据）
-- ============================================
CREATE TABLE spot_status_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    spot_id INT NOT NULL COMMENT '车位ID',
    status VARCHAR(20) NOT NULL COMMENT '状态：free/occupied',
    occupancy_rate FLOAT NOT NULL DEFAULT 0.0 COMMENT '全局占用率(0~1)',
    total_occupied INT NOT NULL DEFAULT 0 COMMENT '当前占用数',
    total_free INT NOT NULL DEFAULT 0 COMMENT '当前空闲数',
    hour TINYINT NOT NULL DEFAULT 0 COMMENT '小时(0-23)',
    day_of_week TINYINT NOT NULL DEFAULT 0 COMMENT '星期几(0=周一,6=周日)',
    is_weekend TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否周末',
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
    FOREIGN KEY (spot_id) REFERENCES parking_spots(id) ON DELETE CASCADE,
    INDEX idx_spot (spot_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_hour (hour),
    INDEX idx_day (day_of_week)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '车位状态日志表';
-- ============================================
-- 初始数据插入
-- ============================================
-- 默认管理员（密码: admin123）
INSERT INTO users (phone, name, password_hash, role, is_resident)
VALUES (
        '13800000000',
        '系统管理员',
        '$2b$12$WvI3JbsyerYmIwhEwiFoSuT0fOUr3JmSrtUBoY3X351D068zGyzdy',
        'admin',
        1
    );
-- 示例业主（密码: 123456）
INSERT INTO users (phone, name, password_hash, role, is_resident)
VALUES (
        '13800000001',
        '张三',
        '$2b$12$3o9aATsOXzjDMSW3A.bLAO2XPGIuZpAuwJYJ5DQt7kGa2qt6hEoli',
        'resident',
        1
    ),
    (
        '13800000002',
        '李四',
        '$2b$12$3o9aATsOXzjDMSW3A.bLAO2XPGIuZpAuwJYJ5DQt7kGa2qt6hEoli',
        'resident',
        1
    ),
    (
        '13800000003',
        '王五',
        '$2b$12$3o9aATsOXzjDMSW3A.bLAO2XPGIuZpAuwJYJ5DQt7kGa2qt6hEoli',
        'resident',
        1
    );
-- 示例车辆（小区白名单）
INSERT INTO vehicles (
        plate_number,
        owner_id,
        brand,
        color,
        is_resident
    )
VALUES ('京A12345', 2, '比亚迪', '白色', 1),
    ('京B67890', 3, '大众', '黑色', 1),
    ('京C11111', 4, '丰田', '银色', 1);
-- 默认收费规则
INSERT INTO fee_rules (
        name,
        free_minutes,
        rate_per_hour,
        max_daily,
        is_active
    )
VALUES ('标准收费', 30, 5.00, 50.00, 1);
-- A区车位（20个）
INSERT INTO parking_spots (spot_number, zone, x_pos, y_pos)
VALUES ('A-01', 'A', 2, 2),
    ('A-02', 'A', 4, 2),
    ('A-03', 'A', 6, 2),
    ('A-04', 'A', 8, 2),
    ('A-05', 'A', 10, 2),
    ('A-06', 'A', 2, 4),
    ('A-07', 'A', 4, 4),
    ('A-08', 'A', 6, 4),
    ('A-09', 'A', 8, 4),
    ('A-10', 'A', 10, 4),
    ('A-11', 'A', 2, 6),
    ('A-12', 'A', 4, 6),
    ('A-13', 'A', 6, 6),
    ('A-14', 'A', 8, 6),
    ('A-15', 'A', 10, 6),
    ('A-16', 'A', 2, 8),
    ('A-17', 'A', 4, 8),
    ('A-18', 'A', 6, 8),
    ('A-19', 'A', 8, 8),
    ('A-20', 'A', 10, 8);
-- B区车位（15个）
INSERT INTO parking_spots (spot_number, zone, x_pos, y_pos)
VALUES ('B-01', 'B', 14, 2),
    ('B-02', 'B', 16, 2),
    ('B-03', 'B', 18, 2),
    ('B-04', 'B', 20, 2),
    ('B-05', 'B', 22, 2),
    ('B-06', 'B', 14, 4),
    ('B-07', 'B', 16, 4),
    ('B-08', 'B', 18, 4),
    ('B-09', 'B', 20, 4),
    ('B-10', 'B', 22, 4),
    ('B-11', 'B', 14, 6),
    ('B-12', 'B', 16, 6),
    ('B-13', 'B', 18, 6),
    ('B-14', 'B', 20, 6),
    ('B-15', 'B', 22, 6);
-- C区车位（15个）
INSERT INTO parking_spots (spot_number, zone, x_pos, y_pos)
VALUES ('C-01', 'C', 2, 12),
    ('C-02', 'C', 4, 12),
    ('C-03', 'C', 6, 12),
    ('C-04', 'C', 8, 12),
    ('C-05', 'C', 10, 12),
    ('C-06', 'C', 2, 14),
    ('C-07', 'C', 4, 14),
    ('C-08', 'C', 6, 14),
    ('C-09', 'C', 8, 14),
    ('C-10', 'C', 10, 14),
    ('C-11', 'C', 2, 16),
    ('C-12', 'C', 4, 16),
    ('C-13', 'C', 6, 16),
    ('C-14', 'C', 8, 16),
    ('C-15', 'C', 10, 16);
-- 为示例业主分配车位
UPDATE parking_spots
SET owner_id = 2
WHERE spot_number = 'A-01';
UPDATE parking_spots
SET owner_id = 3
WHERE spot_number = 'A-02';
UPDATE parking_spots
SET owner_id = 4
WHERE spot_number = 'B-01';
-- ============================================
-- 验证：查看各表数据量
-- ============================================
SELECT '用户表' AS table_name,
    COUNT(*) AS row_count
FROM users
UNION ALL
SELECT '车辆表',
    COUNT(*)
FROM vehicles
UNION ALL
SELECT '车位表',
    COUNT(*)
FROM parking_spots
UNION ALL
SELECT '收费规则表',
    COUNT(*)
FROM fee_rules;