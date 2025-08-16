#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理中间件

统一处理应用程序中的异常和错误。
"""

import time
import traceback
import logging
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import jwt

from .logging import get_request_id

logger = logging.getLogger(__name__)


class CustomHTTPException(HTTPException):
    """
    自定义HTTP异常类
    
    扩展FastAPI的HTTPException，添加更多错误信息。
    """
    
    def __init__(
        self,
        status_code: int,
        detail: str = None,
        headers: dict = None,
        error_code: str = None,
        error_data: dict = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.error_data = error_data or {}


class ErrorResponse:
    """
    标准错误响应格式
    """
    
    def __init__(
        self,
        error: str,
        message: str,
        status_code: int,
        request_id: str = None,
        error_code: str = None,
        details: dict = None,
        timestamp: float = None
    ):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        Returns:
            dict: 错误响应字典
        """
        response = {
            "error": self.error,
            "message": self.message,
            "status_code": self.status_code,
            "timestamp": self.timestamp
        }
        
        if self.request_id:
            response["request_id"] = self.request_id
        
        if self.error_code:
            response["error_code"] = self.error_code
        
        if self.details:
            response["details"] = self.details
        
        return response


async def http_exception_handler(
    request: Request, 
    exc: Union[HTTPException, CustomHTTPException]
) -> JSONResponse:
    """
    HTTP异常处理器
    
    Args:
        request: HTTP请求对象
        exc: HTTP异常
        
    Returns:
        JSONResponse: JSON错误响应
    """
    request_id = get_request_id(request)
    
    # 记录异常信息
    logger.warning(
        f"HTTP异常 - ID: {request_id}, "
        f"状态码: {exc.status_code}, "
        f"详情: {exc.detail}, "
        f"路径: {request.url.path}"
    )
    
    # 构建错误响应
    error_response = ErrorResponse(
        error="HTTP_ERROR",
        message=exc.detail or "HTTP错误",
        status_code=exc.status_code,
        request_id=request_id,
        error_code=getattr(exc, "error_code", None),
        details=getattr(exc, "error_data", {})
    )
    
    headers = {"X-Request-ID": request_id}
    if hasattr(exc, "headers") and exc.headers:
        headers.update(exc.headers)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict(),
        headers=headers
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
        JSONResponse: JSON错误响应
    """
    request_id = get_request_id(request)
    
    # 提取验证错误详情
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    # 记录验证错误
    logger.warning(
        f"请求验证失败 - ID: {request_id}, "
        f"路径: {request.url.path}, "
        f"错误数量: {len(validation_errors)}"
    )
    
    # 构建错误响应
    error_response = ErrorResponse(
        error="VALIDATION_ERROR",
        message="请求参数验证失败",
        status_code=422,
        request_id=request_id,
        error_code="INVALID_INPUT",
        details={"validation_errors": validation_errors}
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.to_dict(),
        headers={"X-Request-ID": request_id}
    )


async def sqlalchemy_exception_handler(
    request: Request, 
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    SQLAlchemy异常处理器
    
    Args:
        request: HTTP请求对象
        exc: SQLAlchemy异常
        
    Returns:
        JSONResponse: JSON错误响应
    """
    request_id = get_request_id(request)
    
    # 记录数据库错误
    logger.error(
        f"数据库错误 - ID: {request_id}, "
        f"类型: {type(exc).__name__}, "
        f"详情: {str(exc)}",
        exc_info=True
    )
    
    # 根据异常类型确定错误信息
    if isinstance(exc, IntegrityError):
        error_message = "数据完整性约束违反"
        error_code = "INTEGRITY_ERROR"
        status_code = 409
    else:
        error_message = "数据库操作失败"
        error_code = "DATABASE_ERROR"
        status_code = 500
    
    # 构建错误响应
    error_response = ErrorResponse(
        error="DATABASE_ERROR",
        message=error_message,
        status_code=status_code,
        request_id=request_id,
        error_code=error_code
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.to_dict(),
        headers={"X-Request-ID": request_id}
    )


