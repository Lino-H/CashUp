#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略服务配置管理

提供策略服务的配置参数管理，包括数据库连接、Redis缓存、
回测引擎参数等配置项。
"""

import os
from typing import Optional, List
from pydantic import validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """策略服务配置类"""
    
    # 应用基础配置
    app_name: str = "CashUp Strategy Service"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8005
    
    # 数据库配置
    database_url: str = "postgresql+asyncpg://cashup:cashup123@postgres:5432/cashup"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis配置
    redis_url: str = "redis://redis:6379"
    redis_db: int = 3  # 策略服务专用数据库
    redis_password: Optional[str] = None
    
    # JWT配置
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS配置
    allowed_origins: List[str] = ["*"]
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]
    
    # 回测引擎配置
    backtest_data_path: str = "/tmp/backtest_data"
    backtest_max_concurrent: int = 5
    backtest_timeout_minutes: int = 60
    
    # 策略执行配置
    strategy_max_positions: int = 10
    strategy_max_leverage: float = 3.0
    strategy_min_balance: float = 100.0
    
    # 风险管理配置
    risk_max_drawdown: float = 0.2  # 最大回撤20%
    risk_max_daily_loss: float = 0.05  # 单日最大亏损5%
    risk_position_size_limit: float = 0.1  # 单个仓位最大占比10%
    
    # 数据源配置
    market_data_source: str = "gateio"
    historical_data_days: int = 365
    
    # 通知配置
    notification_service_url: str = "http://localhost:8006"
    
    # 安全配置
    enable_rate_limit: bool = False
    rate_limit_requests_per_minute: int = 60
    ip_whitelist: Optional[List[str]] = None
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "logs/strategy_service.log"
    log_max_size: str = "10MB"
    log_backup_count: int = 5
    
    @validator('database_url')
    def validate_database_url(cls, v):
        """验证数据库URL格式"""
        if not v.startswith(('postgresql://', 'postgresql+psycopg2://', 'postgresql+asyncpg://')):
            raise ValueError('数据库URL必须是PostgreSQL格式')
        return v
    
    @validator('redis_url')
    def validate_redis_url(cls, v):
        """验证Redis URL格式"""
        if not v.startswith('redis://'):
            raise ValueError('Redis URL格式错误')
        return v
    
    @validator('risk_max_drawdown', 'risk_max_daily_loss', 'risk_position_size_limit')
    def validate_risk_ratios(cls, v):
        """验证风险比例参数"""
        if not 0 < v <= 1:
            raise ValueError('风险比例必须在0-1之间')
        return v
    
    class Config:
        env_file = ".env"
        env_prefix = "STRATEGY_"


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 全局配置实例
settings = get_settings()