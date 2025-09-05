# 策略平台 API 文档

## 服务概述

**服务名称**: Strategy Platform  
**服务端口**: 8003  
**服务地址**: http://localhost:8003  
**API文档**: http://localhost:8003/docs  
**健康检查**: http://localhost:8003/health  

## 主要功能

- 策略管理
- 回测引擎
- 数据管理
- 性能分析
- 策略监控
- 模板管理

## 接口列表

### 1. 策略管理接口

#### 1.1 获取策略列表
- **接口地址**: `GET /api/strategies`
- **功能描述**: 获取策略列表
- **请求参数**:
  - `skip`: 跳过记录数 (默认: 0)
  - `limit`: 限制记录数 (默认: 100)
  - `status`: 策略状态筛选 (可选: active, inactive, archived)
  - `type`: 策略类型筛选 (可选)
  - `search`: 搜索关键词 (可选)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "strategies": [
    {
      "id": 1,
      "name": "MA Cross Strategy",
      "description": "双均线交叉策略",
      "type": "technical",
      "status": "active",
      "version": "1.0.0",
      "author": "admin",
      "symbols": ["BTC/USDT", "ETH/USDT"],
      "timeframe": "1h",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z",
      "performance": {
        "total_return": 15.5,
        "sharpe_ratio": 1.8,
        "max_drawdown": 8.2,
        "win_rate": 65.0
      }
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 1.2 获取策略详情
- **接口地址**: `GET /api/strategies/{strategy_id}`
- **功能描述**: 获取指定策略详情
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": 1,
  "name": "MA Cross Strategy",
  "description": "双均线交叉策略",
  "type": "technical",
  "status": "active",
  "version": "1.0.0",
  "author": "admin",
  "symbols": ["BTC/USDT", "ETH/USDT"],
  "timeframe": "1h",
  "parameters": {
    "fast_period": 10,
    "slow_period": 30,
    "quantity": 0.001
  },
  "code": "class MACrossStrategy(StrategyBase):\n    def __init__(self, config):\n        super().__init__(config)\n        self.fast_period = config.get('fast_period', 10)\n        self.slow_period = config.get('slow_period', 30)\n\n    def on_data(self, data):\n        # 策略逻辑实现\n        pass",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z",
  "performance": {
    "total_return": 15.5,
    "sharpe_ratio": 1.8,
    "max_drawdown": 8.2,
    "win_rate": 65.0,
    "total_trades": 120,
    "profit_trades": 78,
    "loss_trades": 42
  }
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (策略不存在)

#### 1.3 创建策略
- **接口地址**: `POST /api/strategies`
- **功能描述**: 创建新策略
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "name": "My Strategy",
  "description": "我的策略",
  "type": "technical",
  "symbols": ["BTC/USDT"],
  "timeframe": "1h",
  "parameters": {
    "fast_period": 10,
    "slow_period": 30,
    "quantity": 0.001
  },
  "code": "class MyStrategy(StrategyBase):\n    def __init__(self, config):\n        super().__init__(config)\n        self.fast_period = config.get('fast_period', 10)\n        self.slow_period = config.get('slow_period', 30)\n\n    def on_data(self, data):\n        # 策略逻辑实现\n        pass"
}
```
- **响应示例**:
```json
{
  "id": 2,
  "name": "My Strategy",
  "description": "我的策略",
  "type": "technical",
  "status": "inactive",
  "version": "1.0.0",
  "author": "admin",
  "symbols": ["BTC/USDT"],
  "timeframe": "1h",
  "parameters": {
    "fast_period": 10,
    "slow_period": 30,
    "quantity": 0.001
  },
  "created_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 201 (创建成功), 400 (参数错误), 401 (认证失败)

#### 1.4 更新策略
- **接口地址**: `PUT /api/strategies/{strategy_id}`
- **功能描述**: 更新策略信息
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "name": "Updated Strategy",
  "description": "更新后的策略描述",
  "parameters": {
    "fast_period": 15,
    "slow_period": 35,
    "quantity": 0.002
  },
  "status": "active"
}
```
- **响应示例**:
```json
{
  "id": 1,
  "name": "Updated Strategy",
  "description": "更新后的策略描述",
  "type": "technical",
  "status": "active",
  "version": "1.0.0",
  "author": "admin",
  "symbols": ["BTC/USDT", "ETH/USDT"],
  "timeframe": "1h",
  "parameters": {
    "fast_period": 15,
    "slow_period": 35,
    "quantity": 0.002
  },
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (更新成功), 400 (参数错误), 401 (认证失败), 404 (策略不存在)

#### 1.5 删除策略
- **接口地址**: `DELETE /api/strategies/{strategy_id}`
- **功能描述**: 删除策略
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "message": "策略删除成功"
}
```
- **状态码**: 200 (删除成功), 401 (认证失败), 404 (策略不存在)

#### 1.6 启动策略
- **接口地址**: `POST /api/strategies/{strategy_id}/start`
- **功能描述**: 启动策略
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "exchange_id": 1,
  "initial_capital": 10000.0
}
```
- **响应示例**:
```json
{
  "id": 1,
  "name": "MA Cross Strategy",
  "status": "running",
  "started_at": "2023-01-01T00:00:00Z",
  "exchange_id": 1,
  "initial_capital": 10000.0
}
```
- **状态码**: 200 (启动成功), 400 (参数错误), 401 (认证失败), 404 (策略不存在)

#### 1.7 停止策略
- **接口地址**: `POST /api/strategies/{strategy_id}/stop`
- **功能描述**: 停止策略
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": 1,
  "name": "MA Cross Strategy",
  "status": "stopped",
  "stopped_at": "2023-01-01T00:00:00Z",
  "run_time": 3600
}
```
- **状态码**: 200 (停止成功), 401 (认证失败), 404 (策略不存在)

### 2. 回测接口

#### 2.1 运行回测
- **接口地址**: `POST /api/strategies/{strategy_id}/backtest`
- **功能描述**: 运行策略回测
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "start_date": "2023-01-01T00:00:00Z",
  "end_date": "2023-12-31T23:59:59Z",
  "initial_capital": 10000.0,
  "symbols": ["BTC/USDT"],
  "timeframe": "1h",
  "parameters": {
    "fast_period": 10,
    "slow_period": 30,
    "quantity": 0.001
  }
}
```
- **响应示例**:
```json
{
  "id": "backtest_123",
  "strategy_id": 1,
  "status": "running",
  "start_date": "2023-01-01T00:00:00Z",
  "end_date": "2023-12-31T23:59:59Z",
  "initial_capital": 10000.0,
  "progress": 0,
  "created_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 202 (回测开始), 400 (参数错误), 401 (认证失败), 404 (策略不存在)

#### 2.2 获取回测结果
- **接口地址**: `GET /api/backtests/{backtest_id}`
- **功能描述**: 获取回测结果
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": "backtest_123",
  "strategy_id": 1,
  "status": "completed",
  "start_date": "2023-01-01T00:00:00Z",
  "end_date": "2023-12-31T23:59:59Z",
  "initial_capital": 10000.0,
  "final_capital": 11550.0,
  "total_return": 15.5,
  "annual_return": 15.5,
  "sharpe_ratio": 1.8,
  "max_drawdown": 8.2,
  "win_rate": 65.0,
  "total_trades": 120,
  "profit_trades": 78,
  "loss_trades": 42,
  "profit_factor": 1.8,
  "calmar_ratio": 1.9,
  "sortino_ratio": 2.1,
  "trades": [
    {
      "id": "trade_1",
      "symbol": "BTC/USDT",
      "side": "buy",
      "entry_time": "2023-01-01T01:00:00Z",
      "exit_time": "2023-01-01T02:00:00Z",
      "entry_price": 30000.0,
      "exit_price": 30100.0,
      "quantity": 0.001,
      "pnl": 1.0,
      "pnl_percent": 3.33,
      "fee": 0.9
    }
  ],
  "equity_curve": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "equity": 10000.0
    },
    {
      "timestamp": "2023-01-01T01:00:00Z",
      "equity": 10001.0
    }
  ],
  "drawdown_curve": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "drawdown": 0.0
    },
    {
      "timestamp": "2023-01-01T01:00:00Z",
      "drawdown": 0.0
    }
  ],
  "created_at": "2023-01-01T00:00:00Z",
  "completed_at": "2023-01-01T00:10:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (回测不存在)

#### 2.3 获取回测列表
- **接口地址**: `GET /api/backtests`
- **功能描述**: 获取回测历史列表
- **请求参数**:
  - `skip`: 跳过记录数 (默认: 0)
  - `limit`: 限制记录数 (默认: 100)
  - `strategy_id`: 策略ID筛选 (可选)
  - `status`: 状态筛选 (可选: running, completed, failed)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "backtests": [
    {
      "id": "backtest_123",
      "strategy_id": 1,
      "strategy_name": "MA Cross Strategy",
      "status": "completed",
      "start_date": "2023-01-01T00:00:00Z",
      "end_date": "2023-12-31T23:59:59Z",
      "initial_capital": 10000.0,
      "final_capital": 11550.0,
      "total_return": 15.5,
      "duration": 600,
      "created_at": "2023-01-01T00:00:00Z",
      "completed_at": "2023-01-01T00:10:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 2.4 生成回测报告
- **接口地址**: `POST /api/backtests/{backtest_id}/report`
- **功能描述**: 生成回测报告
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "format": "pdf",
  "include_charts": true,
  "include_trades": true
}
```
- **响应示例**:
```json
{
  "report_id": "report_123",
  "format": "pdf",
  "file_url": "/reports/backtest_123.pdf",
  "generated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (生成成功), 400 (参数错误), 401 (认证失败), 404 (回测不存在)

### 3. 数据管理接口

#### 3.1 获取数据源列表
- **接口地址**: `GET /api/data/sources`
- **功能描述**: 获取数据源列表
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "sources": [
    {
      "id": 1,
      "name": "Binance",
      "type": "exchange",
      "status": "active",
      "symbols": ["BTC/USDT", "ETH/USDT"],
      "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
      "last_update": "2023-01-01T00:00:00Z",
      "data_count": 1000000
    }
  ]
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 3.2 获取历史数据
- **接口地址**: `GET /api/data/{symbol}/history`
- **功能描述**: 获取历史数据
- **请求参数**:
  - `timeframe`: 时间框架 (1m, 5m, 15m, 30m, 1h, 4h, 1d)
  - `start_date`: 开始时间 (可选)
  - `end_date`: 结束时间 (可选)
  - `limit`: 限制数量 (默认: 1000)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "data": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "open": 30000.0,
      "high": 30100.0,
      "low": 29900.0,
      "close": 30050.0,
      "volume": 100.0
    }
  ],
  "total": 1000,
  "start_date": "2023-01-01T00:00:00Z",
  "end_date": "2023-01-01T23:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (数据不存在)

#### 3.3 更新数据
- **接口地址**: `POST /api/data/{symbol}/update`
- **功能描述**: 更新指定交易对的数据
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "timeframes": ["1h", "4h", "1d"],
  "start_date": "2023-01-01T00:00:00Z",
  "end_date": "2023-01-01T23:59:59Z"
}
```
- **响应示例**:
```json
{
  "symbol": "BTC/USDT",
  "updated_records": 24,
  "timeframes": ["1h", "4h", "1d"],
  "start_date": "2023-01-01T00:00:00Z",
  "end_date": "2023-01-01T23:59:59Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (更新成功), 400 (参数错误), 401 (认证失败)

### 4. 策略模板接口

#### 4.1 获取策略模板列表
- **接口地址**: `GET /api/templates`
- **功能描述**: 获取策略模板列表
- **请求参数**:
  - `category`: 分类筛选 (可选: technical, fundamental, machine_learning)
  - `difficulty`: 难度筛选 (可选: beginner, intermediate, advanced)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "templates": [
    {
      "id": 1,
      "name": "Moving Average Cross",
      "description": "双均线交叉策略",
      "category": "technical",
      "difficulty": "beginner",
      "author": "system",
      "version": "1.0.0",
      "downloads": 1000,
      "rating": 4.5,
      "tags": ["trend", "moving_average"],
      "created_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 4.2 获取策略模板详情
- **接口地址**: `GET /api/templates/{template_id}`
- **功能描述**: 获取策略模板详情
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": 1,
  "name": "Moving Average Cross",
  "description": "双均线交叉策略",
  "category": "technical",
  "difficulty": "beginner",
  "author": "system",
  "version": "1.0.0",
  "parameters": {
    "fast_period": {
      "type": "integer",
      "default": 10,
      "min": 1,
      "max": 50,
      "description": "快线周期"
    },
    "slow_period": {
      "type": "integer",
      "default": 30,
      "min": 1,
      "max": 200,
      "description": "慢线周期"
    }
  },
  "code": "class MACrossStrategy(StrategyBase):\n    def __init__(self, config):\n        super().__init__(config)\n        self.fast_period = config.get('fast_period', 10)\n        self.slow_period = config.get('slow_period', 30)\n\n    def on_data(self, data):\n        # 策略逻辑实现\n        pass",
  "tags": ["trend", "moving_average"],
  "examples": [
    {
      "title": "BTC/USDT 示例",
      "description": "在BTC/USDT上的回测结果",
      "return": 15.5,
      "sharpe_ratio": 1.8
    }
  ],
  "created_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (模板不存在)

#### 4.3 从模板创建策略
- **接口地址**: `POST /api/templates/{template_id}/create-strategy`
- **功能描述**: 从模板创建策略
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "name": "My MA Strategy",
  "description": "基于模板的双均线策略",
  "symbols": ["BTC/USDT"],
  "timeframe": "1h",
  "parameters": {
    "fast_period": 15,
    "slow_period": 35
  }
}
```
- **响应示例**:
```json
{
  "id": 3,
  "name": "My MA Strategy",
  "description": "基于模板的双均线策略",
  "type": "technical",
  "status": "inactive",
  "version": "1.0.0",
  "author": "admin",
  "symbols": ["BTC/USDT"],
  "timeframe": "1h",
  "parameters": {
    "fast_period": 15,
    "slow_period": 35,
    "quantity": 0.001
  },
  "template_id": 1,
  "created_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 201 (创建成功), 400 (参数错误), 401 (认证失败), 404 (模板不存在)

### 5. 策略监控接口

#### 5.1 获取策略运行状态
- **接口地址**: `GET /api/strategies/{strategy_id}/status`
- **功能描述**: 获取策略运行状态
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "strategy_id": 1,
  "name": "MA Cross Strategy",
  "status": "running",
  "started_at": "2023-01-01T00:00:00Z",
  "uptime": 3600,
  "current_capital": 10050.0,
  "total_pnl": 50.0,
  "total_pnl_percent": 0.5,
  "active_trades": 1,
  "total_trades": 10,
  "performance": {
    "sharpe_ratio": 1.2,
    "max_drawdown": 2.5,
    "win_rate": 60.0
  },
  "last_signal": {
    "timestamp": "2023-01-01T01:00:00Z",
    "symbol": "BTC/USDT",
    "action": "buy",
    "price": 30000.0,
    "quantity": 0.001
  },
  "system_status": {
    "cpu_usage": "10%",
    "memory_usage": "50MB",
    "error_count": 0,
    "warning_count": 1
  }
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (策略不存在)

#### 5.2 获取策略信号历史
- **接口地址**: `GET /api/strategies/{strategy_id}/signals`
- **功能描述**: 获取策略信号历史
- **请求参数**:
  - `skip`: 跳过记录数 (默认: 0)
  - `limit`: 限制记录数 (默认: 100)
  - `start_date`: 开始时间 (可选)
  - `end_date`: 结束时间 (可选)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "signals": [
    {
      "id": "signal_1",
      "timestamp": "2023-01-01T01:00:00Z",
      "symbol": "BTC/USDT",
      "action": "buy",
      "price": 30000.0,
      "quantity": 0.001,
      "reason": "Golden cross",
      "confidence": 0.8,
      "executed": true,
      "order_id": "order_123"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (策略不存在)

### 6. 系统监控接口

#### 6.1 健康检查
- **接口地址**: `GET /health`
- **功能描述**: 系统健康检查
- **响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z",
  "version": "2.0.0",
  "components": {
    "database": "connected",
    "redis": "connected",
    "data_service": "running",
    "backtest_engine": "ready",
    "strategy_runtime": "active"
  },
  "active_strategies": 2,
  "running_backtests": 1,
  "memory_usage": "100MB",
  "cpu_usage": "15%"
}
```
- **状态码**: 200 (健康), 503 (服务异常)

## 错误处理

所有接口返回的错误格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  }
}
```

常见错误码：
- `UNAUTHORIZED`: 认证失败
- `FORBIDDEN`: 权限不足
- `NOT_FOUND`: 资源不存在
- `VALIDATION_ERROR`: 参数验证失败
- `STRATEGY_NOT_FOUND`: 策略不存在
- `BACKTEST_NOT_FOUND`: 回测不存在
- `TEMPLATE_NOT_FOUND`: 模板不存在
- `DATA_NOT_AVAILABLE`: 数据不可用
- `STRATEGY_ALREADY_RUNNING`: 策略已在运行
- `BACKTEST_ALREADY_RUNNING`: 回测已在运行
- `INVALID_STRATEGY_CODE`: 策略代码无效
- `INSUFFICIENT_DATA`: 数据不足
- `BACKTEST_TIMEOUT`: 回测超时
- `INTERNAL_ERROR`: 服务器内部错误

## 认证方式

使用Bearer Token认证：

```http
Authorization: Bearer <access_token>
```

Token通过核心服务登录接口获取。