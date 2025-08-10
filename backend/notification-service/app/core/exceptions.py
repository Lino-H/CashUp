#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知服务异常处理

定义自定义异常类和异常处理器
"""

import logging
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
import traceback

logger = logging.getLogger(__name__)


class NotificationServiceException(Exception):
    """
    通知服务基础异常类
    
    所有通知服务相关的异常都应该继承此类
    """
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or "NOTIFICATION_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class NotificationNotFoundError(NotificationServiceException):
    """
    通知未找到异常
    """
    def __init__(self, notification_id: str):
        super().__init__(
            message=f"Notification with ID {notification_id} not found",
            error_code="NOTIFICATION_NOT_FOUND",
            details={"notification_id": notification_id}
        )


class TemplateNotFoundError(NotificationServiceException):
    """
    模板未找到异常
    """
    def __init__(self, template_id: str):
        super().__init__(
            message=f"Template with ID {template_id} not found",
            error_code="TEMPLATE_NOT_FOUND",
            details={"template_id": template_id}
        )


class ChannelNotFoundError(NotificationServiceException):
    """
    通知渠道未找到异常
    """
    def __init__(self, channel_name: str):
        super().__init__(
            message=f"Notification channel '{channel_name}' not found",
            error_code="CHANNEL_NOT_FOUND",
            details={"channel_name": channel_name}
        )


class NotificationValidationError(NotificationServiceException):
    """
    通知验证异常
    """
    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=message,
            error_code="NOTIFICATION_VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class NotificationSendError(NotificationServiceException):
    """
    通知发送异常
    """
    def __init__(self, message: str, channel: str = None, recipient: str = None):
        super().__init__(
            message=message,
            error_code="NOTIFICATION_SEND_ERROR",
            details={
                "channel": channel,
                "recipient": recipient
            }
        )


class TemplateRenderError(NotificationServiceException):
    """
    模板渲染异常
    """
    def __init__(self, message: str, template_id: str = None):
        super().__init__(
            message=message,
            error_code="TEMPLATE_RENDER_ERROR",
            details={"template_id": template_id} if template_id else {}
        )


class RateLimitError(NotificationServiceException):
    """
    频率限制异常
    """
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED"
        )


class DatabaseError(NotificationServiceException):
    """
    数据库异常
    """
    def __init__(self, message: str, operation: str = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details={"operation": operation} if operation else {}
        )


# 异常处理器函数

async def notification_service_exception_handler(
    request: Request, 
    exc: NotificationServiceException
) -> JSONResponse:
    """
    通知服务异常处理器
    
    Args:
        request: HTTP请求对象
        exc: 通知服务异常
        
    Returns:
        JSONResponse: JSON格式的错误响应
    """
    logger.error(
        f"NotificationServiceException: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def http_exception_handler(
    request: Request, 
    exc: Union[HTTPException, StarletteHTTPException]
) -> JSONResponse:
    """
    HTTP异常处理器
    
    Args:
        request: HTTP请求对象
        exc: HTTP异常
        
    Returns:
        JSONResponse: JSON格式的错误响应
    """
    logger.warning(
        f"HTTP Exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {}
            }
        }
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    请求验证异常处理器
    
    Args:
        request: HTTP请求对象
        exc: 请求验证异常
        
    Returns:
        JSONResponse: JSON格式的错误响应
    """
    logger.warning(
        f"Validation Error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors()
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "validation_errors": exc.errors()
                }
            }
        }
    )


async def database_exception_handler(
    request: Request, 
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    数据库异常处理器
    
    Args:
        request: HTTP请求对象
        exc: SQLAlchemy异常
        
    Returns:
        JSONResponse: JSON格式的错误响应
    """
    logger.error(
        f"Database Error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Database operation failed",
                "details": {}
            }
        }
    )


async def generic_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """
    通用异常处理器
    
    Args:
        request: HTTP请求对象
        exc: 通用异常
        
    Returns:
        JSONResponse: JSON格式的错误响应
    """
    logger.error(
        f"Unhandled Exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        }
    )


def setup_exception_handlers(app: FastAPI):
    """
    设置异常处理器
    
    Args:
        app: FastAPI应用实例
    """
    # 注册自定义异常处理器
    app.add_exception_handler(NotificationServiceException, notification_service_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered successfully")