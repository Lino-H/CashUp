# CashUp 量化交易系统 - 项目总览文档

> 📅 **最后更新**: 2024年12月
> 🎯 **当前版本**: V4.0
> 📊 **项目状态**: 开发中 - 微服务架构搭建阶段

## 📋 项目概述

**CashUp** 是一个专业的量化交易系统，采用微服务架构，支持多交易所接入、策略回测、实时监控和智能通知。系统面向专业交易员和量化团队，提供高可用、可扩展的量化交易解决方案。

### 核心特性
- 🎯 **专业性**: 面向专业交易员和量化团队
- 🚀 **高性能**: 支持高频交易和大规模数据处理  
- 🔧 **可扩展**: 微服务架构，易于扩展和维护
- 🛡️ **安全性**: 多层安全防护，资金安全保障
- 📊 **智能化**: AI辅助决策和风险管理

## 🏗️ 技术架构

### 微服务架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Load Balancer │
│   (React)       │◄──►│   (Nginx)       │◄──►│   (Docker)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
        │ User Service │ │Trading Svc│ │Strategy Svc │
        └──────────────┘ └───────────┘ └─────────────┘
                │               │               │
        ┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
        │Market Service│ │Order Svc  │ │Notification │
        └──────────────┘ └───────────┘ └─────────────┘
                │               │               │
        ┌───────▼──────┐ ┌─────▼─────┐
        │Config Service│ │Monitor Svc│
        └──────────────┘ └───────────┘
```

### 技术栈

#### 后端技术
- **语言**: Python 3.12+
- **框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL (主库) + Redis (缓存)
- **消息队列**: RabbitMQ
- **ORM**: SQLAlchemy 2.0
- **依赖管理**: UV (现代化 Python 包管理)
- **容器化**: Docker + Docker Compose

#### 前端技术
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **路由**: React Router
- **图表**: Recharts
- **UI组件**: Lucide React Icons

#### 外部集成
- **交易所**: Gate.io API (REST + WebSocket)
- **通知渠道**: QANotify, WXPusher, PushPlus, Telegram Bot, Email (SMTP)

## 📁 项目结构

```
CashUp/
├── .trae/documents/          # 需求文档 (V1-V4)
├── backend/                  # 后端微服务
│   ├── shared/               # 共享库
│   │   └── gateio/          # Gate.io 客户端共享库
│   ├── user-service/         # 用户认证服务 (8001)
│   ├── trading-service/      # 交易执行服务 (8002)
│   ├── strategy-service/     # 策略管理服务 (8003)
│   ├── market-service/       # 行情数据服务 (8004)
│   ├── order-service/        # 订单管理服务 (8005)
│   ├── notification-service/ # 通知服务 (8006)
│   ├── config-service/       # 配置管理服务 (8007)
│   └── monitoring-service/   # 监控服务 (8008)
├── frontend/                 # React 前端应用
├── configs/                  # 配置文件
├── docker/                   # Docker 相关文件
├── docs/                     # 项目文档
├── scripts/                  # 工具脚本
├── docker-compose.yml        # 容器编排
├── Makefile                  # 构建脚本
├── PROJECT_RULES.md          # 项目规则文档
└── PROJECT_ALL_IN_ONE.md     # 本文档
```

## 🎯 核心功能模块

### 用户角色
| 角色    | 注册方式  | 核心权限           |
| ----- | ----- | -------------- |
| 交易员   | 邮箱注册  | 策略执行、交易监控、风险管理 |
| 策略开发者 | 邀请码注册 | 策略开发、回测分析、模型优化 |
| 系统管理员 | 内部分配  | 系统配置、用户管理、监控运维 |

### 核心页面
1. **仪表板页面**: 实时行情展示、持仓概览、收益统计、系统状态监控
2. **策略管理页面**: 策略列表、策略配置、回测报告、策略性能分析
3. **交易监控页面**: 实时交易、订单管理、风险控制、交易历史
4. **通知中心页面**: 通知模板管理、渠道配置、消息历史、告警设置
5. **市场分析页面**: 行情图表、技术指标、市场情绪、资金流向
6. **风险管理页面**: 实时风险监控、组合分析、压力测试、风险报告
7. **系统设置页面**: 用户配置、API管理、安全设置、日志查看

### 微服务详情

| 服务名称 | 端口 | 职责 | 主要技术 | 状态 |
|---------|------|------|----------|------|
| user-service | 8001 | 用户认证、权限管理 | FastAPI, JWT, Redis | 🔄 开发中 |
| trading-service | 8002 | 交易执行、订单管理 | FastAPI, CCXT, WebSocket | 🔄 开发中 |
| strategy-service | 8003 | 策略管理、回测引擎 | FastAPI, NumPy, Pandas | ⏳ 待开发 |
| market-service | 8004 | 行情数据、技术指标 | FastAPI, WebSocket, Redis | 🔄 开发中 |
| order-service | 8005 | 订单生命周期管理 | FastAPI, PostgreSQL | ⏳ 待开发 |
| notification-service | 8006 | 多渠道消息推送 | FastAPI, Celery, Templates | ✅ 已完成 |
| config-service | 8007 | 配置管理、参数调优 | FastAPI, Apollo | ⏳ 待开发 |
| monitoring-service | 8008 | 系统监控、告警 | FastAPI, Prometheus | ⏳ 待开发 |

## 🔧 开发环境配置

### 系统要求
- **操作系统**: macOS (主要开发环境)
- **Python**: 3.12+ (使用 UV 管理)
- **Node.js**: 23.10.0 (LTS)
- **Docker**: 最新版本
- **虚拟环境**: `cashup` (统一环境名称)

### 快速启动
```bash
# 1. 激活 Python 环境
source cashup/bin/activate

