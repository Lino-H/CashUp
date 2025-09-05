# CashUp 核心服务

## 概述

CashUp 核心服务是整个量化交易系统的基础服务，提供了用户认证、配置管理、权限控制等核心功能。该服务由原来的 user-service 和 config-service 合并而成，采用现代化的 FastAPI 框架构建。

## 功能特性

### 🔐 用户认证与授权
- JWT Token 认证
- 用户注册、登录、密码管理
- 基于角色的访问控制 (RBAC)
- 密码加密存储 (bcrypt)

### ⚙️ 配置管理
- 系统配置和用户配置分离
- 配置分类管理
- 批量配置操作
- 配置权限控制

### 👥 用户管理
- 用户信息管理
- 角色权限控制
- 用户状态管理
- 用户行为日志

### 🌐 API 接口
- RESTful API 设计
- 自动生成 Swagger 文档
- 统一的错误处理
- 完善的数据验证

## 技术栈

- **框架**: FastAPI 0.104.1
- **数据库**: PostgreSQL 15 + SQLAlchemy 2.0
- **缓存**: Redis 7
- **认证**: JWT + python-jose
- **密码**: bcrypt + passlib
- **数据验证**: Pydantic 2.5
- **异步支持**: asyncpg + uvicorn

## 目录结构

```
core-service/
├── main.py                 # 应用入口
├── start_server.py         # 启动脚本
├── requirements.txt        # 依赖列表
├── Dockerfile             # Docker配置
├── api/                   # API层
│   ├── routes/           # 路由定义
│   │   ├── auth.py       # 认证相关接口
│   │   ├── users.py      # 用户管理接口
│   │   └── config.py     # 配置管理接口
│   └── __init__.py
├── auth/                  # 认证模块
│   ├── dependencies.py    # 认证依赖
│   └── __init__.py
├── schemas/               # 数据模型
│   ├── auth.py          # 认证相关模型
│   ├── user.py          # 用户相关模型
│   ├── config.py        # 配置相关模型
│   └── __init__.py
├── services/             # 业务逻辑层
│   ├── auth.py          # 认证服务
│   ├── user.py          # 用户服务
│   ├── config.py        # 配置服务
│   └── __init__.py
├── models/               # 数据库模型
│   └── models.py        # SQLAlchemy模型
├── database/             # 数据库相关
│   ├── connection.py    # 数据库连接
│   └── init_db.py       # 数据库初始化
├── config/               # 配置管理
│   └── settings.py      # 应用配置
└── utils/                # 工具函数
    └── logger.py         # 日志工具
```

## 快速启动

### 方式一：使用 Docker (推荐)

```bash
# 1. 启动基础服务 (PostgreSQL + Redis)
cd CashUp_v2
docker-compose up -d postgres redis

# 2. 构建并启动核心服务
docker-compose up -d core-service

# 3. 查看服务状态
docker-compose ps
docker-compose logs core-service
```

### 方式二：本地开发环境

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动基础服务
docker-compose up -d postgres redis

# 4. 初始化数据库
python database/init_db.py

# 5. 启动服务
python start_server.py
```

### 方式三：直接使用 uvicorn

```bash
# 1. 确保基础服务已启动
docker-compose up -d postgres redis

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
uvicorn core_service.main:app --host 0.0.0.0 --port 8001 --reload
```

## 配置说明

### 环境变量

服务支持以下环境变量配置：

```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://cashup:cashup@localhost:5432/cashup

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 应用配置
DEBUG=true
HOST=0.0.0.0
PORT=8001

# CORS配置
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### 配置文件

可以在 `config/settings.py` 中修改默认配置，推荐使用环境变量进行配置。

## API 接口

### 基础信息

- **服务地址**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health
- **API前缀**: /api

### 认证接口

