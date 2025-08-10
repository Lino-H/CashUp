# CashUp 配置管理服务

CashUp量化交易系统的配置管理服务，提供系统配置、用户配置、策略配置的统一管理，支持配置版本控制、热更新、权限控制等功能。

## 功能特性

### 核心功能
- **配置管理**: 支持系统、用户、策略等多种配置类型
- **版本控制**: 完整的配置版本历史和回滚功能
- **模板系统**: 预定义配置模板，快速创建标准配置
- **权限控制**: 基于角色的配置访问控制
- **热更新**: 配置变更实时生效，无需重启服务
- **审计日志**: 完整的配置变更审计追踪

### 技术特性
- **高性能**: Redis缓存 + PostgreSQL存储
- **高可用**: 支持集群部署和故障转移
- **安全性**: JWT认证 + 数据加密
- **可扩展**: 插件化架构，支持自定义配置类型
- **监控**: 完整的性能监控和告警

## 技术栈

- **框架**: FastAPI + Pydantic
- **数据库**: PostgreSQL (主存储) + Redis (缓存)
- **认证**: JWT Token
- **部署**: Docker + Docker Compose
- **监控**: Prometheus + Grafana

## 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (可选)

### 本地开发

1. **克隆项目**
```bash
cd backend/config-service
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和Redis连接
```

4. **初始化数据库**
```bash
# 确保PostgreSQL运行，然后执行初始化脚本
psql -U postgres -f init.sql
```

5. **启动服务**
```bash
python main.py
```

服务将在 `http://localhost:8003` 启动

### Docker部署

1. **使用Docker Compose**
```bash
docker-compose up -d
```

这将启动以下服务：
- `config-service`: 配置管理服务 (端口: 8003)
- `postgres`: PostgreSQL数据库 (端口: 5435)
- `redis`: Redis缓存 (端口: 6382)
- `pgadmin`: PostgreSQL管理界面 (端口: 8080)
- `redis-commander`: Redis管理界面 (端口: 8081)

2. **访问服务**
- API文档: http://localhost:8003/docs
- 健康检查: http://localhost:8003/health
- PgAdmin: http://localhost:8080 (admin@cashup.com / admin123)
- Redis Commander: http://localhost:8081

## API文档

### 配置管理

#### 创建配置
```http
POST /api/v1/configs
Content-Type: application/json
Authorization: Bearer <token>

{
  "key": "trading.max_position",
  "name": "最大持仓",
  "description": "单个策略最大持仓金额",
  "type": "trading",
  "scope": "global",
  "value": {"amount": 1000000},
  "format": "json"
}
```

#### 获取配置列表
```http
GET /api/v1/configs?type=trading&scope=global&page=1&size=20
Authorization: Bearer <token>
```

#### 获取配置详情
```http
GET /api/v1/configs/{config_id}
Authorization: Bearer <token>
```

#### 按键获取配置
```http
GET /api/v1/configs/by-key/{config_key}?scope=global
Authorization: Bearer <token>
```

#### 更新配置
```http
PUT /api/v1/configs/{config_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "value": {"amount": 2000000},
  "description": "更新后的描述"
}
```

#### 删除配置
```http
DELETE /api/v1/configs/{config_id}
Authorization: Bearer <token>
```

### 配置模板

#### 获取模板列表
```http
GET /api/v1/templates?type=trading&page=1&size=20
Authorization: Bearer <token>
```

#### 应用模板
```http
POST /api/v1/templates/{template_id}/apply
Content-Type: application/json
Authorization: Bearer <token>

{
  "config_key": "my.trading.config",
  "config_name": "我的交易配置",
  "values": {
    "max_position_size": 500000
  }
}
```

### 版本管理

#### 获取版本历史
```http
GET /api/v1/configs/{config_id}/versions
Authorization: Bearer <token>
```

#### 回滚到指定版本
```http
POST /api/v1/configs/{config_id}/rollback
Content-Type: application/json
Authorization: Bearer <token>

{
  "version": 3,
  "reason": "回滚原因"
}
```

## 配置类型

### 系统配置 (system)
- 应用基础设置
- 服务端口配置
- 日志级别设置
- 功能开关

### 用户配置 (user)
- 个人偏好设置
- 界面配置
- 通知设置

### 策略配置 (strategy)
- 策略参数
- 风险控制
- 执行设置

### 交易配置 (trading)
- 交易限制
- 手续费设置
- 滑点控制

