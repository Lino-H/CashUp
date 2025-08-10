-- CashUp配置管理服务数据库初始化脚本

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS cashup_config;

-- 使用数据库
\c cashup_config;

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建配置类型枚举
CREATE TYPE config_type AS ENUM (
    'system',
    'user',
    'strategy',
    'trading',
    'risk',
    'notification',
    'api',
    'database',
    'cache',
    'security',
    'monitoring',
    'custom'
);

-- 创建配置作用域枚举
CREATE TYPE config_scope AS ENUM (
    'global',
    'user',
    'strategy',
    'session'
);

-- 创建配置状态枚举
CREATE TYPE config_status AS ENUM (
    'active',
    'inactive',
    'deprecated',
    'draft'
);

-- 创建配置格式枚举
CREATE TYPE config_format AS ENUM (
    'json',
    'yaml',
    'toml',
    'ini',
    'env'
);

-- 创建配置表
CREATE TABLE IF NOT EXISTS configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type config_type NOT NULL DEFAULT 'custom',
    scope config_scope NOT NULL DEFAULT 'global',
    format config_format NOT NULL DEFAULT 'json',
    value JSONB NOT NULL DEFAULT '{}',
    default_value JSONB,
    schema JSONB,
    status config_status NOT NULL DEFAULT 'active',
    is_encrypted BOOLEAN NOT NULL DEFAULT FALSE,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    is_readonly BOOLEAN NOT NULL DEFAULT FALSE,
    tags TEXT[] DEFAULT '{}',
    category VARCHAR(100),
    priority INTEGER DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    template_id UUID,
    parent_id UUID,
    user_id UUID,
    strategy_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    
    CONSTRAINT configs_key_scope_unique UNIQUE (key, scope, user_id, strategy_id),
    CONSTRAINT configs_parent_fk FOREIGN KEY (parent_id) REFERENCES configs(id) ON DELETE SET NULL
);

-- 创建配置模板表
CREATE TABLE IF NOT EXISTS config_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    type config_type NOT NULL,
    format config_format NOT NULL DEFAULT 'json',
    template JSONB NOT NULL DEFAULT '{}',
    schema JSONB,
    default_values JSONB DEFAULT '{}',
    is_builtin BOOLEAN NOT NULL DEFAULT FALSE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    tags TEXT[] DEFAULT '{}',
    category VARCHAR(100),
    version VARCHAR(50) DEFAULT '1.0.0',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID
);

-- 创建配置版本表
CREATE TABLE IF NOT EXISTS config_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_id UUID NOT NULL,
    version INTEGER NOT NULL,
    value JSONB NOT NULL,
    schema JSONB,
    change_summary TEXT,
    change_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    
    CONSTRAINT config_versions_config_fk FOREIGN KEY (config_id) REFERENCES configs(id) ON DELETE CASCADE,
    CONSTRAINT config_versions_unique UNIQUE (config_id, version)
);

-- 创建配置审计日志表
CREATE TABLE IF NOT EXISTS config_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_id UUID,
    template_id UUID,
    action VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    change_details JSONB,
    user_id UUID,
    user_ip INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    session_id VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT audit_logs_config_fk FOREIGN KEY (config_id) REFERENCES configs(id) ON DELETE SET NULL,
    CONSTRAINT audit_logs_template_fk FOREIGN KEY (template_id) REFERENCES config_templates(id) ON DELETE SET NULL
);

-- 创建索引

-- 配置表索引
CREATE INDEX IF NOT EXISTS idx_configs_key ON configs(key);
CREATE INDEX IF NOT EXISTS idx_configs_type ON configs(type);
CREATE INDEX IF NOT EXISTS idx_configs_scope ON configs(scope);
CREATE INDEX IF NOT EXISTS idx_configs_status ON configs(status);
CREATE INDEX IF NOT EXISTS idx_configs_user_id ON configs(user_id);
CREATE INDEX IF NOT EXISTS idx_configs_strategy_id ON configs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_configs_template_id ON configs(template_id);
CREATE INDEX IF NOT EXISTS idx_configs_parent_id ON configs(parent_id);
CREATE INDEX IF NOT EXISTS idx_configs_category ON configs(category);
CREATE INDEX IF NOT EXISTS idx_configs_tags ON configs USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_configs_created_at ON configs(created_at);
CREATE INDEX IF NOT EXISTS idx_configs_updated_at ON configs(updated_at);
CREATE INDEX IF NOT EXISTS idx_configs_value ON configs USING GIN(value);

