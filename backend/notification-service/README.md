# CashUp通知服务

CashUp量化交易系统的统一通知服务，提供多渠道通知发送、模板管理、实时WebSocket通信等功能。

## 功能特性

### 核心功能
- 🚀 **多渠道通知发送**：支持邮件、短信、微信、Telegram、Slack、Discord、Webhook、Push等多种通知渠道
- 📝 **模板管理**：支持Jinja2模板引擎，提供模板创建、编辑、预览、验证等功能
- 🔄 **实时通信**：基于WebSocket的实时通知推送和状态更新
- ⏰ **任务调度**：支持定时发送、延迟发送、重试机制等调度功能
- 📊 **监控统计**：提供详细的发送统计、渠道健康监控、系统指标等
- 🔧 **批量操作**：支持批量通知发送、模板管理、渠道配置等

### 技术特性
- ⚡ **异步架构**：基于FastAPI和asyncio的高性能异步处理
- 🗄️ **数据持久化**：使用SQLAlchemy ORM和PostgreSQL数据库
- 🔒 **安全可靠**：支持数据加密、访问控制、错误处理等安全机制
- 📈 **可扩展性**：模块化设计，支持水平扩展和微服务架构
- 🐳 **容器化部署**：提供Docker和Docker Compose配置
- 📋 **API文档**：自动生成的OpenAPI文档和交互式API测试

## 快速开始

### 环境要求
- Python 3.11+
- PostgreSQL 12+
- Redis 6+ (可选，用于缓存)

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd notification-service

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/notification_db

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0

# 应用配置
DEBUG=true
LOG_LEVEL=debug
SECRET_KEY=your-secret-key

# CORS配置
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# 短信配置（示例）
SMS_API_KEY=your-sms-api-key
SMS_API_SECRET=your-sms-api-secret

# 微信配置（示例）
WECHAT_APP_ID=your-wechat-app-id
WECHAT_APP_SECRET=your-wechat-app-secret
```

### 数据库初始化

```bash
# 创建数据库迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 启动服务

```bash
# 开发环境
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产环境
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f notification-service
```

## API文档

启动服务后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 主要API端点

### 通知管理
- `POST /api/v1/notifications` - 创建通知
- `POST /api/v1/notifications/batch` - 批量创建通知
- `GET /api/v1/notifications` - 获取通知列表
- `GET /api/v1/notifications/{id}` - 获取单个通知
- `PUT /api/v1/notifications/{id}` - 更新通知
- `DELETE /api/v1/notifications/{id}` - 删除通知
- `POST /api/v1/notifications/{id}/retry` - 重试发送
- `POST /api/v1/notifications/{id}/cancel` - 取消发送

### 模板管理
- `POST /api/v1/templates` - 创建模板
- `GET /api/v1/templates` - 获取模板列表
- `GET /api/v1/templates/{id}` - 获取单个模板
- `PUT /api/v1/templates/{id}` - 更新模板
- `DELETE /api/v1/templates/{id}` - 删除模板
- `POST /api/v1/templates/{id}/render` - 渲染模板
- `POST /api/v1/templates/{id}/preview` - 预览模板
- `POST /api/v1/templates/{id}/clone` - 克隆模板

### 渠道管理
- `POST /api/v1/channels` - 创建渠道
- `GET /api/v1/channels` - 获取渠道列表
- `GET /api/v1/channels/{id}` - 获取单个渠道
- `PUT /api/v1/channels/{id}` - 更新渠道
- `DELETE /api/v1/channels/{id}` - 删除渠道
- `POST /api/v1/channels/{id}/test` - 测试渠道
- `GET /api/v1/channels/{id}/health` - 获取渠道健康状态

### WebSocket连接
- `WS /api/v1/websocket/connect` - WebSocket连接
- `GET /api/v1/websocket/stats` - 获取连接统计
- `POST /api/v1/websocket/broadcast` - 广播消息

### 健康检查
- `GET /health` - 基础健康检查
- `GET /api/v1/health/detailed` - 详细健康检查
- `GET /api/v1/health/metrics` - 获取系统指标

## 使用示例

### 发送简单通知

```python
import httpx

# 创建通知
notification_data = {
    "title": "交易提醒",
    "content": "您的订单已成功执行",
    "channel_type": "email",
    "recipients": ["user@example.com"],
    "priority": "normal"
}

response = httpx.post(
    "http://localhost:8000/api/v1/notifications",
    json=notification_data
)

print(response.json())
```

### 使用模板发送通知

