"""
策略平台配置管理
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
from pathlib import Path
import os

class Settings(BaseSettings):
    """策略平台配置"""
    
    # 基础配置
    DEBUG: bool = Field(default=False, env="DEBUG")  # 生产环境关闭调试
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8003, env="PORT")
    
    # 数据目录配置
    DATA_DIR: str = Field(default="./data", env="DATA_DIR")
    STRATEGIES_DIR: str = Field(default="./strategies", env="STRATEGIES_DIR")
    REPORTS_DIR: str = Field(default="./reports", env="REPORTS_DIR")
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://cashup:cashup@localhost:5432/cashup",
        env="DATABASE_URL"
    )
    
    # Redis配置
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # 核心服务配置
    CORE_SERVICE_URL: str = Field(
        default="http://localhost:8001",
        env="CORE_SERVICE_URL"
    )
    
    # 交易引擎配置
    TRADING_ENGINE_URL: str = Field(
        default="http://localhost:8002",
        env="TRADING_ENGINE_URL"
    )
    
    # API配置
    API_V1_STR: str = "/api/v1"
    
    # CORS配置 - 生产环境只允许特定域名
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "https://cashup.com", "https://www.cashup.com"],
        env="ALLOWED_ORIGINS"
    )
    
    # 策略配置
    MAX_STRATEGIES: int = Field(default=10, env="MAX_STRATEGIES")
    STRATEGY_TIMEOUT: int = Field(default=30, env="STRATEGY_TIMEOUT")
    
    # 回测配置
    MAX_BACKTEST_DAYS: int = Field(default=365, env="MAX_BACKTEST_DAYS")
    BACKTEST_TIMEOUT: int = Field(default=300, env="BACKTEST_TIMEOUT")
    
    # 数据配置
    DATA_CACHE_TTL: int = Field(default=300, env="DATA_CACHE_TTL")
    DATA_REQUEST_TIMEOUT: int = Field(default=10, env="DATA_REQUEST_TIMEOUT")
    
    # 安全配置
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.DATA_DIR,
            self.STRATEGIES_DIR,
            self.REPORTS_DIR,
            f"{self.DATA_DIR}/historical",
            f"{self.DATA_DIR}/cache",
            f"{self.DATA_DIR}/realtime",
            f"{self.STRATEGIES_DIR}/templates",
            f"{self.STRATEGIES_DIR}/examples",
            f"{self.STRATEGIES_DIR}/custom",
            f"{self.REPORTS_DIR}/html",
            f"{self.REPORTS_DIR}/json",
            f"{self.REPORTS_DIR}/charts"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @property
    def database_url_sync(self) -> str:
        """同步数据库URL"""
        return self.DATABASE_URL.replace("+asyncpg", "")
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return not self.DEBUG
    
    @property
    def cors_origins(self) -> List[str]:
        """CORS源列表"""
        if self.DEBUG:
            return ["*"]
        return self.ALLOWED_ORIGINS

# 创建全局配置实例
settings = Settings()