async def jwt_exception_handler(
    request: Request, 
    exc: jwt.PyJWTError
) -> JSONResponse:
    """
    JWT异常处理器
    
    Args:
        request: HTTP请求对象
        exc: JWT异常
        
    Returns:
        JSONResponse: JSON错误响应
    """
    request_id = get_request_id(request)
    
    # 记录JWT错误
    logger.warning(
        f"JWT错误 - ID: {request_id}, "
        f"类型: {type(exc).__name__}, "
        f"详情: {str(exc)}"
    )
    
    # 根据异常类型确定错误信息
    if isinstance(exc, jwt.ExpiredSignatureError):
        error_message = "Token已过期"
        error_code = "TOKEN_EXPIRED"
    elif isinstance(exc, jwt.InvalidTokenError):
        error_message = "无效的Token"
        error_code = "INVALID_TOKEN"
    else:
        error_message = "Token验证失败"
        error_code = "TOKEN_ERROR"
    
    # 构建错误响应
    error_response = ErrorResponse(
        error="AUTHENTICATION_ERROR",
        message=error_message,
        status_code=401,
        request_id=request_id,
        error_code=error_code
    )
    
    return JSONResponse(
        status_code=401,
        content=error_response.to_dict(),
        headers={
            "X-Request-ID": request_id,
            "WWW-Authenticate": "Bearer"
        }
    )


async def general_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """
    通用异常处理器
    
    Args:
        request: HTTP请求对象
        exc: 通用异常
        
    Returns:
        JSONResponse: JSON错误响应
    """
    request_id = get_request_id(request)
    
    # 记录未处理的异常
    logger.error(
        f"未处理异常 - ID: {request_id}, "
        f"类型: {type(exc).__name__}, "
        f"详情: {str(exc)}, "
        f"路径: {request.url.path}",
        exc_info=True
    )
    
    # 构建错误响应
    error_response = ErrorResponse(
        error="INTERNAL_ERROR",
        message="内部服务器错误",
        status_code=500,
        request_id=request_id,
        error_code="UNEXPECTED_ERROR"
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.to_dict(),
        headers={"X-Request-ID": request_id}
    )


def setup_error_handlers(app: FastAPI) -> None:
    """
    设置错误处理器
    
    Args:
        app: FastAPI应用实例
    """
    try:
        # 注册异常处理器
        app.add_exception_handler(HTTPException, http_exception_handler)
        app.add_exception_handler(CustomHTTPException, http_exception_handler)
        app.add_exception_handler(StarletteHTTPException, http_exception_handler)
        app.add_exception_handler(RequestValidationError, validation_exception_handler)
        app.add_exception_handler(ValidationError, validation_exception_handler)
        app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
        app.add_exception_handler(jwt.PyJWTError, jwt_exception_handler)
        app.add_exception_handler(Exception, general_exception_handler)
        
        logger.info("错误处理器设置完成")
        
    except Exception as e:
        logger.error(f"设置错误处理器失败: {e}")
        raise


def raise_http_error(
    status_code: int,
    message: str,
    error_code: str = None,
    error_data: dict = None
) -> None:
    """
    抛出自定义HTTP错误
    
    Args:
        status_code: HTTP状态码
        message: 错误消息
        error_code: 错误代码
        error_data: 错误数据
        
    Raises:
        CustomHTTPException: 自定义HTTP异常
    """
    raise CustomHTTPException(
        status_code=status_code,
        detail=message,
        error_code=error_code,
        error_data=error_data
    )


def raise_validation_error(
    field: str,
    message: str,
    value: any = None
) -> None:
    """
    抛出验证错误
    
    Args:
        field: 字段名
        message: 错误消息
        value: 字段值
        
    Raises:
        CustomHTTPException: 自定义HTTP异常
    """
    raise CustomHTTPException(
        status_code=422,
        detail="参数验证失败",
        error_code="VALIDATION_ERROR",
        error_data={
            "field": field,
            "message": message,
            "value": value
        }
    )


def raise_not_found_error(resource: str, identifier: any = None) -> None:
    """
    抛出资源不存在错误
    
    Args:
        resource: 资源名称
        identifier: 资源标识符
        
    Raises:
        CustomHTTPException: 自定义HTTP异常
    """
    message = f"{resource}不存在"
    if identifier:
        message += f": {identifier}"
    
    raise CustomHTTPException(
        status_code=404,
        detail=message,
        error_code="RESOURCE_NOT_FOUND",
        error_data={
            "resource": resource,
            "identifier": identifier
        }
    )


def raise_permission_error(action: str, resource: str = None) -> None:
    """
    抛出权限不足错误
    
    Args:
        action: 操作名称
        resource: 资源名称
        
    Raises:
        CustomHTTPException: 自定义HTTP异常
    """
    message = f"无权限执行操作: {action}"
    if resource:
        message += f" (资源: {resource})"
    
    raise CustomHTTPException(
        status_code=403,
        detail=message,
        error_code="PERMISSION_DENIED",
        error_data={
            "action": action,
            "resource": resource
        }
    )