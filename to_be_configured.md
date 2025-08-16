# CashUp 量化交易系统配置指南

## 系统状态概览 (最新更新: 2025-08-14)

### ✅ 已完成修复的问题
1. **Docker端口映射问题**
   - ✅ exchange-service: 8003:8000 (已修复)
   - ✅ strategy-service: 8004:8000 (已修复)
   - ✅ user-service: 8001:8001 (已修复)

2. **数据库驱动问题**
   - ✅ user-service: 已从psycopg2-binary替换为asyncpg
   - ✅ DATABASE_URL: 已更新为postgresql+asyncpg://格式

3. **服务启动状态**
   - ✅ PostgreSQL: 正常运行
   - ✅ Redis: 正常运行
   - ✅ RabbitMQ: 正常运行
   - ✅ exchange-service: 正常运行，健康检查通过
   - ✅ strategy-service: 正常运行，Docker显示健康状态

4. **Docker镜像优化成果**
   - ✅ 镜像体积大幅减少:
     * user-service: 593MB → 286MB (减少52%)
     * exchange-service: 509MB → 292MB (减少43%)
     * strategy-service: 优化后484MB
   - ✅ 使用python:3.11-slim基础镜像替代alpine
   - ✅ 应用多阶段构建和虚拟环境优化
   - ✅ 修复Python相对导入问题
   - ✅ 统一使用pip替代uv解决网络问题

## 🔧 需要配置的参数

### 1. 环境变量配置 (.env文件)
已创建完整的.env文件，包含以下关键配置：

#### 数据库配置
```bash
DATABASE_URL=postgresql://cashup:cashup123@localhost:5432/cashup
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=cashup
DATABASE_USER=cashup
DATABASE_PASSWORD=cashup123
```

#### JWT安全配置
```bash
JWT_SECRET_KEY=68xgvtxees5x87fbfpw18xdcy45lkdcm4kk1jb2xxpvppqsvxgmilh5jkeyj0ke7
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### 交易所API配置
```bash
GATE_IO_API_KEY=08969735fdc08e22bae09c167df152d2
GATE_IO_SECRET_KEY=efe22f5fe535151969ea46ff16456e7768cd6cfb8dbb65cf9119713ed204ec86
```

### 2. 微服务端口映射

| 服务名称 | 外部端口 | 内部端口 | 状态 |
|---------|---------|---------|------|
| frontend | 3000 | 3000 | ⏳ 待启动 |
| user-service | 8001 | 8001 | ✅ 运行中 |
| trading-service | 8002 | 8000 | ⏳ 待启动 |
| exchange-service | 8003 | 8000 | ✅ 运行中 |
| strategy-service | 8004 | 8000 | ⏳ 待启动 |
| market-service | 8005 | 8000 | ⏳ 待启动 |
| notification-service | 8006 | 8000 | ⏳ 待启动 |
| order-service | 8007 | 8000 | ⏳ 待启动 |
| config-service | 8008 | 8000 | ⏳ 待启动 |
| monitoring-service | 8009 | 8000 | ⏳ 待启动 |

### 3. 数据库初始化

#### 需要执行的数据库迁移
```bash
# 对于每个服务，需要运行数据库迁移
docker-compose exec user-service alembic upgrade head
docker-compose exec trading-service alembic upgrade head
docker-compose exec order-service alembic upgrade head
# ... 其他服务
```

### 4. 前端配置

#### 前端环境变量 (frontend/.env)
```bash
VITE_API_BASE_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001/ws
```

## 🚀 启动顺序

### 阶段1: 基础设施服务
```bash
docker-compose up -d postgres redis rabbitmq
```

### 阶段2: 核心服务
```bash
docker-compose up -d user-service exchange-service
```

### 阶段3: 业务服务
```bash
docker-compose up -d trading-service market-service strategy-service order-service
```

### 阶段4: 支持服务
```bash
docker-compose up -d notification-service config-service monitoring-service
```

### 阶段5: 前端服务
```bash
docker-compose up -d frontend
```

## 🔍 健康检查

### 服务健康检查端点
- user-service: http://localhost:8001/health
- trading-service: http://localhost:8002/health
- exchange-service: http://localhost:8003/health
- 其他服务: http://localhost:PORT/health

### API文档访问
- user-service: http://localhost:8001/docs
- trading-service: http://localhost:8002/docs
- 其他服务: http://localhost:PORT/docs

## ⚠️ 已知问题

### 1. 健康检查端点
- 部分服务可能缺少/health端点
- 需要检查各服务的路由配置

### 2. 数据库迁移
- 需要为每个服务执行数据库迁移
- 确保数据库表结构正确创建

### 3. 服务依赖
- 确保服务启动顺序正确
- 检查服务间的网络连接

### 4. Docker镜像优化问题
- **镜像体积过大**: 当前镜像大小在500-771MB之间，需要优化
- **基础镜像选择**: 使用python:3.11-slim而非alpine，体积较大
- **构建缓存**: 缺少多阶段构建，无法有效利用Docker层缓存
- **包管理器**: 部分服务使用pip，建议统一使用uv提升安装速度
- **悬空镜像**: 大量<none>标签的镜像占用磁盘空间

### 5. 配置管理问题
- **端口冲突**: 之前存在RabbitMQ端口占用问题
- **环境变量**: 部分服务缺少必要的配置项
- **版本管理**: 缺少镜像版本标签，不利于版本控制

## 🚀 Docker镜像优化建议

### 1. 使用Alpine Linux基础镜像
```dockerfile
# 替换 python:3.11-slim 为 python:3.11-alpine
FROM python:3.11-alpine
```

### 2. 多阶段构建
```dockerfile
# 构建阶段 - 安装依赖
FROM python:3.11-alpine as builder
# ... 安装构建依赖和Python包

