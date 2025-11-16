-- ============================================================================
-- CashUp v2 数据库初始化脚本（根据详细设计方案）
-- 生成时间: $(date '+%Y-%m-%d %H:%M:%S')
-- 方案版本: 1.0
-- ============================================================================

-- 启用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- 1. 用户管理模块
-- ============================================================================

-- 用户表
cREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- API密钥表（敏感信息加密存储）
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exchange VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    key_data TEXT NOT NULL,
    secret_data TEXT NOT NULL,
    passphrase TEXT,
    is_active BOOLEAN DEFAULT true,
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_exchange ON api_keys(exchange, is_active);

-- 用户登录历史
CREATE TABLE IF NOT EXISTS login_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    ip_address INET,
    user_agent TEXT,
    login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN,
    failure_reason VARCHAR(100)
);

CREATE INDEX idx_login_history_user ON login_history(user_id, login_at DESC);
CREATE INDEX idx_login_history_time ON login_history(login_at DESC);

-- ============================================================================
-- 2. 策略管理模块（核心）
-- ============================================================================

-- 因子定义表
CREATE TABLE IF NOT EXISTS strategy_factors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    description TEXT,
    parameters JSONB DEFAULT '{}',
    is_builtin BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_factors_name ON strategy_factors(name);
CREATE INDEX idx_factors_type ON strategy_factors(type, category);
CREATE INDEX idx_factors_builtin ON strategy_factors(is_builtin);

-- 策略模板表
CREATE TABLE IF NOT EXISTS strategy_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50),
    factors JSONB DEFAULT '[]',
    config JSONB DEFAULT '{}',
    code TEXT,
    is_template BOOLEAN DEFAULT true,
    is_builtin BOOLEAN DEFAULT false,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_type ON strategy_templates(strategy_type);
CREATE INDEX idx_templates_builtin ON strategy_templates(is_builtin);
CREATE INDEX idx_templates_created ON strategy_templates(created_by, created_at DESC);

-- 策略实例表（实际运行的策略）
CREATE TABLE IF NOT EXISTS strategy_instances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template_id INTEGER REFERENCES strategy_templates(id),
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10),
    status VARCHAR(20) DEFAULT 'stopped',
    config JSONB DEFAULT '{}',
    position JSONB DEFAULT '{}',
    performance JSONB DEFAULT '{}',
    risk_config JSONB DEFAULT '{}',
    started_at TIMESTAMP,
    stopped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_strategies_user ON strategy_instances(user_id, status);
CREATE INDEX idx_strategies_exchange ON strategy_instances(exchange, symbol);
CREATE INDEX idx_strategies_template ON strategy_instances(template_id);
CREATE INDEX idx_strategies_status ON strategy_instances(status, updated_at DESC);

