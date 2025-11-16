## 结论
- 我提供的是“完整的首期实现与重构计划”，RSS 新闻与市场情绪只是其中一个模块。下述计划覆盖：Nginx、RabbitMQ、Redis、Celery（worker/beat）、WebSocket、前端、交易所适配、策略引擎、行情采集、通知、回测、数据库（PostgreSQL/TimescaleDB）、部署与验收。

## 架构与保留项
- 网关：Nginx（HTTPS、反向代理 `/api` 与 `/ws`、静态托管）
- 后端：FastAPI（REST + WebSocket）
- 消息队列：RabbitMQ（事件总线、Celery broker）
- 缓存与结果：Redis（会话/缓存、Celery result backend、轻量限流）
- 调度：Celery（worker/beat），所有定时与异步任务走队列
- 数据库：PostgreSQL 15 + TimescaleDB（统一存 K 线、逐笔、指标、新闻与回测结果）
- 前端：React + Vite + Ant Design + TradingView/Lightweight Charts（含策略管理、实时监控、回测、新闻情绪）

## 关键模块
- 交易所适配：Gate.io/Binance（余额/持仓/下单/撤单/订单查询；REST 优先、WS 后置）
- 策略引擎：因子化（RSI/MA/MACD 起步），组合策略、生命周期管理（启动/停止/错误处理）
- 行情采集：K 线（REST 轮询 + Timescale 超表批量写入），逐步接入订单簿/逐笔 WS
- RSS 新闻与情绪：
  - Celery 定时抓取（feedparser/aiohttp），去重入库 `market_news`
  - 情绪分析（英文 VADER，中文 SnowNLP）打分与标签；发布 `NEWS_PUBLISHED` 事件
  - 通知联动（Telegram/Webhook，阈值触发）；前端新闻列表/详情与筛选
- 通知系统：事件驱动发送（订单成交、风险预警、每日简报、新闻提醒），模板化内容
- 回测引擎（v1）：基于历史 K 线执行策略，统计收益、夏普、回撤、胜率；前端结果视图
- WebSocket：频道 `/ws/strategies` 与 `/ws/news` 广播策略状态与新闻摘要情绪

## 数据库设计
- 使用 TimescaleDB 超表：`kline_data(time)` 与可选 `market_news(published_at)`；分区与索引优化
- 明细表：`orders/positions/account_balances/market_trades` 按需索引（`user+status`、`exchange+symbol`）
- 回测与绩效：`backtest_jobs/backtest_trades/backtest_daily_pnl` 按日期与任务建索引

## API 与前端
- API 套件：
  - 策略：创建/实例化/启停/列表
  - 交易：下单/撤单/持仓/余额
  - 行情：K 线/订单簿/逐笔（分页与窗口查询）
  - 新闻：列表与详情（来源/类别/情绪/币种筛选）
- 前端页面：策略管理、实时监控（PNL/K 线）、回测、新闻情绪；WebSocket 实时刷新

## 事件与调度
- 事件主题：策略/交易/行情/新闻/通知分队列，重试与死信队列
- 调度项：
  - 行情抓取：按交易对与周期调度
  - 每日简报与资金费率提醒（beat 定时）
  - RSS 抓取与情绪分析流水线
  - 回测任务提交与结果汇总

## 部署与资源控制
- docker-compose 服务：`timescaledb|postgres`、`redis`、`rabbitmq`、`core-app`、`celery-worker`、`celery-beat`、`nginx`、`frontend`
- 资源限额：为队列/缓存/DB/worker 设置 `cpus/memory`；抓取频率受 `fetch_interval` 控制
- 安全：首期不启用认证，限制来源与速率、仅内网/网关控制；后期再开用户体系

## 验收标准
- 端到端闭环：策略启动→行情入库→信号→下单→成交→通知→前端展示→回测结果
- RSS 新闻：抓取 5+ 主流源、入库与情绪标签有效；`NEWS_PUBLISHED` 推送到前端与通知渠道
- 性能：API（95%）< 500ms、WS 延时 < 200ms、1 万条 K 线回测 < 30s

## 首期时间线（4 周）
- 第 1 周：容器与骨架（Nginx/RabbitMQ/Redis/TimescaleDB/FastAPI/Celery），交易所连通（余额/持仓），WS 基线
- 第 2 周：策略生命周期与因子（RSI/MA/MACD），K 线入库与查询 API，前端框架 + 监控面板
- 第 3 周：通知（Telegram/Webhook）与模板；回测 v1 与前端视图；RSS 抓取入库与新闻列表/详情
- 第 4 周：情绪分析与事件联动、WS 新闻推送、索引与性能调优、E2E 验收与使用说明
