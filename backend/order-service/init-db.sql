-- CashUp订单服务数据库初始化脚本

-- 创建数据库（如果不存在）
-- 注意：在Docker环境中，数据库已通过环境变量创建

-- 设置时区
SET timezone = 'UTC';

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- 创建自定义类型（枚举）
DO $$ 
BEGIN
    -- 订单状态枚举
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_status') THEN
        CREATE TYPE order_status AS ENUM (
            'PENDING',
            'SUBMITTED',
            'PARTIALLY_FILLED',
            'FILLED',
            'CANCELLED',
            'REJECTED',
            'EXPIRED',
            'FAILED'
        );
    END IF;
    
    -- 订单类型枚举
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_type') THEN
        CREATE TYPE order_type AS ENUM (
            'MARKET',
            'LIMIT',
            'STOP',
            'STOP_LIMIT',
            'TRAILING_STOP'
        );
    END IF;
    
    -- 订单方向枚举
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_side') THEN
        CREATE TYPE order_side AS ENUM (
            'BUY',
            'SELL'
        );
    END IF;
    
    -- 有效期类型枚举
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'time_in_force') THEN
        CREATE TYPE time_in_force AS ENUM (
            'GTC',  -- Good Till Cancelled
            'IOC',  -- Immediate Or Cancel
            'FOK',  -- Fill Or Kill
            'GTD'   -- Good Till Date
        );
    END IF;
END $$;

-- 创建函数：更新时间戳
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建函数：生成订单ID
CREATE OR REPLACE FUNCTION generate_order_id()
RETURNS TEXT AS $$
BEGIN
    RETURN 'ORD_' || TO_CHAR(NOW(), 'YYYYMMDD') || '_' || 
           LPAD(EXTRACT(EPOCH FROM NOW())::BIGINT::TEXT, 10, '0') || '_' ||
           LPAD(FLOOR(RANDOM() * 10000)::TEXT, 4, '0');
END;
$$ LANGUAGE plpgsql;

-- 创建函数：生成执行记录ID
CREATE OR REPLACE FUNCTION generate_execution_id()
RETURNS TEXT AS $$
BEGIN
    RETURN 'EXE_' || TO_CHAR(NOW(), 'YYYYMMDD') || '_' || 
           LPAD(EXTRACT(EPOCH FROM NOW())::BIGINT::TEXT, 10, '0') || '_' ||
           LPAD(FLOOR(RANDOM() * 10000)::TEXT, 4, '0');
END;
$$ LANGUAGE plpgsql;

-- 创建序列
CREATE SEQUENCE IF NOT EXISTS order_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS execution_sequence START 1;

-- 授权给应用用户
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cashup;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cashup;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO cashup;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cashup;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO cashup;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO cashup;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO cashup;

-- 创建索引（在表创建后通过Alembic迁移添加）
-- 这里只是预留注释，实际索引通过迁移脚本创建

/*
预期的索引结构：

-- 订单表索引
CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id);
CREATE INDEX CONCURRENTLY idx_orders_exchange_name ON orders(exchange_name);
CREATE INDEX CONCURRENTLY idx_orders_symbol ON orders(symbol);
CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);
CREATE INDEX CONCURRENTLY idx_orders_created_at ON orders(created_at);
CREATE INDEX CONCURRENTLY idx_orders_user_status ON orders(user_id, status);
CREATE INDEX CONCURRENTLY idx_orders_user_symbol ON orders(user_id, symbol);
CREATE INDEX CONCURRENTLY idx_orders_exchange_symbol ON orders(exchange_name, symbol);
CREATE INDEX CONCURRENTLY idx_orders_strategy_id ON orders(strategy_id) WHERE strategy_id IS NOT NULL;

-- 订单执行记录表索引
CREATE INDEX CONCURRENTLY idx_order_executions_order_id ON order_executions(order_id);
CREATE INDEX CONCURRENTLY idx_order_executions_execution_time ON order_executions(execution_time);
CREATE INDEX CONCURRENTLY idx_order_executions_order_execution_time ON order_executions(order_id, execution_time);

-- 复合索引用于查询优化
CREATE INDEX CONCURRENTLY idx_orders_user_created_status ON orders(user_id, created_at DESC, status);
CREATE INDEX CONCURRENTLY idx_orders_active ON orders(status, created_at) WHERE status IN ('PENDING', 'SUBMITTED', 'PARTIALLY_FILLED');
*/

-- 创建视图：活跃订单
CREATE OR REPLACE VIEW active_orders AS
SELECT *
FROM orders
WHERE status IN ('PENDING', 'SUBMITTED', 'PARTIALLY_FILLED')
ORDER BY created_at DESC;

-- 创建视图：订单统计
CREATE OR REPLACE VIEW order_statistics AS
SELECT 
    user_id,
    exchange_name,
    symbol,
    COUNT(*) as total_orders,
    COUNT(CASE WHEN status = 'FILLED' THEN 1 END) as filled_orders,
    COUNT(CASE WHEN status = 'CANCELLED' THEN 1 END) as cancelled_orders,
    COUNT(CASE WHEN status = 'REJECTED' THEN 1 END) as rejected_orders,
    SUM(CASE WHEN side = 'BUY' THEN quantity ELSE 0 END) as total_buy_quantity,
    SUM(CASE WHEN side = 'SELL' THEN quantity ELSE 0 END) as total_sell_quantity,
    SUM(CASE WHEN side = 'BUY' THEN filled_quantity ELSE 0 END) as filled_buy_quantity,
    SUM(CASE WHEN side = 'SELL' THEN filled_quantity ELSE 0 END) as filled_sell_quantity,
    AVG(CASE WHEN status = 'FILLED' THEN 
        EXTRACT(EPOCH FROM (updated_at - created_at)) 
    END) as avg_fill_time_seconds
FROM orders
GROUP BY user_id, exchange_name, symbol;

-- 插入初始数据（如果需要）
-- 这里可以插入一些测试数据或配置数据

-- 创建分区表函数（为未来的数据分区做准备）
CREATE OR REPLACE FUNCTION create_monthly_partition(
    table_name TEXT,
    start_date DATE
) RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    end_date DATE;
BEGIN
    partition_name := table_name || '_' || TO_CHAR(start_date, 'YYYY_MM');
    end_date := start_date + INTERVAL '1 month';
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF %I 
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, table_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

-- 设置数据库参数优化
-- 这些设置可以根据实际需求调整
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;

-- 重新加载配置
-- SELECT pg_reload_conf();

-- 创建监控用户（可选）
-- CREATE USER monitor WITH PASSWORD 'monitor123';
-- GRANT pg_monitor TO monitor;

COMMIT;