-- 配置模板表索引
CREATE INDEX IF NOT EXISTS idx_templates_name ON config_templates(name);
CREATE INDEX IF NOT EXISTS idx_templates_type ON config_templates(type);
CREATE INDEX IF NOT EXISTS idx_templates_category ON config_templates(category);
CREATE INDEX IF NOT EXISTS idx_templates_is_builtin ON config_templates(is_builtin);
CREATE INDEX IF NOT EXISTS idx_templates_is_default ON config_templates(is_default);
CREATE INDEX IF NOT EXISTS idx_templates_tags ON config_templates USING GIN(tags);

-- 配置版本表索引
CREATE INDEX IF NOT EXISTS idx_versions_config_id ON config_versions(config_id);
CREATE INDEX IF NOT EXISTS idx_versions_created_at ON config_versions(created_at);

-- 审计日志表索引
CREATE INDEX IF NOT EXISTS idx_audit_config_id ON config_audit_logs(config_id);
CREATE INDEX IF NOT EXISTS idx_audit_template_id ON config_audit_logs(template_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON config_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON config_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON config_audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_request_id ON config_audit_logs(request_id);

-- 创建触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器
CREATE TRIGGER update_configs_updated_at
    BEFORE UPDATE ON configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at
    BEFORE UPDATE ON config_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入默认配置模板
INSERT INTO config_templates (name, description, type, format, template, is_builtin, is_default) VALUES
('system_basic', '系统基础配置模板', 'system', 'json', '{
  "app_name": "CashUp",
  "version": "1.0.0",
  "debug": false,
  "log_level": "INFO",
  "timezone": "UTC"
}', true, true),

('database_config', '数据库配置模板', 'database', 'json', '{
  "host": "localhost",
  "port": 5432,
  "database": "cashup",
  "username": "cashup",
  "password": "password",
  "pool_size": 10,
  "max_overflow": 20,
  "pool_timeout": 30
}', true, true),

('redis_config', '缓存配置模板', 'cache', 'json', '{
  "host": "localhost",
  "port": 6379,
  "database": 0,
  "password": null,
  "max_connections": 100,
  "timeout": 5
}', true, true),

('trading_config', '交易配置模板', 'trading', 'json', '{
  "max_position_size": 1000000,
  "max_daily_trades": 100,
  "risk_limit": 0.02,
  "stop_loss": 0.05,
  "take_profit": 0.1,
  "slippage_tolerance": 0.001
}', true, true),

('notification_config', '通知配置模板', 'notification', 'json', '{
  "email": {
    "enabled": true,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "",
    "password": ""
  },
  "webhook": {
    "enabled": false,
    "url": "",
    "timeout": 10
  }
}', true, true);

-- 插入一些示例配置
INSERT INTO configs (key, name, description, type, scope, value) VALUES
('app.name', '应用名称', 'CashUp量化交易系统名称', 'system', 'global', '"CashUp"'),
('app.version', '应用版本', '当前应用版本号', 'system', 'global', '"1.0.0"'),
('app.debug', '调试模式', '是否启用调试模式', 'system', 'global', 'false'),
('trading.max_position', '最大持仓', '单个策略最大持仓金额', 'trading', 'global', '1000000'),
('risk.daily_loss_limit', '日损失限制', '每日最大损失限制', 'risk', 'global', '0.05');

-- 创建用户和权限（如果需要）
-- 这里可以添加用户管理相关的表和数据

COMMIT;