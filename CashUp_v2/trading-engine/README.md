# CashUp交易引擎

CashUp交易引擎是一个专业的量化交易系统核心组件，提供完整的交易执行、策略管理和风险控制功能。

## 📋 功能特性

### 🔗 核心功能
- **多交易所支持**: 集成Gate.io、Binance等主流交易所API
- **策略管理**: 支持网格交易、趋势跟踪、套利等多种交易策略
- **实时交易**: 支持现货和永续合约的实时交易
- **风险控制**: 内置止损、止盈、仓位管理等功能
- **WebSocket集成**: 实时市场数据推送和订单状态更新

### 🛠️ 技术特性
- **异步架构**: 基于FastAPI和asyncio的高性能异步架构
- **模块化设计**: 支持插件化扩展和微服务部署
- **配置管理**: 灵活的配置管理，支持环境变量和数据库配置
- **API完整性**: RESTful API设计，支持所有常用交易操作
- **监控支持**: 内置健康检查和性能监控

## 🚀 快速开始

### 环境要求
- Python 3.12+
- Node.js 18+ (可选，用于前端)
- Docker & Docker Compose (可选)
- UV (Python包管理器)

### 安装依赖
```bash
# 创建虚拟环境
uv venv cashup
source cashup/bin/activate  # Linux/Mac
# cashup\Scripts\activate  # Windows

# 安装依赖
uv pip install -r requirements.txt
```

### 配置设置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

### 初始化数据库
```bash
# 运行数据库初始化脚本
python scripts/init_database_config.py

# 或者使用部署脚本
make migrate
```

### 启动交易引擎
```bash
# 开发模式
uvicorn main:app --reload --host 0.0.0.0 --port 8002

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8002
```

## 📖 API文档

### 策略管理API

#### 获取所有策略状态
```bash
GET /api/v1/strategies/status
```

#### 启动策略
```bash
POST /api/v1/strategies/{strategy_name}/start
```

#### 停止策略
```bash
POST /api/v1/strategies/{strategy_name}/stop
```

#### 获取策略信号
```bash
GET /api/v1/strategies/{strategy_name}/signals?limit=10
```

#### 获取策略持仓
```bash
GET /api/v1/strategies/{strategy_name}/positions
```

### 交易管理API

#### 获取订单列表
```bash
GET /api/v1/orders
```

#### 创建订单
```bash
POST /api/v1/orders
{
    "symbol": "BTC/USDT",
    "side": "buy",
    "type": "limit",
    "quantity": 0.1,
    "price": 30000.0
}
```

#### 获取持仓列表
```bash
GET /api/v1/positions
```

#### 获取账户余额
```bash
GET /api/v1/balances
```

#### 获取账户信息
```bash
GET /api/v1/account/info
```

### 高级交易API

#### 获取交易历史
```bash
GET /trading/orders/history?limit=100&status=filled
```

#### 获取账户摘要
```bash
GET /trading/account/summary
```

#### 获取可用交易对
```bash
GET /trading/symbols
```

#### 获取交易费率
```bash
GET /trading/fees
```

## 📁 项目结构

```
trading-engine/
├── main.py                    # 主应用入口
├── requirements.txt           # Python依赖
├── README.md                  # 项目说明
├── test_trading_engine.py     # 完整功能测试
├── start_test.py             # 启动测试脚本
├── test_api.py               # API测试脚本
├── api/                      # API路由
│   ├── routes/
│   │   ├── strategies.py     # 策略管理API
│   │   └── trading.py       # 交易管理API
├── exchanges/                # 交易所集成
│   ├── base.py              # 基础交易所类
│   ├── gateio.py            # Gate.io实现
│   ├── gateio_ws.py         # WebSocket实现
│   └── binance.py           # Binance实现
├── simulator/                # 模拟交易
│   ├── trading_simulator.py # 交易模拟器
│   └── market_simulator.py  # 市场模拟器
├── strategies/              # 交易策略
│   ├── base_strategy.py     # 策略基类
│   ├── strategy_manager.py  # 策略管理器
│   ├── grid_strategy.py     # 网格策略
│   ├── trend_strategy.py    # 趋势策略
│   └── arbitrage_strategy.py # 套利策略
├── services/                # 服务层
│   ├── config_service.py    # 配置管理服务
│   └── api_service.py       # API服务
└── scripts/                  # 工具脚本
    ├── init_database_config.py # 数据库初始化
    └── test_runner.py       # 测试运行器
```

