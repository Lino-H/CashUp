# CashUp Project Rules（项目协作规则）

本规则基于仓库内 `CLAUDE.md`、`CODEBUDDY.md`、`DEPLOYMENT.md` 与当前代码结构整理，约束日常协作、编码规范、提交流程与发布运维。除非特别说明，项目沟通与文档统一使用中文。

## 1. 通用原则
- 清晰、可维护、可测试优先；避免过度抽象，拒绝一次性写死。
- 约定优于配置：各服务目录、端口、接口前缀、工具统一。
- 安全第一：不提交任何密钥；最小权限；输入校验；遵循 CORS 规则。
- 性能优先使用异步与连接池；热点数据缓存到 Redis；实时场景使用 WebSocket。
- 文档即代码：新增/变更能力必须同步更新文档与示例。
- 质量门槛：所有代码必须通过 lint、格式化和测试方可合并。

## 2. 架构与模块边界
- 服务与端口约定：
  - Core Service（认证/配置/用户）：8001 → `/api/auth/*`, `/api/users/*`, `/api/config/*`
  - Trading Engine（交易执行/持仓）：8002 → `/api/v1/*`
  - Strategy Platform（策略/回测/数据）：8003 → `/api/*`
  - Notification Service（通知）：8004 → `/api/*`
  - Frontend：3000，统一通过 Nginx 反向代理
- 服务间只通过 HTTP API 通信；Core Service 作为统一认证中心。
- 配置集中化：公共配置放 `configs/`，交易所配置放 `configs/exchanges.yaml`。
- 数据流：前端 → Nginx → 各服务 → PostgreSQL/Redis → 外部交易所API
- 服务间通信：HTTP/REST API，内部使用 JWT 认证

## 3. 开发环境与命令

### 3.1 系统要求
- **操作系统**：macOS 或 Linux（推荐 Ubuntu 20.04+）
- **Python**：3.11+（使用 UV 包管理器）
- **Node.js**：18+ LTS
- **Docker**：20.10+ 和 docker-compose
- **数据库**：PostgreSQL 14+、Redis 6.2+
- **其他工具**：make、pre-commit、curl、jq

### 3.2 环境初始化
```bash
# 1. 克隆项目
git clone <repository-url>
cd CashUp_v2

# 2. 激活 Python 环境
source v-quant/bin/activate

# 3. 安装 UV 包管理器（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 4. 安装后端依赖
make install-deps

# 5. 安装前端依赖
cd frontend && npm install && cd ..

# 6. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写必要的配置信息

# 7. 初始化数据库
make init-db

# 8. 启动基础设施
make up
```

### 3.3 服务启动顺序
1. `make up`（PostgreSQL + Redis + Nginx）
2. `make core` → `make strategy` → `make trading` → `make notify`
3. `make frontend`

### 3.4 开发工具配置
- **统一格式化**：Python 使用 `black`；前端使用 `prettier`；提交前 `pre-commit run --all-files`
- **统一日志**：结构化 JSON，字段 `time/level/service/message/trace_id`；开发环境同时输出可读文本
- **热重载**：各服务自带 `--reload`；前端 `npm start`

## 4. 代码规范（后端 Python）

### 4.1 代码风格
- **格式化**：Black（行宽 88 字符）
- **导入排序**：isort（标准库、第三方、本地库分组）
- **代码检查**：flake8（最大行长度 88）
- **类型检查**：mypy（严格模式）
- **导入规则**：绝对导入优先，避免循环导入

### 4.2 目录结构
```
service/
├── main.py              # 服务入口，只负责启动
├── api/routes/          # 路由层，仅做参数校验和调用 service
├── services/            # 业务逻辑层
├── models/              # SQLAlchemy ORM，禁止裸 SQL
├── schemas/             # Pydantic 模型，区分 Create/Update/Response
├── utils/               # 纯函数、三方 SDK 封装、日志格式化
├── config/              # 环境变量与设置，统一用 Pydantic Settings
└── tests/               # 单元测试和集成测试
```

