#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 市场数据服务配置管理

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
    APP_NAME: str = "CashUp Market Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # 服务配置
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    PORT: int = Field(default=8003, description="服务监听端口")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="允许的主机列表")
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://cashup:cashup123@localhost:5432/cashup",
        description="数据库连接URL"
    )
    DATABASE_ECHO: bool = Field(default=False, description="是否打印SQL语句")
    
    # Redis 配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/2",
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
    
    # 市场数据配置
    DATA_UPDATE_INTERVAL: int = Field(default=1, description="数据更新间隔(秒)")
    KLINE_INTERVALS: List[str] = Field(
        default=["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        description="支持的K线间隔"
    )
    MAX_KLINE_LIMIT: int = Field(default=1000, description="K线数据最大数量")
    
    # 数据缓存配置
    TICKER_CACHE_TTL: int = Field(default=5, description="行情数据缓存时间(秒)")
    ORDERBOOK_CACHE_TTL: int = Field(default=1, description="订单簿缓存时间(秒)")
    KLINE_CACHE_TTL: int = Field(default=60, description="K线数据缓存时间(秒)")
    
    # WebSocket配置
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, description="WebSocket心跳间隔(秒)")
    WS_RECONNECT_INTERVAL: int = Field(default=5, description="WebSocket重连间隔(秒)")
    WS_MAX_RECONNECT_ATTEMPTS: int = Field(default=10, description="WebSocket最大重连次数")
    
    # 技术指标配置
    INDICATOR_CACHE_TTL: int = Field(default=300, description="技术指标缓存时间(秒)")
    MAX_INDICATOR_PERIODS: int = Field(default=200, description="技术指标最大周期数")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    
    # 性能配置
    DATA_PROCESSING_WORKERS: int = Field(default=4, description="数据处理工作线程数")
    BATCH_SIZE: int = Field(default=100, description="批处理大小")
    
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
        
        # 验证K线间隔
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        for interval in settings.KLINE_INTERVALS:
            if interval not in valid_intervals:
                raise ValueError(f"Invalid kline interval: {interval}")
        
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