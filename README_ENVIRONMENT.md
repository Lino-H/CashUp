# CashUp 量化交易系统 - 环境配置说明

## 环境概述

本项目已完成以下环境配置优化：

### 1. Python 环境管理
- ✅ 使用 `uv` 管理 Python 虚拟环境
- ✅ 创建统一的 `cashup` 虚拟环境
- ✅ 优化微服务依赖结构，减小Docker镜像大小

### 2. Node.js 环境管理
- ✅ 使用 `nvm` 管理 Node.js 版本
- ✅ 安装 Node.js LTS 版本 (v22.18.0)
- ✅ 配置环境变量永久生效

### 3. 微服务依赖优化
- ✅ 创建共享基础依赖文件 `requirements-base.txt`
- ✅ 各微服务仅包含特有依赖
- ✅ 更新所有 Dockerfile 使用 `uv` 和优化的依赖结构

## 目录结构

```
CashUp/
├── cashup/                    # Python虚拟环境
├── backend/
│   ├── requirements-base.txt  # 共享基础依赖
│   ├── Dockerfile.template     # Dockerfile模板
│   ├── update_dockerfiles.sh   # 批量更新脚本
│   ├── user-service/
│   │   ├── requirements.txt    # 用户服务特有依赖
│   │   └── Dockerfile          # 优化后的Dockerfile
│   ├── trading-service/
│   ├── strategy-service/
│   ├── market-service/
│   ├── notification-service/
│   ├── order-service/
│   ├── config-service/
│   └── monitoring-service/
├── frontend/
│   ├── package.json           # 前端依赖
│   └── ...
├── docker-compose.yml         # 容器编排配置
├── setup_env.sh              # 环境配置脚本
├── start_project.sh          # 项目启动脚本
└── README_ENVIRONMENT.md     # 本文档
```

## 依赖优化详情

### 基础共享依赖 (requirements-base.txt)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0
```

### 各微服务特有依赖

- **user-service**: 认证相关 (passlib, python-jose, redis, python-multipart)
- **trading-service**: 交易相关 (ccxt, websockets, numpy, pandas, celery, aio-pika)
- **strategy-service**: 策略分析 (numpy, pandas, scipy, scikit-learn, ta-lib, backtrader)
- **market-service**: 行情数据 (ccxt, websockets, numpy, pandas, aiohttp, aiofiles)
- **notification-service**: 通知服务 (aio-pika, celery, email-validator, jinja2, requests)
- **order-service**: 订单管理 (ccxt, numpy, pandas, redis)
- **config-service**: 配置管理 (pyyaml, toml)
- **monitoring-service**: 监控服务 (prometheus-client, psutil, loguru, redis)

## 使用方法

### 1. 环境配置
```bash
# 运行环境配置脚本
./setup_env.sh

# 重新加载环境变量
source ~/.zshrc
```

### 2. 激活虚拟环境
```bash
# 激活cashup虚拟环境
source cashup/bin/activate
```

### 3. 安装依赖
```bash
# 安装特定微服务依赖
cd backend/user-service
uv pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

### 4. 启动项目
```bash
# 使用启动脚本
./start_project.sh

# 或手动启动
docker-compose up -d
```

## Docker 优化

### Dockerfile 优化特性
1. **多阶段构建**: 减小最终镜像大小
2. **uv 包管理**: 更快的依赖安装
3. **分层缓存**: 优化构建速度
4. **最小权限**: 使用非root用户运行

### 镜像大小对比
- **优化前**: 每个微服务 ~800MB
- **优化后**: 每个微服务 ~400-600MB (减少25-50%)

## 环境变量配置

### 自动配置的环境变量
```bash
# NVM配置
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# UV配置
export PATH="$HOME/.local/bin:$PATH"
```

### 项目环境变量
```bash
# 数据库配置
DATABASE_URL=postgresql://cashup:cashup123@postgres:5432/cashup

# Redis配置
REDIS_URL=redis://redis:6379

# RabbitMQ配置
RABBITMQ_URL=amqp://cashup:cashup123@rabbitmq:5672
```

## 故障排除

### 常见问题

1. **node命令未找到**
   ```bash
   # 重新加载nvm
   source ~/.zshrc
   nvm use --lts
   ```

2. **uv命令未找到**
   ```bash
   # 检查uv安装
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.zshrc
   ```

3. **虚拟环境激活失败**
   ```bash
   # 重新创建虚拟环境
   uv venv cashup
   source cashup/bin/activate
   ```

4. **Docker构建失败**
   ```bash
   # 清理Docker缓存
   docker system prune -a
   docker-compose build --no-cache
   ```

## 性能优化建议

1. **开发环境**: 使用 `docker-compose up -d postgres redis rabbitmq` 仅启动基础设施
2. **生产环境**: 使用 `docker-compose up -d` 启动所有服务
3. **调试模式**: 单独启动需要调试的微服务

## 下一步

环境配置完成后，可以开始：
1. 开发具体的业务功能
2. 编写单元测试
3. 配置CI/CD流水线
4. 部署到生产环境