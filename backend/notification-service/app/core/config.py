#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知服务配置

管理通知服务的所有配置参数
"""

import os
from typing import List, Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    通知服务配置类
    
    从环境变量和配置文件中加载配置
    """
    
    # 应用基础配置
    APP_NAME: str = "CashUp Notification Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # 服务配置
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    PORT: int = Field(default=8006, description="服务端口")
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://cashup:cashup123@localhost:5432/cashup_notification",
        description="数据库连接URL"
    )
    
    # Redis配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/8",
        description="Redis连接URL"
    )
    
    # 安全配置
    SECRET_KEY: str = Field(
        default="notification-service-secret-key-change-in-production",
        description="JWT密钥"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="访问令牌过期时间（分钟）")
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"],
        description="允许的主机列表"
    )
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="CORS允许的源列表"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    
    # 邮件配置
    SMTP_HOST: str = Field(default="smtp.qq.com", description="SMTP服务器地址")
    SMTP_PORT: int = Field(default=587, description="SMTP服务器端口")
    SMTP_USERNAME: str = Field(default="371886367@qq.com", description="SMTP用户名")
    SMTP_PASSWORD: str = Field(default="", description="SMTP密码")
    SMTP_USE_TLS: bool = Field(default=True, description="是否使用TLS")
    SMTP_USE_SSL: bool = Field(default=False, description="是否使用SSL")
    
    # 短信配置
    SMS_PROVIDER: str = Field(default="aliyun", description="短信服务提供商")
    SMS_ACCESS_KEY: str = Field(default="", description="短信服务访问密钥")
    SMS_SECRET_KEY: str = Field(default="", description="短信服务密钥")
    SMS_SIGN_NAME: str = Field(default="CashUp", description="短信签名")
    
    # 微信推送配置
    WXPUSHER_APP_TOKEN: str = Field(
        default="AT_Dlr9mx3PXLg3GItFtz3C2RyJnhMKBUgf",
        description="WXPusher应用Token"
    )
    
    # QANotify配置
    QANOTIFY_KEY: str = Field(
        default="oL-C4w0kBQFjzMHKH4pnl6oMuCyc",
        description="QANotify密钥"
    )
    
    # PushPlus配置
    PUSHPLUS_TOKEN: str = Field(
        default="60ad54690c904ed3b35a06640e1af904",
        description="PushPlus Token"
    )
    
    # Telegram配置
    TELEGRAM_BOT_TOKEN: str = Field(
        default="8411704076:AAGKsaXRYDVmkYhlXQlSu2nBlCJhOfTXhjg",
        description="Telegram Bot Token"
    )
    TELEGRAM_CHAT_ID: str = Field(default="", description="Telegram聊天ID")
    
    # WebSocket配置
    WEBSOCKET_HOST: str = Field(default="0.0.0.0", description="WebSocket监听地址")
    WEBSOCKET_PORT: int = Field(default=8106, description="WebSocket端口")
    
    # 通知配置
    MAX_RETRY_ATTEMPTS: int = Field(default=3, description="最大重试次数")
    RETRY_DELAY_SECONDS: int = Field(default=60, description="重试延迟时间（秒）")
    BATCH_SIZE: int = Field(default=100, description="批量发送大小")
    NOTIFICATION_HISTORY_DAYS: int = Field(default=30, description="通知历史保留天数")
    
    # Celery配置
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/9",
        description="Celery消息代理URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/10",
        description="Celery结果后端URL"
    )
    
    # 监控配置
    ENABLE_METRICS: bool = Field(default=True, description="启用指标收集")
    METRICS_PORT: int = Field(default=9006, description="指标端口")
    
    # 外部服务配置
    USER_SERVICE_URL: str = Field(
        default="http://localhost:8001",
        description="用户服务URL"
    )
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of {valid_levels}')
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def validate_config() -> bool:
    """
    验证配置的有效性
    
    Returns:
        bool: 配置是否有效
    """
    try:
        # 验证必要的配置项
        required_configs = [
            settings.DATABASE_URL,
            settings.REDIS_URL,
            settings.SECRET_KEY
        ]
        
        for config in required_configs:
            if not config:
                return False
        
        return True
    except Exception:
        return False


def get_database_config() -> dict:
    """
    获取数据库配置字典
    
    Returns:
        dict: 数据库配置
    """
    return {
        "url": settings.DATABASE_URL,
        "echo": settings.DEBUG,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 3600
    }


def get_redis_config() -> dict:
    """
    获取Redis配置字典
    
    Returns:
        dict: Redis配置
    """
    return {
        "url": settings.REDIS_URL,
        "encoding": "utf-8",
        "decode_responses": True,
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
        "retry_on_timeout": True
    }


def get_email_config() -> dict:
    """
    获取邮件配置字典
    
    Returns:
        dict: 邮件配置
    """
    return {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "username": settings.SMTP_USERNAME,
        "password": settings.SMTP_PASSWORD,
        "use_tls": settings.SMTP_USE_TLS,
        "use_ssl": settings.SMTP_USE_SSL
    }


def get_notification_channels() -> Dict[str, Dict[str, Any]]:
    """
    获取通知渠道配置
    
    Returns:
        Dict[str, Dict[str, Any]]: 通知渠道配置字典
    """
    return {
        "email": {
            "enabled": bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD),
            "config": get_email_config()
        },
        "wxpusher": {
            "enabled": bool(settings.WXPUSHER_APP_TOKEN),
            "token": settings.WXPUSHER_APP_TOKEN
        },
        "qanotify": {
            "enabled": bool(settings.QANOTIFY_KEY),
            "key": settings.QANOTIFY_KEY
        },
        "pushplus": {
            "enabled": bool(settings.PUSHPLUS_TOKEN),
            "token": settings.PUSHPLUS_TOKEN
        },
        "telegram": {
            "enabled": bool(settings.TELEGRAM_BOT_TOKEN),
            "bot_token": settings.TELEGRAM_BOT_TOKEN,
            "chat_id": settings.TELEGRAM_CHAT_ID
        }
    }


def get_settings() -> Settings:
    """
    获取配置设置实例
    
    Returns:
        Settings: 配置实例
    """
    return settings


def get_config() -> Settings:
    """
    获取配置实例
    
    Returns:
        Settings: 配置实例
    """
    return settings


def get_database_url() -> str:
    """
    获取数据库连接URL
    
    Returns:
        str: 数据库URL
    """
    if settings.DATABASE_URL:
        # 如果是PostgreSQL URL，确保使用asyncpg驱动
        if settings.DATABASE_URL.startswith("postgresql://"):
            return settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif settings.DATABASE_URL.startswith("postgres://"):
            return settings.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        return settings.DATABASE_URL
    
    # 默认使用SQLite数据库
    return "sqlite+aiosqlite:///./cashup_notification.db"