```python
# 首先创建模板
template_data = {
    "name": "交易成功模板",
    "channel_type": "email",
    "subject": "交易成功 - {{symbol}}",
    "content": "您的{{symbol}}订单已成功执行，数量：{{quantity}}，价格：{{price}}",
    "variables": ["symbol", "quantity", "price"]
}

template_response = httpx.post(
    "http://localhost:8000/api/v1/templates",
    json=template_data
)

template_id = template_response.json()["id"]

# 使用模板发送通知
notification_data = {
    "template_id": template_id,
    "recipients": ["user@example.com"],
    "variables": {
        "symbol": "AAPL",
        "quantity": 100,
        "price": 150.25
    }
}

response = httpx.post(
    "http://localhost:8000/api/v1/notifications",
    json=notification_data
)
```

### WebSocket实时通知

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/websocket/connect?user_id=123');

// 监听消息
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('收到通知:', data);
};

// 订阅频道
ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'trading_alerts'
}));
```

## 项目结构

```
notification-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 应用入口
│   ├── core/                   # 核心配置
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库配置
│   │   ├── logging.py         # 日志配置
│   │   └── security.py        # 安全配置
│   ├── models/                 # 数据模型
│   │   ├── notification.py    # 通知模型
│   │   ├── template.py        # 模板模型
│   │   └── channel.py         # 渠道模型
│   ├── schemas/                # API模式
│   │   ├── notification.py    # 通知模式
│   │   ├── template.py        # 模板模式
│   │   ├── channel.py         # 渠道模式
│   │   └── common.py          # 通用模式
│   ├── services/               # 业务逻辑
│   │   ├── notification_service.py
│   │   ├── template_service.py
│   │   ├── channel_service.py
│   │   ├── sender_service.py
│   │   ├── websocket_service.py
│   │   └── scheduler_service.py
│   └── api/                    # API路由
│       └── v1/
│           ├── notifications.py
│           ├── templates.py
│           ├── channels.py
│           ├── websocket.py
│           └── health.py
├── alembic/                    # 数据库迁移
├── tests/                      # 测试文件
├── scripts/                    # 脚本文件
├── nginx/                      # Nginx配置
├── requirements.txt            # 依赖包
├── Dockerfile                  # Docker配置
├── docker-compose.yml          # Docker Compose配置
└── README.md                   # 项目文档
```

## 开发指南

### 代码规范

```bash
# 代码格式化
black app/
isort app/

# 代码检查
flake8 app/
mypy app/

# 运行测试
pytest tests/ -v --cov=app
```

### 添加新的通知渠道

1. 在 `services/sender_service.py` 中添加新的发送方法
2. 在 `models/channel.py` 中添加渠道类型
3. 在 `services/channel_service.py` 中添加配置验证
4. 更新相关的API模式和文档

### 添加新的模板功能

1. 在 `services/template_service.py` 中添加新的方法
2. 在 `schemas/template.py` 中添加相关模式
3. 在 `api/v1/templates.py` 中添加API端点
4. 更新测试和文档

## 监控和运维

### 健康检查

```bash
# 基础健康检查
curl http://localhost:8000/health

# 详细健康检查
curl http://localhost:8000/api/v1/health/detailed

# 系统指标
curl http://localhost:8000/api/v1/health/metrics
```

### 日志管理

日志文件位置：
- 应用日志：`logs/app.log`
- 错误日志：`logs/error.log`
- 访问日志：`logs/access.log`

### 性能优化

1. **数据库优化**：添加适当的索引，优化查询
2. **缓存策略**：使用Redis缓存频繁访问的数据
3. **连接池**：配置合适的数据库连接池大小
4. **异步处理**：使用异步任务处理耗时操作
5. **负载均衡**：使用Nginx进行负载均衡

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否启动
   - 验证连接字符串配置
   - 检查网络连接

2. **邮件发送失败**
   - 验证SMTP配置
   - 检查邮箱密码或应用密码
   - 确认防火墙设置

3. **WebSocket连接断开**
   - 检查网络稳定性
   - 验证认证信息
   - 查看服务器日志

4. **任务调度异常**
   - 检查调度服务状态
   - 查看任务队列
   - 验证任务配置

### 调试技巧

```bash
# 启用调试模式
export DEBUG=true
export LOG_LEVEL=debug

# 查看详细日志
tail -f logs/app.log

# 检查服务状态
docker-compose ps
docker-compose logs notification-service
```

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/new-feature`)
3. 提交更改 (`git commit -am 'Add new feature'`)
4. 推送到分支 (`git push origin feature/new-feature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证，详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目主页：[GitHub Repository]
- 问题反馈：[GitHub Issues]
- 邮箱：support@cashup.com

---

**CashUp通知服务** - 为量化交易系统提供可靠、高效的通知解决方案。