#### 用户注册
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com", 
  "password": "test123",
  "full_name": "测试用户"
}
```

#### 用户登录
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

#### 获取当前用户信息
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### 用户管理接口

#### 获取用户列表
```http
GET /api/users/?skip=0&limit=10
Authorization: Bearer <token>
```

#### 获取用户详情
```http
GET /api/users/{user_id}
Authorization: Bearer <token>
```

#### 更新用户信息
```http
PUT /api/users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "新姓名",
  "email": "new_email@example.com"
}
```

### 配置管理接口

#### 获取配置列表
```http
GET /api/config/?category=system&skip=0&limit=10
Authorization: Bearer <token>
```

#### 创建配置
```http
POST /api/config/
Authorization: Bearer <token>
Content-Type: application/json

{
  "key": "test_config",
  "value": "test_value",
  "description": "测试配置",
  "category": "test"
}
```

#### 更新配置
```http
PUT /api/config/{config_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "value": "new_value"
}
```

## 数据库模型

### 用户表 (users)
- id: 主键
- username: 用户名
- email: 邮箱
- full_name: 姓名
- hashed_password: 密码哈希
- role: 角色 (user, admin, trader)
- status: 状态 (active, inactive, suspended)
- is_verified: 是否验证
- created_at: 创建时间
- updated_at: 更新时间
- last_login: 最后登录时间

### 配置表 (configs)
- id: 主键
- key: 配置键
- value: 配置值
- description: 描述
- category: 分类
- config_type: 类型 (string, number, boolean, json, array)
- is_system: 是否系统配置
- is_sensitive: 是否敏感配置
- user_id: 所属用户ID
- created_at: 创建时间
- updated_at: 更新时间

## 测试验证

### 健康检查
```bash
curl http://localhost:8001/health
```

### 运行测试脚本
```bash
# 在项目根目录运行
python scripts/test_core_service.py
```

### 测试用户认证
```bash
# 注册用户
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"test123"}'

# 登录获取token
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 默认账户

系统初始化后会创建默认管理员账户：
- **用户名**: admin
- **密码**: admin123
- **角色**: admin

## 日志和监控

### 日志配置
服务使用 Python 标准库 logging 进行日志记录：
- 日志级别: INFO
- 输出格式: 时间戳 - 服务名 - 级别 - 消息
- 输出位置: 控制台

### 健康检查
服务提供健康检查接口 `/health`，返回服务状态和数据库连接状态。

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 PostgreSQL 服务是否启动
   - 验证数据库连接字符串
   - 确认数据库用户权限

2. **Redis 连接失败**
   - 检查 Redis 服务是否启动
   - 验证 Redis 连接字符串

3. **JWT 认证失败**
   - 检查 SECRET_KEY 配置
   - 验证 Token 是否过期

4. **端口占用**
   - 检查 8001 端口是否被占用
   - 修改 config/settings.py 中的 PORT 配置

### 调试模式

设置 `DEBUG=true` 启用调试模式：
- 显示详细的错误信息
- 启用 API 文档 (/docs)
- 启用热重载

## 开发指南

### 添加新的 API 接口

1. 在 `api/routes/` 目录下创建新的路由文件
2. 在 `schemas/` 目录下定义数据模型
3. 在 `services/` 目录下实现业务逻辑
4. 在 `main.py` 中注册新的路由

### 数据库迁移

1. 修改 `models/models.py` 中的模型定义
2. 运行数据库初始化脚本
3. 重启服务

### 环境配置

开发环境和生产环境应使用不同的配置：
- 开发环境: DEBUG=true, 本地数据库
- 生产环境: DEBUG=false, 生产数据库, 强密码

## 部署说明

### 生产环境部署

1. **修改配置**
   - 设置强密码的 SECRET_KEY
   - 配置生产数据库连接
   - 禁用调试模式 (DEBUG=false)

2. **使用 Docker**
   ```bash
   docker build -t cashup-core-service .
   docker run -d -p 8001:8001 --name core-service cashup-core-service
   ```

3. **使用 docker-compose**
   ```bash
   docker-compose up -d
   ```

### 负载均衡

可以使用 Nginx 进行负载均衡和反向代理，参考项目根目录的 nginx 配置。

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 参与讨论

---

**注意**: 本服务是 CashUp 量化交易系统的核心组件，请确保在生产环境中使用适当的安全配置。