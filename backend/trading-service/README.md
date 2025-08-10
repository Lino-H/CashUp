# CashUp Trading Service

CashUp量化交易系统的交易服务模块，提供订单管理、交易记录、持仓管理和余额管理等核心功能。

## 功能特性

### 核心功能
- **订单管理**: 创建、更新、取消、查询订单
- **交易记录**: 记录和查询交易历史
- **持仓管理**: 实时持仓跟踪和风险控制
- **余额管理**: 多资产余额管理和转账

### 技术特性
- **异步架构**: 基于FastAPI和asyncio的高性能异步服务
- **数据库支持**: PostgreSQL + SQLAlchemy ORM
- **缓存系统**: Redis缓存提升性能
- **认证授权**: JWT令牌认证和角色权限控制
- **API文档**: 自动生成的OpenAPI文档
- **容器化**: Docker和Docker Compose支持
- **日志系统**: 结构化日志记录
- **健康检查**: 服务健康状态监控

## 项目结构

```
trading-service/
├── app/
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   ├── orders.py          # 订单API
│   │   ├── trades.py          # 交易API
│   │   ├── positions.py       # 持仓API
│   │   └── balances.py        # 余额API
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── redis.py           # Redis连接
│   │   ├── logging.py         # 日志配置
│   │   └── security.py        # 安全认证
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── order.py           # 订单模型
│   │   ├── trade.py           # 交易模型
│   │   ├── position.py        # 持仓模型
│   │   └── balance.py         # 余额模型
│   ├── schemas/                # Pydantic模式
│   │   ├── __init__.py
│   │   ├── order.py           # 订单模式
│   │   ├── trade.py           # 交易模式
│   │   ├── position.py        # 持仓模式
│   │   └── balance.py         # 余额模式
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── order_service.py   # 订单服务
│   │   ├── trade_service.py   # 交易服务
│   │   ├── position_service.py # 持仓服务
│   │   └── balance_service.py # 余额服务
│   └── main.py                # 应用入口
├── alembic/                   # 数据库迁移
├── tests/                     # 测试文件
├── logs/                      # 日志目录
├── requirements.txt           # Python依赖
├── Dockerfile                # Docker配置
├── docker-compose.yml        # Docker Compose配置
└── README.md                 # 项目文档
```

## 快速开始

### 环境要求
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker (可选)

### 本地开发

1. **克隆项目**
```bash
git clone <repository-url>
cd trading-service
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，配置数据库和Redis连接
```

5. **初始化数据库**
```bash
alembic upgrade head
```

6. **启动服务**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker部署

1. **使用Docker Compose**
```bash
docker-compose up -d
```

2. **查看服务状态**
```bash
docker-compose ps
```

3. **查看日志**
```bash
docker-compose logs -f trading-service
```

## API文档

启动服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要API接口

### 订单管理
- `POST /api/v1/orders` - 创建订单
- `GET /api/v1/orders` - 获取订单列表
- `GET /api/v1/orders/{order_id}` - 获取订单详情
- `PUT /api/v1/orders/{order_id}` - 更新订单
- `DELETE /api/v1/orders/{order_id}` - 取消订单

### 交易记录
- `POST /api/v1/trades` - 创建交易记录
- `GET /api/v1/trades` - 获取交易列表
- `GET /api/v1/trades/{trade_id}` - 获取交易详情
- `GET /api/v1/trades/summary` - 获取交易摘要

### 持仓管理
- `POST /api/v1/positions` - 创建持仓
- `GET /api/v1/positions` - 获取持仓列表
- `GET /api/v1/positions/{symbol}` - 获取指定交易对持仓
- `POST /api/v1/positions/close` - 平仓

### 余额管理
- `POST /api/v1/balances` - 创建余额记录
- `GET /api/v1/balances` - 获取余额列表
- `GET /api/v1/balances/{asset}` - 获取指定资产余额
- `POST /api/v1/balances/transfer` - 余额转账

## 配置说明

### 环境变量

```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/trading_db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
DEBUG=false
ALLOWED_HOSTS=["localhost", "127.0.0.1"]

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=./logs
```

## 数据库迁移

### 创建迁移
```bash
alembic revision --autogenerate -m "描述信息"
```

### 应用迁移
```bash
alembic upgrade head
```

### 回滚迁移
```bash
alembic downgrade -1
```

## 测试

### 运行测试
```bash
pytest
```

### 测试覆盖率
```bash
pytest --cov=app --cov-report=html
```

## 监控和日志

### 健康检查
- 基本健康检查: `GET /health`
- 就绪检查: `GET /health/ready`

### 日志文件
- 应用日志: `logs/app.log`
- 错误日志: `logs/error.log`
- 访问日志: `logs/access.log`

## 性能优化

### 数据库优化
- 使用连接池
- 索引优化
- 查询优化

### 缓存策略
- Redis缓存热点数据
- 查询结果缓存
- 会话缓存

### 异步处理
- 异步数据库操作
- 异步Redis操作
- 异步HTTP请求

## 安全考虑

### 认证授权
- JWT令牌认证
- 角色权限控制
- API访问限制

### 数据安全
- 敏感数据加密
- SQL注入防护
- XSS防护

## 部署建议

### 生产环境
- 使用HTTPS
- 配置防火墙
- 设置监控告警
- 定期备份数据

### 扩展性
- 水平扩展支持
- 负载均衡
- 微服务架构

## 故障排除

### 常见问题
1. **数据库连接失败**: 检查数据库配置和网络连接
2. **Redis连接失败**: 检查Redis服务状态
3. **认证失败**: 检查JWT配置和令牌有效性
4. **性能问题**: 检查数据库查询和缓存策略

### 日志分析
```bash
# 查看错误日志
tail -f logs/error.log

# 查看应用日志
tail -f logs/app.log

# 搜索特定错误
grep "ERROR" logs/app.log
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

如有问题或建议，请联系开发团队。