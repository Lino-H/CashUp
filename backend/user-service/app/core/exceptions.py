#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 异常处理模块

定义自定义异常类和异常处理器
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


class CashUpException(Exception):
    """
    CashUp系统基础异常类
    """
    def __init__(
        self,
        message: str,
        error_code: str = "CASHUP_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class UserException(CashUpException):
    """
    用户相关异常基类
    """
    pass


class UserNotFoundError(UserException):
    """
    用户不存在异常
    """
    def __init__(self, user_id: Optional[str] = None, username: Optional[str] = None):
        if user_id:
            message = f"用户ID {user_id} 不存在"
        elif username:
            message = f"用户名 {username} 不存在"
        else:
            message = "用户不存在"
        
        super().__init__(
            message=message,
            error_code="USER_NOT_FOUND",
            details={"user_id": user_id, "username": username}
        )


class UserAlreadyExistsError(UserException):
    """
    用户已存在异常
    """
    def __init__(self, field: str, value: str):
        message = f"{field} '{value}' 已被使用"
        super().__init__(
            message=message,
            error_code="USER_ALREADY_EXISTS",
            details={"field": field, "value": value}
        )


class AuthenticationError(UserException):
    """
    认证失败异常
    """
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_FAILED"
        )


class InvalidCredentialsError(AuthenticationError):
    """
    无效凭据异常
    """
    def __init__(self):
        super().__init__(message="用户名或密码错误")
        self.error_code = "INVALID_CREDENTIALS"


class TokenExpiredError(AuthenticationError):
    """
    令牌过期异常
    """
    def __init__(self):
        super().__init__(message="令牌已过期")
        self.error_code = "TOKEN_EXPIRED"


class InvalidTokenError(AuthenticationError):
    """
    无效令牌异常
    """
    def __init__(self):
        super().__init__(message="无效的令牌")
        self.error_code = "INVALID_TOKEN"


class PermissionDeniedError(UserException):
    """
    权限不足异常
    """
    def __init__(self, required_permission: Optional[str] = None):
        message = "权限不足"
        if required_permission:
            message = f"需要权限: {required_permission}"
        
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            details={"required_permission": required_permission}
        )


class AccountLockedError(UserException):
    """
    账户被锁定异常
    """
    def __init__(self, unlock_time: Optional[str] = None):
        message = "账户已被锁定"
        if unlock_time:
            message = f"账户已被锁定，解锁时间: {unlock_time}"
        
        super().__init__(
            message=message,
            error_code="ACCOUNT_LOCKED",
            details={"unlock_time": unlock_time}
        )


class WeakPasswordError(UserException):
    """
    密码强度不足异常
    """
    def __init__(self, requirements: list):
        message = "密码强度不足"
        super().__init__(
            message=message,
            error_code="WEAK_PASSWORD",
            details={"requirements": requirements}
        )


class RateLimitExceededError(UserException):
    """
    请求频率限制异常
    """
    def __init__(self, retry_after: Optional[int] = None):
        message = "请求过于频繁，请稍后再试"
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )


class DatabaseError(CashUpException):
    """
    数据库操作异常
    """
    def __init__(self, message: str = "数据库操作失败", operation: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details={"operation": operation}
        )


class RedisError(CashUpException):
    """
    Redis操作异常
    """
    def __init__(self, message: str = "Redis操作失败", operation: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="REDIS_ERROR",
            details={"operation": operation}
        )


# 异常处理器
async def cashup_exception_handler(request: Request, exc: CashUpException) -> JSONResponse:
    """
    CashUp自定义异常处理器
    """
    logger.error(f"CashUp异常: {exc.error_code} - {exc.message}", extra={
        "error_code": exc.error_code,
        "details": exc.details,
        "path": request.url.path,
        "method": request.method
    })
    
    # 根据异常类型确定HTTP状态码
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    if isinstance(exc, UserNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, UserAlreadyExistsError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, (AuthenticationError, InvalidCredentialsError, InvalidTokenError)):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, TokenExpiredError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, PermissionDeniedError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, AccountLockedError):
        status_code = status.HTTP_423_LOCKED
    elif isinstance(exc, (WeakPasswordError, RateLimitExceededError)):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, DatabaseError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exc, RedisError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    HTTP异常处理器
    """
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}", extra={
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": {},
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    请求验证异常处理器
    """
    logger.warning(f"请求验证失败: {exc.errors()}", extra={
        "errors": exc.errors(),
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "message": "请求参数验证失败",
            "details": {
                "errors": exc.errors()
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器
    """
    logger.error(f"未处理的异常: {type(exc).__name__} - {str(exc)}", extra={
        "exception_type": type(exc).__name__,
        "path": request.url.path,
        "method": request.method
    }, exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误",
            "details": {},
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )