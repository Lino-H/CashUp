#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 配置管理

系统配置和环境变量管理
"""

import os
from typing import Optional, List, Any
from pydantic import validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "CashUp Monitoring Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API配置
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://cashup:cashup123@localhost:5432/cashup_monitoring"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Redis缓存配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_POOL_SIZE: int = 10
    
    # 缓存配置
    CACHE_TTL_DEFAULT: int = 300  # 5分钟
    CACHE_TTL_SHORT: int = 60     # 1分钟
    CACHE_TTL_LONG: int = 3600    # 1小时
    
    # JWT安全配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",
        "https://localhost:3000",
        "https://localhost:8080",
        "https://localhost:5173"
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json 或 text
    LOG_FILE: Optional[str] = None
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # 监控配置
    METRICS_RETENTION_DAYS: int = 30
    ALERTS_RETENTION_DAYS: int = 90
    HEALTH_CHECK_INTERVAL: int = 60  # 秒
    METRICS_COLLECTION_INTERVAL: int = 30  # 秒
    
    # 告警配置
    ALERT_NOTIFICATION_TIMEOUT: int = 30  # 秒
    ALERT_MAX_RETRIES: int = 3
    ALERT_RETRY_DELAY: int = 60  # 秒
    
    # 邮件配置
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: Optional[str] = None
    
    # Slack配置
    SLACK_WEBHOOK_URL: Optional[str] = None
    SLACK_CHANNEL: str = "#alerts"
    
    # 钉钉配置
    DINGTALK_WEBHOOK_URL: Optional[str] = None
    DINGTALK_SECRET: Optional[str] = None
    
    # 企业微信配置
    WECHAT_WEBHOOK_URL: Optional[str] = None
    
    # Prometheus配置
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    PROMETHEUS_METRICS_PATH: str = "/metrics"
    
    # 文件存储配置
    UPLOAD_DIR: str = "/tmp/uploads"
    BACKUP_DIR: str = "/tmp/backups"
    LOG_DIR: str = "/tmp/logs"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # 安全配置
    ALLOWED_HOSTS: List[str] = ["*"]
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # 秒
    
    # 性能配置
    WORKER_PROCESSES: int = 1
    WORKER_CONNECTIONS: int = 1000
    KEEPALIVE_TIMEOUT: int = 65
    
    # 第三方服务配置
    EXTERNAL_API_TIMEOUT: int = 30  # 秒
    EXTERNAL_API_RETRIES: int = 3
    
    # 开发配置
    RELOAD: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 别名函数，保持兼容性
def get_config() -> Settings:
    """获取配置实例（别名）"""
    return get_settings()


# 全局配置实例
settings = get_settings()


# 环境检查函数
def is_development() -> bool:
    """检查是否为开发环境"""
    return settings.ENVIRONMENT.lower() in ["development", "dev"]


def is_production() -> bool:
    """检查是否为生产环境"""
    return settings.ENVIRONMENT.lower() in ["production", "prod"]


def is_testing() -> bool:
    """检查是否为测试环境"""
    return settings.ENVIRONMENT.lower() in ["testing", "test"]


# 配置验证函数
def validate_config() -> List[str]:
    """验证配置"""
    errors = []
    
    # 检查必需的配置
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-here-change-in-production":
        if is_production():
            errors.append("SECRET_KEY must be set in production")
    
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required")
    
    if not settings.REDIS_URL:
        errors.append("REDIS_URL is required")
    
    # 检查邮件配置（如果启用）
    if settings.SMTP_HOST:
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            errors.append("SMTP_USERNAME and SMTP_PASSWORD are required when SMTP_HOST is set")
        if not settings.EMAIL_FROM:
            errors.append("EMAIL_FROM is required when SMTP_HOST is set")
    
    # 检查目录权限
    for directory in [settings.UPLOAD_DIR, settings.BACKUP_DIR, settings.LOG_DIR]:
        try:
            os.makedirs(directory, exist_ok=True)
            if not os.access(directory, os.W_OK):
                errors.append(f"Directory {directory} is not writable")
        except Exception as e:
            errors.append(f"Cannot create or access directory {directory}: {e}")
    
    return errors


# 配置打印函数
def print_config():
    """打印当前配置（隐藏敏感信息）"""
    sensitive_keys = {
        "SECRET_KEY", "DATABASE_URL", "REDIS_URL", "REDIS_PASSWORD",
        "SMTP_PASSWORD", "SLACK_WEBHOOK_URL", "DINGTALK_WEBHOOK_URL",
        "DINGTALK_SECRET", "WECHAT_WEBHOOK_URL"
    }
    
    print("\n=== CashUp Monitoring Service Configuration ===")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print(f"API Version: {settings.API_V1_STR}")
    
    print("\n--- Database ---")
    db_url = settings.DATABASE_URL
    if "@" in db_url:
        # 隐藏密码
        parts = db_url.split("@")
        if ":" in parts[0]:
            user_pass = parts[0].split(":")
            if len(user_pass) >= 3:
                user_pass[2] = "***"
                parts[0] = ":".join(user_pass)
        db_url = "@".join(parts)
    print(f"Database URL: {db_url}")
    print(f"Pool Size: {settings.DATABASE_POOL_SIZE}")
    
    print("\n--- Cache ---")
    redis_url = settings.REDIS_URL
    if settings.REDIS_PASSWORD:
        redis_url = redis_url.replace(settings.REDIS_PASSWORD, "***")
    print(f"Redis URL: {redis_url}")
    print(f"Default TTL: {settings.CACHE_TTL_DEFAULT}s")
    
    print("\n--- Security ---")
    print(f"Algorithm: {settings.ALGORITHM}")
    print(f"Token Expire: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}min")
    
    print("\n--- Monitoring ---")
    print(f"Metrics Retention: {settings.METRICS_RETENTION_DAYS} days")
    print(f"Alerts Retention: {settings.ALERTS_RETENTION_DAYS} days")
    print(f"Health Check Interval: {settings.HEALTH_CHECK_INTERVAL}s")
    
    print("\n--- Logging ---")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print(f"Log Format: {settings.LOG_FORMAT}")
    print(f"Log File: {settings.LOG_FILE or 'Console only'}")
    
    print("\n--- Notifications ---")
    print(f"SMTP Enabled: {bool(settings.SMTP_HOST)}")
    print(f"Slack Enabled: {bool(settings.SLACK_WEBHOOK_URL)}")
    print(f"DingTalk Enabled: {bool(settings.DINGTALK_WEBHOOK_URL)}")
    print(f"WeChat Enabled: {bool(settings.WECHAT_WEBHOOK_URL)}")
    
    print("\n--- Performance ---")
    print(f"Worker Processes: {settings.WORKER_PROCESSES}")
    print(f"Worker Connections: {settings.WORKER_CONNECTIONS}")
    print(f"Rate Limit: {settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW}s")
    
    print("\n=== End Configuration ===")


if __name__ == "__main__":
    # 验证配置
    errors = validate_config()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid")
    
    # 打印配置
    print_config()