## 检查目标
- 验证功能与架构完整性：后端核心、通知服务、队列事件、定时任务、前端联动。
- 验证基础设施：PostgreSQL、Redis、RabbitMQ 的可用与健康。
- 执行端到端测试：行情→策略→下单→事件→通知→绩效视图→前端展示。

## 架构完整性评估
- 服务/端点存在性：
  - 核心服务 `apps/core/main.py`，健康 `GET /health`，API 前缀：`/api` 与 `/api/v1`。
  - 通知服务 `notification-service/main.py`，健康 `GET /health`，通知接口：`POST /api/v1/notify/send`。
  - Celery Worker/Beat：`apps/core/celery_app.py` 配置，任务：`tasks.rss.*`、`tasks.trading.sync`、`tasks.rss.compute_correlation`。
  - 队列事件：发布 `apps/core/events/rabbitmq.py`；消费 `notification-service/consumer.py` + 模板 `notification-service/templates.py`。
  - 数据脚本：`scripts/init_database_v2.sql`，含关键表与视图（`strategy_*`、`orders/positions/account_balances`、`kline_data`、`market_news`、`strategy_performance/account_overview`）。
- 编排一致性：`docker-compose.yml` 指向 `apps/core`，并声明 postgres/redis/rabbitmq/通知/前端/worker/beat。

## 环境准备
- Mac 终端激活环境：`source v-quant/bin/activate`
- 设置环境变量：
  - `DATABASE_URL`、`REDIS_URL`、`RABBITMQ_URL`、`NOTIFICATION_URL=http://localhost:8004`
  - 交易所密钥（如 Gate.io/Binance），或启用测试网/只读以避免真实交易
- 初始化数据库（Compose 已挂载 `scripts/init_database_v2.sql`），首次启动自动执行。

## 健康检查清单
- 容器层：
  - Postgres：`pg_isready -U cashup` 返回 `accepting connections`
  - Redis：`redis-cli -h redis ping` 返回 `PONG`
  - RabbitMQ：`rabbitmq-diagnostics -q ping` 返回 `Ping succeeded`
- 应用层：
  - 核心服务：`curl http://localhost:8001/health` 返回 `{"status":"ok"}`；根路径 `GET /` 包含服务说明
  - 通知服务：`curl http://localhost:8004/health` 返回 `ok`
  - Worker/Beat：日志包含任务注册：`tasks.rss.fetch_feeds` 等；Beat 输出心跳与计划

## 功能验证流程
1) 行情与存储
- `GET /api/v1/market/klines?exchange=gateio&symbol=ETH_USDT&timeframe=1h&limit=5` 返回标准化 K 线
- 校验 `kline_data` 有数据（若落库路径已启用）；否则作为只读展示

2) 策略创建与启停
- `POST /api/v1/strategies/instances`（含 `config.factors` 与 `risk_management`）
- `POST /api/v1/strategies/instances/{id}/start` 启动；查看 Worker 日志中策略信号入库（`strategy_signals`）

3) 下单与事件
- `POST /api/v1/trading/orders`（建议用极小 `quantity`/测试网）；检查 `orders` 写入
- 队列发布事件 `order.created/order.filled`；通知服务消费并发送（可用 Telegram/Webhook/Email 三选一进行验证）

4) 余额/持仓同步
- 等待 `tasks.trading.sync` 周期（默认 60s）；调用 `GET /api/v1/trading/positions` 与 `GET /api/v1/account/overview` 查看更新

5) 回测与绩效
- `POST /api/v1/backtest`（传入 `exchange/symbol/timeframe/start_date/end_date/factors`）返回盈亏统计
- `GET /api/v1/strategies/{id}/performance`、`/statistics`、`/equity`、`/winrate_series` 验证统计数据

6) 前端联动
- 启动前端容器或开发服务器，打开策略管理与账户总览：
  - 策略管理页显示实例列表、启停、权益曲线/胜率趋势
  - 账户总览页支持交易所切换、自动刷新、汇总视图、导出 CSV/SVG

## 测试命令与示例
- 终端激活：`source v-quant/bin/activate`
- 启动：`docker compose up -d`
- 健康：
  - `curl http://localhost:8001/health`
  - `curl http://localhost:8004/health`
- 通知直发：
  - `curl -X POST http://localhost:8004/api/v1/notify/send -H 'Content-Type: application/json' -d '{"title":"测试","content":"Hello","level":"info","channels":["webhook"]}'`

## 验收标准
- 所有健康检查返回成功；Worker/Beat 正常心跳与任务执行无错误。
- API 端到端链路无 5xx/4xx（除非真实交易权限受限）。
- 队列事件成功发布与消费，通知服务按模板发送。
- 前端页面正确展示策略与账户数据，图表与导出功能可用。

## 风险与修复建议
- 真实交易风险：建议在 `.env` 配置测试网或开关只读模式。
- 外部依赖不可用：RabbitMQ/Redis/数据库端口冲突时需调整 Compose 端口。
- 数据稀疏：若 `kline_data` 未落库，图表以回测/策略信号驱动展示，或增加采集任务。

## 交付与后续
- 我将按以上清单逐项执行健康检查与端到端测试，必要时补充最小日志与脚本用于验证。
- 完成后提供测试报告（成功与失败项、修复建议与对应提交列表）。