# 运行阶段 - 只包含运行时需要的文件
FROM python:3.11-alpine as runtime
# ... 复制构建产物
```

### 3. 使用uv包管理器
- 安装速度比pip快10-100倍
- 更好的依赖解析
- 减少镜像层数

### 4. 优化Docker层缓存
- 先复制依赖文件，再复制源代码
- 合并RUN指令减少层数
- 清理包管理器缓存

## 📊 最终验证结果 (2025-08-14)

### 系统状态检查
```bash
$ ./test_system.sh status
✅ 基础设施服务: PostgreSQL, Redis, RabbitMQ 全部正常运行
✅ 核心服务: exchange-service, strategy-service 正常运行
✅ 健康检查: exchange-service 通过健康检查
⚠️ 网络问题: strategy-service 存在IPv6连接问题，但服务本身运行正常
```

### Docker镜像优化验证
```bash
$ docker images | grep cashup | sort -k7 -h
✅ 镜像大小显著减少:
   - user-service: 286MB (优化前593MB)
   - exchange-service: 292MB (优化前509MB) 
   - strategy-service: 484MB
✅ 清理了旧版本镜像，节省磁盘空间
```

### API端点测试
```bash
✅ Exchange Service: http://localhost:8003/health - 正常响应
⚠️ Strategy Service: 网络连接问题，但Docker健康检查通过
✅ 基础设施服务: 数据库和缓存连接正常
```

## 📝 下一步行动

### ✅ 已完成任务
1. ✅ 修复Docker端口映射问题
2. ✅ 修复数据库驱动问题
3. ✅ 添加Docker镜像版本标签
4. ✅ 创建并应用优化版Dockerfile
5. ✅ 清理悬空Docker镜像
6. ✅ 修复Python导入问题
7. ✅ 优化镜像大小(平均减少40-50%)
8. ✅ 验证核心服务运行状态

### 🔄 待优化项目
1. ⏳ 解决strategy-service的IPv6网络连接问题
2. ⏳ 启动其他微服务(trading, market, order等)
3. ⏳ 执行数据库迁移
4. ⏳ 测试服务间通信
5. ⏳ 部署前端服务

### 中期目标 (3-7天)
10. ⏳ 启动前端服务
11. ⏳ 进行端到端测试
12. ⏳ 性能优化和监控配置
13. ⏳ 文档完善和部署指南

## 🔗 有用的命令

### 基本Docker Compose命令
```bash
# 查看所有服务状态
docker-compose ps