### 4.3 编码规范
- **依赖注入**：使用 FastAPI Depends，禁止在函数内手动 new 实例
- **异常处理**：自定义 `CashUpException` → 统一 `exception_handler` → 日志 + 统一响应格式 `{code, msg, data}`
- **日志规范**：使用 `utils.logger` 实例，禁止 print；trace_id 从头传到尾
- **配置管理**：所有可配置项必须进 YAML 或环境变量，禁止硬编码
- **数据库操作**：使用 ORM，禁止裸 SQL；复杂查询使用 SQLAlchemy 表达式
- **API 设计**：RESTful 风格，统一使用 `/api/v1/` 前缀
- **输入校验**：使用 Pydantic 模型，在路由层完成所有参数校验
- **错误码规范**：统一错误码格式，业务错误码范围 1000-9999

## 5. 代码规范（前端 TypeScript/React）

### 5.1 技术栈
- **语言**：TypeScript 5.0+
- **框架**：React 18+（函数组件 + Hooks）
- **构建工具**：Webpack 5、Babel、ESLint、Prettier
- **状态管理**：React Query、React Context + useReducer
- **样式**：Tailwind CSS 3.0+
- **测试**：Jest、React Testing Library、Cypress（E2E）

### 5.2 目录结构
```
frontend/src/
├── pages/               # 页面级组件，仅做路由与数据获取
├── components/          # 通用 UI 组件，必须写 Props 接口
├── services/            # API 调用层，统一封装 Axios
├── hooks/               # 自定义 Hooks，禁止在组件内写业务逻辑
├── utils/               # 纯函数、常量、格式化
├── contexts/            # 全局状态管理（Context + useReducer）
├── types/               # TypeScript 类型定义
├── styles/              # 全局样式和 Tailwind 配置
└── __tests__/           # 单元测试文件
```

### 5.3 编码规范
- **类型安全**：严格 TypeScript 模式，避免使用 `any`，优先使用 `unknown`
- **组件设计**：
  - 函数组件优先，使用 Hooks 管理状态和副作用
  - 组件 props 必须定义接口，避免使用可选链操作符滥用
  - 复杂组件拆分为子组件，保持单一职责
- **状态管理**：
  - 组件内状态：useState
  - 跨组件状态：Context + useReducer
  - 服务端状态：React Query（缓存、重试、乐观更新）
- **API 调用**：
  - 统一封装 Axios 实例，拦截器自动添加 trace_id
  - 所有接口返回统一格式 `{code, msg, data}`
  - HTTP 200 仅表示网络成功，业务失败看 code
- **错误处理**：
  - 网络错误：全局 Toast + 重试按钮
  - 业务错误：按 code 映射到具体文案，弹窗或页面提示
- **性能优化**：
  - 组件懒加载（React.lazy）
  - 图片懒加载
  - 虚拟滚动（长列表场景）
  - 防抖/节流（搜索、滚动等高频操作）
  - 打包分析：`npm run build:analyze`
- **命名规范**：
  - 组件名：PascalCase（如：UserProfile）
  - 函数/变量：camelCase（如：getUserData）
  - 常量：UPPER_SNAKE_CASE（如：API_TIMEOUT）
  - 文件名：组件用 PascalCase，其他用 camelCase

## 6. API 规范

### 6.1 认证与授权
- **认证方式**：Bearer Token（Session-based）
- **签发与校验**：Core Service 统一处理
- **Token 有效期**：默认 24 小时，支持刷新机制
- **权限控制**：基于 RBAC（角色权限控制）

### 6.2 API 路由规范
- **统一前缀**（推荐新增接口使用）：
  - `/api/v1/core/*`：Core Service
  - `/api/v1/strategy/*`：Strategy Platform
  - `/api/v1/trading/*`：Trading Engine
  - `/api/v1/notify/*`：Notification Service
- **兼容路径**（现有保留）：
  - Core：`/api/auth/*`, `/api/users/*`, `/api/config/*`
  - Trading：`/api/v1/*`
  - Strategy/Notification：`/api/*`
- **命名与路径**：资源名复数；动作使用语义化子路径或方法区分（GET/POST/PUT/PATCH/DELETE）

### 6.3 请求与响应格式
- **统一响应格式**：
  ```json
  {
    "code": 0,
    "msg": "ok",
    "data": {},
    "trace_id": "uuid"
  }
  ```
