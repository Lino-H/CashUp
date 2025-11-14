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
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://cashup:cashup@localhost:5432/cashup")
    
    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    # CORS配置 - 生产环境只允许特定域名
    ALLOWED_ORIGINS: List[str] = ["http://localhost", "http://localhost:80", "http://127.0.0.1", "http://127.0.0.1:80", "https://cashup.com", "https://www.cashup.com"]
    
    # 会话配置
    SESSION_EXPIRE_HOURS: int = 24
    
    # 邮件配置
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # 其他服务地址
    TRADING_ENGINE_URL: str = os.getenv("TRADING_ENGINE_URL", "http://localhost:8002")
    STRATEGY_PLATFORM_URL: str = os.getenv("STRATEGY_PLATFORM_URL", "http://localhost:8003")
    NOTIFICATION_URL: str = os.getenv("NOTIFICATION_URL", "http://localhost:8004")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# 创建全局配置实例
settings = Settings()