# CashUp 用户服务 (User Service)

CashUp量化交易系统的用户认证和管理服务，提供用户注册、登录、权限管理等核心功能。

## 🚀 功能特性

### 核心功能
- **用户认证**: 注册、登录、登出
- **JWT令牌管理**: 访问令牌和刷新令牌
- **角色权限系统**: 基于RBAC的权限控制
- **用户管理**: 用户信息CRUD操作
- **安全防护**: 密码加密、速率限制、安全头
- **会话管理**: Redis会话存储和管理

### 用户角色
- **管理员 (ADMIN)**: 系统管理员，拥有所有权限
- **交易员 (TRADER)**: 可执行交易操作
- **分析师 (ANALYST)**: 可查看和分析数据
- **观察者 (VIEWER)**: 只能查看基础信息

### 技术特性
- **异步架构**: 基于FastAPI和asyncio
- **数据库**: PostgreSQL/SQLite + SQLAlchemy ORM
- **缓存**: Redis缓存和会话存储
- **日志**: 结构化日志记录
- **监控**: 性能监控和健康检查
- **安全**: 多层安全防护机制

## 📋 系统要求

- Python 3.11+
- PostgreSQL 13+ (或 SQLite 用于开发)
- Redis 6+
- 内存: 最少 512MB
- 磁盘: 最少 1GB

## 🛠️ 安装和配置

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd CashUp/backend/user-service

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .
```

### 2. 环境配置

创建 `.env` 文件：

```bash
# 应用配置
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here
HOST=0.0.0.0
PORT=8001

# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cashup_user
# 或使用SQLite（开发环境）
# DATABASE_URL=sqlite+aiosqlite:///./cashup_user.db

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# JWT配置
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 安全配置
ALLOWED_HOSTS=["localhost", "127.0.0.1"]
PASSWORD_MIN_LENGTH=8

# 日志配置
LOG_LEVEL=INFO
```

### 3. 数据库初始化

```bash
# 初始化数据库和创建默认用户
python scripts/init_db.py
```

默认用户账户：
- **管理员**: 用户名 `admin`, 密码 `admin123456`
- **交易员**: 用户名 `trader1`, 密码 `trader123456` (仅开发环境)
- **分析师**: 用户名 `analyst1`, 密码 `analyst123456` (仅开发环境)
- **观察者**: 用户名 `viewer1`, 密码 `viewer123456` (仅开发环境)

⚠️ **重要**: 请在生产环境中立即修改默认密码！

## 🚀 启动服务

### 开发模式

```bash
# 使用启动脚本（推荐）
python scripts/start.py --dev

# 或直接使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 生产模式

```bash
# 单进程
python scripts/start.py --prod

# 多进程
python scripts/start.py --prod --workers 4
```

### 自定义配置

```bash
# 自定义主机和端口
python scripts/start.py --host 0.0.0.0 --port 8002

# 启用访问日志
python scripts/start.py --dev --access-log

# 自定义日志级别
python scripts/start.py --dev --log-level debug
```

## 📚 API 文档

启动服务后，可以通过以下链接访问API文档：

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI规范**: http://localhost:8001/openapi.json
- **健康检查**: http://localhost:8001/health

## 🧪 测试

### API测试

```bash
# 运行API测试脚本
python scripts/test_api.py
```

### 单元测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行测试
pytest tests/

# 运行测试并生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

## 📖 API 使用示例

### 用户注册

```bash
curl -X POST "http://localhost:8001/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "SecurePassword123!",
    "full_name": "新用户"
  }'
```

### 用户登录

```bash
curl -X POST "http://localhost:8001/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123456"
  }'
```

### 获取当前用户信息

```bash
curl -X GET "http://localhost:8001/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 刷新令牌

```bash
curl -X POST "http://localhost:8001/api/v1/users/refresh-token" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

## 🏗️ 项目结构