## ⚙️ 配置说明

### 环境变量
```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/cashup
REDIS_URL=redis://localhost:6379

# API配置
ALLOWED_ORIGINS=http://localhost,http://localhost:3000
API_RATE_LIMIT=100

# 交易所配置
GATE_IO_API_KEY=your_api_key
GATE_IO_SECRET_KEY=your_secret_key
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key

# 日志配置
LOG_LEVEL=INFO
LOG_FILE_ENABLED=true
```

### 数据库配置
交易引擎支持以下配置：

- **交易所配置**: 存储各交易所的API密钥和设置
- **交易配置**: 杠杆、仓位限制、风险参数等
- **策略配置**: 策略参数、止损止盈设置等
- **系统配置**: 日志、监控、缓存等设置

## 🧪 测试

### 运行功能测试
```bash
# 运行所有测试
python test_trading_engine.py

# 运行启动测试
python start_test.py

# 运行API测试
python test_api.py
```

### 测试覆盖
- ✅ 依赖项导入测试
- ✅ 模块导入测试
- ✅ 策略管理器测试
- ✅ 基础策略测试
- ✅ 交易所管理器测试
- ✅ 配置服务测试
- ✅ 主应用测试
- ✅ API接口测试

## 🔧 开发指南

### 添加新交易所
1. 在`exchanges/`目录创建新的交易所实现
2. 继承`ExchangeBase`基类
3. 实现必要的API方法
4. 在交易所管理器中注册

### 添加新策略
1. 在`strategies/`目录创建新的策略类
2. 继承`BaseStrategy`基类
3. 实现`analyze_market`方法
4. 在策略管理器中注册

### 扩展API
1. 在`api/routes/`目录创建新的路由文件
2. 在`main.py`中注册路由
3. 编写API文档
4. 添加测试用例

## 🐛 故障排除

### 常见问题
1. **依赖安装失败**: 确保使用Python 3.12+和UV包管理器
2. **数据库连接失败**: 检查数据库配置和网络连接
3. **API调用失败**: 检查API密钥和网络权限
4. **策略运行异常**: 检查策略参数和日志输出

### 日志查看
```bash
# 查看应用日志
tail -f logs/trading_engine.log

# 查看错误日志
tail -f logs/error.log
```

### 性能优化
1. 使用Redis缓存配置和数据
2. 优化数据库查询
3. 合理设置并发限制
4. 监控内存使用情况

## 📈 监控指标

### 系统指标
- CPU使用率
- 内存使用量
- 网络带宽
- 磁盘IO

### 交易指标
- 订单执行延迟
- 成交率
- 滑点
- 手续费支出

### 策略指标
- 策略收益率
- 最大回撤
- 夏普比率
- 交易频率

## 🔒 安全说明

### 安全最佳实践
1. API密钥安全存储，避免硬编码
2. 定期轮换API密钥
3. 实施IP白名单限制
4. 启用API访问日志
5. 监控异常交易行为

### 数据保护
1. 敏感数据加密存储
2. 定期备份数据
3. 访问权限控制
4. 安全审计日志

## 📞 支持

如果您在使用过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目的GitHub Issues
3. 运行测试脚本诊断问题
4. 联系开发团队获取技术支持

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🤝 贡献

欢迎提交Pull Request和Issue来改进项目。请确保：

1. 遵循代码规范
2. 添加适当的测试
3. 更新相关文档
4. 经过充分测试