

## 目标
- 把你提供的配置（数据库、Redis、RabbitMQ、Telegram）完整接入项目，并统一以 `.env` 驱动所有容器与服务。
- 保持 Mac 环境与 Docker Desktop 使用 `host.docker.internal` 的访问方式。

## 变更范围
- `.env`（根目录）：新增/覆盖全部参数
- `docker-compose.yml`：容器环境引用 `.env` 变量，RabbitMQ 账号与密码与端口一致
- 后端服务读取：`core-service/config/settings.py`、各服务启动环境变量（无需改动代码逻辑，只要确保环境读取到）
- 通知服务：读取 `TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID`
- 安全与版本控制：`.env` 不入库（确保 `.gitignore` 覆盖）

## 接入内容（写入 .env）
- 数据库：
  - `DATABASE_URL=postgresql://cashup:cashup123@host.docker.internal:5432/cashup`
  - `DATABASE_HOST=host.docker.internal`
  - `DATABASE_PORT=5432`
  - `DATABASE_NAME=cashup`
  - `DATABASE_USER=cashup`
  - `DATABASE_PASSWORD=cashup123`
- Redis：
  - `REDIS_URL=redis://host.docker.internal:6379`
  - `REDIS_HOST=host.docker.internal`
  - `REDIS_PORT=6379`
  - `REDIS_DB=0`
- RabbitMQ：
  - `RABBITMQ_URL=amqp://cashup:cashup123@host.docker.internal:5672`
  - `RABBITMQ_HOST=host.docker.internal`
  - `RABBITMQ_PORT=5672`
  - `RABBITMQ_USER=cashup`
  - `RABBITMQ_PASSWORD=cashup123`
- Telegram：
  - `TELEGRAM_BOT_TOKEN=...`
  - `TELEGRAM_CHAT_ID=...`

## 编排调整（docker-compose.yml）
- 统一服务环境变量引用 `.env`：`core-service/trading-engine/strategy-platform/notification-service/celery-worker/celery-beat` 使用上述 `DATABASE_URL/REDIS_URL/RABBITMQ_URL` 与 Telegram 变量
- RabbitMQ 容器：设置 `RABBITMQ_DEFAULT_USER=cashup`、`RABBITMQ_DEFAULT_PASS=cashup123`
- 保留健康检查与资源限额不变

## 服务读取与兼容
- `core-service/config/settings.py` 已支持从环境读取 `DATABASE_URL/REDIS_URL`，无需改代码，只要环境变量生效
- Celery 与任务：`core-service/celery_app.py` 使用 `RABBITMQ_URL/REDIS_URL`，跟随 `.env` 生效
- 通知服务读取 Telegram：在其容器环境注入 `TELEGRAM_*`，现有实现按环境变量使用

## 安全与合规
- `.env` 含敏感信息，确保 `.gitignore` 屏蔽；日志与错误输出不打印密钥
- Docker Desktop 上 `host.docker.internal` 可用（Mac），若后续迁移到 Linux 主机需要改为宿主 IP

## 验证与报告
- 重启编排后：
  - 读取环境：`docker inspect` 验证容器 Env 是否匹配 `.env`
  - 连接测试：用 `psql` 验证数据库；Redis、RabbitMQ 用 `redis-cli`、管理 UI 检查连接
  - 日志检查：`docker logs` 关键字扫描
- 产出检查报告：配置一致性、服务健康、潜在问题与修正建议

## 执行步骤
1. 更新 `.env` 注入所有变量
2. 调整 `docker-compose.yml` 环境引用与 RabbitMQ 默认账号
3. 重启容器并逐项验证（镜像/容器/日志/连接）
4. 输出结构化检查报告

请确认后我将按该计划修改 `.env` 与 `docker-compose.yml`，并执行验证。