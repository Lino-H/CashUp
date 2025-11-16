## 已完成清单
- 架构与编排
  - 统一后端核心于 `apps/core`，Docker Compose 指向正确目录，Postgres 初始化采用 `scripts/init_database_v2.sql`
  - 路由注册：`/api/v1` 下的 `market/trading/strategies/reporting/configs/keys/exchanges/scheduler/rss/seed` 已完成
- 交易所与配置
  - 交易所管理器 DB 优先、YAML 与 ENV 回退，支持热重载：`apps/core/api/deps.py:1-88`
  - 密钥管理 API（按 `exchange/name` 更新或插入）与前端密钥页：`apps/core/api/routes/keys.py:22-54`、`frontend/src/pages/KeysManagement.tsx`
  - 系统配置中心 API 与前端配置中心页：`apps/core/api/routes/admin_configs.py:1-92`、`frontend/src/pages/ConfigCenter.tsx`
- 行情与缓存
  - 行情接口增加 Redis 缓存与 DB 回退：`apps/core/api/routes/market.py:1-120`
  - 市场采集任务：采样窗口、覆盖策略、频率限制与写库及写穿缓存：`apps/core/tasks/market_collector.py:1-99`
- 调度与联动
  - 心跳调度统一触发任务（RSS 抓取/分析/关联、交易同步、行情采集）：`apps/core/tasks/scheduler.py:1-120`
  - 调度状态接口（间隔/最近触发/错误趋势与备用源/触发历史）与手动触发：`apps/core/api/routes/scheduler.py:1-120`
  - 前端调度监控页：粒度切换（小时/天）、任务与源下拉筛选、错误统计与触发历史图表：`frontend/src/pages/SchedulerMonitor.tsx`
- RSS 与通知
  - RSS 抓取失败重试、备用源回退与错误累积统计：`apps/core/tasks/rss.py:52-132`
  - 通知服务重构主程序、模板渲染与消费队列：`notification-service/main.py:1-110`、`notification-service/consumer.py`、`notification-service/templates.py`、`notification-service/api.py`
- 策略模块
  - 因子库（RSI/MA/MACD/EMA/BOLL/ATR）、组合策略（加权/投票）、生命周期启停与风控（最大仓位/止损/止盈）、回测引擎与接口：`apps/core/modules/strategy/*`、`apps/core/api/routes/strategies.py`
- 账户与持仓
  - 同步余额/持仓任务（动态间隔与软重载）与账户总览接口：`apps/core/tasks/sync.py`、`apps/core/api/routes/reporting.py`
  - 前端账户总览页（多交易所切换、自动刷新、汇总权益与胜率趋势、导出 CSV/SVG）：`frontend/src/pages/AccountOverview.tsx`
- E2E 测试
  - 独立 `e2e` 项目（Playwright），健康/配置/交易所/调度状态与触发/备用RSS 均通过（6/6）：`e2e/tests/e2e.spec.ts`
- 清理与对齐
  - 删除冗余脚本与编译产物，DDL 对齐 `system_configs` 表与 `api_keys(exchange,name)` 唯一约束：`scripts/init_database_v2.sql`

## 待完成清单
- 行情与采集
  - 公共行情采集的批量写入优化（COPY、批事务）、数据完整性校验与断点续采
  - 适配器扩展：Bybit/Kraken 驱动的只读行情与基础下单（当前仅在 YAML 中注册示例）
- 调度与监控
  - 调度页增加错误趋势的多维对比（按任务堆叠、按源分组）、触发历史的任务分组视图
  - 任务手动触发的结果回显与队列消费成功/失败率指标
- 通知与事件
  - 队列消费的重试与死信队列、模板变量丰富与类别分级（成交/风险/价格预警），可配置渠道优先级
- 安全与密钥
  - API Keys 加密存储与轮换（当前按个人使用未启用），后续可选 RBAC 与操作审计
- 适配器与前端
  - 前端密钥管理增加更多交易所选项与参数校验规则（格式/前缀/字符集）
  - 市场页面与图表（K 线/订单簿）联动缓存TTL与回退提示
- 可观测性
  - Prometheus 指标（任务耗时/错误率/队列滞留/API 命中率）与日志轮转/聚合

## 执行计划（分阶段）
### 阶段1：行情采集与缓存一致性（T+3 天）
- 批写优化：为 `tasks.market.collect` 增加批量 upsert（事务分批、必要时 COPY）与断点续采（按最近 `open_time`）
- 完成缓存策略可配置项：`market.cache.strategy/ttl`，在采集成功后按策略写穿/绕写
- 增加 E2E 验证：采集→写库→缓存命中→接口回退场景

### 阶段2：调度监控增强（T+3 天）
- 后端：在 `scheduler/status` 增加任务分组堆叠与源分组趋势数据结构（series 格式）
- 前端：趋势图增加任务与源的双图联动对比、触发历史任务分组堆叠视图；筛选联动缓存刷新
- 增加 E2E：通过 API 验证趋势数据结构与筛选逻辑

### 阶段3：适配器扩展（T+5 天）
- 实现 Bybit/Kraken 行情适配器（只读K线/订单簿），在 `ExchangeManager` 注册与热重载
- 前端密钥页增加对应交易所选项与校验规则；E2E 覆盖列表与保存

### 阶段4：通知与事件稳健性（T+4 天）
- 消费重试与死信队列、模板变量拓展（事件/源/符号/数量/价格），渠道优先级与并发控制
- 增加状态接口返回队列消费成功/失败率与滞留数量，前端提示

### 阶段5：可观测性与维护（T+4 天）
- 增加 Prometheus 指标导出，关键任务与 API 指标（耗时/错误率/命中率）
- 日志轮转与聚合配置，开发/生产配置分离

### 阶段6：安全与密钥（可选，T+5 天）
- API Keys 加密存储（透明加解密）、轮换与密钥失效策略；前端提示状态

## 验收标准
- 行情采集：批写成功率≥99%，缓存命中率提升，回退稳定无 5xx
- 调度监控：趋势与历史按任务/源筛选正确，UI 响应及时
- 适配器：新增交易所的 K 线/订单簿接口返回正确，前端可配置密钥并热重载
- 通知与事件：队列消费成功率≥99%，模板渲染正确
- 可观测性：关键指标可查询，日志可溯源

## 启动与测试
- 启动：`docker compose up -d`
- 心跳调度与状态：`GET http://localhost:8001/api/v1/scheduler/status?granularity=hour`
- 采集触发：`POST http://localhost:8001/api/v1/scheduler/trigger` `{"task":"market.collect"}`
- 行情接口：`GET http://localhost:8001/api/v1/market/klines?exchange=gateio&symbol=ETH_USDT&timeframe=1h&limit=100`
- E2E：`cd e2e && npm install && npx playwright install chromium && npm test`

以上计划将按阶段推进，过程中每一阶段交付包含：代码实现、接口/前端联动、端到端测试与文档更新，并保持与现有架构的一致性。