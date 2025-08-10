#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务配置

管理订单服务的所有配置参数
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    订单服务配置类
    
    从环境变量和配置文件中加载配置
    """
    
    # 应用基础配置
    APP_NAME: str = "CashUp Order Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # 服务配置
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    PORT: int = Field(default=8002, description="服务端口")
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://cashup:cashup123@localhost:5432/cashup_order",
        description="数据库连接URL"
    )
    
    # Redis配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/5",
        description="Redis连接URL"
    )
    
    # 安全配置
    SECRET_KEY: str = Field(
        default="order-service-secret-key-change-in-production",
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
    TRADING_SERVICE_URL: str = Field(
        default="http://localhost:8002",
        description="交易服务URL"
    )
    EXCHANGE_SERVICE_URL: str = Field(
        default="http://localhost:8009",
        description="交易所服务URL"
    )
    USER_SERVICE_URL: str = Field(
        default="http://localhost:8001",
        description="用户服务URL"
    )
    
    # 订单配置
    ORDER_TIMEOUT_SECONDS: int = Field(default=300, description="订单超时时间（秒）")
    MAX_ORDERS_PER_USER: int = Field(default=100, description="每用户最大订单数")
    ORDER_HISTORY_DAYS: int = Field(default=90, description="订单历史保留天数")
    
    # Celery配置
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/6",
        description="Celery消息代理URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/7",
        description="Celery结果后端URL"
    )
    
    # 监控配置
    ENABLE_METRICS: bool = Field(default=True, description="启用指标收集")
    METRICS_PORT: int = Field(default=9005, description="指标端口")
    
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
    return "sqlite+aiosqlite:///./cashup_order.db"