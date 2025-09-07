# CashUp_v2 量化交易系统

## 项目概述

CashUp_v2 是一个专为个人量化交易者设计的高效交易平台，采用模块化单体架构，重点提升策略开发便利性和回测能力。

## 主要特性

- 🚀 **高效架构**: 模块化单体架构，降低运维复杂度
- 📊 **专业回测**: 完整的策略回测引擎和性能分析
- 🔥 **热部署**: 支持策略动态加载，无需重启系统
- 🏪 **多交易所**: 统一的交易所抽象层，支持主流交易所
- 📈 **实时监控**: 实时策略执行和风险控制
- 🎯 **易用性**: 直观的Web界面和丰富的策略模板

## 系统架构

```
CashUp_v2/
├── core-service/           # 核心服务 (8001)
│   ├── auth/              # 认证和授权
│   ├── config/            # 配置管理
│   ├── database/          # 数据库访问
│   ├── models/            # 数据模型
│   └── api/               # API接口
├── trading-engine/        # 交易引擎 (8002)
│   ├── exchanges/         # 交易所适配器
│   ├── orders/            # 订单管理
│   ├── execution/         # 执行引擎
│   └── risk/              # 风险控制
├── strategy-platform/     # 策略平台 (8003)
│   ├── strategies/        # 策略管理
│   ├── backtest/          # 回测引擎
│   ├── data/              # 数据管理
│   └── monitoring/        # 监控告警
├── notification-service/  # 通知服务 (8004)
│   ├── channels/          # 通知渠道
│   ├── templates/         # 通知模板
│   └── queue/             # 消息队列
├── frontend/              # 前端应用 (3000)
├── nginx/                 # Nginx反向代理 (80/443)
│   ├── 负载均衡
│   ├── SSL终端
│   ├── 静态文件服务
│   └── API路由
└── strategies/            # 策略目录
    ├── templates/         # 策略模板
    ├── examples/          # 示例策略
    └── custom/            # 自定义策略
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- UV (Python包管理器)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/CashUp.git
cd CashUp/CashUp_v2
```

2. **创建Python虚拟环境**
```bash
uv venv cashup
source cashup/bin/activate  # macOS/Linux
# 或
cashup\Scripts\activate     # Windows
```

3. **启动基础设施**
```bash
docker-compose up -d postgres redis
```

4. **安装依赖**
```bash
make install
```

5. **启动服务**
```bash
make dev
```

### 访问地址

- Web界面: http://localhost:80 (通过Nginx反向代理)
- 前端应用: http://localhost:3000 (直接访问)
- 核心服务: http://localhost:8001
- 交易引擎: http://localhost:8002
- 策略平台: http://localhost:8003
- 通知服务: http://localhost:8004
- API文档: http://localhost:8001/docs

## 核心功能

### 策略开发

CashUp_v2 提供了完整的策略开发框架：

```python
from strategy_platform.strategies.base import StrategyBase, StrategyConfig, StrategySignal, SignalType

class MyStrategy(StrategyBase):
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.version = "1.0.0"
        self.author = "Your Name"
    
    def initialize(self):
        """策略初始化"""
        pass
    
    def on_data(self, data):
        """处理市场数据"""
        # 实现你的策略逻辑
        if self.should_buy(data):
            return StrategySignal(
                signal_type=SignalType.BUY,
                symbol=data['symbol'],
                quantity=1.0,
                reason="买入信号"
            )
        return None
```

### 回测引擎

内置专业级回测引擎：

```python
from strategy_platform.backtest.engine import BacktestEngine, BacktestConfig

# 创建回测配置
config = BacktestConfig(
    strategy_name="MyStrategy",
    strategy_class=MyStrategy,
    strategy_params={},
    symbols=["BTC/USDT"],
    timeframe="1h",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    initial_capital=10000.0
)

# 运行回测
engine = BacktestEngine(data_manager)
result = await engine.run_backtest(config)

# 生成报告
engine.generate_report("MyStrategy")
```

### 交易所接入

支持多交易所统一接入：

