# CODEBUDDY.md

本文件为 CodeBuddy Code 在此代码仓库中工作时提供指导。
项目回复都使用中文。

## 项目概述

**CashUp_v2** 是一个专业的量化交易系统，采用模块化单体架构，专为个人量化交易者设计。提供包括策略开发、专业回测、实时交易和多交易所集成在内的综合工具。

## 架构概览

### 服务架构
- **核心服务 (8001)**: 认证授权、用户管理、配置管理、统一数据库访问
- **交易引擎 (8002)**: 订单执行、持仓跟踪、交易所集成、风险管理
- **策略平台 (8003)**: 策略开发框架、回测引擎、市场数据管理
- **通知服务 (8004)**: 多渠道通知、告警、Webhook管理
- **前端应用**: React SPA，由nginx提供静态文件服务和API代理

### 基础设施技术栈
- **数据库**: PostgreSQL 15 配合 asyncpg 异步驱动
- **缓存**: Redis 7 用于会话管理和缓存
- **容器化**: Docker Compose 配备健康检查和服务依赖
- **前端**: React 18 + TypeScript + Ant Design + Webpack
- **后端**: FastAPI + SQLAlchemy + Pydantic
- **包管理**: Python使用UV（现代pip替代品），Node.js使用npm

## 部署和开发命令

### 快速部署（生产环境）
```bash
# 一键部署脚本
./deploy.sh

# 手动部署步骤
cd frontend && npm install && npm run build && cd ..
docker-compose build
docker-compose up -d

# 检查部署状态
docker-compose ps
curl -f http://localhost:8001/health
```

### 数据备份和恢复
```bash
# 创建备份
./backup.sh

# 恢复数据（示例）
docker-compose down
tar -xzf backups/cashup_backup_YYYYMMDD_HHMMSS.tar.gz
docker exec -i cashup_postgres psql -U cashup -d cashup < backup_file.sql
docker-compose up -d
```

### 开发环境搭建
```bash
# 创建并激活Python虚拟环境
uv venv cashup
source cashup/bin/activate  # macOS/Linux

# 安装所有依赖
make install

# 仅启动基础设施服务
docker-compose up -d postgres redis

# 启动完整开发环境
make dev

# 启动容器化环境
make up
```

### 前端开发
```bash
cd frontend

# 开发服务器（热重载）
npm run start  # 或 npm run dev

# 生产构建
npm run build

# 运行测试
npm test

# 代码检查和类型检查
npm run lint
npm run type-check
npm run format
```

### 后端开发
```bash
# 单独运行某个服务（开发模式）
cd core-service  # 或 trading-engine, strategy-platform, notification-service
source ../cashup/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# 运行特定服务的测试
pytest tests/

# 代码质量检查
make lint    # 所有服务的 flake8, mypy
make format  # 所有服务的 black, isort
```

### 数据库操作
```bash
# 运行数据库迁移
make migrate

# 重置数据库（危险操作）
make reset-db

# 备份/恢复数据库
make backup-db
make restore-db

# 直接访问数据库
docker-compose exec postgres psql -U cashup -d cashup
```

### Docker操作
```bash
# 构建所有服务
make build

# 查看服务日志
make logs

# 检查服务状态
make status

# 清理容器和镜像
make clean
```

## 高层架构设计

### 服务通信模式
- **核心服务** 充当中央认证和配置中心
- 所有服务通过HTTP API通信（无直接数据库共享）
- **前端应用** 通过nginx反向代理与所有服务通信
- **基于会话的认证** 由核心服务管理Bearer令牌
- **CORS配置** 每个服务环境有特定的允许源

### 前端架构
- **React Context API** 用于认证状态管理 (`AuthContext.tsx`)
- **受保护路由** 自动重定向功能 (`ProtectedRoute.tsx`)
- **API拦截器** 自动添加Authorization头 (`services/api.ts`)
- **Ant Design** 组件库确保UI一致性
- **Webpack** 自定义配置支持开发和生产构建

