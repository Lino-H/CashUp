## ToDo 列表（按优先级与阶段）
- 阶段1：行情采集与缓存一致性（优先级：高）
  - 批量 upsert/COPY 优化写库（kline_data）
  - 断点续采策略完善（仅写新段、窗口采样）
  - 缓存策略联动与配置（write_through/write_around、TTL）
  - E2E 验证采集→写库→缓存→接口回退链路
- 阶段2：调度监控增强（优先级：高）
  - 后端 status 返回 series（任务堆叠/源分组）
  - 前端趋势双图联动（任务/源维度）与触发历史分组视图
  - 筛选联动缓存刷新与交互优化
  - E2E 验证趋势数据结构与筛选逻辑
- 阶段3：适配器扩展（优先级：中）
  - Bybit/Kraken 行情适配器（只读 K线/订单簿）
  - ExchangeManager 注册与热重载联动
  - 密钥页选项与校验规则扩展
  - E2E 验证新增交易所读数
- 阶段4：通知与事件稳健性（优先级：中）
  - 消费重试与死信队列、并发控制
  - 模板变量丰富与渠道优先级配置
  - 状态接口消费指标与前端提示
- 阶段5：可观测性与维护（优先级：中）
  - Prometheus 指标（任务耗时/错误率/队列滞留/API 命中率）
  - 日志轮转与聚合、开发/生产配置分离
- 阶段6：安全与密钥（可选，优先级：低）
  - API Keys 加密存储与轮换、密钥失效策略与前端提示

## 分步实施安排
### 阶段1（T+3 天）
- 实施：
  - 为 `tasks.market.collect` 增加 COPY/批事务写库与按最近 `open_time` 的断点续采
  - 完善 `market.cache.strategy/ttl` 并验证写穿/绕写逻辑，与 `/api/v1/market/klines` 缓存回退一致
- 交付：代码、配置项、E2E（采集→写库→缓存→回退）与文档

### 阶段2（T+3 天）
- 实施：
  - `scheduler/status` 返回任务堆叠/源分组的 series 数据结构（可选多维过滤）
  - 前端趋势双图联动与触发历史任务分组视图，筛选与粒度交互
- 交付：前后端联动与 E2E（趋势数据结构与筛选）

### 阶段3（T+5 天）
- 实施：
  - Bybit/Kraken 只读适配器，注册至 ExchangeManager 并热重载
  - 密钥页增加选项与校验规则，并验证保存
- 交付：新增交易所读取与 E2E 用例

### 阶段4（T+4 天）
- 实施：
  - 通知消费重试、死信队列与并发控制；模板变量丰富与渠道优先级
  - 状态接口返回消费成功/失败率与滞留，前端提示
- 交付：稳定的通知管线与监控指标

### 阶段5（T+4 天）
- 实施：
  - Prometheus 导出与仪表板配置
  - 日志轮转与聚合、环境配置分离
- 交付：可观测性增强与运维便利

### 阶段6（可选，T+5 天）
- 实施：
  - API Keys 加密与轮换、失效策略与前端提示
- 交付：安全能力增强

## 验收标准
- 行情采集：批写成功率≥99%，缓存命中率提升，回退稳定无 5xx
- 调度监控：趋势与历史按任务/源筛选正确，UI 响应及时
- 适配器：新增交易所 K线/订单簿接口返回正确，前端可配置密钥并热重载
- 通知与事件：消费成功率≥99%，模板渲染正确
- 可观测性：关键指标可查询，日志可溯源

## 启动与测试
- 启动：`docker compose up -d`
- 调度状态：`GET /api/v1/scheduler/status?granularity=hour`
- 采集触发：`POST /api/v1/scheduler/trigger {"task":"market.collect"}`
- 行情接口：`GET /api/v1/market/klines?exchange=gateio&symbol=ETH_USDT&timeframe=1h&limit=100`
- E2E：`cd e2e && npm install && npx playwright install chromium && npm test`

请确认上述 ToDo 与分步安排；确认后我将按顺序逐项实现并在每个阶段完成后进行联动验证与交付。

---

## 已完成功能清单（v2 核心）
- 核心服务 FastAPI 与路由注册（apps/core/main.py）
- 异步数据库引擎与会话管理（apps/core/database/connection.py）
- 配置管理与环境加载（apps/core/config/settings.py）
- Celery 队列、Beat 心跳与任务路由（apps/core/celery_app.py）
- 调度心跳与动态间隔、Redis 去重与历史（apps/core/tasks/scheduler.py）
- RSS 抓取、情绪分析与相关性计算（apps/core/tasks/rss.py）
- 行情采集任务（apps/core/tasks/market_collector.py）
- ORM 模型（用户/策略/订单/回测/配置/通知日志）（apps/core/models/models.py）
- 前端 React+TS+Vite 基础页面与测试用例（frontend/src/*）
- 容器编排与健康检查（docker-compose.yml）

## 未完成功能清单（优先建议）
- 行情批量写库与断点续采的性能优化
- 调度监控前后端联动的趋势/分组视图与指标
- 交易所适配器扩展（Bybit/Kraken 只读）与密钥页增强
- 通知消费重试、死信队列与并发控制、模板与优先级
- Prometheus 指标导出与日志轮转、环境分离
- API Keys 加密与轮换、失效策略与前端提示

## 家庭服务器单节点适配方案
- 目标：在单机上运行核心服务与任务，无 RabbitMQ 依赖，优先 Redis 作为 Broker/Backend。
- 开关：新增 `SINGLE_NODE` 环境变量（默认开启），支持 `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` 覆盖。
- 行为：单节点时 Celery 使用 `Redis` 作为 Broker 与结果后端；分布式时使用 `RabbitMQ` 作为 Broker。
- 影响范围：`apps/core/config/settings.py`、`apps/core/celery_app.py`、`docker-compose.yml`（可选提供单机覆盖）。

## 分步执行（单节点适配）
- 步骤1：配置开关与 Broker 选择逻辑（已完成）
- 步骤2：提供本地运行指南与 compose 覆盖（待执行）
- 步骤3：调度与任务在单机的负载与资源限制优化（待执行）
