#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 核心模块包

提供核心功能和配置
"""

from .config import settings
from .database import get_db, init_database, init_db, close_db, DatabaseManager, get_db_manager
from .security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
    validate_password_strength,
    get_current_user_id,
    require_permissions,
    require_roles,
    security_manager
)
from .redis import redis_manager, get_redis

__all__ = [
    "settings",
    "get_db",
    "init_db",
    "close_db",
    "DatabaseManager",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "get_current_user_id",
    "require_permissions",
    "require_roles",
    "security_manager",
    "redis_manager",
    "get_redis"
]

__version__ = "1.0.0"
__author__ = "CashUp Team"
__description__ = "User Service Core Package"