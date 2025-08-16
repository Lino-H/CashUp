#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 异常处理

自定义异常类和错误处理
"""

import logging
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE
)

logger = logging.getLogger(__name__)


class MonitoringException(Exception):
    """监控服务基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }
    
    def __str__(self) -> str:
        return f"{self.error_code}: {self.message}"


class ValidationError(MonitoringException):
    """数据验证异常"""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=HTTP_422_UNPROCESSABLE_ENTITY
        )


class NotFoundError(MonitoringException):
    """资源不存在异常"""
    
    def __init__(self, resource: str, identifier: Union[str, int] = None, **kwargs):
        message = f"{resource} not found"
        if identifier:
            message += f" (ID: {identifier})"
        
        details = kwargs.get('details', {})
        details['resource'] = resource
        if identifier:
            details['identifier'] = str(identifier)
        
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details=details,
            status_code=HTTP_404_NOT_FOUND
        )


class ConflictError(MonitoringException):
    """资源冲突异常"""
    
    def __init__(self, message: str, resource: str = None, **kwargs):
        details = kwargs.get('details', {})
        if resource:
            details['resource'] = resource
        
        super().__init__(
            message=message,
            error_code="CONFLICT",
            details=details,
            status_code=HTTP_409_CONFLICT
        )


class AuthenticationError(MonitoringException):
    """认证异常"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=kwargs.get('details', {}),
            status_code=HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(MonitoringException):
    """授权异常"""
    
    def __init__(self, message: str = "Access denied", resource: str = None, action: str = None, **kwargs):
        details = kwargs.get('details', {})
        if resource:
            details['resource'] = resource
        if action:
            details['action'] = action
        
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            status_code=HTTP_403_FORBIDDEN
        )


class ServiceUnavailableError(MonitoringException):
    """服务不可用异常"""
    
    def __init__(self, service: str = None, message: str = None, **kwargs):
        if not message:
            message = f"Service {service} is unavailable" if service else "Service unavailable"
        
        details = kwargs.get('details', {})
        if service:
            details['service'] = service
        
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details=details,
            status_code=HTTP_503_SERVICE_UNAVAILABLE
        )


# 业务模块特定异常
class MetricsError(MonitoringException):
    """指标相关异常"""
    
    def __init__(self, message: str, metric_name: str = None, **kwargs):
        details = kwargs.get('details', {})
        if metric_name:
            details['metric_name'] = metric_name
        
        super().__init__(
            message=message,
            error_code="METRICS_ERROR",
            details=details,
            status_code=kwargs.get('status_code', HTTP_400_BAD_REQUEST)
        )


class MetricsCollectionError(MetricsError):
    """指标采集异常"""
    
    def __init__(self, message: str, metric_name: str = None, source: str = None, **kwargs):
        details = kwargs.get('details', {})
        if source:
            details['source'] = source
        
        super().__init__(
            message=message,
            metric_name=metric_name,
            details=details,
            status_code=kwargs.get('status_code', HTTP_500_INTERNAL_SERVER_ERROR)
        )
        self.error_code = "METRICS_COLLECTION_ERROR"


class DataStorageError(MonitoringException):
    """数据存储异常"""
    
    def __init__(self, message: str, operation: str = None, table: str = None, **kwargs):
        details = kwargs.get('details', {})
        if operation:
            details['operation'] = operation
        if table:
            details['table'] = table
        
        super().__init__(
            message=message,
            error_code="DATA_STORAGE_ERROR",
            details=details,
            status_code=kwargs.get('status_code', HTTP_500_INTERNAL_SERVER_ERROR)
        )


class AlertsError(MonitoringException):
    """告警相关异常"""
    
    def __init__(self, message: str, alert_id: str = None, **kwargs):
        details = kwargs.get('details', {})
        if alert_id:
            details['alert_id'] = alert_id
        
        super().__init__(
            message=message,
            error_code="ALERTS_ERROR",
            details=details,
            status_code=kwargs.get('status_code', HTTP_400_BAD_REQUEST)
        )


class AlertProcessingError(AlertsError):
    """告警处理异常"""
    
    def __init__(self, message: str, alert_id: str = None, processing_stage: str = None, **kwargs):
        details = kwargs.get('details', {})
        if processing_stage:
            details['processing_stage'] = processing_stage
        
        super().__init__(
            message=message,
            alert_id=alert_id,
            details=details,
            status_code=kwargs.get('status_code', HTTP_500_INTERNAL_SERVER_ERROR)
        )
        self.error_code = "ALERT_PROCESSING_ERROR"


class HealthCheckError(MonitoringException):
    """健康检查相关异常"""
    
    def __init__(self, message: str, check_name: str = None, **kwargs):
        details = kwargs.get('details', {})
        if check_name:
            details['check_name'] = check_name
        
        super().__init__(
            message=message,
            error_code="HEALTH_CHECK_ERROR",
            details=details,
            status_code=kwargs.get('status_code', HTTP_400_BAD_REQUEST)
        )


class DashboardError(MonitoringException):
    """仪表板相关异常"""
    
    def __init__(self, message: str, dashboard_id: str = None, **kwargs):
        details = kwargs.get('details', {})
        if dashboard_id:
            details['dashboard_id'] = dashboard_id
        
        super().__init__(
            message=message,
            error_code="DASHBOARD_ERROR",
            details=details,
            status_code=kwargs.get('status_code', HTTP_400_BAD_REQUEST)
        )


class SystemError(MonitoringException):
    """系统相关异常"""
    
    def __init__(self, message: str, component: str = None, **kwargs):
        details = kwargs.get('details', {})
        if component:
            details['component'] = component
        
        super().__init__(
            message=message,
            error_code="SYSTEM_ERROR",
            details=details,
            status_code=kwargs.get('status_code', HTTP_500_INTERNAL_SERVER_ERROR)
        )


# 数据库相关异常
class DatabaseError(MonitoringException):
    """数据库异常"""
    
    def __init__(self, message: str, operation: str = None, **kwargs):
        details = kwargs.get('details', {})
        if operation:
            details['operation'] = operation
        
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


class CacheError(MonitoringException):
    """缓存异常"""
    
    def __init__(self, message: str, key: str = None, **kwargs):
        details = kwargs.get('details', {})
        if key:
            details['key'] = key
        
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=details,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


# 外部服务异常
class ExternalServiceError(MonitoringException):
    """外部服务异常"""
    
    def __init__(self, message: str, service: str = None, endpoint: str = None, **kwargs):
        details = kwargs.get('details', {})
        if service:
            details['service'] = service
        if endpoint:
            details['endpoint'] = endpoint
        
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
            status_code=HTTP_503_SERVICE_UNAVAILABLE
        )


# 配置异常
class ConfigurationError(MonitoringException):
    """配置异常"""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        details = kwargs.get('details', {})
        if config_key:
            details['config_key'] = config_key
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR
        )


# 限流异常
class RateLimitError(MonitoringException):
    """限流异常"""
    
    def __init__(self, message: str = "Rate limit exceeded", limit: int = None, window: int = None, **kwargs):
        details = kwargs.get('details', {})
        if limit:
            details['limit'] = limit
        if window:
            details['window'] = window
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details,
            status_code=HTTP_429_TOO_MANY_REQUESTS
        )


# 异常处理器
async def monitoring_exception_handler(request: Request, exc: MonitoringException) -> JSONResponse:
    """监控异常处理器"""
    logger.error(
        f"MonitoringException: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.error(
        f"HTTPException: {exc.status_code} - {exc.detail}",
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


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {
                    "type": type(exc).__name__
                }
            }
        }
    )


# 异常工具函数
def raise_not_found(resource: str, identifier: Union[str, int] = None, **kwargs):
    """抛出资源不存在异常"""
    raise NotFoundError(resource=resource, identifier=identifier, **kwargs)


def raise_validation_error(message: str, field: str = None, value: Any = None, **kwargs):
    """抛出验证异常"""
    raise ValidationError(message=message, field=field, value=value, **kwargs)


def raise_conflict(message: str, resource: str = None, **kwargs):
    """抛出冲突异常"""
    raise ConflictError(message=message, resource=resource, **kwargs)


def raise_unauthorized(message: str = "Authentication required", **kwargs):
    """抛出认证异常"""
    raise AuthenticationError(message=message, **kwargs)


def raise_forbidden(message: str = "Access denied", resource: str = None, action: str = None, **kwargs):
    """抛出授权异常"""
    raise AuthorizationError(message=message, resource=resource, action=action, **kwargs)


def raise_service_unavailable(service: str = None, message: str = None, **kwargs):
    """抛出服务不可用异常"""
    raise ServiceUnavailableError(service=service, message=message, **kwargs)


# 异常装饰器
def handle_exceptions(default_exception: type = MonitoringException):
    """异常处理装饰器"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except MonitoringException:
                raise
            except Exception as e:
                logger.error(f"Unhandled exception in {func.__name__}: {e}", exc_info=True)
                raise default_exception(f"Error in {func.__name__}: {str(e)}")
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except MonitoringException:
                raise
            except Exception as e:
                logger.error(f"Unhandled exception in {func.__name__}: {e}", exc_info=True)
                raise default_exception(f"Error in {func.__name__}: {str(e)}")
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 错误码常量
class ErrorCodes:
    """错误码常量"""
    
    # 通用错误
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    
    # 业务错误
    METRICS_ERROR = "METRICS_ERROR"
    ALERTS_ERROR = "ALERTS_ERROR"
    HEALTH_CHECK_ERROR = "HEALTH_CHECK_ERROR"
    DASHBOARD_ERROR = "DASHBOARD_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    
    # 技术错误
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


# 添加缺失的状态码
HTTP_429_TOO_MANY_REQUESTS = 429