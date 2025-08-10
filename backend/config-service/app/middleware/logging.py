#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 日志中间件

提供请求日志记录和性能监控功能
"""

import time
import uuid
import json
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    日志中间件
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.excluded_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求日志
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录开始时间
        start_time = time.time()
        
        # 获取客户端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 获取用户信息
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)
        
        # 记录请求开始
        if not any(request.url.path.startswith(path) for path in self.excluded_paths):
            logger.info(
                f"Request started",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "user_id": str(user_id) if user_id else None,
                    "username": username,
                    "timestamp": start_time
                }
            )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求完成
            if not any(request.url.path.startswith(path) for path in self.excluded_paths):
                log_data = {
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4),
                    "client_ip": client_ip,
                    "user_id": str(user_id) if user_id else None,
                    "username": username,
                    "response_size": len(response.body) if hasattr(response, 'body') else 0
                }
                
                # 根据状态码选择日志级别
                if response.status_code >= 500:
                    logger.error(f"Request completed with server error", extra=log_data)
                elif response.status_code >= 400:
                    logger.warning(f"Request completed with client error", extra=log_data)
                else:
                    logger.info(f"Request completed successfully", extra=log_data)
                
                # 性能监控
                if process_time > self.settings.SLOW_REQUEST_THRESHOLD:
                    logger.warning(
                        f"Slow request detected",
                        extra={
                            **log_data,
                            "slow_request": True,
                            "threshold": self.settings.SLOW_REQUEST_THRESHOLD
                        }
                    )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录异常
            logger.error(
                f"Request failed with exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "process_time": round(process_time, 4),
                    "client_ip": client_ip,
                    "user_id": str(user_id) if user_id else None,
                    "username": username,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            # 重新抛出异常
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址
        """
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直接连接的IP
        return request.client.host if request.client else "unknown"


class StructuredLogger:
    """
    结构化日志记录器
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.settings = get_settings()
    
    def _log(self, level: str, message: str, **kwargs):
        """
        记录结构化日志
        """
        log_data = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "service": "config-service",
            **kwargs
        }
        
        # 根据配置选择日志格式
        if self.settings.LOG_FORMAT == "json":
            log_message = json.dumps(log_data, ensure_ascii=False)
        else:
            log_message = f"{message} - {json.dumps(kwargs, ensure_ascii=False)}"
        
        getattr(self.logger, level.lower())(log_message)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self._log("CRITICAL", message, **kwargs)


# 创建全局日志实例
config_logger = StructuredLogger("config_service")
api_logger = StructuredLogger("api")
db_logger = StructuredLogger("database")
cache_logger = StructuredLogger("cache")


def log_config_operation(
    operation: str,
    config_id: str = None,
    config_key: str = None,
    user_id: str = None,
    success: bool = True,
    error: str = None,
    **kwargs
):
    """
    记录配置操作日志
    """
    log_data = {
        "operation": operation,
        "config_id": config_id,
        "config_key": config_key,
        "user_id": user_id,
        "success": success,
        **kwargs
    }
    
    if error:
        log_data["error"] = error
        config_logger.error(f"Config operation failed: {operation}", **log_data)
    else:
        config_logger.info(f"Config operation completed: {operation}", **log_data)


def log_template_operation(
    operation: str,
    template_id: str = None,
    template_name: str = None,
    user_id: str = None,
    success: bool = True,
    error: str = None,
    **kwargs
):
    """
    记录模板操作日志
    """
    log_data = {
        "operation": operation,
        "template_id": template_id,
        "template_name": template_name,
        "user_id": user_id,
        "success": success,
        **kwargs
    }
    
    if error:
        log_data["error"] = error
        config_logger.error(f"Template operation failed: {operation}", **log_data)
    else:
        config_logger.info(f"Template operation completed: {operation}", **log_data)


def log_database_operation(
    operation: str,
    table: str = None,
    duration: float = None,
    success: bool = True,
    error: str = None,
    **kwargs
):
    """
    记录数据库操作日志
    """
    log_data = {
        "operation": operation,
        "table": table,
        "duration": duration,
        "success": success,
        **kwargs
    }
    
    if error:
        log_data["error"] = error
        db_logger.error(f"Database operation failed: {operation}", **log_data)
    else:
        db_logger.info(f"Database operation completed: {operation}", **log_data)


def log_cache_operation(
    operation: str,
    key: str = None,
    hit: bool = None,
    duration: float = None,
    success: bool = True,
    error: str = None,
    **kwargs
):
    """
    记录缓存操作日志
    """
    log_data = {
        "operation": operation,
        "key": key,
        "hit": hit,
        "duration": duration,
        "success": success,
        **kwargs
    }
    
    if error:
        log_data["error"] = error
        cache_logger.error(f"Cache operation failed: {operation}", **log_data)
    else:
        cache_logger.debug(f"Cache operation completed: {operation}", **log_data)