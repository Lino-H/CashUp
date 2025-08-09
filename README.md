# CashUp 量化交易系统

基于微服务架构的量化交易平台，支持多交易所接入、策略回测、实时监控和智能通知。

## 项目结构

```
CashUp/
├── frontend/                 # React前端应用
├── backend/                  # 后端微服务
│   ├── user-service/        # 用户管理服务
│   ├── trading-service/     # 交易执行服务
│   ├── strategy-service/    # 策略管理服务
│   ├── market-service/      # 行情数据服务
│   ├── notification-service/ # 通知服务
│   ├── order-service/       # 订单管理服务
│   ├── config-service/      # 配置管理服务
│   └── monitoring-service/  # 监控服务
├── docker/                  # Docker配置文件
├── configs/                 # 配置文件
├── docs/                    # 文档
└── docker-compose.yml       # 容器编排配置
```

## 技术栈

### 前端
- React 18 + TypeScript
- Vite 构建工具
- Ant Design UI组件库
- WebSocket 实时通信

### 后端
- Python 3.12 + FastAPI
- PostgreSQL 数据库
- Redis 缓存
- RabbitMQ 消息队列
- Apollo 配置中心

### 部署
- Docker + Docker Compose
- 微服务架构
- 容器化部署

## 快速开始

### 环境要求
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- uv (Python包管理器)

### 安装依赖

1. 创建Python虚拟环境
```bash
uv venv cashup
source cashup/bin/activate
```

2. 启动基础服务
```bash
docker-compose up -d postgres redis rabbitmq apollo
```

3. 启动后端服务
```bash
# 每个服务单独启动
cd backend/user-service
uv pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

4. 启动前端服务
```bash
cd frontend
npm install
npm run dev
```

### 使用Docker启动全部服务
```bash
docker-compose up -d
```

## 服务端口

- 前端: http://localhost:3000
- 用户服务: http://localhost:8001
- 交易服务: http://localhost:8002
- 策略服务: http://localhost:8003
- 行情服务: http://localhost:8004
- 通知服务: http://localhost:8005
- 订单服务: http://localhost:8006
- 配置服务: http://localhost:8007
- 监控服务: http://localhost:8008
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- RabbitMQ: localhost:5672 (管理界面: http://localhost:15672)
- Apollo: http://localhost:8070

## 开发指南

### 微服务开发
每个微服务都是独立的Python应用，使用FastAPI框架：

1. 进入服务目录
2. 激活虚拟环境: `source ../../cashup/bin/activate`
3. 安装依赖: `uv pip install -r requirements.txt`
4. 启动服务: `uvicorn main:app --reload`

### 前端开发
使用React + TypeScript + Vite：

1. 进入frontend目录
2. 安装依赖: `npm install`
3. 启动开发服务器: `npm run dev`

## 核心功能

- 🔐 用户认证与权限管理
- 📊 多交易所行情数据接入
- 🤖 量化策略管理与回测
- 💹 实时交易执行
- 📈 投资组合管理
- 🔔 智能通知系统
- 📱 响应式Web界面
- 🛡️ 风险管理与监控

## 许可证

MIT License