- **分页格式**：
  ```
  GET /api/v1/xxx?page=1&size=20&sort=created_at:desc
  ```
  返回：
  ```json
  {
    "code": 0,
    "data": {
      "items": [],
      "total": 100,
      "page": 1,
      "size": 20
    }
  }
  ```

### 6.4 错误码规范
- **成功**：0
- **系统级错误**：1~99
- **服务特定错误**（推荐新增接口使用）：
  - 1000~1999：Core Service
  - 2000~2999：Strategy Platform
  - 3000~3999：Trading Engine
  - 4000~4999：Notification Service

### 6.5 WebSocket 规范
- **连接地址**：
  - `/ws/core`：Core Service
  - `/ws/strategy`：Strategy Platform
  - `/ws/trading`：Trading Engine
  - `/ws/notify`：Notification Service
- **消息格式**：`{type, ts, data, trace_id}`
- **心跳机制**：
  - 客户端每 30s 发送 `{"type":"ping"}`
  - 服务端回 `{"type":"pong"}`
  - 连续 3 次未收到响应即断开连接
- **认证**：WebSocket 连接时携带 Token 参数

### 6.6 版本化
- 破坏性变更使用新版本前缀（如 `/api/v2/*`）

## 7. 安全与合规

### 7.1 密钥管理
- **绝不提交密钥**：使用 `.env`（从 `.env.example` 拷贝）+ 环境变量注入
- **前端敏感配置**：走运行时注入（`window.__RUNTIME_CONFIG__`）
- **后端敏感配置**：走 Pydantic Settings，字段 `env="xxx"`
- **数据库连接**：禁止明文落盘；使用 Docker Secret 或云平台安全服务
- **密钥轮换**：定期更新 API 密钥和加密密钥

### 7.2 用户认证
- **密码加密**：Argon2 加密，成本因子 10
- **JWT 配置**：
  - 访问令牌：24 小时过期
  - 刷新令牌：7 天过期
  - 密钥强度：至少 256 位随机密钥
- **多因素认证**：支持 TOTP（基于时间的一次性密码）

### 7.3 输入验证与防护
- **防重放攻击**：
  - 登录/注册/提现/下单等关键接口增加图形验证码或短信验证码
  - 使用 nonce 和时间戳验证请求有效性
- **防注入攻击**：
  - ORM/SQLAlchemy 参数化查询，禁止字符串拼接
  - 前端输入校验 + 后端二次校验
  - 使用白名单验证输入格式
- **文件上传**：
  - 限制文件类型和大小
  - 病毒扫描
  - 文件重命名存储

### 7.4 网络安全
- **CORS 配置**：
  - 前端域名白名单
  - 凭证凭据仅 SameSite=Strict
  - CSRF 令牌验证
- **HTTPS**：强制使用 HTTPS，HSTS 头部
- **Rate Limiting**：基于 IP 和用户 ID 的速率限制
- **DDoS 防护**：使用 CDN 和负载均衡器

### 7.5 数据保护
- **数据加密**：
  - 传输中：TLS 1.3
  - 存储中：AES-256-GCM
- **数据脱敏**：
  - 手机号：138****8888
  - 邮箱：u***@example.com
  - 身份证号：********1234
  - 银行卡号：**** **** **** 1234
  - API Key：sk_***...***abcd
- **数据备份**：加密备份，异地存储

### 7.6 审计与监控
- **操作审计**：关键操作落库（用户、时间、IP、操作、结果）
- **日志脱敏**：敏感信息打码处理
- **安全监控**：
  - 异常登录检测
  - 异常交易监控
  - 系统资源使用监控
- **合规要求**：遵循 GDPR、PCI DSS 等相关法规

## 8. 性能与可用性

### 8.1 性能优化策略
- **异步优先**：全链路异步处理，使用 asyncio 和 Promise
- **连接池管理**：
  - 数据库连接池（PostgreSQL）
  - Redis 连接池
  - 外部 API 连接池（交易所 API）
- **缓存策略**：
  - 热点数据缓存到 Redis
  - TTL 根据业务可配置（5分钟-24小时）
  - 缓存更新策略：Cache-Aside 模式
- **前端优化**：
  - 组件懒加载（React.lazy）
  - 图片懒加载（Intersection Observer）
  - 虚拟滚动（长列表场景）
  - 防抖/节流（搜索、滚动等高频操作）
  - 代码分割和 Tree Shaking
  - CDN 加速静态资源

