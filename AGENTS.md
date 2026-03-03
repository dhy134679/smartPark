# 智能停车场系统 - Codex 开发指南

## 项目概述

基于微信小程序的智能停车场管理系统（毕设项目）。解决老旧小区停车难问题，核心功能包括：车牌识别（PyTorch）、车位预测（LSTM）、停车导航（A*算法）、计时收费、出入模拟。

**运行环境**：localhost 本地运行，不部署互联网。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | UniApp (Vue3) → 微信小程序 |
| 后端 | Python FastAPI |
| 数据库 | MySQL 8.0 |
| ORM | SQLAlchemy 2.0 + PyMySQL |
| 认证 | JWT (PyJWT) |
| 车牌识别 | PyTorch + YOLOv5（检测）+ LPRNet（识别），使用预训练模型权重 |
| 车位预测 | PyTorch LSTM 时序预测 |
| 停车导航 | A* 寻路算法 + Canvas 绘制 |

## 项目结构

```
d:\p1\
├── docs/                          # 项目文档（已完成）
│   ├── 技术定位文档.md
│   ├── 需求分析文档.md
│   ├── 系统设计文档.md
│   ├── 数据库设计文档.md
│   └── 项目架构说明.md
├── backend/                       # 后端（Python FastAPI）
│   ├── app/
│   │   ├── main.py                # FastAPI 入口
│   │   ├── config.py              # 配置（数据库、JWT、停车场、收费规则）
│   │   ├── database.py            # MySQL + SQLAlchemy 异步连接
│   │   ├── models/                # ORM 模型：User, Vehicle, ParkingSpot, ParkingRecord, FeeRule, SpotStatusLog
│   │   ├── schemas/               # Pydantic 数据验证
│   │   ├── routers/               # API 路由：auth, spots, parking, recognize, navigation, predict
│   │   └── services/              # 业务逻辑：auth_service, spot_service, fee_service, parking_service, navigation_service
│   ├── ai/
│   │   ├── plate_recognition/     # YOLOv5 + LPRNet 车牌识别
│   │   │   ├── detector.py        # YOLOv5 检测
│   │   │   ├── recognizer.py      # LPRNet 识别
│   │   │   ├── pipeline.py        # 完整流水线
│   │   │   └── weights/           # 预训练权重 .pth
│   │   └── prediction/            # LSTM 车位预测
│   │       ├── lstm_model.py      # 网络定义
│   │       ├── train.py           # 训练脚本
│   │       ├── predict_service.py # 推理服务
│   │       ├── data_generator.py  # 模拟数据生成
│   │       └── weights/           # 训练好的权重
│   ├── sql/
│   │   └── init.sql               # 数据库初始化（已完成）
│   ├── uploads/                   # 上传图片存储
│   └── requirements.txt
└── frontend/                      # UniApp 前端（已存在，HBuilderX 创建的 Vue3 项目）
    ├── App.vue, main.js           # 已有：根组件、入口
    ├── manifest.json              # 已有：UniApp配置（vueVersion: "3"）
    ├── pages.json                 # 已有：页面路由（需扩展）
    ├── uni.scss                   # 已有：全局样式变量
    ├── pages/                     # 已有 index 页，需新增：login, spots, simulate, navigation, predict, records, profile
```

## 数据库

数据库名：`smart_parking`，字符集 utf8mb4，6 张表：

1. **users** - 用户表（phone, name, password_hash, role, is_resident）
2. **vehicles** - 车辆表（plate_number, owner_id→users, brand, color, is_resident）
3. **parking_spots** - 车位表（spot_number, zone[A/B/C], status[free/occupied/reserved], owner_id, x_pos, y_pos, is_shared）
4. **parking_records** - 停车记录（vehicle_id, spot_id, plate_number, entry_time, exit_time, fee, is_paid, status[parked/exited/paid]）
5. **fee_rules** - 收费规则（free_minutes=30, rate_per_hour=5, max_daily=50）
6. **spot_status_logs** - 车位状态日志（LSTM 训练数据：occupancy_rate, hour, day_of_week, is_weekend）

完整建表 SQL 在 `backend/sql/init.sql`，含 50 个车位（A区20、B区15、C区15）和示例数据。

## API 接口