```python
from trading_engine.exchanges.base import ExchangeManager, OrderRequest, OrderSide, OrderType

# 创建交易所管理器
manager = ExchangeManager()

# 添加交易所
manager.add_exchange("binance", {
    "type": "binance",
    "api_key": "your-api-key",
    "api_secret": "your-api-secret",
    "sandbox": True
})

# 下单
exchange = manager.get_exchange("binance")
order_request = OrderRequest(
    symbol="BTC/USDT",
    side=OrderSide.BUY,
    type=OrderType.MARKET,
    quantity=0.001
)

order = await exchange.place_order(order_request)
```

## 策略模板

系统提供多种策略模板：

- **基础策略**: 简单的价格突破策略
- **均线交叉**: 双均线交叉策略
- **RSI策略**: RSI超买超卖策略
- **网格交易**: 网格交易策略

## 配置说明

### 环境变量

创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://cashup:cashup@localhost:5432/cashup

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_REFRESH_SECRET_KEY=your-jwt-refresh-secret

# 交易所配置
BINANCE_API_KEY=your-binance-api-key
BINANCE_API_SECRET=your-binance-api-secret

# 通知配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 交易所配置

在 `configs/exchanges.yaml` 中配置交易所：

```yaml
exchanges:
  binance:
    type: binance
    api_key: "${BINANCE_API_KEY}"
    api_secret: "${BINANCE_API_SECRET}"
    sandbox: true
    rate_limit: 10
  
  gateio:
    type: gateio
    api_key: "${GATEIO_API_KEY}"
    api_secret: "${GATEIO_API_SECRET}"
    sandbox: true
    rate_limit: 10
```

## 前端认证功能

### 认证系统概述

CashUp_v2 前端采用 React Context API 实现认证状态管理，支持会话认证机制。所有前端代码位于 `frontend/src/` 目录下。

### 认证架构

```
frontend/src/
├── contexts/AuthContext.tsx      # 认证上下文管理
├── components/ProtectedRoute.tsx # 受保护路由组件
├── pages/LoginPage.tsx           # 登录页面
├── services/api.ts              # API服务配置
└── App.tsx                      # 主应用组件
```

### 登录流程

1. **用户输入**: 用户名和密码
2. **API调用**: 发送到 `POST /api/auth/login`
3. **会话创建**: 后端返回 `session_id` 和用户信息
4. **状态管理**: 前端存储 `session_id` 并设置认证状态
5. **页面跳转**: 自动跳转到仪表板页面

### 关键功能

#### 1. 认证上下文 (AuthContext)
```typescript
interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}
```

#### 2. 受保护路由 (ProtectedRoute)
- 检查用户认证状态
- 未认证用户自动重定向到登录页
- 支持加载状态显示

#### 3. API拦截器
- 自动添加 `session_id` 到请求头
- 统一错误处理
- 响应数据预处理

### 登录信息

- **管理员账户**: `admin` / `admin123`
- **API端点**: `POST /api/auth/login`
- **响应格式**: 
  ```json
  {
    "session_id": "...",
    "user": {
      "id": 8,
      "username": "admin",
      "email": "admin@cashup.com",
      "full_name": "系统管理员",
      "role": "ADMIN"
    }
  }
  ```

### 测试认证功能

#### 方法1: 浏览器测试
1. 访问: `http://localhost:3000`
2. 使用 `admin` / `admin123` 登录
3. 验证页面跳转到仪表板
4. 检查用户信息显示在右上角

#### 方法2: API测试
```bash
# 测试登录
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 测试用户信息
curl -X GET http://localhost:8001/api/auth/me \
  -H "Cookie: session_id=你的session_id"
```

#### 方法3: 控制台测试
在浏览器控制台运行以下脚本：
```javascript
// 复制 frontend/public/auth-test.js 到控制台
await runFullTest();
```

### 故障排除

#### 常见问题

1. **登录后页面不跳转**
   - 检查浏览器控制台是否有错误
   - 确认 `localStorage` 中有 `access_token`
   - 验证 `isAuthenticated` 状态是否更新