### 8.2 后端性能
- **FastAPI 配置**：
  - 开启 gzip 压缩
  - CORS 中间件
  - Request ID 中间件
  - 响应缓存（可配置）
- **数据库优化**：
  - SQLAlchemy 连接池配置
  - 复杂查询添加索引
  - 慢查询监控和优化
  - 读写分离（高并发场景）
- **外部 API 调用**：
  - asyncio + aiohttp
  - 熔断器模式（Circuit Breaker）
  - 指数退避重试策略
  - 批量请求优化

### 8.3 监控指标
- **应用层指标**：
  - QPS（每秒查询率）
  - P95/P99 响应时间
  - 错误率（4xx/5xx）
  - 请求并发数
- **系统层指标**：
  - CPU 使用率
  - 内存使用率
  - 磁盘 I/O
  - 网络带宽
- **业务指标**：
  - 用户活跃度
  - 交易成功率
  - 策略执行成功率
  - 消息队列长度

### 8.4 可用性保障
- **健康检查**：
  - 各服务 `/health` 返回 `{status,ts,version,dependencies}`
  - docker-compose 依赖健康检查
  - Kubernetes 就绪性和存活性探针
- **容错机制**：
  - 服务降级（熔断器）
  - 限流（令牌桶算法）
  - 重试机制（指数退避）
- **部署策略**：
  - 蓝绿部署
  - 滚动更新
  - 多可用区部署

## 9. 分支、提交与 PR 流程