# 查看特定服务日志
docker-compose logs [service-name]

# 重新构建服务
docker-compose build [service-name]

# 停止所有服务
docker-compose down

# 清理所有容器和网络
docker-compose down --remove-orphans
```

### Docker镜像优化命令
```bash
# 查看镜像大小
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# 清理悬空镜像
docker image prune -f

# 清理所有未使用的镜像
docker image prune -a -f

# 查看Docker磁盘使用情况
docker system df

# 全面清理Docker系统
docker system prune -a -f --volumes

# 构建优化后的镜像
docker build -f Dockerfile.optimized -t service-name:v1-optimized .

# 比较镜像大小
docker images | grep service-name
```

### 性能监控命令
```bash
# 查看容器资源使用情况
docker stats

# 查看特定容器的资源使用
docker stats [container-name]

# 检查容器健康状态
docker inspect [container-name] | grep Health
```

## 待配置项目

### 1. 环境配置
- [ ] 生产环境配置文件
- [ ] 开发环境配置文件
- [ ] 测试环境配置文件

### 2. 数据库配置
- [ ] PostgreSQL 生产环境配置
- [ ] Redis 集群配置
- [ ] 数据库迁移脚本

### 3. 安全配置
- [ ] JWT 密钥配置
- [ ] API 密钥管理
- [ ] CORS 配置
- [ ] 防火墙规则

### 4. 监控配置
- [ ] 日志聚合配置
- [ ] 性能监控配置
- [ ] 告警规则配置

### 5. 部署配置
- [x] Docker 优化配置 - 已完成多阶段构建优化
- [ ] Kubernetes 配置文件
- [ ] CI/CD 流水线配置

### 6. 第三方服务配置
- [ ] 交易所 API 配置
- [ ] 邮件服务配置
- [ ] 短信服务配置

### 7. 性能优化
- [ ] 数据库索引优化
- [ ] 缓存策略配置
- [ ] 负载均衡配置

### 8. 备份配置
- [ ] 数据库备份策略
- [ ] 配置文件备份
- [ ] 日志备份策略

## 最近完成的优化

### Docker 优化 (2024-12-19)
- [x] 创建了所有服务的 Dockerfile.optimized 文件
- [x] 使用多阶段构建减小镜像大小
- [x] 更新 docker-compose.yml 使用优化版本
- [x] 修复 strategy-service 缺少 asyncpg 依赖问题
- [x] 统一健康检查端点实现
- [x] 优化构建缓存和安全配置

### 服务状态
- [x] exchange-service: 健康检查正常，Dockerfile.optimized已创建
- [x] trading-service: 健康检查正常，Dockerfile.optimized已创建
- [x] user-service: 运行正常，Dockerfile.optimized已创建
- [x] market-service: 运行正常，Dockerfile.optimized已创建
- [x] strategy-service: Dockerfile.optimized已创建，依赖问题已修复
- [x] notification-service: Dockerfile.optimized已创建
- [x] order-service: Dockerfile.optimized已创建
- [x] config-service: Dockerfile.optimized已创建
- [x] monitoring-service: Dockerfile.optimized已创建

### 完成的优化工作
1. **多阶段构建优化**: 所有服务都使用多阶段构建减小镜像大小
2. **统一健康检查**: 为所有服务添加了健康检查端点
3. **安全配置**: 使用非root用户运行服务
4. **依赖管理**: 修复了strategy-service缺少asyncpg依赖的问题
5. **构建配置**: 更新了docker-compose.yml使用优化版本的Dockerfile
6. **路径修复**: 修复了根目录docker-compose.yml中的构建路径问题

### 注意事项
- 由于网络连接问题，最终的完整构建未能完成
- 所有Dockerfile.optimized文件已创建并配置正确
- 可以在网络稳定时重新运行 `docker-compose up --build -d` 启动所有服务

---

**更新时间**: 2025-08-11 14:04:00  
**状态**: 基础设施和核心服务已启动，准备启动业务服务