2. **401认证错误**
   - 检查 `session_id` 是否正确存储
   - 确认API请求是否包含Cookie头
   - 验证用户状态是否正常

3. **页面显示空白**
   - 检查React应用是否正常加载
   - 确认路由配置是否正确
   - 查看浏览器控制台是否有JavaScript错误

#### 调试工具

- **浏览器开发者工具**: 查看网络请求和控制台错误
- **Docker日志**: `docker-compose logs -f frontend`
- **API测试**: 使用curl或Postman测试后端API

### 配置说明

#### 环境变量
在 `frontend/.env` 中配置：
```env
REACT_APP_API_URL=http://localhost:8001/api
REACT_APP_TRADING_URL=http://localhost:8002/api
REACT_APP_STRATEGY_URL=http://localhost:8003/api
REACT_APP_NOTIFICATION_URL=http://localhost:8004/api
```

#### API路由配置
前端API调用使用以下格式：
```typescript
// 认证相关
authAPI.login(username, password)           // POST /api/auth/login
authAPI.getCurrentUser()                    // GET /api/auth/me

// 策略相关
strategyAPI.getStrategies()                 // GET /strategies
strategyAPI.createStrategy(data)           // POST /strategies

// 交易相关
tradingAPI.getOrders()                      // GET /orders
tradingAPI.createOrder(data)                // POST /orders
```

## 常用命令

### 开发命令
```bash
# 启动开发环境
make dev

# 运行测试
make test

# 代码检查
make lint

# 代码格式化
make format
```

### Docker命令
```bash
# 构建所有服务
make build

# 启动所有服务
make up

# 停止所有服务
make down

# 查看日志
make logs
```

### 数据库命令
```bash
# 运行迁移
make migrate

# 重置数据库
make reset-db

# 备份数据库
make backup-db
```

## API文档

### 核心服务API

- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/users/me` - 获取当前用户信息
- `GET /api/config/*` - 配置管理

### 策略平台API

- `GET /api/strategies` - 获取策略列表
- `POST /api/strategies` - 创建策略
- `PUT /api/strategies/{id}` - 更新策略
- `DELETE /api/strategies/{id}` - 删除策略
- `POST /api/strategies/{id}/backtest` - 运行回测

### 交易引擎API

- `GET /api/exchanges` - 获取交易所列表
- `POST /api/orders` - 下单
- `GET /api/orders` - 获取订单列表
- `DELETE /api/orders/{id}` - 取消订单

## 部署指南

### 开发环境部署

1. 按照快速开始步骤完成基础安装
2. 配置环境变量和交易所API
3. 启动所有服务
4. 访问Web界面进行配置

### 生产环境部署

1. 修改 `docker-compose.yml` 中的环境变量
2. 使用HTTPS证书
3. 配置数据库备份
4. 设置监控告警

```bash
# 生产环境构建
docker-compose -f docker-compose.prod.yml build

# 生产环境启动
docker-compose -f docker-compose.prod.yml up -d
```

### Nginx反向代理

系统包含Nginx反向代理服务，提供以下功能：

- **负载均衡**: 分发请求到后端服务
- **SSL终端**: HTTPS证书管理和加密
- **静态文件服务**: 高效提供前端静态资源
- **API路由**: 统一的API入口点
- **WebSocket支持**: 实时数据传输

配置文件位置：`frontend/nginx.conf`

主要路由规则：
- `/` → 前端应用
- `/api/core/` → 核心服务
- `/api/trading/` → 交易引擎
- `/api/strategy/` → 策略平台
- `/api/notification/` → 通知服务
- `/ws/` → WebSocket连接

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 许可证

MIT License

## 技术支持

- GitHub Issues: [项目Issues](https://github.com/your-username/CashUp/issues)
- 邮箱: support@cashup.com
- QQ群: 123456789

## 更新日志

### v2.0.0
- 重构为模块化单体架构
- 新增专业回测引擎
- 支持策略热部署
- 新增交易所抽象层
- 完善Web界面
- 增加多种策略模板