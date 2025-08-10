#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 核心模块

核心功能模块的初始化文件
"""

from .config import settings
from .database import get_db, engine, SessionLocal
from .cache import CacheManager
from .exceptions import (
    MonitoringException,
    MetricsError,
    AlertsError,
    HealthCheckError,
    DashboardError,
    SystemError,
    ValidationError,
    NotFoundError,
    ServiceUnavailableError
)
from .security import (
    create_access_token,
    verify_token,
    get_current_user,
    hash_password,
    verify_password
)
from .logging import setup_logging, get_logger

__all__ = [
    # 配置
    "settings",
    
    # 数据库
    "get_db",
    "engine",
    "SessionLocal",
    
    # 缓存
    "CacheManager",
    
    # 异常
    "MonitoringException",
    "MetricsError",
    "AlertsError",
    "HealthCheckError",
    "DashboardError",
    "SystemError",
    "ValidationError",
    "NotFoundError",
    "ServiceUnavailableError",
    
    # 安全
    "create_access_token",
    "verify_token",
    "get_current_user",
    "hash_password",
    "verify_password",
    
    # 日志
    "setup_logging",
    "get_logger"
]