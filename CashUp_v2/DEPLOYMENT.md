# CashUp v2 部署文档

## 📋 目录

- [系统要求](#系统要求)
- [架构概述](#架构概述)
- [部署准备](#部署准备)
- [数据库初始化](#数据库初始化)
- [服务部署](#服务部署)
- [前端部署](#前端部署)
- [配置管理](#配置管理)
- [启动和验证](#启动和验证)
- [监控和维护](#监控和维护)
- [故障排除](#故障排除)

## 🖥️ 系统要求

### 最低配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 20GB 可用空间
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+

### 推荐配置
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 50GB SSD
- **操作系统**: Ubuntu 22.04 LTS
- **网络**: 稳定的互联网连接

### 软件依赖
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.20+
- **Python**: 3.12+
- **Node.js**: 18+
- **PostgreSQL**: 15+
- **Redis**: 7+

## 🏗️ 架构概述

CashUp v2 采用模块化单体架构，包含4个核心服务 + Nginx反向代理：

```
CashUp v2/
├── core-service/           # 核心服务 (8001)
│   ├── 用户认证
│   ├── 配置管理
│   └── 数据库访问
├── trading-engine/         # 交易引擎 (8002)
│   ├── 交易所适配器
│   ├── 订单管理
│   └── 执行引擎
├── strategy-platform/      # 策略平台 (8003)
│   ├── 策略管理
│   ├── 回测引擎
│   └── 监控告警
├── notification-service/   # 通知服务 (8004)
│   ├── 通知渠道
│   └── 消息模板
├── frontend/              # 前端应用 (3000)
│   ├── React应用
│   └── 静态资源
└── nginx/                 # Nginx反向代理 (80/443)
    ├── 负载均衡
    ├── SSL终端
    ├── 静态文件服务
    └── API路由
```

## 📦 部署准备

### 1. 环境准备

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget git build-essential

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 安装Python和UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. 项目克隆

```bash
# 克隆项目
git clone https://github.com/your-username/CashUp.git
cd CashUp/CashUp_v2

# 创建必要的目录
mkdir -p logs data backups strategies/templates strategies/examples strategies/custom
```

### 3. 环境变量配置

```bash
# 创建环境变量文件
cp .env.example .env

# 编辑环境变量
nano .env
```

`.env` 文件内容：
```bash
# 数据库配置
DATABASE_URL=postgresql://cashup:cashup_password@localhost:5432/cashup
REDIS_URL=redis://localhost:6379

# JWT配置
JWT_SECRET=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# 服务配置
CORE_SERVICE_PORT=8001
TRADING_ENGINE_PORT=8002
STRATEGY_PLATFORM_PORT=8003
NOTIFICATION_SERVICE_PORT=8004
FRONTEND_PORT=3000

# 交易所API密钥
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
GATEIO_API_KEY=your_gateio_api_key
GATEIO_API_SECRET=your_gateio_api_secret

# 通知配置
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_email_password
```

## 🗄️ 数据库初始化

### 1. PostgreSQL 安装和配置

```bash
# 安装PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 启动PostgreSQL服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库用户
sudo -u postgres psql -c "CREATE USER cashup WITH PASSWORD 'cashup_password';"
sudo -u postgres psql -c "CREATE DATABASE cashup OWNER cashup;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cashup TO cashup;"
sudo -u postgres psql -c "ALTER USER cashup CREATEDB;"

# 创建扩展
sudo -u postgres psql -d cashup -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
sudo -u postgres psql -d cashup -c "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";"
sudo -u postgres psql -d cashup -c "CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";"
```

### 2. Redis 安装和配置

```bash
# 安装Redis
sudo apt install -y redis-server

# 配置Redis
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup
sudo tee /etc/redis/redis.conf > /dev/null <<EOF
bind 127.0.0.1
port 6379
protected-mode yes
timeout 0
tcp-keepalive 300
daemonize yes
supervised systemd
loglevel notice
databases 16
always-show-logo yes
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5
repl-ping-replica-period 10
repl-timeout 60
repl-disable-tcp-nodelay no
repl-backlog-size 1mb
repl-backlog-ttl 3600
maxmemory-policy allkeys-lru
lazyfree-lazy-eviction no
lazyfree-lazy-expire no
lazyfree-lazy-server-del no
lazyfree-lazy-replica-flush no
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes
lua-time-limit 5000
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 0
notify-keyspace-events ""
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
EOF

# 启动Redis服务
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 3. 数据库表结构初始化

创建数据库初始化脚本 `scripts/init_database.sql`：

```sql
-- CashUp v2 数据库初始化脚本

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    avatar TEXT,
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    language VARCHAR(10) DEFAULT 'zh-CN',
    theme VARCHAR(10) DEFAULT 'light',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户配置表
CREATE TABLE IF NOT EXISTS user_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    notifications JSONB DEFAULT '{}',
    security JSONB DEFAULT '{}',
    trading JSONB DEFAULT '{}',
    api JSONB DEFAULT '{}',
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 策略表
CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    code TEXT NOT NULL,
    config JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    is_public BOOLEAN DEFAULT false,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 回测表
CREATE TABLE IF NOT EXISTS backtests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    initial_capital DECIMAL(15,2) NOT NULL,
    final_capital DECIMAL(15,2),
    total_return DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    win_rate DECIMAL(10,4),
    profit_factor DECIMAL(10,4),
    trades_count INTEGER DEFAULT 0,
    config JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 回测交易记录表
CREATE TABLE IF NOT EXISTS backtest_trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_id UUID REFERENCES backtests(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    type VARCHAR(20) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,8) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    fee DECIMAL(15,8) DEFAULT 0,
    pnl DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'filled',
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 交易所配置表
CREATE TABLE IF NOT EXISTS exchange_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL,
    api_key TEXT NOT NULL,
    api_secret TEXT NOT NULL,
    passphrase TEXT,
    enabled BOOLEAN DEFAULT true,
    testnet BOOLEAN DEFAULT false,
    rate_limits JSONB DEFAULT '{}',
    features JSONB DEFAULT '{}',
    last_sync TIMESTAMP,
    status VARCHAR(20) DEFAULT 'disconnected',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES strategies(id) ON DELETE SET NULL,
    exchange_config_id UUID REFERENCES exchange_configs(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    type VARCHAR(20) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,8),
    amount DECIMAL(15,2) NOT NULL,
    fee DECIMAL(15,8) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    exchange_order_id VARCHAR(100),
    filled_quantity DECIMAL(15,8) DEFAULT 0,
    filled_price DECIMAL(15,8),
    leverage INTEGER DEFAULT 1,
    stop_loss DECIMAL(15,8),
    take_profit DECIMAL(15,8),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 持仓表
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES strategies(id) ON DELETE SET NULL,
    exchange_config_id UUID REFERENCES exchange_configs(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    entry_price DECIMAL(15,8) NOT NULL,
    current_price DECIMAL(15,8),
    unrealized_pnl DECIMAL(15,2) DEFAULT 0,
    realized_pnl DECIMAL(15,2) DEFAULT 0,
    margin DECIMAL(15,2) NOT NULL,
    leverage INTEGER DEFAULT 1,
    liquidation_price DECIMAL(15,8),
    status VARCHAR(20) DEFAULT 'open',
    open_time TIMESTAMP NOT NULL,
    close_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 交易记录表
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES strategies(id) ON DELETE SET NULL,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    exchange_config_id UUID REFERENCES exchange_configs(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,8) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    fee DECIMAL(15,8) DEFAULT 0,
    pnl DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'completed',
    exchange_trade_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 市场数据表
CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(15,8) NOT NULL,
    high DECIMAL(15,8) NOT NULL,
    low DECIMAL(15,8) NOT NULL,
    close DECIMAL(15,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    quote_volume DECIMAL(20,2) DEFAULT 0,
    trades_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_market_data UNIQUE (symbol, timeframe, timestamp)
);

-- 通知表
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    channel VARCHAR(20) DEFAULT 'web',
    read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP
);

-- API密钥表
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    key VARCHAR(100) UNIQUE NOT NULL,
    secret VARCHAR(100) NOT NULL,
    permissions TEXT[] DEFAULT '{}',
    ip_whitelist TEXT[] DEFAULT '{}',
    rate_limit INTEGER DEFAULT 1000,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Webhook配置表
CREATE TABLE IF NOT EXISTS webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500) NOT NULL,
    events TEXT[] NOT NULL,
    headers JSONB DEFAULT '{}',
    retries INTEGER DEFAULT 3,
    timeout INTEGER DEFAULT 30,
    active BOOLEAN DEFAULT true,
    last_triggered TIMESTAMP,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户活动日志表
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(20) DEFAULT 'success',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据备份表
CREATE TABLE IF NOT EXISTS data_backups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL,
    size BIGINT,
    status VARCHAR(20) DEFAULT 'pending',
    file_path TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);
CREATE INDEX IF NOT EXISTS idx_backtests_user_id ON backtests(user_id);
CREATE INDEX IF NOT EXISTS idx_backtests_strategy_id ON backtests(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtests_status ON backtests(status);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_user_id ON positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timeframe ON market_data(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建更新时间触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_configs_updated_at BEFORE UPDATE ON user_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON strategies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_backtests_updated_at BEFORE UPDATE ON backtests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 4. 执行数据库初始化

```bash
# 创建数据库初始化脚本目录
mkdir -p scripts

# 执行数据库初始化
sudo -u postgres psql -d cashup -f scripts/init_database.sql

# 验证表是否创建成功
sudo -u postgres psql -d cashup -c "\dt"
```

## 🚀 服务部署

### 1. 创建Docker Compose配置

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: cashup
      POSTGRES_USER: cashup
      POSTGRES_PASSWORD: cashup_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_database.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - cashup-network
    restart: unless-stopped

  # Redis缓存
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
      - ./redis.conf:/etc/redis/redis.conf
    ports:
      - "6379:6379"
    networks:
      - cashup-network
    restart: unless-stopped
    command: redis-server /etc/redis/redis.conf

  # 核心服务
  core-service:
    build:
      context: ./core-service
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://cashup:cashup_password@postgres:5432/cashup
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - CORE_SERVICE_PORT=8001
    ports:
      - "8001:8001"
    depends_on:
      - postgres
      - redis
    networks:
      - cashup-network
    volumes:
      - ./logs:/app/logs
      - ./configs:/app/configs
    restart: unless-stopped

  # 交易引擎
  trading-engine:
    build:
      context: ./trading-engine
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://cashup:cashup_password@postgres:5432/cashup
      - REDIS_URL=redis://redis:6379
      - CORE_SERVICE_URL=http://core-service:8001
      - TRADING_ENGINE_PORT=8002
    ports:
      - "8002:8002"
    depends_on:
      - postgres
      - redis
      - core-service
    networks:
      - cashup-network
    volumes:
      - ./logs:/app/logs
      - ./configs:/app/configs
    restart: unless-stopped

  # 策略平台
  strategy-platform:
    build:
      context: ./strategy-platform
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://cashup:cashup_password@postgres:5432/cashup
      - REDIS_URL=redis://redis:6379
      - CORE_SERVICE_URL=http://core-service:8001
      - TRADING_ENGINE_URL=http://trading-engine:8002
      - STRATEGY_PLATFORM_PORT=8003
    ports:
      - "8003:8003"
    depends_on:
      - postgres
      - redis
      - core-service
      - trading-engine
    networks:
      - cashup-network
    volumes:
      - ./logs:/app/logs
      - ./configs:/app/configs
      - ./strategies:/app/strategies
    restart: unless-stopped

  # 通知服务
  notification-service:
    build:
      context: ./notification-service
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://cashup:cashup_password@postgres:5432/cashup
      - REDIS_URL=redis://redis:6379
      - NOTIFICATION_SERVICE_PORT=8004
    ports:
      - "8004:8004"
    depends_on:
      - postgres
      - redis
    networks:
      - cashup-network
    volumes:
      - ./logs:/app/logs
      - ./configs:/app/configs
    restart: unless-stopped

  # 前端应用
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - REACT_APP_API_URL=http://localhost:8001
      - REACT_APP_WS_URL=ws://localhost:8002
    ports:
      - "3000:3000"
    depends_on:
      - core-service
      - trading-engine
      - strategy-platform
    networks:
      - cashup-network
    restart: unless-stopped

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: cashup_nginx
    volumes:
      - ./frontend/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - frontend
      - core-service
      - trading-engine
      - strategy-platform
      - notification-service
    networks:
      - cashup-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  cashup-network:
    driver: bridge
```

### 2. 创建Nginx配置

创建 `nginx.conf` 文件：

```nginx
events {
    worker_connections 1024;
}

http {
    upstream core_service {
        server core-service:8001;
    }

    upstream trading_engine {
        server trading-engine:8002;
    }

    upstream strategy_platform {
        server strategy-platform:8003;
    }

    upstream notification_service {
        server notification-service:8004;
    }

    upstream frontend {
        server frontend:3000;
    }

    # 基本配置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # MIME类型
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate max-age=0 auth;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # HTTP服务器
    server {
        listen 80;
        server_name localhost;

        # 重定向到HTTPS（生产环境）
        # return 301 https://$server_name$request_uri;

        # 开发环境直接代理
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API代理
        location /api/core/ {
            proxy_pass http://core_service/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/trading/ {
            proxy_pass http://trading_engine/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/strategy/ {
            proxy_pass http://strategy_platform/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/notification/ {
            proxy_pass http://notification_service/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket代理
        location /ws/ {
            proxy_pass http://trading_engine;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 静态文件缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # HTTPS服务器（生产环境）
    # server {
    #     listen 443 ssl http2;
    #     server_name localhost;
    #
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #
    #     ssl_session_cache shared:SSL:1m;
    #     ssl_session_timeout 5m;
    #     ssl_ciphers HIGH:!aNULL:!MD5;
    #     ssl_prefer_server_ciphers on;
    #
    #     location / {
    #         proxy_pass http://frontend;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Real-IP $remote_addr;
    #         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #         proxy_set_header X-Forwarded-Proto $scheme;
    #     }
    #
    #     # 其他location配置与HTTP服务器相同
    # }
}
```

### 3. 创建各服务的Dockerfile

**core-service/Dockerfile**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY pyproject.toml .
COPY uv.lock .

# 安装Python依赖
RUN pip install uv
RUN uv sync --frozen

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["uv", "run", "python", "main.py"]
```

**trading-engine/Dockerfile**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY pyproject.toml .
COPY uv.lock .

# 安装Python依赖
RUN pip install uv
RUN uv sync --frozen

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8002

# 启动命令
CMD ["uv", "run", "python", "main.py"]
```

**strategy-platform/Dockerfile**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY pyproject.toml .
COPY uv.lock .

# 安装Python依赖
RUN pip install uv
RUN uv sync --frozen

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8003

# 启动命令
CMD ["uv", "run", "python", "main.py"]
```

**notification-service/Dockerfile**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY pyproject.toml .
COPY uv.lock .

# 安装Python依赖
RUN pip install uv
RUN uv sync --frozen

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8004

# 启动命令
CMD ["uv", "run", "python", "main.py"]
```

**frontend/Dockerfile**:
```dockerfile
FROM node:18-alpine

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 使用nginx提供静态文件
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 3000

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
```

### 4. 创建启动脚本

创建 `scripts/start.sh`:
```bash
#!/bin/bash

# CashUp v2 启动脚本

set -e

echo "🚀 启动 CashUp v2..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查Docker Compose是否可用
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Docker Compose未安装"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs data backups strategies/templates strategies/examples strategies/custom ssl

# 设置权限
chmod +x scripts/*.sh

# 加载环境变量
if [ -f .env ]; then
    echo "🔧 加载环境变量..."
    export $(cat .env | xargs)
fi

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose down

# 构建并启动服务
echo "🏗️ 构建服务镜像..."
docker-compose build --no-cache

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 运行健康检查
echo "🏥 运行健康检查..."
./scripts/health-check.sh

echo "✅ CashUp v2 启动完成！"
echo "🌐 前端地址: http://localhost:3000"
echo "📚 API文档: http://localhost:8001/docs"
echo "📊 系统状态: http://localhost:8001/health"
```

创建 `scripts/stop.sh`:
```bash
#!/bin/bash

# CashUp v2 停止脚本

set -e

echo "🛑 停止 CashUp v2..."

# 停止所有服务
docker-compose down

# 可选：清理volumes（取消注释以清理数据）
# docker-compose down -v

echo "✅ CashUp v2 已停止"
```

创建 `scripts/health-check.sh`:
```bash
#!/bin/bash

# CashUp v2 健康检查脚本

set -e

echo "🏥 执行健康检查..."

# 检查核心服务
echo "📡 检查核心服务..."
curl -f http://localhost:8001/health || echo "❌ 核心服务不可用"

# 检查交易引擎
echo "📈 检查交易引擎..."
curl -f http://localhost:8002/health || echo "❌ 交易引擎不可用"

# 检查策略平台
echo "🎯 检查策略平台..."
curl -f http://localhost:8003/health || echo "❌ 策略平台不可用"

# 检查通知服务
echo "📧 检查通知服务..."
curl -f http://localhost:8004/health || echo "❌ 通知服务不可用"

# 检查前端
echo "🌐 检查前端..."
curl -f http://localhost:3000 || echo "❌ 前端不可用"

echo "✅ 健康检查完成"
```

### 5. 创建备份脚本

创建 `scripts/backup.sh`:
```bash
#!/bin/bash

# CashUp v2 备份脚本

set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="cashup_backup_$DATE"

echo "💾 开始备份 CashUp v2..."

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
echo "🗄️ 备份数据库..."
docker-compose exec postgres pg_dump -U cashup cashup > $BACKUP_DIR/${BACKUP_NAME}_database.sql

# 备份Redis数据
echo "🔴 备份Redis数据..."
docker-compose exec redis redis-cli --rdb $BACKUP_DIR/${BACKUP_NAME}_redis.rdb

# 备份配置文件
echo "⚙️ 备份配置文件..."
tar -czf $BACKUP_DIR/${BACKUP_NAME}_configs.tar.gz configs/ .env

# 备份策略文件
echo "📜 备份策略文件..."
tar -czf $BACKUP_DIR/${BACKUP_NAME}_strategies.tar.gz strategies/

# 压缩所有备份
echo "📦 压缩备份文件..."
tar -czf $BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz \
    $BACKUP_DIR/${BACKUP_NAME}_database.sql \
    $BACKUP_DIR/${BACKUP_NAME}_redis.rdb \
    $BACKUP_DIR/${BACKUP_NAME}_configs.tar.gz \
    $BACKUP_DIR/${BACKUP_NAME}_strategies.tar.gz

# 清理临时文件
rm $BACKUP_DIR/${BACKUP_NAME}_database.sql \
   $BACKUP_DIR/${BACKUP_NAME}_redis.rdb \
   $BACKUP_DIR/${BACKUP_NAME}_configs.tar.gz \
   $BACKUP_DIR/${BACKUP_NAME}_strategies.tar.gz

echo "✅ 备份完成: $BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz"
```

## ⚙️ 配置管理

### 1. 服务配置文件

**configs/database.yaml**:
```yaml
database:
  url: "${DATABASE_URL}"
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600

redis:
  url: "${REDIS_URL}"
  max_connections: 50
  timeout: 5
  retry_on_timeout: true

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/app.log"
  max_size: "100MB"
  backup_count: 5
```

**configs/exchanges.yaml**:
```yaml
exchanges:
  binance:
    name: "Binance"
    type: "binance"
    api_key: "${BINANCE_API_KEY}"
    api_secret: "${BINANCE_API_SECRET}"
    testnet: false
    rate_limits:
      requests: 1200
      window: "1m"
    features:
      spot: true
      margin: true
      futures: true
      trading_bot: true
  
  gateio:
    name: "Gate.io"
    type: "gateio"
    api_key: "${GATEIO_API_KEY}"
    api_secret: "${GATEIO_API_SECRET}"
    testnet: false
    rate_limits:
      requests: 100
      window: "1s"
    features:
      spot: true
      margin: true
      futures: false
      trading_bot: true
```

**configs/notifications.yaml**:
```yaml
email:
  host: "${EMAIL_HOST}"
  port: ${EMAIL_PORT}
  username: "${EMAIL_USER}"
  password: "${EMAIL_PASSWORD}"
  use_tls: true

templates:
  trade_completed:
    subject: "交易完成通知"
    body: "您的交易已成功完成"
  
  risk_alert:
    subject: "风险提醒"
    body: "检测到风险事件，请及时处理"
  
  system_error:
    subject: "系统错误"
    body: "系统发生错误，请联系管理员"
```

### 2. 策略模板

**strategies/templates/ma_cross.py**:
```python
"""
移动平均交叉策略模板
"""
import numpy as np
from typing import Dict, List, Any

class MACrossStrategy:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fast_period = config.get('fast_period', 10)
        self.slow_period = config.get('slow_period', 30)
        self.symbol = config.get('symbol', 'BTCUSDT')
        
    def calculate_signals(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """计算交易信号"""
        signals = []
        
        if len(data) < self.slow_period:
            return signals
            
        # 计算移动平均线
        closes = [float(d['close']) for d in data]
        fast_ma = np.mean(closes[-self.fast_period:])
        slow_ma = np.mean(closes[-self.slow_period:])
        
        # 生成信号
        if fast_ma > slow_ma:
            signals.append({
                'symbol': self.symbol,
                'side': 'buy',
                'type': 'market',
                'quantity': self.config.get('quantity', 0.001),
                'reason': 'Golden cross'
            })
        elif fast_ma < slow_ma:
            signals.append({
                'symbol': self.symbol,
                'side': 'sell',
                'type': 'market',
                'quantity': self.config.get('quantity', 0.001),
                'reason': 'Death cross'
            })
            
        return signals
    
    def on_tick(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理实时数据"""
        # 实现tick数据处理逻辑
        return []
    
    def on_order_update(self, order: Dict[str, Any]) -> None:
        """处理订单更新"""
        # 实现订单更新逻辑
        pass
```

## 🚀 启动和验证

### 1. 启动服务

```bash
# 设置脚本权限
chmod +x scripts/*.sh

# 启动所有服务
./scripts/start.sh
```

### 2. 验证服务状态

```bash
# 检查容器状态
docker-compose ps

# 查看服务日志
docker-compose logs -f core-service
docker-compose logs -f trading-engine
docker-compose logs -f strategy-platform
docker-compose logs -f notification-service
docker-compose logs -f frontend

# 运行健康检查
./scripts/health-check.sh
```

### 3. 功能验证

**API端点验证：**
```bash
# 核心服务健康检查
curl http://localhost:8001/health

# 交易引擎健康检查
curl http://localhost:8002/health

# 策略平台健康检查
curl http://localhost:8003/health

# 通知服务健康检查
curl http://localhost:8004/health

# API文档访问
open http://localhost:8001/docs
```

**前端验证：**
```bash
# 访问前端应用
open http://localhost:3000

# 验证主要功能：
# 1. 用户注册/登录
# 2. 策略管理
# 3. 回测功能
# 4. 实时交易
# 5. 数据分析
# 6. 用户设置
```

### 4. 数据库验证

```bash
# 连接到数据库
sudo -u postgres psql -d cashup

# 验证表结构
\dt

# 验证数据
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM strategies;
SELECT COUNT(*) FROM orders;
```

## 📊 监控和维护

### 1. 系统监控

创建 `scripts/monitor.sh`:
```bash
#!/bin/bash

# CashUp v2 监控脚本

set -e

echo "📊 系统监控..."

# 检查服务状态
echo "🔍 服务状态:"
docker-compose ps

# 检查资源使用
echo "💾 资源使用:"
docker stats --no-stream

# 检查日志错误
echo "❌ 错误日志:"
docker-compose logs --tail=100 | grep -i error

# 检查数据库连接
echo "🗄️ 数据库连接:"
docker-compose exec postgres pg_isready

# 检查Redis连接
echo "🔴 Redis连接:"
docker-compose exec redis redis-cli ping
```

### 2. 日志管理

创建 `scripts/logs.sh`:
```bash
#!/bin/bash

# CashUp v2 日志管理脚本

set -e

LOG_DIR="./logs"

echo "📋 日志管理..."

# 清理旧日志
echo "🧹 清理30天前的日志..."
find $LOG_DIR -name "*.log" -mtime +30 -delete

# 压缩日志
echo "📦 压缩日志文件..."
find $LOG_DIR -name "*.log" -mtime +1 -exec gzip {} \;

# 查看日志大小
echo "📏 日志文件大小:"
du -sh $LOG_DIR/*

# 查看最新日志
echo "📄 最新日志:"
tail -n 50 $LOG_DIR/core-service.log
```

### 3. 性能优化

**数据库优化：**
```sql
-- 定期清理过期数据
DELETE FROM system_logs WHERE created_at < NOW() - INTERVAL '30 days';
DELETE FROM user_activity_logs WHERE created_at < NOW() - INTERVAL '90 days';

-- 更新统计信息
ANALYZE;

-- 重建索引
REINDEX DATABASE cashup;
```

**Redis优化：**
```bash
# 设置内存策略
docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 清理过期键
docker-compose exec redis redis-cli --scan --pattern "*" | xargs redis-cli DEL
```

### 4. 定期维护

创建 `scripts/maintenance.sh`:
```bash
#!/bin/bash

# CashUp v2 维护脚本

set -e

echo "🔧 执行定期维护..."

# 备份数据
echo "💾 备份数据..."
./scripts/backup.sh

# 清理日志
echo "🧹 清理日志..."
./scripts/logs.sh

# 更新依赖
echo "📦 更新依赖..."
docker-compose pull
docker-compose build --no-cache

# 重启服务
echo "🔄 重启服务..."
docker-compose restart

echo "✅ 维护完成"
```

## 🚨 故障排除

### 1. 常见问题

**服务启动失败：**
```bash
# 查看具体错误
docker-compose logs [service_name]

# 检查端口占用
netstat -tulpn | grep :8001
netstat -tulpn | grep :5432

# 检查磁盘空间
df -h
```

**数据库连接问题：**
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 重启PostgreSQL
sudo systemctl restart postgresql

# 检查连接数
sudo -u postgres psql -d cashup -c "SELECT count(*) FROM pg_stat_activity;"
```

**Redis连接问题：**
```bash
# 检查Redis状态
sudo systemctl status redis-server

# 重启Redis
sudo systemctl restart redis-server

# 检查内存使用
docker-compose exec redis redis-cli INFO memory
```

### 2. 性能问题

**高CPU使用：**
```bash
# 查看CPU使用情况
docker stats

# 查看进程详情
docker top [container_name]

# 重启服务
docker-compose restart [service_name]
```

**内存泄漏：**
```bash
# 查看内存使用
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# 重启服务
docker-compose restart

# 增加内存限制
# 编辑docker-compose.yml，添加mem_limit配置
```

### 3. 数据恢复

**从备份恢复：**
```bash
# 停止服务
docker-compose down

# 恢复数据库
docker-compose run --rm postgres psql -U cashup -d cashup < backups/backup_file.sql

# 恢复Redis
docker-compose run --rm redis redis-cli --rdb /path/to/backup.rdb

# 启动服务
docker-compose up -d
```

### 4. 紧急恢复

**完整系统恢复：**
```bash
# 停止所有服务
docker-compose down -v

# 重新初始化数据库
sudo -u postgres psql -c "DROP DATABASE cashup;"
sudo -u postgres psql -c "CREATE DATABASE cashup OWNER cashup;"
sudo -u postgres psql -d cashup -f scripts/init_database.sql

# 从备份恢复数据
tar -xzf backups/complete_backup.tar.gz -C /tmp/
sudo -u postgres psql -d cashup < /tmp/database_backup.sql

# 重新启动服务
docker-compose up -d
```

## 📈 扩展部署

### 1. 生产环境部署

**使用HTTPS：**
```bash
# 生成SSL证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem

# 更新nginx.conf启用HTTPS
# 取消HTTPS server块的注释
```

**使用环境变量：**
```bash
# 生产环境.env文件
echo "ENVIRONMENT=production" >> .env
echo "DEBUG=false" >> .env
echo "LOG_LEVEL=WARNING" >> .env
```

**使用负载均衡：**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    image: cashup:latest
    deploy:
      replicas: 3
    environment:
      - ENVIRONMENT=production
```

### 2. 云平台部署

**Docker Swarm部署：**
```bash
# 初始化Swarm
docker swarm init

# 部署栈
docker stack deploy -c docker-compose.yml cashup
```

**Kubernetes部署：**
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cashup
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cashup
  template:
    metadata:
      labels:
        app: cashup
    spec:
      containers:
      - name: cashup
        image: cashup:latest
        ports:
        - containerPort: 8001
```

### 3. 监控和告警

**Prometheus监控：**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cashup'
    static_configs:
      - targets: ['localhost:8001', 'localhost:8002', 'localhost:8003']
```

**Grafana仪表板：**
```json
{
  "dashboard": {
    "title": "CashUp监控",
    "panels": [
      {
        "title": "服务状态",
        "type": "stat",
        "targets": [{"expr": "up{job='cashup'}"}]
      }
    ]
  }
}
```

## 📝 总结

本部署文档提供了CashUp v2的完整部署指南，包括：

1. ✅ **系统要求** - 详细的硬件和软件要求
2. ✅ **数据库初始化** - PostgreSQL和Redis的完整配置
3. ✅ **服务部署** - Docker容器化部署方案
4. ✅ **配置管理** - 环境变量和配置文件管理
5. ✅ **启动验证** - 完整的启动和验证流程
6. ✅ **监控维护** - 系统监控和维护脚本
7. ✅ **故障排除** - 常见问题和解决方案
8. ✅ **扩展部署** - 生产环境和云平台部署

按照此文档操作，您应该能够成功部署和运行CashUp v2量化交易系统。如有问题，请参考故障排除部分或查看日志文件获取更多信息。