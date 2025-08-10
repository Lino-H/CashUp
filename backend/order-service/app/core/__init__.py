#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务核心模块

导出核心功能模块
"""

from .config import get_settings, Settings
from .database import (
    get_database_session,
    get_database_session_context,
    init_database,
    close_database,
    Base,
    check_database_health,
    get_database_info
)
from .auth import (
    get_current_user,
    get_current_active_user,
    require_permissions,
    require_roles,
    create_service_token,
    verify_service_token,
    PERMISSIONS,
    ROLES
)
from .middleware import (
    setup_cors_middleware,
    setup_middleware,
    RequestLoggingMiddleware,
    PerformanceMiddleware,
    SecurityMiddleware,
    RateLimitMiddleware,
    ErrorHandlingMiddleware
)
from .exceptions import (
    OrderServiceException,
    OrderNotFoundError,
    OrderValidationError,
    OrderStateError,
    ExchangeError,
    InsufficientBalanceError,
    RateLimitError,
    DatabaseError,
    ExternalServiceError,
    setup_exception_handlers
)
from .logging import (
    setup_logging,
    get_logger,
    get_context_logger,
    LoggerAdapter,
    app_logger,
    order_logger,
    exchange_logger,
    database_logger,
    access_logger
)

__all__ = [
    # 配置
    "get_settings",
    "Settings",
    
    # 数据库
    "get_database_session",
    "get_database_session_context",
    "init_database",
    "close_database",
    "Base",
    "check_database_health",
    "get_database_info",
    
    # 认证
    "get_current_user",
    "get_current_active_user",
    "require_permissions",
    "require_roles",
    "create_service_token",
    "verify_service_token",
    "PERMISSIONS",
    "ROLES",
    
    # 中间件
    "setup_cors_middleware",
    "setup_middleware",
    "RequestLoggingMiddleware",
    "PerformanceMiddleware",
    "SecurityMiddleware",
    "RateLimitMiddleware",
    "ErrorHandlingMiddleware",
    
    # 异常
    "OrderServiceException",
    "OrderNotFoundError",
    "OrderValidationError",
    "OrderStateError",
    "ExchangeError",
    "InsufficientBalanceError",
    "RateLimitError",
    "DatabaseError",
    "ExternalServiceError",
    "setup_exception_handlers",
    
    # 日志
    "setup_logging",
    "get_logger",
    "get_context_logger",
    "LoggerAdapter",
    "app_logger",
    "order_logger",
    "exchange_logger",
    "database_logger",
    "access_logger"
]