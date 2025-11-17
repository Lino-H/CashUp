"""
核心服务配置管理
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    """应用配置
    函数集注释：
    - Settings: 配置模型，加载环境变量与默认值
    - settings: 全局配置实例
    """
    
    # 基础配置
    APP_NAME: str = "CashUp 核心服务"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://cashup:cashup@postgres:5432/cashup")
    
    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    # Celery配置
    SINGLE_NODE: bool = os.getenv("SINGLE_NODE", "true").lower() == "true"
    CELERY_BROKER_URL: str | None = os.getenv("CELERY_BROKER_URL", None)
    CELERY_RESULT_BACKEND: str | None = os.getenv("CELERY_RESULT_BACKEND", None)
    
    # CORS配置 - 生产环境只允许特定域名
    ALLOWED_ORIGINS: List[str] = ["http://localhost", "http://localhost:80", "http://127.0.0.1", "http://127.0.0.1:80", "https://cashup.com", "https://www.cashup.com"]
    
    # 会话配置
    SESSION_EXPIRE_HOURS: int = 24
    # 认证开关
    ENABLE_AUTH: bool = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    
    # 邮件配置
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # 其他服务地址
    TRADING_ENGINE_URL: str = os.getenv("TRADING_ENGINE_URL", "http://localhost:8002")
    STRATEGY_PLATFORM_URL: str = os.getenv("STRATEGY_PLATFORM_URL", "http://localhost:8003")
    NOTIFICATION_URL: str = os.getenv("NOTIFICATION_URL", "http://localhost:8004")
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "./logs")
    LOG_ROTATE_MB: int = int(os.getenv("LOG_ROTATE_MB", "20"))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra='ignore',
    )

# 创建全局配置实例
settings = Settings()