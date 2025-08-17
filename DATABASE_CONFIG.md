# CashUp 数据库配置文档

## 概述

本文档详细说明了 CashUp 量化交易系统中 PostgreSQL 数据库配置不一致的问题，并提供了修复步骤和建议。

## 问题分析

### 1. PostgreSQL 用户配置不一致

系统中存在多个不同的数据库用户配置，导致服务连接失败：

#### 主要配置文件对比：

**根目录 docker-compose.yml:**
```yaml
postgres:
  environment:
    POSTGRES_DB: cashup
    POSTGRES_USER: cashup
    POSTGRES_PASSWORD: cashup123
```

**各服务连接字符串:**
- `postgresql+asyncpg://cashup:cashup123@postgres:5432/cashup`
- `postgresql://cashup:cashup123@postgres:5432/cashup`
- `postgresql+asyncpg://postgres:password@postgres:5432/cashup_db`

### 2. 数据库名称不一致

不同服务使用了不同的数据库名称：
- `cashup` (主数据库)
- `cashup_db` (部分服务)
- `cashup_config` (配置服务)
- `cashup_orders` (订单服务)

### 3. 端口映射问题

部分服务的端口配置与实际监听端口不匹配。

## 需要手动处理的配置项清单

### 1. 数据库用户统一

**推荐配置:**
```yaml
postgres:
  environment:
    POSTGRES_DB: cashup
    POSTGRES_USER: cashup
    POSTGRES_PASSWORD: cashup123
```

**统一连接字符串格式:**
```
postgresql+asyncpg://cashup:cashup123@postgres:5432/cashup
```

### 2. 各服务数据库连接配置对比

| 服务名称 | 当前配置 | 推荐配置 | 状态 |
|---------|---------|---------|------|
| user-service | `postgresql+asyncpg://cashup:cashup123@postgres:5432/cashup` | ✅ 正确 | 正常 |
| trading-service | `postgresql+asyncpg://cashup:cashup123@postgres:5432/cashup` | ✅ 正确 | 正常 |
| exchange-service | `postgresql://cashup:cashup123@postgres:5432/cashup` | ⚠️ 缺少 asyncpg | 需修复 |
| strategy-service | `postgresql://cashup:cashup123@postgres:5432/cashup` | ⚠️ 缺少 asyncpg | 需修复 |
| market-service | `postgresql://cashup:cashup123@postgres:5432/cashup` | ⚠️ 缺少 asyncpg | 需修复 |
| notification-service | `postgresql+asyncpg://cashup:cashup123@postgres:5432/cashup` | ✅ 正确 | 正常 |
| order-service | `postgresql+asyncpg://cashup:cashup123@postgres:5432/cashup` | ✅ 正确 | 正常 |
| config-service | `postgresql+asyncpg://cashup:cashup123@postgres:5432/cashup` | ✅ 正确 | 正常 |
| monitoring-service | `postgresql+asyncpg://cashup:cashup123@postgres:5432/cashup` | ✅ 正确 | 依赖问题 |

### 3. 端口配置对比

| 服务名称 | Docker 端口映射 | 内部端口 | 外部访问端口 | 状态 |
|---------|---------------|---------|-------------|------|
| user-service | `8001:8001` | 8001 | 8001 | ✅ 正确 |
| trading-service | `8002:8000` | 8000 | 8002 | ⚠️ 不一致 |
| exchange-service | `8003:8000` | 8000 | 8003 | ⚠️ 不一致 |
| strategy-service | `8005:8005` | 8005 | 8005 | ✅ 正确 |
| market-service | `8004:8000` | 8000 | 8004 | ⚠️ 不一致 |
| notification-service | `8006:8000` | 8000 | 8006 | ⚠️ 不一致 |
| order-service | `8007:8000` | 8000 | 8007 | ⚠️ 不一致 |
| config-service | `8008:8000` | 8000 | 8008 | ⚠️ 不一致 |
| monitoring-service | `8009:8000` | 8000 | 8009 | ⚠️ 不一致 |

## 修复步骤

### 步骤 1: 统一数据库连接配置

1. **更新 docker-compose.yml 中的环境变量:**
   ```bash
   # 确保所有服务使用统一的数据库连接字符串
   DATABASE_URL=postgresql+asyncpg://cashup:cashup123@postgres:5432/cashup
   ```

2. **修复缺少 asyncpg 的服务:**
   - exchange-service
   - strategy-service
   - market-service

### 步骤 2: 修复端口配置不一致

**选项 A: 统一内部端口为 8000**
```yaml
# 修改各服务的启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**选项 B: 统一外部端口映射**
```yaml
# 修改 docker-compose.yml 端口映射
user-service:
  ports:
    - "8001:8000"  # 统一内部端口为 8000
```

### 步骤 3: 修复依赖问题

1. **monitoring-service 缺少 asyncpg 依赖:**
   ```bash
   # 在 pyproject.toml 中添加
   "asyncpg==0.29.0"
   ```

2. **重新构建有问题的服务:**
   ```bash
   docker-compose build monitoring-service strategy-service
   docker-compose up -d monitoring-service strategy-service
   ```

### 步骤 4: 验证修复

1. **检查所有服务状态:**
   ```bash
   docker-compose ps
   ```

2. **测试健康检查端点:**
   ```bash
   curl http://localhost:8001/health  # user-service
   curl http://localhost:8002/health  # trading-service
   curl http://localhost:8003/health  # exchange-service
   # ... 其他服务
   ```

3. **查看服务日志:**
   ```bash
   docker-compose logs -f [service-name]
   ```

## 建议的最终配置

### 统一的环境变量配置
```yaml
environment:
  - DATABASE_URL=postgresql+asyncpg://cashup:cashup123@postgres:5432/cashup
  - REDIS_URL=redis://redis:6379
  - RABBITMQ_URL=amqp://cashup:cashup123@rabbitmq:5672
```

### 统一的端口配置
```yaml
# 推荐：所有服务内部使用 8000 端口，外部端口按服务区分
ports:
  - "800X:8000"  # X 为服务编号
```

### 统一的健康检查配置
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## 注意事项

1. **数据库初始化:** 确保 PostgreSQL 容器完全启动后再启动应用服务
2. **依赖顺序:** 遵循 depends_on 配置的启动顺序
3. **网络配置:** 确保所有服务在同一个 Docker 网络中
4. **环境变量:** 敏感信息应使用 .env 文件管理
5. **日志监控:** 定期检查服务日志，及时发现问题

## 故障排除

### 常见错误及解决方案

1. **"No module named 'asyncpg'"**
   - 解决方案: 在 pyproject.toml 中添加 asyncpg 依赖

2. **"Connection refused"**
   - 解决方案: 检查数据库服务是否启动，网络配置是否正确

3. **"Authentication failed"**
   - 解决方案: 检查用户名密码配置是否一致

4. **"Port already in use"**
   - 解决方案: 检查端口冲突，停止占用端口的进程

---

**文档版本:** 1.0  
**更新时间:** 2025-01-20  
**维护者:** CashUp 开发团队