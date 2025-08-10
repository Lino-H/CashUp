from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    APP_NAME: str = "Exchange Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/exchange_db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 交易所API配置
    GATEIO_API_KEY: str = ""
    GATEIO_API_SECRET: str = ""
    GATEIO_TESTNET: bool = True
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    # 缓存配置
    CACHE_TTL: int = 60  # 缓存过期时间（秒）
    
    # 速率限制配置
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # 时间窗口（秒）
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局设置实例
settings = Settings()