#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 用户服务配置管理

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
    APP_NAME: str = "CashUp User Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # 服务配置
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    PORT: int = Field(default=8001, description="服务监听端口")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="允许的主机列表")
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://cashup:cashup123@localhost:5432/cashup_user",
        description="数据库连接URL"
    )
    DATABASE_ECHO: bool = Field(default=False, description="是否打印SQL语句")
    
    # Redis 配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
    
    # JWT 配置
    SECRET_KEY: str = Field(
        default="cashup-secret-key-change-in-production",
        description="JWT密钥"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="访问令牌过期时间(分钟)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="刷新令牌过期时间(天)")
    
    # 密码配置
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="密码最小长度")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, description="密码是否需要大写字母")
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True, description="密码是否需要小写字母")
    PASSWORD_REQUIRE_DIGITS: bool = Field(default=True, description="密码是否需要数字")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=False, description="密码是否需要特殊字符")
    
    # 用户配置
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, description="最大登录尝试次数")
    ACCOUNT_LOCKOUT_DURATION: int = Field(default=300, description="账户锁定时长(秒)")
    
    # 邮箱配置
    SMTP_SERVER: Optional[str] = Field(default=None, description="SMTP服务器")
    SMTP_PORT: int = Field(default=587, description="SMTP端口")
    SMTP_USERNAME: Optional[str] = Field(default=None, description="SMTP用户名")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP密码")
    SMTP_USE_TLS: bool = Field(default=True, description="是否使用TLS")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    
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