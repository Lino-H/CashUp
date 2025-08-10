#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 配置服务配置

管理配置服务的所有配置参数
"""

import os
from typing import List, Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    配置服务配置类
    
    从环境变量和配置文件中加载配置
    """
    
    # 应用基础配置
    APP_NAME: str = "CashUp Config Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # 服务配置
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    PORT: int = Field(default=8007, description="服务端口")
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://cashup:cashup123@localhost:5432/cashup_config",
        description="数据库连接URL"
    )
    
    # Redis配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/8",
        description="Redis连接URL"
    )
    
    # 安全配置
    SECRET_KEY: str = Field(
        default="config-service-secret-key-change-in-production",
        description="JWT密钥"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="访问令牌过期时间（分钟）")
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"],
        description="允许的主机列表"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    
    # 外部服务配置
    USER_SERVICE_URL: str = Field(
        default="http://localhost:8001",
        description="用户服务URL"
    )
    NOTIFICATION_SERVICE_URL: str = Field(
        default="http://localhost:8006",
        description="通知服务URL"
    )
    
    # 配置管理配置
    CONFIG_CACHE_TTL: int = Field(default=300, description="配置缓存TTL（秒）")
    CONFIG_VERSION_LIMIT: int = Field(default=50, description="配置版本保留数量")
    CONFIG_BACKUP_ENABLED: bool = Field(default=True, description="启用配置备份")
    CONFIG_AUDIT_ENABLED: bool = Field(default=True, description="启用配置审计")
    
    # 配置类型支持
    SUPPORTED_CONFIG_TYPES: List[str] = Field(
        default=["json", "yaml", "toml", "env"],
        description="支持的配置类型"
    )
    
    # 配置模板配置
    TEMPLATE_DIR: str = Field(
        default="templates",
        description="配置模板目录"
    )
    DEFAULT_TEMPLATE: str = Field(
        default="default.json",
        description="默认配置模板"
    )
    
    # 权限配置
    ADMIN_ROLES: List[str] = Field(
        default=["admin", "system_admin"],
        description="管理员角色列表"
    )
    CONFIG_MANAGER_ROLES: List[str] = Field(
        default=["config_manager", "admin"],
        description="配置管理员角色列表"
    )
    
    # 监控配置
    ENABLE_METRICS: bool = Field(default=True, description="启用指标收集")
    METRICS_PORT: int = Field(default=9007, description="指标端口")
    
    # 热更新配置
    HOT_RELOAD_ENABLED: bool = Field(default=True, description="启用热更新")
    HOT_RELOAD_INTERVAL: int = Field(default=30, description="热更新检查间隔（秒）")
    
    # 配置同步配置
    SYNC_ENABLED: bool = Field(default=True, description="启用配置同步")
    SYNC_INTERVAL: int = Field(default=60, description="同步间隔（秒）")
    SYNC_BATCH_SIZE: int = Field(default=100, description="同步批次大小")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


# 配置验证函数
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


# 获取数据库配置
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


# 获取Redis配置
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


# 获取配置类型映射
def get_config_type_mapping() -> Dict[str, str]:
    """
    获取配置类型映射
    
    Returns:
        Dict[str, str]: 配置类型映射
    """
    return {
        "json": "application/json",
        "yaml": "application/x-yaml",
        "toml": "application/toml",
        "env": "text/plain"
    }


# 获取默认配置模板
def get_default_config_template() -> Dict[str, Any]:
    """
    获取默认配置模板
    
    Returns:
        Dict[str, Any]: 默认配置模板
    """
    return {
        "system": {
            "name": "CashUp Trading System",
            "version": "1.0.0",
            "environment": "development",
            "debug": False
        },
        "database": {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30
        },
        "trading": {
            "max_orders_per_user": 100,
            "order_timeout": 300,
            "risk_limit": 0.02
        },
        "notification": {
            "enabled": True,
            "channels": ["email", "websocket"],
            "retry_count": 3
        }
    }


# 获取设置实例
def get_settings() -> Settings:
    """
    获取配置设置实例
    
    Returns:
        Settings: 配置实例
    """
    return settings


# 获取数据库URL
def get_database_url() -> str:
    """
    获取数据库连接URL
    
    Returns:
        str: 数据库URL
    """
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    
    # 默认使用SQLite数据库
    return "sqlite+aiosqlite:///./cashup_config.db"