### 后端服务结构
每个后端服务遵循一致的模式：
```
<service-name>/
├── main.py              # FastAPI应用入口，包含CORS和中间件
├── models/              # SQLAlchemy ORM模型
├── schemas/             # Pydantic请求/响应模式
├── crud/                # 数据库操作层
├── api/                 # FastAPI路由端点
├── services/            # 业务逻辑层
├── utils/               # 工具函数
├── requirements.txt     # 依赖项
└── pyproject.toml      # 现代Python项目配置
```

### 数据库架构
- **主数据库**: PostgreSQL 配合 asyncpg 连接池
- **模式初始化**: `scripts/init.sql` 在容器启动时运行
- **迁移策略**: 通过Makefile命令执行SQL脚本
- **连接模式**: 每个服务维护自己的数据库连接池

### 认证流程
1. **登录**: `POST /api/auth/login` 返回 `session_id` 和用户信息
2. **会话存储**: 前端将会话存储在localStorage和cookies中
3. **API请求**: 所有请求在Authorization头中包含session_id
4. **受保护路由**: 前端在渲染前检查认证状态
5. **默认管理员**: `admin` / `admin123` 用于初始系统访问

### API端点模式
```
核心服务 (8001):
  /api/auth/*           # 认证端点
  /api/users/*          # 用户管理
  /api/config/*         # 配置管理

交易引擎 (8002):
  /api/v1/orders        # 订单管理
  /api/v1/positions     # 持仓跟踪
  /api/v1/exchanges     # 交易所集成

策略平台 (8003):
  /api/strategies       # 策略CRUD操作
  /api/backtest         # 回测引擎
  /api/data/*           # 市场数据管理

通知服务 (8004):
  /api/notifications    # 通知管理
  /api/webhooks         # Webhook处理
```

### Docker Compose架构
- **健康检查**: 所有服务都有健康检查端点 (`/health`)
- **服务依赖**: 使用 `depends_on` 配合 `condition: service_healthy`
- **卷挂载**: 开发环境使用卷挂载，生产环境使用构建镜像
- **网络**: 所有服务通过 `cashup_network` 桥接网络通信

### 前端构建和部署
- **开发环境**: Webpack开发服务器，3000端口热重载
- **生产环境**: 静态文件构建到 `frontend/build/`，由nginx提供服务
- **nginx配置**: `frontend/nginx/default.conf` 处理静态文件 + API代理
- **容器策略**: 前端Dockerfile将构建文件复制到nginx:alpine镜像

### 配置管理
- **环境变量**: 本地开发使用 `.env` 文件
- **交易所配置**: `configs/exchanges.yaml` 用于交易集成
- **Docker环境**: 环境变量通过docker-compose.yml传递
- **CORS配置**: 每个服务的ALLOWED_ORIGINS环境变量

### 测试策略
- **后端**: pytest 配合异步测试支持
- **前端**: React Testing Library + Jest
- **端到端**: Cypress 用于端到端测试
- **API测试**: 内置FastAPI测试客户端用于集成测试

### 包管理
- **Python**: UV（pip/pip-tools的现代替代品）配合虚拟环境 `cashup`
- **依赖项**: 每个服务都有 `requirements.txt` 和 `pyproject.toml`
- **前端**: npm 配合 package-lock.json 确保确定性构建

### 开发工作流程
1. **环境搭建**: `make install` 创建虚拟环境并安装所有依赖
2. **开发模式**: `make dev` 启动所有带热重载的服务
3. **测试**: `make test` 运行所有后端和前端测试
4. **代码质量**: `make lint` 和 `make format` 保持代码风格一致
5. **生产构建**: `make build` 创建用于部署的Docker镜像

### 已知架构决策
- **模块化单体**: 服务分离但一起部署，简化复杂性
- **基于会话的认证**: 使用cookies + localStorage而非纯JWT，提高安全性
- **nginx作为前端**: 单个nginx容器提供静态文件服务和API代理
- **UV包管理器**: 选择用于更快的Python依赖解析
- **健康检查依赖**: 服务等待依赖项健康后再启动