-- 策略信号记录
CREATE TABLE IF NOT EXISTS strategy_signals (
    id SERIAL PRIMARY KEY,
    strategy_instance_id INTEGER REFERENCES strategy_instances(id) ON DELETE CASCADE,
    signal_type VARCHAR(20),
    signal_data JSONB DEFAULT '{}',
    price DECIMAL(20, 8),
    executed BOOLEAN DEFAULT false,
    executed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signals_strategy ON strategy_signals(strategy_instance_id, created_at DESC);
CREATE INDEX idx_signals_type ON strategy_signals(signal_type, created_at DESC);
CREATE INDEX idx_signals_unexecuted ON strategy_signals(strategy_instance_id, executed) WHERE executed = false;

-- 策略运行日志
CREATE TABLE IF NOT EXISTS strategy_logs (
    id SERIAL PRIMARY KEY,
    strategy_instance_id INTEGER REFERENCES strategy_instances(id) ON DELETE CASCADE,
    level VARCHAR(20),
    message TEXT,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_strategy ON strategy_logs(strategy_instance_id, created_at DESC);
CREATE INDEX idx_logs_level ON strategy_logs(level, created_at DESC);

-- ============================================================================
-- 3. 交易执行模块
-- ============================================================================

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_instance_id INTEGER REFERENCES strategy_instances(id) ON DELETE SET NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    client_order_id VARCHAR(100),
    exchange_order_id VARCHAR(100),
    order_type VARCHAR(20),
    side VARCHAR(10),
    price DECIMAL(20, 8),
    quantity DECIMAL(20, 8),
    filled_quantity DECIMAL(20, 8) DEFAULT 0,
    filled_value DECIMAL(20, 8) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    fee DECIMAL(20, 8) DEFAULT 0,
    fee_currency VARCHAR(10),
    error_message TEXT,
    order_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_user ON orders(user_id, created_at DESC);
CREATE INDEX idx_orders_exchange ON orders(exchange, symbol, status);
CREATE INDEX idx_orders_strategy ON orders(strategy_instance_id);
CREATE INDEX idx_orders_exchange_id ON orders(exchange_order_id);
CREATE INDEX idx_orders_client_id ON orders(client_order_id);

-- 持仓表
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_instance_id INTEGER REFERENCES strategy_instances(id) ON DELETE SET NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10),
    quantity DECIMAL(20, 8) DEFAULT 0,
    entry_price DECIMAL(20, 8) DEFAULT 0,
    mark_price DECIMAL(20, 8) DEFAULT 0,
    liquidation_price DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0,
    realized_pnl DECIMAL(20, 8) DEFAULT 0,
    margin DECIMAL(20, 8) DEFAULT 0,
    leverage DECIMAL(10, 2),
    auto_deleverage BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_positions_user ON positions(user_id, status);
CREATE INDEX idx_positions_exchange ON positions(exchange, symbol, status);
CREATE UNIQUE INDEX idx_positions_unique ON positions(user_id, exchange, symbol, side, status) WHERE status = 'open';

-- 账户余额表
CREATE TABLE IF NOT EXISTS account_balances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exchange VARCHAR(50) NOT NULL,
    asset VARCHAR(10) NOT NULL,
    balance DECIMAL(20, 8) DEFAULT 0,
    available DECIMAL(20, 8) DEFAULT 0,
    locked DECIMAL(20, 8) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_balances_user_asset ON account_balances(user_id, exchange, asset);
CREATE INDEX idx_balances_exchange ON account_balances(exchange, asset);

-- 风控记录表
CREATE TABLE IF NOT EXISTS risk_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_instance_id INTEGER REFERENCES strategy_instances(id) ON DELETE CASCADE,
    event_type VARCHAR(50),
    event_data JSONB,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_user ON risk_events(user_id, created_at DESC);
CREATE INDEX idx_risk_strategy ON risk_events(strategy_instance_id, created_at DESC);

-- ============================================================================
-- 4. 行情数据模块
-- ============================================================================

-- K线数据表
CREATE TABLE IF NOT EXISTS kline_data (
    id BIGSERIAL PRIMARY KEY,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open_time TIMESTAMP NOT NULL,
    open DECIMAL(20, 8),
    high DECIMAL(20, 8),
    low DECIMAL(20, 8),
    close DECIMAL(20, 8),
    volume DECIMAL(20, 8),
    quote_volume DECIMAL(20, 8),
    trade_count INTEGER,
    taker_buy_base DECIMAL(20, 8),
    taker_buy_quote DECIMAL(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_kline_unique ON kline_data(exchange, symbol, timeframe, open_time);
CREATE INDEX idx_kline_query ON kline_data(exchange, symbol, timeframe, open_time DESC);
CREATE INDEX idx_kline_time ON kline_data(open_time DESC);

-- 订单簿数据（快照）
CREATE TABLE IF NOT EXISTS orderbook_snapshots (
    id BIGSERIAL PRIMARY KEY,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    bids JSONB,
    asks JSONB,
    checksum BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orderbook_query ON orderbook_snapshots(exchange, symbol, timestamp DESC);
CREATE INDEX idx_orderbook_time ON orderbook_snapshots(timestamp DESC);

-- 最新成交价
CREATE TABLE IF NOT EXISTS market_trades (
    id BIGSERIAL PRIMARY KEY,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    trade_id VARCHAR(100),
    price DECIMAL(20, 8),
    quantity DECIMAL(20, 8),
    side VARCHAR(10),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_trades_unique ON market_trades(exchange, trade_id) WHERE trade_id IS NOT NULL;
CREATE INDEX idx_trades_query ON market_trades(exchange, symbol, timestamp DESC);
CREATE INDEX idx_trades_time ON market_trades(timestamp DESC);

-- ============================================================================
-- 5. RSS新闻模块（新增）
-- ============================================================================

-- RSS源配置表
CREATE TABLE IF NOT EXISTS rss_feeds (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500) NOT NULL UNIQUE,
    category VARCHAR(50),
    language VARCHAR(10) DEFAULT 'zh-CN',
    is_active BOOLEAN DEFAULT true,
    last_fetch TIMESTAMP,
    fetch_interval INTEGER DEFAULT 300,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rss_active ON rss_feeds(is_active);
CREATE INDEX idx_rss_category ON rss_feeds(category);

-- 市场新闻表
CREATE TABLE IF NOT EXISTS market_news (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(100),
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    url VARCHAR(500) UNIQUE,
    published_at TIMESTAMP,
    category VARCHAR(50),
    tags JSONB DEFAULT '[]',
    sentiment_score FLOAT,
    sentiment_label VARCHAR(20),
    relevance_score FLOAT,
    symbols JSONB DEFAULT '[]',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_news_published ON market_news(published_at DESC);
CREATE INDEX idx_news_symbols ON market_news USING GIN (symbols);
CREATE INDEX idx_news_sentiment ON market_news(sentiment_score);
CREATE INDEX idx_news_query ON market_news(category, published_at DESC);

-- 新闻-价格关联分析
CREATE TABLE IF NOT EXISTS news_price_correlation (
    id BIGSERIAL PRIMARY KEY,
    news_id BIGINT REFERENCES market_news(id) ON DELETE CASCADE,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price_before DECIMAL(20, 8),
    price_after_5m DECIMAL(20, 8),
    price_change_5m DECIMAL(10, 4),
    price_after_15m DECIMAL(20, 8),
    price_change_15m DECIMAL(10, 4),
    price_after_1h DECIMAL(20, 8),
    price_change_1h DECIMAL(10, 4),
    volume_before DECIMAL(20, 8),
    volume_after DECIMAL(20, 8),
    correlation_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_correlation_news ON news_price_correlation(news_id);
CREATE INDEX idx_correlation_symbol ON news_price_correlation(exchange, symbol, created_at DESC);

-- ============================================================================
-- 6. 通知推送模块
-- ============================================================================

-- 通知渠道配置表
CREATE TABLE IF NOT EXISTS notification_channels (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    channel_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_channels_user ON notification_channels(user_id, channel_type);
CREATE INDEX idx_channels_active ON notification_channels(is_active);

-- 通知模板表
CREATE TABLE IF NOT EXISTS notification_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    title_template TEXT,
    content_template TEXT,
    variables JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_event ON notification_templates(event_type);
CREATE INDEX idx_templates_active ON notification_templates(is_active);

-- 通知记录表
CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    channel_id INTEGER REFERENCES notification_channels(id),
    template_id INTEGER REFERENCES notification_templates(id),
    event_type VARCHAR(50),
    title TEXT,
    content TEXT,
    data JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_status ON notifications(status, created_at);
CREATE INDEX idx_notifications_event ON notifications(event_type, created_at DESC);

-- ============================================================================
-- 7. 回测分析模块
-- ============================================================================

-- 回测任务表
CREATE TABLE IF NOT EXISTS backtest_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_instance_id INTEGER REFERENCES strategy_instances(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    config JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    result JSONB,
    performance_metrics JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_backtest_user ON backtest_jobs(user_id, created_at DESC);
CREATE INDEX idx_backtest_strategy ON backtest_jobs(strategy_instance_id);
CREATE INDEX idx_backtest_status ON backtest_jobs(status);

-- 回测交易记录
CREATE TABLE IF NOT EXISTS backtest_trades (
    id BIGSERIAL PRIMARY KEY,
    backtest_job_id INTEGER REFERENCES backtest_jobs(id) ON DELETE CASCADE,
    trade_id VARCHAR(100),
    trade_type VARCHAR(20),
    price DECIMAL(20, 8),
    quantity DECIMAL(20, 8),
    fee DECIMAL(20, 8) DEFAULT 0,
    timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_backtest_trades_job ON backtest_trades(backtest_job_id, timestamp);

-- 回测每日绩效
CREATE TABLE IF NOT EXISTS backtest_daily_pnl (
    id BIGSERIAL PRIMARY KEY,
    backtest_job_id INTEGER REFERENCES backtest_jobs(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    starting_balance DECIMAL(20, 8),
    ending_balance DECIMAL(20, 8),
    daily_pnl DECIMAL(20, 8),
    daily_pnl_rate DECIMAL(10, 4),
    trade_count INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    loss_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_backtest_daily_unique ON backtest_daily_pnl(backtest_job_id, date);
CREATE INDEX idx_backtest_daily_date ON backtest_daily_pnl(date);

-- ============================================================================
-- 8. 系统配置与日志
-- ============================================================================

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_secret BOOLEAN DEFAULT false,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_configs_key ON system_configs(config_key);

-- 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id BIGSERIAL PRIMARY KEY,
    level VARCHAR(20),
    logger VARCHAR(100),
    message TEXT,
    data JSONB,
    trace_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_level ON system_logs(level, created_at DESC);
CREATE INDEX idx_logs_trace ON system_logs(trace_id, created_at);
CREATE INDEX idx_logs_time ON system_logs(created_at DESC);

-- ============================================================================
-- 9. 视图
-- ============================================================================

-- 策略实时绩效视图
CREATE OR REPLACE VIEW strategy_performance AS
SELECT
    si.id AS strategy_id,
    si.name AS strategy_name,
    u.username AS owner,
    si.exchange,
    si.symbol,
    si.status,
    COALESCE(SUM(p.unrealized_pnl + p.realized_pnl), 0) AS total_pnl,
    CASE
        WHEN SUM(p.margin) > 0 THEN SUM(p.unrealized_pnl + p.realized_pnl) / SUM(p.margin) * 100
        ELSE 0
    END AS pnl_rate,
    COUNT(DISTINCT o.id) AS total_trades,
    si.created_at,
    si.started_at
FROM strategy_instances si
JOIN users u ON si.user_id = u.id
LEFT JOIN positions p ON si.id = p.strategy_instance_id AND p.status = 'open'
LEFT JOIN orders o ON si.id = o.strategy_instance_id AND o.status = 'filled'
GROUP BY si.id, u.username;

-- 账户总览视图
CREATE OR REPLACE VIEW account_overview AS
SELECT
    u.id AS user_id,
    u.username,
    ab.exchange,
    SUM(ab.balance) AS total_balance,
    SUM(ab.available) AS total_available,
    SUM(COALESCE(p.unrealized_pnl, 0)) AS total_unrealized_pnl,
    MAX(ab.updated_at) AS last_updated
FROM users u
JOIN account_balances ab ON u.id = ab.user_id
LEFT JOIN positions p ON u.id = p.user_id AND p.status = 'open'
GROUP BY u.id, u.username, ab.exchange;

-- 策略统计视图
CREATE OR REPLACE VIEW strategy_statistics AS
SELECT
    si.id AS strategy_id,
    si.name AS strategy_name,
    si.status,
    COUNT(DISTINCT s.id) AS total_signals,
    COUNT(DISTINCT CASE WHEN s.executed = true THEN s.id END) AS executed_signals,
    COUNT(DISTINCT o.id) AS total_orders,
    COUNT(DISTINCT CASE WHEN o.status = 'filled' THEN o.id END) AS filled_orders,
    COALESCE(SUM(o.filled_value), 0) AS total_volume,
    COALESCE(SUM(o.fee), 0) AS total_fees,
    MAX(o.created_at) AS last_trade_at
FROM strategy_instances si
LEFT JOIN strategy_signals s ON si.id = s.strategy_instance_id
LEFT JOIN orders o ON si.id = o.strategy_instance_id
GROUP BY si.id, si.name, si.status;

-- ============================================================================
-- 10. 触发器与函数
-- ============================================================================

-- 自动更新时间戳函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为用户表添加触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 为API密钥表添加触发器
DROP TRIGGER IF EXISTS update_api_keys_updated_at ON api_keys;
CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 为策略实例表添加触发器
DROP TRIGGER IF EXISTS update_strategy_instances_updated_at ON strategy_instances;
CREATE TRIGGER update_strategy_instances_updated_at BEFORE UPDATE ON strategy_instances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 为策略模板表添加触发器
DROP TRIGGER IF EXISTS update_strategy_templates_updated_at ON strategy_templates;
CREATE TRIGGER update_strategy_templates_updated_at BEFORE UPDATE ON strategy_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 11. 初始数据
-- ============================================================================

-- 插入系统配置
INSERT INTO system_configs (config_key, config_value, description, is_secret) VALUES
('app_name', '"CashUp"', '应用名称', false),
('app_version', '"2.0.0"', '应用版本', false),
('default_timezone', '"Asia/Shanghai"', '默认时区', false),
('default_language', '"zh-CN"', '默认语言', false)
ON CONFLICT (config_key) DO NOTHING;

-- 插入内置因子
INSERT INTO strategy_factors (name, type, category, description, parameters, is_builtin, is_active) VALUES
('rsi', 'technical', 'momentum', 'RSI相对强弱指标', '{"period": 14, "overbought": 70, "oversold": 30}', true, true),
('macd', 'technical', 'momentum', 'MACD指数平滑移动平均线', '{"fast": 12, "slow": 26, "signal": 9}', true, true),
('ma', 'technical', 'trend', '移动平均线', '{"period": 20, "type": "sma"}', true, true),
('ema', 'technical', 'trend', '指数移动平均线', '{"period": 20}', true, true),
('volume', 'technical', 'volume', '成交量', '{"period": 20, "multiplier": 2.0}', true, true)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 初始化完成
-- ============================================================================

SELECT CURRENT_TIMESTAMP as initialized_at, 
       'CashUp v2 database schema initialized successfully' as message;
-- Ensure system_configs table alignment with runtime
CREATE TABLE IF NOT EXISTS system_configs (
    config_key VARCHAR(255) PRIMARY KEY,
    config_value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ensure api_keys unique constraint on (exchange, name)
ALTER TABLE IF EXISTS public.api_keys
    ADD CONSTRAINT api_keys_exchange_name_unique UNIQUE (exchange, name);