# 2. 启动基础设施
docker-compose up -d postgres redis rabbitmq

# 3. 启动前端开发服务器
cd frontend
npm run dev

# 4. 启动后端服务 (按需)
cd backend/user-service
uvicorn app.main:app --reload --port 8001
```

### 环境变量配置
重要配置项已在 `.env.production` 中定义：

#### 数据库配置
- **PostgreSQL**: `postgresql://cashup:cashup123@localhost:5432/cashup`
- **Redis**: `redis://localhost:6379`
- **RabbitMQ**: `amqp://cashup:cashup123@localhost:5672`

#### 交易所配置
- **Gate.io API**: 已配置测试密钥
- **REST API**: https://www.gate.com/docs/developers/apiv4/en/#futures
- **WebSocket**: https://www.gate.com/docs/developers/futures/ws/en/#gate-futures-websocket-v4

#### 通知渠道配置
- **QANotify**: `oL-C4w0kBQFjzMHKH4pnl6oMuCyc`
- **WXPusher**: `AT_Dlr9mx3PXLg3GItFtz3C2RyJnhMKBUgf`
- **PushPlus**: `60ad54690c904ed3b35a06640e1af904`
- **Telegram**: `8411704076:AAGKsaXRYDVmkYhlXQlSu2nBlCJhOfTXhjg`
- **SMTP**: `371886367@qq.com` (QQ邮箱)

## 📊 当前开发状态

### ✅ 已完成
1. **项目基础架构搭建**
   - 微服务目录结构创建
   - Docker 环境配置优化
   - UV 包管理器集成
   - 共享库结构设计

2. **代码重构优化**
   - Gate.io 客户端代码统一到 `backend/shared/gateio/`
   - 移除 trading-service 和 market-service 中的重复代码
   - 更新导入路径使用共享库

3. **环境配置完善**
   - Python 虚拟环境统一管理
   - Node.js 环境配置
   - Docker Compose 服务编排
   - 生产环境配置文件完善

4. **Notification Service 开发完成**
   - 完整的通知服务架构设计
   - 多渠道通知支持（邮件、短信、微信、Telegram等）
   - 模板管理系统和Jinja2引擎集成
   - WebSocket实时通知功能
   - 任务调度和重试机制
   - 健康检查和监控指标
   - Docker容器化部署配置

### 🔄 进行中
1. **Market Service 开发**
   - Gate.io WebSocket 连接调试
   - 行情数据接收和处理
   - Redis 缓存集成

2. **Trading Service 开发**
   - 交易执行引擎
   - 订单管理逻辑
   - 风险控制模块

3. **User Service 开发**
   - JWT 认证系统
   - 用户权限管理
   - 数据库模型设计

### ⏳ 待开发
1. **Strategy Service**: 策略管理、回测引擎
2. **Order Service**: 订单生命周期管理
3. **Config Service**: 配置管理中心
4. **Monitoring Service**: 系统监控告警
5. **Frontend**: React 前端界面

## 🚨 已知问题和解决方案

### Market Service 启动问题
**问题**: 服务启动时出现协程未等待错误
**状态**: 🔄 修复中
**解决方案**: 
- 修复 `get_market_service()` 和 `get_redis()` 协程调用
- 优化服务初始化流程
- 统一异步函数调用规范

### 代码重复问题
**问题**: trading-service 和 market-service 中存在重复的 Gate.io 客户端代码
**状态**: ✅ 已解决
**解决方案**: 
- 创建 `backend/shared/gateio/` 共享库
- 移动 `gateio_client.py` 到共享目录
- 更新所有服务的导入路径

## 📚 重要文档引用

### 需求文档
- 📄 [需求文档 V4.0](.trae/documents/Requirement-V4.md) - 详细功能需求和架构设计

### 配置文档
- 📄 [环境配置说明](README_ENVIRONMENT.md) - 开发环境搭建指南
- 📄 [项目规则文档](PROJECT_RULES.md) - 开发规范和最佳实践
- 📄 [生产环境配置](.env.production) - 正式环境参数配置

### 技术文档
- 🌐 [Gate.io REST API](https://www.gate.com/docs/developers/apiv4/en/#futures)
- 🌐 [Gate.io WebSocket API](https://www.gate.com/docs/developers/futures/ws/en/#gate-futures-websocket-v4)

## 🎯 下一步开发计划

### 短期目标 (1-2周)
1. **完成 Market Service 调试**
   - 解决 WebSocket 连接问题
   - 实现行情数据缓存
   - 添加技术指标计算

2. **完善 Trading Service**
   - 实现基础交易功能
   - 集成风险控制模块
   - 添加订单状态管理

3. **开发 User Service**
   - 实现用户认证系统
   - 设计权限管理模块
   - 创建用户数据模型

### 中期目标 (1个月)
1. **Strategy Service 开发**
   - 策略管理框架
   - 回测引擎实现
   - 多因子模型支持

2. **前端界面开发**
   - 仪表板页面
   - 策略管理界面
   - 交易监控面板

### 长期目标 (3个月)
1. **系统集成测试**
2. **性能优化和监控**
3. **生产环境部署**
4. **用户文档和培训**

## 📞 联系信息

- **项目负责人**: Domi
- **开发团队**: CashUp Team
- **技术支持**: 通过项目 Issues 提交
- **文档维护**: 每次重要变更后更新

---

> 💡 **使用说明**: 本文档是项目的中央信息枢纽，包含了项目的所有重要信息。建议在每次开发会话开始时查阅本文档，了解当前项目状态和开发重点。文档会随着项目进展持续更新。

> 🔄 **更新频率**: 每次重要功能完成或架构调整后更新

> 📋 **版本控制**: 文档变更记录在 Git 提交历史中