# 交易引擎 API 文档

## 服务概述

**服务名称**: Trading Engine  
**服务端口**: 8002  
**服务地址**: http://localhost:8002  
**API文档**: http://localhost:8002/docs  
**健康检查**: http://localhost:8002/health  

## 主要功能

- 交易所管理
- 订单管理
- 持仓管理
- 交易执行
- 风险控制
- 市场数据

## 接口列表

### 1. 交易所管理接口

#### 1.1 获取交易所列表
- **接口地址**: `GET /api/exchanges`
- **功能描述**: 获取所有支持的交易所列表
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "exchanges": [
    {
      "id": 1,
      "name": "Binance",
      "type": "binance",
      "status": "connected",
      "features": {
        "spot": true,
        "margin": true,
        "futures": true,
        "trading_bot": true
      },
      "rate_limits": {
        "requests": 1200,
        "window": "1m"
      },
      "created_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 1.2 获取交易所详情
- **接口地址**: `GET /api/exchanges/{exchange_id}`
- **功能描述**: 获取指定交易所详情
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": 1,
  "name": "Binance",
  "type": "binance",
  "status": "connected",
  "api_key": "binance_***",
  "api_secret": "******",
  "sandbox": true,
  "features": {
    "spot": true,
    "margin": true,
    "futures": true,
    "trading_bot": true
  },
  "rate_limits": {
    "requests": 1200,
    "window": "1m"
  },
  "balance": {
    "total": 10000.0,
    "available": 8000.0,
    "locked": 2000.0,
    "currency": "USDT"
  },
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (交易所不存在)

#### 1.3 添加交易所
- **接口地址**: `POST /api/exchanges`
- **功能描述**: 添加新的交易所配置
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "name": "Binance",
  "type": "binance",
  "api_key": "your-api-key",
  "api_secret": "your-api-secret",
  "sandbox": true,
  "description": "Binance交易所"
}
```
- **响应示例**:
```json
{
  "id": 1,
  "name": "Binance",
  "type": "binance",
  "status": "connected",
  "api_key": "binance_***",
  "sandbox": true,
  "features": {
    "spot": true,
    "margin": true,
    "futures": true,
    "trading_bot": true
  },
  "created_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 201 (创建成功), 400 (参数错误), 401 (认证失败), 409 (交易所已存在)

#### 1.4 更新交易所
- **接口地址**: `PUT /api/exchanges/{exchange_id}`
- **功能描述**: 更新交易所配置
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "api_key": "new-api-key",
  "api_secret": "new-api-secret",
  "sandbox": false,
  "status": "disabled"
}
```
- **响应示例**:
```json
{
  "id": 1,
  "name": "Binance",
  "type": "binance",
  "status": "disabled",
  "api_key": "binance_***",
  "sandbox": false,
  "features": {
    "spot": true,
    "margin": true,
    "futures": true,
    "trading_bot": true
  },
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (更新成功), 400 (参数错误), 401 (认证失败), 404 (交易所不存在)

#### 1.5 删除交易所
- **接口地址**: `DELETE /api/exchanges/{exchange_id}`
- **功能描述**: 删除交易所配置
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "message": "交易所删除成功"
}
```
- **状态码**: 200 (删除成功), 401 (认证失败), 404 (交易所不存在)

#### 1.6 测试交易所连接
- **接口地址**: `POST /api/exchanges/{exchange_id}/test`
- **功能描述**: 测试交易所连接状态
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "status": "success",
  "message": "连接测试成功",
  "details": {
    "connection_time": 120,
    "api_version": "v3",
    "server_time": "2023-01-01T00:00:00Z"
  }
}
```
- **状态码**: 200 (测试成功), 400 (连接失败), 401 (认证失败), 404 (交易所不存在)

### 2. 订单管理接口

#### 2.1 获取订单列表
- **接口地址**: `GET /api/orders`
- **功能描述**: 获取订单列表
- **请求参数**:
  - `skip`: 跳过记录数 (默认: 0)
  - `limit`: 限制记录数 (默认: 100)
  - `exchange_id`: 交易所ID筛选 (可选)
  - `symbol`: 交易对筛选 (可选)
  - `status`: 订单状态筛选 (可选)
  - `side`: 买卖方向筛选 (可选)
  - `start_date`: 开始日期 (可选)
  - `end_date`: 结束日期 (可选)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "orders": [
    {
      "id": "12345",
      "exchange_id": 1,
      "exchange_order_id": "BINANCE_12345",
      "symbol": "BTC/USDT",
      "side": "buy",
      "type": "limit",
      "quantity": 0.001,
      "price": 30000.0,
      "status": "filled",
      "filled_quantity": 0.001,
      "average_price": 30000.0,
      "fee": 0.9,
      "fee_currency": "USDT",
      "strategy_id": 1,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 2.2 获取订单详情
- **接口地址**: `GET /api/orders/{order_id}`
- **功能描述**: 获取指定订单详情
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": "12345",
  "exchange_id": 1,
  "exchange_order_id": "BINANCE_12345",
  "symbol": "BTC/USDT",
  "side": "buy",
  "type": "limit",
  "quantity": 0.001,
  "price": 30000.0,
  "status": "filled",
  "filled_quantity": 0.001,
  "average_price": 30000.0,
  "fee": 0.9,
  "fee_currency": "USDT",
  "strategy_id": 1,
  "trades": [
    {
      "id": "TRADE_123",
      "exchange_trade_id": "BINANCE_TRADE_123",
      "quantity": 0.001,
      "price": 30000.0,
      "fee": 0.9,
      "fee_currency": "USDT",
      "timestamp": "2023-01-01T00:00:00Z"
    }
  ],
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (订单不存在)

#### 2.3 创建订单
- **接口地址**: `POST /api/orders`
- **功能描述**: 创建新订单
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "exchange_id": 1,
  "symbol": "BTC/USDT",
  "side": "buy",
  "type": "limit",
  "quantity": 0.001,
  "price": 30000.0,
  "strategy_id": 1,
  "client_order_id": "CLIENT_123"
}
```
- **响应示例**:
```json
{
  "id": "12345",
  "exchange_id": 1,
  "exchange_order_id": "BINANCE_12345",
  "symbol": "BTC/USDT",
  "side": "buy",
  "type": "limit",
  "quantity": 0.001,
  "price": 30000.0,
  "status": "open",
  "filled_quantity": 0.0,
  "average_price": 0.0,
  "fee": 0.0,
  "strategy_id": 1,
  "client_order_id": "CLIENT_123",
  "created_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 201 (创建成功), 400 (参数错误), 401 (认证失败), 404 (交易所不存在)

#### 2.4 取消订单
- **接口地址**: `DELETE /api/orders/{order_id}`
- **功能描述**: 取消指定订单
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": "12345",
  "exchange_id": 1,
  "exchange_order_id": "BINANCE_12345",
  "symbol": "BTC/USDT",
  "side": "buy",
  "type": "limit",
  "quantity": 0.001,
  "price": 30000.0,
  "status": "cancelled",
  "filled_quantity": 0.0,
  "average_price": 0.0,
  "fee": 0.0,
  "strategy_id": 1,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (取消成功), 400 (订单不可取消), 401 (认证失败), 404 (订单不存在)

#### 2.5 批量取消订单
- **接口地址**: `POST /api/orders/cancel-batch`
- **功能描述**: 批量取消订单
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "exchange_id": 1,
  "symbol": "BTC/USDT",
  "order_ids": ["12345", "12346"]
}
```
- **响应示例**:
```json
{
  "cancelled_orders": ["12345"],
  "failed_orders": ["12346"],
  "total_cancelled": 1,
  "total_failed": 1
}
```
- **状态码**: 200 (处理完成), 400 (参数错误), 401 (认证失败)

### 3. 持仓管理接口

#### 3.1 获取持仓列表
- **接口地址**: `GET /api/positions`
- **功能描述**: 获取持仓列表
- **请求参数**:
  - `skip`: 跳过记录数 (默认: 0)
  - `limit`: 限制记录数 (默认: 100)
  - `exchange_id`: 交易所ID筛选 (可选)
  - `symbol`: 交易对筛选 (可选)
  - `side`: 持仓方向筛选 (可选)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "positions": [
    {
      "id": 1,
      "exchange_id": 1,
      "symbol": "BTC/USDT",
      "side": "long",
      "quantity": 0.001,
      "entry_price": 30000.0,
      "current_price": 31000.0,
      "unrealized_pnl": 1.0,
      "realized_pnl": 0.0,
      "margin": 30.0,
      "leverage": 1.0,
      "status": "open",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 3.2 获取持仓详情
- **接口地址**: `GET /api/positions/{position_id}`
- **功能描述**: 获取指定持仓详情
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": 1,
  "exchange_id": 1,
  "symbol": "BTC/USDT",
  "side": "long",
  "quantity": 0.001,
  "entry_price": 30000.0,
  "current_price": 31000.0,
  "unrealized_pnl": 1.0,
  "realized_pnl": 0.0,
  "margin": 30.0,
  "leverage": 1.0,
  "status": "open",
  "orders": [
    {
      "id": "12345",
      "side": "buy",
      "quantity": 0.001,
      "price": 30000.0,
      "status": "filled"
    }
  ],
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (持仓不存在)

#### 3.3 平仓
- **接口地址**: `POST /api/positions/{position_id}/close`
- **功能描述**: 平仓指定持仓
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "quantity": 0.001,
  "type": "market",
  "price": null
}
```
- **响应示例**:
```json
{
  "id": 1,
  "exchange_id": 1,
  "symbol": "BTC/USDT",
  "side": "long",
  "quantity": 0.0,
  "entry_price": 30000.0,
  "exit_price": 31000.0,
  "unrealized_pnl": 0.0,
  "realized_pnl": 1.0,
  "status": "closed",
  "closed_at": "2023-01-01T00:00:00Z",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (平仓成功), 400 (参数错误), 401 (认证失败), 404 (持仓不存在)

### 4. 交易接口

#### 4.1 获取交易列表
- **接口地址**: `GET /api/trades`
- **功能描述**: 获取交易历史
- **请求参数**:
  - `skip`: 跳过记录数 (默认: 0)
  - `limit`: 限制记录数 (默认: 100)
  - `exchange_id`: 交易所ID筛选 (可选)
  - `symbol`: 交易对筛选 (可选)
  - `start_date`: 开始日期 (可选)
  - `end_date`: 结束日期 (可选)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "trades": [
    {
      "id": "TRADE_123",
      "exchange_id": 1,
      "exchange_trade_id": "BINANCE_TRADE_123",
      "order_id": "12345",
      "symbol": "BTC/USDT",
      "side": "buy",
      "quantity": 0.001,
      "price": 30000.0,
      "fee": 0.9,
      "fee_currency": "USDT",
      "strategy_id": 1,
      "timestamp": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```
- **状态码**: 200 (成功), 401 (认证失败)

### 5. 市场数据接口

#### 5.1 获取市场数据
- **接口地址**: `GET /api/market/{symbol}/ticker`
- **功能描述**: 获取指定交易对的行情数据
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "symbol": "BTC/USDT",
  "price": 30000.0,
  "bid": 29999.0,
  "ask": 30001.0,
  "high": 31000.0,
  "low": 29000.0,
  "volume": 1000.0,
  "quote_volume": 30000000.0,
  "timestamp": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (交易对不存在)

#### 5.2 获取K线数据
- **接口地址**: `GET /api/market/{symbol}/klines`
- **功能描述**: 获取K线数据
- **请求参数**:
  - `interval`: K线间隔 (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
  - `limit`: 限制数量 (默认: 100, 最大: 1000)
  - `start_time`: 开始时间 (可选)
  - `end_time`: 结束时间 (可选)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "symbol": "BTC/USDT",
  "interval": "1h",
  "klines": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "open": 30000.0,
      "high": 31000.0,
      "low": 29000.0,
      "close": 30500.0,
      "volume": 100.0
    }
  ]
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (交易对不存在)

#### 5.3 获取深度数据
- **接口地址**: `GET /api/market/{symbol}/depth`
- **功能描述**: 获取订单簿深度数据
- **请求参数**:
  - `limit`: 深度数量 (默认: 100)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "symbol": "BTC/USDT",
  "bids": [
    [29999.0, 0.1],
    [29998.0, 0.2]
  ],
  "asks": [
    [30001.0, 0.1],
    [30002.0, 0.2]
  ],
  "timestamp": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (交易对不存在)

### 6. 风险控制接口

#### 6.1 获取风险指标
- **接口地址**: `GET /api/risk/metrics`
- **功能描述**: 获取风险控制指标
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "total_value": 10000.0,
  "total_pnl": 100.0,
  "total_pnl_percent": 1.0,
  "daily_pnl": 10.0,
  "daily_pnl_percent": 0.1,
  "max_drawdown": 5.0,
  "sharpe_ratio": 1.5,
  "win_rate": 0.6,
  "total_trades": 100,
  "winning_trades": 60,
  "losing_trades": 40,
  "risk_level": "low",
  "margin_usage": 0.1,
  "leverage_usage": 0.5
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 6.2 设置风险限制
- **接口地址**: `PUT /api/risk/limits`
- **功能描述**: 设置风险限制
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "max_position_size": 1000.0,
  "max_daily_loss": 100.0,
  "max_drawdown": 10.0,
  "max_leverage": 3.0,
  "stop_loss_percent": 5.0,
  "take_profit_percent": 10.0
}
```
- **响应示例**:
```json
{
  "max_position_size": 1000.0,
  "max_daily_loss": 100.0,
  "max_drawdown": 10.0,
  "max_leverage": 3.0,
  "stop_loss_percent": 5.0,
  "take_profit_percent": 10.0,
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (更新成功), 400 (参数错误), 401 (认证失败)

### 7. 系统监控接口

#### 7.1 健康检查
- **接口地址**: `GET /health`
- **功能描述**: 系统健康检查
- **响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z",
  "version": "2.0.0",
  "exchanges": {
    "connected": 1,
    "total": 1,
    "status": "all_connected"
  },
  "active_orders": 0,
  "active_positions": 0,
  "memory_usage": "50MB",
  "cpu_usage": "10%"
}
```
- **状态码**: 200 (健康), 503 (服务异常)

## WebSocket 接口

### 实时数据推送

**连接地址**: `ws://localhost:8002/ws`

**订阅方式**:
```json
{
  "action": "subscribe",
  "channel": "trades",
  "symbol": "BTC/USDT"
}
```

**推送数据格式**:
```json
{
  "channel": "trades",
  "symbol": "BTC/USDT",
  "data": {
    "price": 30000.0,
    "quantity": 0.001,
    "timestamp": "2023-01-01T00:00:00Z"
  }
}
```

支持的频道：
- `trades`: 实时成交
- `ticker`: 行情更新
- `depth`: 深度更新
- `orders`: 订单状态更新
- `positions`: 持仓更新

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
- `EXCHANGE_ERROR`: 交易所错误
- `INSUFFICIENT_BALANCE`: 余额不足
- `ORDER_NOT_FOUND`: 订单不存在
- `POSITION_NOT_FOUND`: 持仓不存在
- `RISK_LIMIT_EXCEEDED`: 风险限制超出
- `INTERNAL_ERROR`: 服务器内部错误

## 认证方式

使用Bearer Token认证：

```http
Authorization: Bearer <access_token>
```

Token通过核心服务登录接口获取。