### 9.1 分支模型
- **main**：生产分支，仅接受合并，禁止直接推送
- **develop**：集成测试分支，功能稳定后合并到 main
- **feature/***：功能分支，从 develop 切出，完成后合并回 develop
- **hotfix/***：紧急修复，从 main 切出，完成后同时合并到 main 与 develop
- **release/***：发布分支，用于准备新版本发布

### 9.2 Commit 规范（Conventional Commits）
```
<type>(<scope>): <subject>

<body>

Closes #<issue>
```

**type 类型**：
- `feat`：新功能
- `fix`：修复 bug
- `docs`：文档更新
- `style`：代码格式调整
- `refactor`：代码重构
- `test`：测试相关
- `chore`：构建过程或辅助工具的变动

**scope 范围**：core/strategy/trading/notify/frontend

### 9.3 PR 流程
- **PR 模板**：
  - 标题同 Commit subject
  - 描述包含「背景、方案、测试、回滚」
  - 关联相关 Issue
- **质量门禁**：
  - 必须过 CI（lint + test + build）
  - 必须 1 人 approve
  - 必须 rebase 无冲突
  - 代码覆盖率不低于 80%
- **代码审查要点**：
  - 业务逻辑正确性
  - 代码可读性和维护性
  - 性能影响评估
  - 安全漏洞检查

### 9.4 发布流程
- **版本号规范**：语义化版本 `v<major>.<minor>.<patch>`
- **发布步骤**：
  1. 从 develop 创建 release 分支
  2. 更新版本号和 CHANGELOG
  3. 合并到 main 并打 Tag
  4. 自动生成 Release Notes
  5. 构建 Docker 镜像并推送
- **Docker 镜像**：`ghcr.io/cashup/<service>:<tag>`
- **回滚策略**：
  - Git revert 回滚代码
  - 回滚 Docker 镜像版本
  - 数据库迁移回滚（如有必要）

## 10. 测试与质量

### 10.1 测试策略
- **测试金字塔**：
  - 单元测试：70%（快速、独立）
  - 集成测试：20%（服务间交互）
  - E2E 测试：10%（用户场景）

### 10.2 后端测试
- **单元测试**：
  - 框架：pytest
  - 覆盖率要求：≥80%
  - 测试数据：使用 faker 和工厂模式
  - 测试数据库：独立实例，支持事务回滚
- **集成测试**：
  - 使用 TestClient 测试 API
  - 测试服务间交互
  - 冒烟测试（docker-compose 环境）
- **Mock 策略**：
  - 外部交易所 API：使用 pytest-mock 或 responses
  - 数据库：使用内存数据库或测试数据库
  - 消息队列：使用 mock 队列

### 10.3 前端测试
- **单元测试**：
  - 框架：Jest + React Testing Library
  - 覆盖率要求：≥80%
  - 组件测试：测试组件渲染和交互
- **集成测试**：
  - 测试页面路由和数据流
  - 测试自定义 Hooks
- **E2E 测试**：
  - 框架：Cypress
  - 覆盖核心用户场景
  - 跨浏览器测试
- **Mock 策略**：
  - API 调用：使用 MSW（Mock Service Worker）
  - 全局状态：mock Context 和 Redux

### 10.4 性能测试
- **工具**：k6
- **测试脚本**：`tests/perf/`
- **基准测试**：
  - PR 阶段跑基准性能对比
  - 监控响应时间和吞吐量
  - 识别性能回归

### 10.5 质量门禁
- **后端**：（见 4.1 节）
  - 覆盖率 ≥80%
  - mypy 无错误
  - flake8 无警告
  - 单元测试全过
- **前端**：（见 5.1 节）
  - 覆盖率 ≥80%
  - ESLint 无错误
  - 单元测试全过

### 10.6 CI/CD 流程
- **GitHub Actions 工作流**：
  1. 代码检出
  2. 环境设置
  3. 依赖安装
  4. 代码质量检查（lint、format）
  5. 运行测试（单元测试、集成测试）
  6. 构建应用
  7. 推送 Docker 镜像
  8. 部署到测试环境
- **并行执行**：不同服务可并行测试
- **缓存策略**：缓存依赖和构建产物

## 11. 日志与监控

### 11.1 日志规范
- **日志格式**：结构化 JSON，包含字段：
  ```json
  {
    "time": "2024-01-01T12:00:00Z",
    "level": "INFO",
    "service": "core-service",
    "message": "用户登录成功",
    "trace_id": "uuid-12345",
    "user_id": "123",
    "ip": "192.168.1.1"
  }
  ```
- **日志级别**：
  - DEBUG：调试信息（开发环境）
  - INFO：一般信息（生产环境默认）
  - WARNING：警告信息
  - ERROR：错误信息
  - CRITICAL：严重错误
- **敏感信息脱敏**：手机号、邮箱、身份证号、银行卡号、API Key 等
- **日志输出**：
  - 开发环境：同时输出可读文本和 JSON
  - 生产环境：仅输出 JSON 格式

### 11.2 监控体系
- **技术栈**：Prometheus + Grafana + Loki + OpenTelemetry + Jaeger
- **关键指标**：
  - **应用层**：QPS、P95/P99 响应时间、错误率
  - **系统层**：CPU、内存、磁盘 I/O、网络带宽
  - **业务层**：用户活跃度、交易成功率、策略执行成功率
  - **资源层**：数据库连接数、Redis 连接数、消息队列长度

### 11.3 告警规则
- **错误率告警**：错误率 >1% 持续 5min
- **响应时间告警**：P99 响应时间 >2s 持续 5min
- **队列积压告警**：队列积压 >1000 持续 3min
- **服务不可用告警**：健康检查失败
- **资源告警**：
  - CPU 使用率 >80% 持续 10min
  - 内存使用率 >85% 持续 10min
  - 磁盘使用率 >90%

### 11.4 链路追踪
- **技术栈**：OpenTelemetry + Jaeger
- **trace_id 生成**：在网关层生成，贯穿所有服务
- **追踪信息**：
  - 请求链路
  - 数据库查询
  - 外部 API 调用
  - 消息队列操作
- **采样策略**：生产环境使用概率采样（1%）

### 11.5 监控仪表板
- **业务仪表板**：
  - 用户注册/登录趋势
  - 交易量统计
  - 策略执行统计
- **技术仪表板**：
  - 服务健康状况
  - 系统资源使用
  - 错误日志聚合
- **告警仪表板**：
  - 活跃告警列表
  - 告警处理状态
  - 告警趋势分析

## 12. 部署与发布

### 12.1 容器化策略
- **技术栈**：Docker + docker-compose + Kubernetes（生产）
- **构建命令**：`make build` 统一构建所有服务镜像
- **镜像仓库**：GitHub Container Registry（ghcr.io）
- **镜像标签**：
  - `latest`：最新稳定版
  - `v1.2.3`：语义化版本
  - `sha-abc123`：基于 commit SHA

### 12.2 环境管理
- **环境层级**：本地 → 测试 → 预发布 → 生产
- **部署流程**：
  1. 本地开发测试
  2. 自动部署到测试环境（GitHub Actions）
  3. 手动触发预发布环境部署
  4. 生产环境发布（需要审批）

### 12.3 配置管理
- **配置方式**：环境变量 + YAML 配置文件
- **生产配置**：
  - Kubernetes Secret：敏感信息（API 密钥、数据库密码）
  - Kubernetes ConfigMap：非敏感配置
  - 配置中心：考虑使用 Consul 或 etcd
- **配置验证**：部署前验证配置格式和必填项

### 12.4 数据库管理
- **迁移工具**：Flyway 或 Alembic
- **迁移流程**：
  1. CI 中自动执行迁移
  2. 支持回滚到指定版本
  3. 生产环境迁移需要审批
- **备份策略**：
  - 定期逻辑备份：`make backup-db`
  - 备份加密并异地存储
  - 保留 30 天内的备份
  - 定期恢复演练

### 12.5 回滚机制
- **代码回滚**：
  - GitHub Release 页面一键回滚
  - 支持回滚到任意历史版本
- **数据库回滚**：
  - 迁移脚本支持回滚
  - 重大版本升级前创建数据库快照
- **服务回滚**：
  - Kubernetes 支持快速版本切换
  - 蓝绿部署支持零停机回滚

### 12.6 部署脚本
```bash
# 构建所有服务
make build

# 部署到测试环境
make deploy-test

# 部署到生产环境
make deploy-prod

# 回滚到上一版本
make rollback

# 数据库备份
make backup-db

# 查看部署状态
make status
```

## 13. 配置与环境

### 13.1 环境变量规范
- **命名规则**：`CASHUP_<SERVICE>_<KEY>`，全大写
- **必需配置**：
  ```bash
  # 数据库配置
  CASHUP_DB_HOST=localhost
  CASHUP_DB_PORT=5432
  CASHUP_DB_NAME=cashup
  CASHUP_DB_USER=cashup_user
  CASHUP_DB_PASSWORD=your_secure_password
  
  # Redis 配置
  CASHUP_REDIS_HOST=localhost
  CASHUP_REDIS_PORT=6379
  CASHUP_REDIS_PASSWORD=your_redis_password
  
  # JWT 配置
  CASHUP_JWT_SECRET_KEY=your_jwt_secret_key
  CASHUP_JWT_ALGORITHM=HS256
  CASHUP_JWT_EXPIRATION_HOURS=24
  
  # 交易所 API 配置
  CASHUP_BINANCE_API_KEY=your_binance_api_key
  CASHUP_BINANCE_SECRET_KEY=your_binance_secret
  CASHUP_GATEIO_API_KEY=your_gateio_api_key
  CASHUP_GATEIO_SECRET_KEY=your_gateio_secret
  
  # 通知服务配置
  CASHUP_EMAIL_SMTP_HOST=smtp.gmail.com
  CASHUP_EMAIL_SMTP_PORT=587
  CASHUP_EMAIL_USERNAME=your_email@gmail.com
  CASHUP_EMAIL_PASSWORD=your_email_password
  ```

### 13.2 配置文件管理
- **YAML 配置**：统一放 `configs/` 目录
- **配置分类**：
  - `database.yaml`：数据库连接配置
  - `exchanges.yaml`：交易所 API 配置
  - `notifications.yaml`：通知服务配置
  - `strategies.yaml`：策略相关配置
- **配置验证**：启动时验证配置文件格式和必填项

### 13.3 多环境配置
- **环境区分**：本地/测试/预发布/生产
- **配置文件**：
  - `docker-compose.<env>.yml`：Docker 环境配置
  - `nginx.<env>.conf`：Nginx 配置
  - `config.<env>.yaml`：应用配置
- **配置下发**：
  - Core Service 提供 `/api/v1/core/config` 接口
  - 各服务启动时拉取配置
  - 支持配置热更新

### 13.4 密钥管理
- **生产环境**：
  - Kubernetes Secret：敏感信息（API 密钥、数据库密码）
  - 密钥轮换：定期更新密钥
- **开发环境**：
  - `.env` 文件（不提交到版本控制）
  - `.env.example`：模板文件，包含所有配置项
- **CI/CD 环境**：
  - GitHub Encrypted Secrets
  - 环境变量注入
- **密钥加密**：
  - 使用 AES-256-GCM 加密存储
  - 传输中使用 TLS 1.3

## 14. 文档与知识沉淀

### 14.1 文档规范
- **文档位置**：所有文档必须放在 `docs/` 目录下
- **文档类型**：
  - `docs/api/`：API 文档（OpenAPI 规范）
  - `docs/architecture/`：架构设计文档
  - `docs/deployment/`：部署指南
  - `docs/development/`：开发指南
  - `docs/ops/`：运维文档
  - `docs/incidents/`：故障复盘报告

### 14.2 代码文档
- **代码即文档**：
  - 所有公开接口必须有 docstring
  - 复杂业务逻辑必须写行内注释
  - 关键算法需要详细注释说明
- **注释标准**：
  - Python：遵循 Google Python Style Guide
  - TypeScript：遵循 TSDoc 规范
  - 注释覆盖率要求 > 80%

### 14.3 变更记录
- **发布说明**：
  - 每次发版在 `docs/release-notes/vx.y.z.md` 中记录
  - 包含内容：
    - 新增功能
    - 修复的 bug
    - 破坏性变更
    - 回滚方案
    - 影响面分析
- **版本对比**：提供与上一版本的详细对比

### 14.4 故障复盘
- **复盘要求**：
  - P1/P2 级故障必须写复盘报告
  - 复盘报告模板：
    ```markdown
    # 故障复盘报告
    
    ## 故障概述
    - 故障时间：
    - 影响范围：
    - 持续时间：
    - 严重程度：
    
    ## 故障原因
    - 直接原因：
    - 根本原因：
    
    ## 处理过程
    - 发现时间：
    - 响应时间：
    - 解决时间：
    
    ## 改进措施
    - 短期措施：
    - 长期措施：
    
    ## 经验教训
    ```

### 14.5 运维文档
- **工具文档**：
  - Makefile 使用说明
  - CI/CD 流程说明
  - Docker 使用指南
  - 监控告警配置
  - 日志查看方法
- **操作手册**：
  - 日常维护操作
  - 故障排查流程
  - 性能调优指南
  - 安全操作规范

### 14.6 知识分享
- **技术分享**：每月至少一次技术分享会
- **最佳实践**：定期更新开发最佳实践文档
- **FAQ**：维护常见问题解答文档
- **视频教程**：重要功能制作视频教程

## 15. 进行中的重点与已知问题（同步 CLAUDE.md）

### 15.1 进行中的重点任务
- **交易所客户端开发**：
  - Binance API 集成（现货交易）
  - Gate.io API 集成（合约交易）
  - 统一交易接口抽象层
  - 订单状态实时同步

- **实时 WebSocket 系统**：
  - 价格数据实时推送
  - 订单状态实时更新
  - 用户通知实时推送
  - WebSocket 连接池管理

- **策略执行引擎**：
  - 策略模板系统
  - 策略回测功能
  - 策略性能分析
  - 策略风险管理

- **风控系统**：
  - 实时风险监控
  - 自动止损机制
  - 异常交易检测
  - 风险预警通知

### 15.2 已知技术问题
- **WebSocket 重连风暴**：
  - 问题：大量客户端同时重连导致服务器压力
  - 影响：服务响应延迟，部分连接失败
  - 临时方案：增加重连随机延迟
  - 长期方案：实现智能重连策略

- **策略并发性能**：
  - 问题：多策略同时执行时性能下降
  - 影响：策略执行延迟，错过交易时机
  - 临时方案：限制并发策略数量
  - 长期方案：优化策略执行引擎

- **前端实时图表性能**：
  - 问题：大量数据点导致图表渲染卡顿
  - 影响：用户体验下降，浏览器内存占用高
  - 临时方案：限制显示数据点数量
  - 长期方案：实现数据分层加载

- **Docker Compose 网络隔离**：
  - 问题：服务间网络通信不稳定
  - 影响：服务间调用偶尔失败
  - 临时方案：重启相关服务
  - 长期方案：优化网络配置

### 15.3 业务需求待完善
- **移动端适配**：响应式设计需要优化
- **多语言支持**：目前仅支持中文和英文
- **社交功能**：用户间交流和策略分享
- **高级图表**：技术指标和深度分析工具

### 15.4 性能优化计划
- **数据库查询优化**：慢查询分析和索引优化
- **缓存策略优化**：Redis 缓存命中率提升
- **CDN 部署**：静态资源加速
- **负载均衡**：多实例部署和流量分发

## 16. 故障排查与应急响应

### 16.1 故障分类与响应时间
- **P0 级故障（紧急）**：
  - 定义：系统完全不可用，影响所有用户
  - 响应时间：5 分钟内响应，30 分钟内解决
  - 处理流程：立即启动应急响应

- **P1 级故障（高）**：
  - 定义：核心功能不可用，影响大部分用户
  - 响应时间：15 分钟内响应，2 小时内解决
  - 处理流程：优先处理，必要时升级

- **P2 级故障（中）**：
  - 定义：非核心功能异常，影响部分用户
  - 响应时间：1 小时内响应，24 小时内解决
  - 处理流程：正常排期处理

- **P3 级故障（低）**：
  - 定义：优化类问题，影响用户体验
  - 响应时间：24 小时内响应，下个版本解决
  - 处理流程：规划到后续版本

### 16.2 故障排查流程
1. **发现问题**：
   - 监控告警发现
   - 用户反馈
   - 内部测试发现

2. **初步分析**：
   - 查看错误日志
   - 检查系统状态
   - 复现问题

3. **定位原因**：
   - 分析代码变更
   - 检查配置变更
   - 查看依赖服务状态

4. **制定方案**：
   - 临时解决方案
   - 根本解决方案
   - 回滚方案（如需要）

5. **执行修复**：
   - 按照方案执行
   - 验证修复效果
   - 监控系统状态

6. **总结复盘**：
   - 记录故障详情
   - 分析根本原因
   - 制定预防措施

### 16.3 常用排查命令
```bash
# 查看服务状态
make status
docker-compose ps
docker logs <service_name>

# 查看系统资源
htop
df -h
free -m

# 查看网络连接
netstat -tulpn
ss -tulpn

# 查看数据库状态
make db-status
psql -h localhost -U cashup_user -d cashup -c "SELECT * FROM pg_stat_activity;"

# 查看 Redis 状态
redis-cli ping
redis-cli info

# 查看日志
tail -f logs/<service_name>.log
grep "ERROR" logs/<service_name>.log
```

### 16.4 应急联系人
- **技术负责人**：张三（电话：138****1234）
- **运维负责人**：李四（电话：139****5678）
- **产品负责人**：王五（电话：137****9012）
- **紧急联系群**：CashUp 应急响应群（微信群）

---

## 17. 规则更新与维护

### 17.1 更新流程
- **提出变更**：
  - 任何团队成员都可以提出规则变更
  - 通过 Issue 或 PR 形式提交
  - 说明变更动机和预期影响

- **评审流程**：
  - 技术团队评审技术可行性
  - 产品团队评审业务影响
  - 运维团队评审运维成本

- **实施变更**：
  - 获得必要审批后实施
  - 同步更新相关文档
  - 通知所有团队成员

### 17.2 版本管理
- **版本号规则**：`v<major>.<minor>.<patch>`
  - major：重大规则变更
  - minor：新增规则或重要修改
  - patch：小修改和错误修正

- **发布记录**：
  - 每次更新都要记录变更内容
  - 记录生效日期
  - 记录影响范围

### 17.3 同步更新
- **相关文档同步**：
  - 同步更新 `CLAUDE.md`
  - 同步更新 `CODEBUDDY.md`
  - 同步更新 `DEPLOYMENT.md`
  - 更新相关技术文档

- **团队通知**：
  - 通过邮件通知所有团队成员
  - 在团队会议上说明重要变更
  - 更新内部知识库

---

**最后更新**：2024 年 12 月
**维护团队**：CashUp 技术团队
**联系方式**：tech-support@cashup.com

如需变更本规则，请在 PR 中说明调整动机、受影响范围与过渡方案，并同步更新 `CLAUDE.md` 与相关文档。
