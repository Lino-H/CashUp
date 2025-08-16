#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 配置服务异常处理

定义配置服务相关的异常类和异常处理器
"""

import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


# 自定义异常类
class ConfigServiceException(Exception):
    """
    配置服务基础异常类
    
    所有配置服务相关异常的基类
    """
    
    def __init__(self, message: str, error_code: str = "CONFIG_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigNotFoundError(ConfigServiceException):
    """
    配置未找到异常
    """
    
    def __init__(self, config_key: str, details: Dict[str, Any] = None):
        message = f"Configuration not found: {config_key}"
        super().__init__(message, "CONFIG_NOT_FOUND", details)
        self.config_key = config_key


class ConfigValidationError(ConfigServiceException):
    """
    配置验证异常
    """
    
    def __init__(self, message: str, validation_errors: list = None, details: Dict[str, Any] = None):
        super().__init__(message, "CONFIG_VALIDATION_ERROR", details)
        self.validation_errors = validation_errors or []


class ConfigPermissionError(ConfigServiceException):
    """
    配置权限异常
    """
    
    def __init__(self, message: str, required_permission: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "CONFIG_PERMISSION_ERROR", details)
        self.required_permission = required_permission


class ConfigVersionError(ConfigServiceException):
    """
    配置版本异常
    """
    
    def __init__(self, message: str, current_version: int = None, required_version: int = None, details: Dict[str, Any] = None):
        super().__init__(message, "CONFIG_VERSION_ERROR", details)
        self.current_version = current_version
        self.required_version = required_version


class ConfigLockError(ConfigServiceException):
    """
    配置锁异常
    """
    
    def __init__(self, config_key: str, details: Dict[str, Any] = None):
        message = f"Configuration is locked: {config_key}"
        super().__init__(message, "CONFIG_LOCK_ERROR", details)
        self.config_key = config_key


class ConfigSyncError(ConfigServiceException):
    """
    配置同步异常
    """
    
    def __init__(self, message: str, sync_target: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "CONFIG_SYNC_ERROR", details)
        self.sync_target = sync_target


class ConfigTemplateError(ConfigServiceException):
    """
    配置模板异常
    """
    
    def __init__(self, message: str, template_name: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "CONFIG_TEMPLATE_ERROR", details)
        self.template_name = template_name


class ConfigCacheError(ConfigServiceException):
    """
    配置缓存异常
    """
    
    def __init__(self, message: str, cache_operation: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "CONFIG_CACHE_ERROR", details)
        self.cache_operation = cache_operation


class ConfigConflictError(ConfigServiceException):
    """
    配置冲突异常
    """
    
    def __init__(self, message: str, conflicting_key: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "CONFIG_CONFLICT_ERROR", details)
        self.conflicting_key = conflicting_key


class ConfigDatabaseError(ConfigServiceException):
    """
    配置数据库异常
    """
    
    def __init__(self, message: str, operation: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "CONFIG_DATABASE_ERROR", details)
        self.operation = operation


# 异常处理器
async def config_service_exception_handler(request: Request, exc: ConfigServiceException) -> JSONResponse:
    """
    配置服务异常处理器
    
    Args:
        request: 请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.error(f"Config service error: {exc.message}, details: {exc.details}")
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "type": "config_service_error"
            }
        }
    )


async def config_not_found_handler(request: Request, exc: ConfigNotFoundError) -> JSONResponse:
    """
    配置未找到异常处理器
    
    Args:
        request: 请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.warning(f"Config not found: {exc.config_key}")
    
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "config_key": exc.config_key,
                "type": "config_not_found"
            }
        }
    )


async def config_validation_error_handler(request: Request, exc: ConfigValidationError) -> JSONResponse:
    """
    配置验证异常处理器
    
    Args:
        request: 请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.error(f"Config validation error: {exc.message}, errors: {exc.validation_errors}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "validation_errors": exc.validation_errors,
                "type": "config_validation_error"
            }
        }
    )


async def config_permission_error_handler(request: Request, exc: ConfigPermissionError) -> JSONResponse:
    """
    配置权限异常处理器
    
    Args:
        request: 请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.warning(f"Config permission error: {exc.message}, required: {exc.required_permission}")
    
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "required_permission": exc.required_permission,
                "type": "config_permission_error"
            }
        }
    )


async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    数据库异常处理器
    
    Args:
        request: 请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.error(f"Database error: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Database operation failed",
                "type": "database_error"
            }
        }
    )


async def redis_error_handler(request: Request, exc: RedisError) -> JSONResponse:
    """
    Redis异常处理器
    
    Args:
        request: 请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.error(f"Redis error: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "CACHE_ERROR",
                "message": "Cache operation failed",
                "type": "redis_error"
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP异常处理器
    
    Args:
        request: 请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "type": "http_error"
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    请求验证异常处理器
    
    Args:
        request: 请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.error(f"Request validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
                "type": "validation_error"
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器
    
    Args:
        request: 请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "type": "internal_error"
            }
        }
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    设置异常处理器
    
    Args:
        app: FastAPI应用实例
    """
    # 配置服务异常
    app.add_exception_handler(ConfigServiceException, config_service_exception_handler)
    app.add_exception_handler(ConfigNotFoundError, config_not_found_handler)
    app.add_exception_handler(ConfigValidationError, config_validation_error_handler)
    app.add_exception_handler(ConfigPermissionError, config_permission_error_handler)
    
    # 数据库和缓存异常
    app.add_exception_handler(SQLAlchemyError, database_error_handler)
    app.add_exception_handler(RedisError, redis_error_handler)
    
    # HTTP异常
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # 验证异常
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # 通用异常
    app.add_exception_handler(Exception, generic_exception_handler)