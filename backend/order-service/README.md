# CashUp 订单服务 (Order Service)

CashUp量化交易系统的订单管理微服务，负责处理交易订单的完整生命周期管理。

## 功能特性

### 核心功能
- 📋 **订单管理**: 创建、查询、更新、取消订单
- 🔄 **订单状态跟踪**: 实时跟踪订单状态变化
- 📊 **订单执行记录**: 记录订单的执行详情
- 📈 **订单统计**: 提供订单相关的统计信息
- 🔗 **交易所集成**: 与多个交易所进行订单交互
- 🔔 **通知服务**: 订单状态变化通知

### 技术特性
- ⚡ **异步处理**: 基于FastAPI的异步架构
- 🗄️ **数据持久化**: PostgreSQL数据库存储
- 🔐 **安全认证**: JWT令牌认证和权限控制
- 📝 **结构化日志**: JSON格式日志记录
- 🚀 **高性能**: 支持高并发订单处理
- 🔍 **监控指标**: 完整的性能监控

## 技术栈

- **框架**: FastAPI 0.104.1
- **数据库**: PostgreSQL (异步SQLAlchemy)
- **缓存**: Redis
- **任务队列**: Celery
- **数据验证**: Pydantic
- **数据库迁移**: Alembic
- **HTTP客户端**: httpx
- **日志**: 结构化JSON日志

## 项目结构

```
order-service/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # API路由主文件
│   │       └── orders.py          # 订单相关接口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # 配置管理
│   │   ├── database.py            # 数据库配置
│   │   ├── auth.py                # 认证授权
│   │   ├── middleware.py          # 中间件
│   │   ├── exceptions.py          # 异常处理
│   │   └── logging.py             # 日志配置
│   ├── models/
│   │   ├── __init__.py
│   │   └── order.py               # 订单数据模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── order.py               # 订单数据模式
│   └── services/
│       ├── __init__.py
│       ├── order_service.py       # 订单业务逻辑
│       ├── exchange_client.py     # 交易所客户端
│       └── notification_service.py # 通知服务
├── alembic/                       # 数据库迁移
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── logs/                          # 日志文件
├── main.py                        # 应用入口
├── pyproject.toml                 # 项目配置
├── alembic.ini                    # Alembic配置
└── README.md
```

## 快速开始

### 环境要求

- Python 3.9+
- PostgreSQL 13+
- Redis 6+

### 安装依赖

```bash
# 使用pip安装
pip install -e .

# 或使用poetry安装
poetry install
```

### 环境配置

创建 `.env` 文件：

```env
# 应用配置
APP_NAME=CashUp Order Service
APP_VERSION=1.0.0
DEBUG=true
PORT=8002

# 数据库配置
DATABASE_URL=postgresql+asyncpg://cashup:cashup123@localhost:5432/cashup_orders

# Redis配置
REDIS_URL=redis://localhost:6379/2

# JWT配置
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 外部服务URL
TRADING_SERVICE_URL=http://localhost:8001
EXCHANGE_SERVICE_URL=http://localhost:8003
USER_SERVICE_URL=http://localhost:8000

# 日志级别
LOG_LEVEL=INFO
```

### 数据库初始化

```bash
# 创建数据库迁移
alembic revision --autogenerate -m "Initial migration"

# 执行数据库迁移
alembic upgrade head
```

### 启动服务

```bash
# 开发模式
python main.py

# 或使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## API 文档

启动服务后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc
- **OpenAPI JSON**: http://localhost:8002/openapi.json

## 主要接口

### 订单管理

- `POST /api/v1/orders/` - 创建订单
- `GET /api/v1/orders/` - 获取订单列表
- `GET /api/v1/orders/{order_id}` - 获取订单详情
- `PUT /api/v1/orders/{order_id}` - 更新订单
- `DELETE /api/v1/orders/{order_id}` - 取消订单

### 订单执行

- `POST /api/v1/orders/{order_id}/executions` - 添加执行记录
- `POST /api/v1/orders/status/update` - 更新订单状态

### 统计信息

- `GET /api/v1/orders/statistics/summary` - 获取订单统计

### 系统接口

- `GET /api/v1/` - 服务信息
- `GET /api/v1/health` - 健康检查

## 数据模型

### 订单模型 (Order)

```python
class Order(Base):
    id: str                    # 订单ID
    user_id: str              # 用户ID
    exchange_name: str        # 交易所名称
    exchange_order_id: str    # 交易所订单ID
    symbol: str               # 交易对
    order_type: OrderType     # 订单类型
    side: OrderSide           # 买卖方向
    quantity: Decimal         # 订单数量
    price: Decimal            # 订单价格
    filled_quantity: Decimal  # 已成交数量
    status: OrderStatus       # 订单状态
    time_in_force: TimeInForce # 有效期类型
    # ... 更多字段
```

### 订单执行记录 (OrderExecution)

```python
class OrderExecution(Base):
    id: str                   # 执行记录ID
    order_id: str            # 订单ID
    execution_id: str        # 执行ID
    quantity: Decimal        # 成交数量
    price: Decimal           # 成交价格
    fee: Decimal             # 手续费
    # ... 更多字段
```

## 配置说明

### 应用配置

- `APP_NAME`: 应用名称
- `APP_VERSION`: 应用版本
- `DEBUG`: 调试模式
- `PORT`: 服务端口

### 数据库配置

- `DATABASE_URL`: 数据库连接URL
- `DATABASE_POOL_SIZE`: 连接池大小
- `DATABASE_MAX_OVERFLOW`: 最大溢出连接数

### 订单配置

- `ORDER_TIMEOUT_SECONDS`: 订单超时时间
- `MAX_ORDERS_PER_USER`: 每用户最大订单数
- `ORDER_HISTORY_RETENTION_DAYS`: 订单历史保留天数

## 监控和日志

### 日志配置

- 支持JSON格式结构化日志
- 自动日志轮转和压缩
- 分级日志记录（应用、访问、错误）

### 监控指标

- 订单处理性能指标
- 数据库连接状态
- 外部服务健康状态
- 系统资源使用情况

## 开发指南

### 代码规范

- 使用Python类型提示
- 遵循PEP 8代码风格
- 编写单元测试
- 添加适当的文档字符串

### 测试

```bash
# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app
```

### 数据库迁移

```bash
# 创建新的迁移
alembic revision --autogenerate -m "描述变更"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 部署

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8002
CMD ["python", "main.py"]
```

### 生产环境配置

- 使用环境变量管理配置
- 配置反向代理（Nginx）
- 设置日志聚合
- 配置监控告警

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 确认网络连通性

2. **订单创建失败**
   - 检查交易所服务状态
   - 验证订单参数
   - 查看错误日志

3. **性能问题**
   - 检查数据库查询性能
   - 监控系统资源使用
   - 优化查询索引

### 日志分析

```bash
# 查看应用日志
tail -f logs/order-service.log

# 查看错误日志
tail -f logs/order-service-error.log

# 查看访问日志
tail -f logs/order-service-access.log
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: CashUp Team
- 邮箱: dev@cashup.com
- 文档: https://docs.cashup.com