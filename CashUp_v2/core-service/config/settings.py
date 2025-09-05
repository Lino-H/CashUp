"""
核心服务配置管理
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    APP_NAME: str = "CashUp 核心服务"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://cashup:cashup@localhost:5432/cashup"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000"
    ]
    
    # 会话配置
    SESSION_EXPIRE_HOURS: int = 24
    
    # 邮件配置
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    
    # 其他服务地址
    TRADING_ENGINE_URL: str = "http://localhost:8002"
    STRATEGY_PLATFORM_URL: str = "http://localhost:8003"
    NOTIFICATION_URL: str = "http://localhost:8004"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# 创建全局配置实例
settings = Settings()