```
user-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # API路由主文件
│   │       └── users.py           # 用户相关API
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # 配置管理
│   │   ├── database.py            # 数据库连接
│   │   ├── security.py            # 安全认证
│   │   ├── redis.py               # Redis连接
│   │   ├── logging.py             # 日志配置
│   │   ├── exceptions.py          # 异常处理
│   │   ├── middleware.py          # 中间件
│   │   └── dependencies.py        # 依赖注入
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py                # 用户数据模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py                # 数据模式定义
│   ├── services/
│   │   ├── __init__.py
│   │   └── user_service.py        # 用户业务逻辑
│   └── __init__.py
├── scripts/
│   ├── init_db.py                 # 数据库初始化
│   ├── start.py                   # 启动脚本
│   └── test_api.py                # API测试脚本
├── tests/                         # 测试文件
├── logs/                          # 日志文件
├── main.py                        # 应用入口
├── pyproject.toml                 # 项目配置
├── Dockerfile                     # Docker配置
└── README.md                      # 项目文档
```

## 🔧 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 | 必需 |
|--------|------|--------|------|
| `ENVIRONMENT` | 运行环境 | `development` | 否 |
| `DEBUG` | 调试模式 | `false` | 否 |
| `SECRET_KEY` | JWT密钥 | - | 是 |
| `DATABASE_URL` | 数据库连接 | - | 是 |
| `REDIS_HOST` | Redis主机 | `localhost` | 否 |
| `REDIS_PORT` | Redis端口 | `6379` | 否 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌过期时间 | `30` | 否 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 刷新令牌过期时间 | `7` | 否 |

### 数据库配置

支持的数据库：
- **PostgreSQL**: `postgresql+asyncpg://user:pass@host:port/db`
- **SQLite**: `sqlite+aiosqlite:///path/to/db.sqlite`

### Redis配置

用于会话存储、缓存和速率限制：
- 会话存储：用户登录状态
- 缓存：用户信息缓存
- 速率限制：API请求频率控制

## 🔒 安全特性

### 认证和授权
- JWT令牌认证
- 基于角色的访问控制 (RBAC)
- 权限细粒度控制
- 会话管理和撤销

### 密码安全
- bcrypt密码哈希
- 密码强度验证
- 登录失败锁定
- 密码重置功能

### API安全
- CORS配置
- 速率限制
- 安全响应头
- 请求验证
- SQL注入防护

### 监控和日志
- 结构化日志记录
- 安全事件监控
- 性能监控
- 错误追踪

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -t cashup-user-service .
```

### 运行容器

```bash
docker run -d \
  --name cashup-user-service \
  -p 8001:8001 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" \
  -e REDIS_HOST="redis-host" \
  -e SECRET_KEY="your-secret-key" \
  cashup-user-service
```

### Docker Compose

```yaml
version: '3.8'
services:
  user-service:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/cashup
      - REDIS_HOST=redis
      - SECRET_KEY=your-secret-key
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=cashup
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## 🔍 监控和维护

### 健康检查

```bash
# 基础健康检查
curl http://localhost:8001/health

# 详细健康检查
curl http://localhost:8001/api/v1/health
```

### 日志查看

```bash
# 查看应用日志
tail -f logs/user-service.log

# 查看错误日志
tail -f logs/user-service-error.log
```

### 性能监控

- 响应时间监控
- 慢请求检测
- 内存使用监控
- 数据库连接池监控

## 🚨 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接字符串格式
   - 确认网络连接

2. **Redis连接失败**
   - 检查Redis服务状态
   - 验证主机和端口配置
   - 检查防火墙设置

3. **JWT令牌无效**
   - 检查SECRET_KEY配置
   - 验证令牌是否过期
   - 确认令牌格式正确

4. **权限不足**
   - 检查用户角色配置
   - 验证权限分配
   - 确认API端点权限要求

### 调试模式

```bash
# 启用调试模式
python scripts/start.py --dev --log-level debug

# 查看详细错误信息
export DEBUG=true
python scripts/start.py --dev
```

## 📞 支持和贡献

### 获取帮助
- 查看API文档: http://localhost:8001/docs
- 检查日志文件: `logs/user-service.log`
- 运行测试脚本: `python scripts/test_api.py`

### 贡献指南
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 运行测试
5. 创建Pull Request

### 开发规范
- 遵循PEP 8代码风格
- 编写单元测试
- 更新文档
- 使用类型注解

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**CashUp量化交易系统** - 专业的量化交易平台