### 风险配置 (risk)
- 风险限制
- 止损设置
- 仓位控制

### API配置 (api)
- 外部API密钥
- 接口限制
- 超时设置

## 配置格式

支持多种配置格式：

### JSON
```json
{
  "max_position": 1000000,
  "risk_limit": 0.02,
  "enabled": true
}
```

### YAML
```yaml
max_position: 1000000
risk_limit: 0.02
enabled: true
```

### TOML
```toml
max_position = 1000000
risk_limit = 0.02
enabled = true
```

### INI
```ini
[trading]
max_position = 1000000
risk_limit = 0.02
enabled = true
```

### ENV
```env
MAX_POSITION=1000000
RISK_LIMIT=0.02
ENABLED=true
```

## 权限系统

### 角色定义
- **super_admin**: 超级管理员，拥有所有权限
- **admin**: 管理员，可管理配置和模板
- **user**: 普通用户，只能读取和修改自己的配置
- **readonly**: 只读用户，只能查看配置

### 权限列表
- `config:read`: 读取配置
- `config:write`: 创建和修改配置
- `config:delete`: 删除配置
- `config:admin`: 配置管理权限
- `template:read`: 读取模板
- `template:write`: 创建和修改模板
- `template:delete`: 删除模板
- `template:admin`: 模板管理权限
- `system:admin`: 系统管理权限
- `audit:read`: 审计日志查看权限
- `batch:operation`: 批量操作权限
- `import:export`: 导入导出权限

## 监控和告警

### 健康检查
```http
GET /health
```

返回服务健康状态：
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0",
  "uptime": 3600
}
```

### 性能指标
- 请求响应时间
- 数据库连接状态
- Redis连接状态
- 缓存命中率
- 配置变更频率

## 开发指南

### 项目结构
```
config-service/
├── app/
│   ├── api/v1/          # API路由
│   ├── core/            # 核心模块
│   ├── models/          # 数据模型
│   ├── schemas/         # Pydantic模式
│   ├── services/        # 业务逻辑
│   ├── middleware/      # 中间件
│   └── utils/           # 工具函数
├── main.py              # 应用入口
├── requirements.txt     # 依赖列表
├── Dockerfile          # Docker镜像
├── docker-compose.yml  # Docker编排
├── init.sql            # 数据库初始化
└── README.md           # 项目文档
```

### 添加新的配置类型

1. 在 `app/models/config.py` 中添加新的枚举值
2. 在 `app/services/template_service.py` 中添加内置模板
3. 更新API文档和测试用例

### 添加新的配置格式

1. 在 `app/models/config.py` 中添加格式枚举
2. 在 `app/utils/helpers.py` 中实现解析和序列化函数
3. 添加相应的测试用例

## 部署指南

### 生产环境部署

1. **环境变量配置**
```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db

# Redis配置
REDIS_URL=redis://host:port/db

# 安全配置
JWT_SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
```

2. **数据库迁移**
```bash
# 执行数据库初始化脚本
psql -U user -h host -d database -f init.sql
```

3. **启动服务**
```bash
# 使用Docker
docker run -d \
  --name config-service \
  -p 8003:8003 \
  -e DATABASE_URL=... \
  -e REDIS_URL=... \
  cashup/config-service:latest

# 或使用Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### 负载均衡

配置Nginx反向代理：
```nginx
upstream config_service {
    server config-service-1:8003;
    server config-service-2:8003;
    server config-service-3:8003;
}

server {
    listen 80;
    server_name config.cashup.com;
    
    location / {
        proxy_pass http://config_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接字符串和凭据
   - 检查网络连接和防火墙设置

2. **Redis连接失败**
   - 检查Redis服务状态
   - 验证Redis配置和密码
   - 检查内存使用情况

3. **JWT认证失败**
   - 检查JWT密钥配置
   - 验证token格式和有效期
   - 检查时钟同步

4. **配置缓存不一致**
   - 清理Redis缓存
   - 重启服务实例
   - 检查缓存同步机制

### 日志分析

查看服务日志：
```bash
# Docker日志
docker logs config-service

# 应用日志
tail -f /var/log/cashup/config-service.log
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 添加测试用例
5. 更新文档
6. 提交Pull Request

## 许可证

MIT License

## 联系我们

- 项目主页: https://github.com/cashup/config-service
- 问题反馈: https://github.com/cashup/config-service/issues
- 邮箱: dev@cashup.com