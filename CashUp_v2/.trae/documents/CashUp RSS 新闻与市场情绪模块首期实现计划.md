## 目标
- 首期集成“RSS 新闻采集 + 市场情绪分析 + 前端展示 + 通知联动”。
- 保持现有架构：Nginx 反代、RabbitMQ 事件队列、Redis 缓存/Celery 结果、Celery worker/beat、WebSocket。
- 时序与明细统一存 Postgres（推荐 TimescaleDB 扩展）。

## 功能范围
- RSS订阅：按 `configs/rss_feeds.yaml` 周期抓取（feedparser/aiohttp），去重入库。
- 情绪分析：英文用 `vaderSentiment`，中文用 `snownlp`（轻量），生成 `sentiment_score/-1..1` 与 `sentiment_label`。
- 事件通知：入库后发布 `NEWS_PUBLISHED` 到 RabbitMQ，通知模块消费并推送（Telegram/Webhook）。
- API/前端：提供新闻列表/详情查询与筛选（来源/类别/情绪/币种），前端页面展示并与策略关注交易对联动。
- WebSocket：广播最新新闻与情绪标签到前端订阅频道。

## 数据模型与索引（沿用文档表并优化）
- `rss_feeds`：来源、URL、分类、抓取间隔；唯一索引 `url`。
- `market_news`：`source/title/summary/url/published_at/category/tags/symbols/sentiment_score/sentiment_label/relevance_score`；
  - 索引：`published_at DESC`、`category+published_at`、`GIN(symbols)`、`sentiment_score`。
- 价格相关度表 `news_price_correlation` 保留但首期不实现计算，仅为后续扩展。
- 若启用 TimescaleDB：将 `market_news(published_at)` 设为超表时间列，便于时间窗口查询。

## 后端实现
- 依赖：`feedparser`, `aiohttp`, `vaderSentiment`, `snownlp`（中文可选），`pydantic`。
- Celery 任务：
  - `rss.fetch_feeds()`：读取 `rss_feeds` 活跃源，按 `fetch_interval` 调度抓取；并发请求、错误重试与退避。
  - `rss.parse_and_store(feed)`：解析条目→去重（按 `url/guid`）→标准化→入库 `market_news`。
  - `rss.analyze_sentiment(news_id)`：VADER/SnowNLP 打分与标签，更新 `market_news`。
  - `rss.publish_event(news_id)`：发布 `Events.NEWS_PUBLISHED` 到 RabbitMQ。
- API 路由（FastAPI）：
  - `GET /api/v1/news`：支持 `symbol/category/sentiment/limit` 过滤与分页。
  - `GET /api/v1/news/{id}`：返回详情与情绪字段。
  - `GET /api/v1/rss/feeds`：查看已配置源与状态（可选）。
- WebSocket：
  - 频道 `/ws/news`：推送最新新闻摘要 + 情绪标签 + symbols；前端订阅展示。

## 事件与通知联动
- 事件主题：沿用文档 `exchange.market`/`exchange.notification` 设计；事件 `NEWS_PUBLISHED`。
- 通知模板：复用 `news_alert` 模板（标题、摘要、情绪、相关币种、链接）。
- 发送策略：重要来源或高情绪绝对值新闻触发 Telegram/Webhook，其他在前端列表展示。

## 前端实现
- 页面：
  - `NewsList`：筛选（来源/类别/情绪/币种）、分页、情绪徽标；订阅 `/ws/news` 实时刷新。
  - `NewsDetail`：显示全文/摘要、情绪分数与标签、相关币种、外链跳转。
- 集成：在 `SentimentAnalysis.tsx` 页中加入新闻列表模块，与策略关注交易对联动筛选。

## 部署与编排
- Docker Compose 保持 `timescaledb | postgres`、`redis`、`rabbitmq`、`core-app`、`celery-worker`、`celery-beat`、`nginx`、`frontend`。
- 资源限额：为 `celery-worker` 设置并发与内存上限；抓取频率按源 `fetch_interval` 控制。
- 配置：`configs/rss_feeds.yaml` 管理源；环境变量控制并发/重试/超时。

## 验收标准
- 能定时抓取 5+ 主流源并入库（去重正确）。
- 英文/中文新闻情绪打分有效，标签分布合理。
- `NEWS_PUBLISHED` 事件触发后可在前端实时看到更新，并能推送到 Telegram/Webhook。
- API 列表/详情查询响应 < 500ms（95%）。

## 时间线（并入首期 4 周计划）
- 第 2 周：实现 RSS 抓取入库与前端新闻列表/详情；基础筛选与分页。
- 第 3 周：上线情绪分析任务与通知模板 `news_alert`；WebSocket 实时推送；联动策略页筛选。
- 第 4 周：索引与性能调优、错误重试与退避、重要新闻阈值推送与灰度控制；E2E 验收。