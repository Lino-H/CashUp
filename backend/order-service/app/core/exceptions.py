#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务异常处理

定义自定义异常和异常处理器
"""

import logging
from typing import Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class CashUpException(Exception):
    """
    CashUp系统基础异常
    """
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class OrderServiceException(CashUpException):
    """
    订单服务基础异常
    """
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class OrderNotFoundError(OrderServiceException):
    """
    订单未找到异常
    """
    def __init__(self, order_id: str):
        super().__init__(
            message=f"Order {order_id} not found",
            error_code="ORDER_NOT_FOUND"
        )
        self.order_id = order_id


class OrderValidationError(OrderServiceException):
    """
    订单验证异常
    """
    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=message,
            error_code="ORDER_VALIDATION_ERROR"
        )
        self.field = field


class OrderStateError(OrderServiceException):
    """
    订单状态异常
    """
    def __init__(self, message: str, current_state: str = None):
        super().__init__(
            message=message,
            error_code="ORDER_STATE_ERROR"
        )
        self.current_state = current_state


class ExchangeError(OrderServiceException):
    """
    交易所异常
    """
    def __init__(self, message: str, exchange_name: str = None):
        super().__init__(
            message=message,
            error_code="EXCHANGE_ERROR"
        )
        self.exchange_name = exchange_name


class InsufficientBalanceError(OrderServiceException):
    """
    余额不足异常
    """
    def __init__(self, asset: str, required: str, available: str):
        super().__init__(
            message=f"Insufficient {asset} balance. Required: {required}, Available: {available}",
            error_code="INSUFFICIENT_BALANCE"
        )
        self.asset = asset
        self.required = required
        self.available = available


class RateLimitError(OrderServiceException):
    """
    速率限制异常
    """
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED"
        )


class DatabaseError(OrderServiceException):
    """
    数据库异常
    """
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR"
        )
        self.original_error = original_error


class ExternalServiceError(OrderServiceException):
    """
    外部服务异常
    """
    def __init__(self, service_name: str, message: str):
        super().__init__(
            message=f"{service_name} service error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR"
        )
        self.service_name = service_name


async def order_not_found_handler(request: Request, exc: OrderNotFoundError) -> JSONResponse:
    """
    订单未找到异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": {
                "order_id": exc.order_id
            }
        }
    )


async def order_validation_error_handler(request: Request, exc: OrderValidationError) -> JSONResponse:
    """
    订单验证异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": {
                "field": exc.field
            } if exc.field else None
        }
    )


async def order_state_error_handler(request: Request, exc: OrderStateError) -> JSONResponse:
    """
    订单状态异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": {
                "current_state": exc.current_state
            } if exc.current_state else None
        }
    )


async def exchange_error_handler(request: Request, exc: ExchangeError) -> JSONResponse:
    """
    交易所异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": {
                "exchange_name": exc.exchange_name
            } if exc.exchange_name else None
        }
    )


async def insufficient_balance_error_handler(request: Request, exc: InsufficientBalanceError) -> JSONResponse:
    """
    余额不足异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": {
                "asset": exc.asset,
                "required": exc.required,
                "available": exc.available
            }
        }
    )


async def rate_limit_error_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    """
    速率限制异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "retry_after": 60
        },
        headers={"Retry-After": "60"}
    )


async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """
    数据库异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.error(f"Database error: {exc.message}", exc_info=exc.original_error)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": exc.error_code,
            "message": "Database operation failed",
            "details": None  # 不暴露内部错误详情
        }
    )


async def external_service_error_handler(request: Request, exc: ExternalServiceError) -> JSONResponse:
    """
    外部服务异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": {
                "service_name": exc.service_name
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    请求验证异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": errors
        }
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    SQLAlchemy异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.error(f"SQLAlchemy error: {str(exc)}", exc_info=True)
    
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "INTEGRITY_ERROR",
                "message": "Data integrity constraint violation"
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "DATABASE_ERROR",
            "message": "Database operation failed"
        }
    )


async def cashup_exception_handler(request: Request, exc: CashUpException) -> JSONResponse:
    """
    CashUp异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.error_code or "CASHUP_ERROR",
            "message": exc.message
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器
    
    Args:
        request: HTTP请求
        exc: 异常实例
        
    Returns:
        JSONResponse: 错误响应
    """
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        f"Unhandled exception - Request ID: {request_id}, "
        f"Method: {request.method}, URL: {request.url}, "
        f"Error: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "request_id": request_id
        }
    )


def setup_exception_handlers(app):
    """
    设置异常处理器
    
    Args:
        app: FastAPI应用实例
    """
    # 基础异常处理器
    app.add_exception_handler(CashUpException, cashup_exception_handler)
    
    # 自定义异常处理器
    app.add_exception_handler(OrderNotFoundError, order_not_found_handler)
    app.add_exception_handler(OrderValidationError, order_validation_error_handler)
    app.add_exception_handler(OrderStateError, order_state_error_handler)
    app.add_exception_handler(ExchangeError, exchange_error_handler)
    app.add_exception_handler(InsufficientBalanceError, insufficient_balance_error_handler)
    app.add_exception_handler(RateLimitError, rate_limit_error_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(ExternalServiceError, external_service_error_handler)
    
    # 标准异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    
    # 通用异常处理器（最后添加）
    app.add_exception_handler(Exception, generic_exception_handler)