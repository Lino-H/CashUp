## 目标补充
- 在首期加入“新闻获取 + 市场情绪分析”模块，先实现轻量版本
- 支持 RSS 订阅源采集、入库、情绪打分与前端展示；与事件/通知联动

## 模块设计（轻量版）
- 采集：
  - Celery 定时任务（beat）周期调用 `rss.fetch_feeds`，使用 `feedparser` 请求并解析
  - 去重：按 `url/guid` 去重；错误退避重试
  - 入库：写入 `market_news`（参考 `684-706`），字段含 `source/title/summary/url/published_at/category/tags/symbols`
- 情绪分析：
  - 英文：`vaderSentiment`（轻量，无模型下载）或 `textblob`（备选）
  - 中文：`snownlp`（轻量，词典法）
  - 打分与标签：`sentiment_score ∈ [-1,1]`，`sentiment_label ∈ {positive,neutral,negative}`
  - Celery 异步任务 `rss.analyze_sentiment(news_id)` 在入库后触发
- 订阅源配置：
  - `configs/rss_feeds.yaml`（参考 `1969-2027`），分类与抓取间隔可控
- 相关度与事件：
  - 发布 `NEWS_PUBLISHED` 事件到 RabbitMQ（参考 `942-990`）
  - 触发通知（Telegram/Webhook）走模板 `news_alert`（参考 `2301-2315`）
  - 价格相关度分析先暂缓，保留表结构（参考 `707-728`）

## 前端页面
- 新闻列表：分页/过滤（来源/类别/情绪/币种），情绪徽标，时间排序
- 新闻详情：标题、摘要、情绪分数、相关币种、外链跳转
- 与策略页联动：按关注交易对筛选相关新闻

## 数据流与任务编排
- `celery-beat`：按源的 `fetch_interval` 调度抓取
- `celery-worker`：执行抓取与情绪分析任务；失败重试 + 指数退避
- 事件：抓取成功→入库→发布 `NEWS_PUBLISHED`→通知模块消费并发送（可筛选）

## Docker/依赖
- 依赖：`feedparser`, `vaderSentiment`, `snownlp`（中文可选），`aiohttp`（抓取并发）
- 编排：沿用现有 `rabbitmq/redis/core-app/celery-worker/celery-beat/nginx/frontend/timescaledb`

## 首期时间线更新（与原 4 周计划对齐）
- 第 2 周：完成 RSS 抓取入库与前端新闻列表/详情
- 第 3 周：接入情绪分析任务与通知模板 `news_alert`；前端展示情绪标签与过滤

## 验证
- 单元：解析与情绪打分函数；入库与去重
- 集成：`celery-beat` 调度→抓取→入库→情绪→事件→通知→前端展示
