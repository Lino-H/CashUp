#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易服务配置管理

统一管理应用配置，支持环境变量和默认值
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类
    
    使用 Pydantic Settings 管理配置，支持环境变量覆盖
    """
    
    # 应用基础配置
    APP_NAME: str = "CashUp Trading Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # 服务配置
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    PORT: int = Field(default=8002, description="服务监听端口")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="允许的主机列表")
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://cashup:cashup123@localhost:5432/cashup_trading",
        description="数据库连接URL"
    )
    DATABASE_ECHO: bool = Field(default=False, description="是否打印SQL语句")
    
    # Redis 配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Redis连接URL"
    )
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
    
    # JWT 配置 (用于验证用户服务的令牌)
    SECRET_KEY: str = Field(
        default="cashup-secret-key-change-in-production",
        description="JWT密钥"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT算法")
    
    # 用户服务配置
    USER_SERVICE_URL: str = Field(
        default="http://localhost:8001",
        description="用户服务URL"
    )
    
    # 交易所服务配置
    EXCHANGE_SERVICE_URL: str = Field(
        default="http://localhost:8003",
        description="交易所服务URL"
    )
    
    # 交易配置
    MAX_POSITION_SIZE: float = Field(default=1000000.0, description="最大持仓金额")
    MAX_ORDER_SIZE: float = Field(default=100000.0, description="最大单笔订单金额")
    MAX_DAILY_LOSS: float = Field(default=50000.0, description="最大日损失")
    RISK_CHECK_ENABLED: bool = Field(default=True, description="是否启用风险检查")
    
    # 市场数据配置
    MARKET_DATA_WEBSOCKET_URL: str = Field(
        default="wss://stream.binance.com:9443/ws",
        description="市场数据WebSocket URL"
    )
    EXCHANGE_API_KEY: Optional[str] = Field(default=None, description="交易所API密钥")
    EXCHANGE_SECRET_KEY: Optional[str] = Field(default=None, description="交易所密钥")
    EXCHANGE_SANDBOX: bool = Field(default=True, description="是否使用沙盒环境")
    
    # Gate.io 交易所配置
    GATEIO_API_KEY: Optional[str] = Field(default=None, description="Gate.io API密钥")
    GATEIO_API_SECRET: Optional[str] = Field(default=None, description="Gate.io API密钥")
    GATEIO_TESTNET: bool = Field(default=True, description="是否使用Gate.io测试网")
    GATEIO_BASE_URL: str = Field(
        default="https://api.gateio.ws",
        description="Gate.io API基础URL"
    )
    GATEIO_WS_URL: str = Field(
        default="wss://api.gateio.ws/ws/v4/",
        description="Gate.io WebSocket URL"
    )
    GATEIO_TIMEOUT: int = Field(default=30, description="Gate.io API超时时间(秒)")
    GATEIO_RATE_LIMIT: int = Field(default=100, description="Gate.io API速率限制(每秒请求数)")
    
    # 消息队列配置
    RABBITMQ_URL: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        description="RabbitMQ连接URL"
    )
    
    # Celery配置
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/2",
        description="Celery代理URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/3",
        description="Celery结果后端URL"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    
    # 性能配置
    ORDER_PROCESSING_TIMEOUT: int = Field(default=30, description="订单处理超时时间(秒)")
    POSITION_UPDATE_INTERVAL: int = Field(default=5, description="持仓更新间隔(秒)")
    RISK_CHECK_INTERVAL: int = Field(default=10, description="风险检查间隔(秒)")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


# 配置验证函数
def validate_config() -> bool:
    """
    验证配置是否正确
    
    Returns:
        bool: 配置是否有效
    """
    try:
        # 验证数据库URL
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")
        
        # 验证JWT密钥
        if settings.SECRET_KEY == "cashup-secret-key-change-in-production":
            if not settings.DEBUG:
                raise ValueError("SECRET_KEY must be changed in production")
        
        # 验证Redis URL
        if not settings.REDIS_URL:
            raise ValueError("REDIS_URL is required")
        
        # 验证交易配置
        if settings.MAX_ORDER_SIZE > settings.MAX_POSITION_SIZE:
            raise ValueError("MAX_ORDER_SIZE cannot exceed MAX_POSITION_SIZE")
        
        return True
        
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    # 配置验证测试
    if validate_config():
        print("Configuration is valid")
        print(f"App: {settings.APP_NAME}")
        print(f"Debug: {settings.DEBUG}")
        print(f"Database: {settings.DATABASE_URL}")
    else:
        print("Configuration validation failed")