| 模块 | 路径 | 方法 | 说明 |
|------|------|------|------|
| 认证 | `/api/auth/register` | POST | 注册（phone, name, password） |
| 认证 | `/api/auth/login` | POST | 登录 → JWT token |
| 车辆 | `/api/vehicles` | GET/POST | 车辆列表/绑定车辆 |
| 车位 | `/api/spots` | GET | 车位列表（支持 ?zone= 筛选） |
| 车位 | `/api/spots/summary` | GET | 总数/空闲/占用统计 |
| 车位 | `/api/spots/{id}/share` | PUT | 车主上传空闲共享 |
| 识别 | `/api/recognize` | POST | 上传图片 → 车牌识别 |
| 入场 | `/api/parking/entry` | POST | 入场：识别→判断→分配→计时 |
| 出场 | `/api/parking/exit` | POST | 出场：识别→计费→释放 |
| 记录 | `/api/parking/records` | GET | 停车记录分页 |
| 统计 | `/api/parking/statistics` | GET | 今日统计 |
| 导航 | `/api/navigation/map` | GET | 停车场地图数据 |
| 导航 | `/api/navigation/route` | POST | A* 路径规划 |
| 预测 | `/api/predict/availability` | GET | 预测空闲时间 |
| 预测 | `/api/predict/trend` | GET | 占用率趋势 |

**统一响应格式**：`{ "code": 200, "message": "success", "data": {} }`

## 核心业务逻辑

### 车辆入场流程
上传图片 → YOLOv5检测车牌 → LPRNet识别字符 → 查白名单(vehicles表is_resident) → 小区车免费/外来车计时 → 查空闲车位 → A*路径规划 → 返回导航路线

### 车辆出场流程
识别车牌 → 查parking_records → 计算时长 → 计费(首30分钟免费, 5元/小时, 日封顶50) → 小区车直接放行 → 释放车位

### 计费规则
```python
if duration <= 30min: fee = 0
elif is_resident: fee = 0
else: fee = min(ceil(duration/60) * 5, 50)
```

### 车位预测
LSTM(2层, hidden=128/64) 输入过去24个时间步(特征: 占用率,小时,星期,是否周末,历史均值) → 输出未来12个时间步占用率

## 开发规范

- 代码注释使用**中文**
- Git 提交格式：`feat: 添加xxx功能` / `fix: 修复xxx问题`
- 文件名小写下划线，类名大驼峰，函数名小写下划线
- API 路径小写，数据库表名小写下划线复数

## 待实现模块（按顺序）

1. ✅ 项目文档（全部已完成）
2. ✅ 数据库初始化脚本（init.sql + init_db.py）
3. ✅ 后端 FastAPI 基础架构（main.py, config.py, database.py, models/, schemas/）
4. ✅ 认证模块（routers/auth.py, services/auth_service.py, dependencies/auth.py）
5. ✅ 车位管理（routers/spots.py, services/spot_service.py）
6. ✅ 计费与出入管理（routers/parking.py, services/fee_service.py, parking_service.py）
7. ✅ 车牌识别集成（ai/plate_recognition/ pipeline+detector+recognizer）
8. ✅ 停车导航（routers/navigation.py, services/navigation_service.py —— A*算法）
9. ✅ 车位预测（ai/prediction/ lstm_model+predict_service+data_generator+train）
10. ✅ UniApp 前端全部 8 个页面（含 Canvas 停车场地图 + 图片上传识别）
11. ⬜ 用户本地测试联调

## 车牌识别模型来源

使用开源预训练模型，推荐 [Chinese_license_plate_detection_recognition](https://github.com/we0091234/Chinese_license_plate_detection_recognition)：
- YOLOv5 车牌检测 → 预训练权重直接加载
- LPRNet 字符识别 → 预训练权重直接加载
- 无需自行训练，下载 .pth 文件放入 `ai/plate_recognition/weights/` 即可

## 重要参考文件

- 详细表结构和 SQL → `docs/数据库设计文档.md` + `backend/sql/init.sql`
- 完整接口设计 → `docs/系统设计文档.md`
- 完整需求列表 → `docs/需求分析文档.md`
- 技术栈和算法 → `docs/技术定位文档.md`
- 目录结构和规范 → `docs/项目架构说明.md`
