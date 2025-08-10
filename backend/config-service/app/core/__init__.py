#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 核心模块

提供数据库、缓存、配置、异常处理等核心功能
"""

from .config import get_settings
from .database import (
    init_database,
    close_database,
    get_database_session,
    get_database_transaction,
    check_database_health,
    execute_raw_sql,
    get_database_info
)
from .cache import (
    init_redis,
    close_redis,
    get_redis_client,
    check_redis_health,
    ConfigCache
)
from .exceptions import (
    ConfigServiceException,
    ConfigNotFoundError,
    ConfigValidationError,
    ConfigPermissionError,
    ConfigConflictError,
    ConfigVersionError,
    ConfigTemplateError,
    ConfigCacheError,
    ConfigDatabaseError,
    ConfigSyncError,
    setup_exception_handlers
)

__all__ = [
    "get_settings",
    "init_database",
    "close_database",
    "get_database_session",
    "get_database_transaction",
    "check_database_health",
    "execute_raw_sql",
    "get_database_info",
    "init_redis",
    "close_redis",
    "get_redis_client",
    "check_redis_health",
    "ConfigCache",
    "ConfigServiceException",
    "ConfigNotFoundError",
    "ConfigValidationError",
    "ConfigPermissionError",
    "ConfigConflictError",
    "ConfigVersionError",
    "ConfigTemplateError",
    "ConfigCacheError",
    "ConfigDatabaseError",
    "ConfigSyncError",
    "setup_exception_handlers"
]