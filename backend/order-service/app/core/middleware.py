#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务中间件

定义各种中间件组件
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录所有HTTP请求的详细信息
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录日志
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        logger.info(
            f"Request started - ID: {request_id}, Method: {request.method}, "
            f"URL: {request.url}, Client: {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"Request completed - ID: {request_id}, Status: {response.status_code}, "
                f"Time: {process_time:.3f}s"
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误信息
            logger.error(
                f"Request failed - ID: {request_id}, Error: {str(e)}, "
                f"Time: {process_time:.3f}s"
            )
            
            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "message": "An unexpected error occurred"
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Process-Time": str(process_time)
                }
            )


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件
    
    监控请求性能并记录慢请求
    """
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并监控性能
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        start_time = time.time()
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 检查是否为慢请求
        if process_time > self.slow_request_threshold:
            request_id = getattr(request.state, 'request_id', 'unknown')
            logger.warning(
                f"Slow request detected - ID: {request_id}, "
                f"Method: {request.method}, URL: {request.url}, "
                f"Time: {process_time:.3f}s"
            )
        
        # 添加性能头
        response.headers["X-Response-Time"] = f"{process_time:.3f}"
        
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    安全中间件
    
    添加安全相关的HTTP头
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并添加安全头
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 移除服务器信息
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件
    
    简单的内存速率限制实现
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # {client_ip: [timestamp, ...]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并检查速率限制
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 跳过健康检查和内部请求
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        current_time = time.time()
        
        # 清理过期记录
        if client_ip in self.requests:
            self.requests[client_ip] = [
                timestamp for timestamp in self.requests[client_ip]
                if current_time - timestamp < 60  # 保留最近1分钟的记录
            ]
        else:
            self.requests[client_ip] = []
        
        # 检查速率限制
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for client {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.requests_per_minute} requests per minute allowed",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # 记录请求
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    错误处理中间件
    
    统一处理未捕获的异常
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并捕获异常
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
            
            logger.error(
                f"Unhandled exception - ID: {request_id}, "
                f"Method: {request.method}, URL: {request.url}, "
                f"Error: {str(e)}",
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "message": "An unexpected error occurred"
                },
                headers={"X-Request-ID": request_id}
            )


def setup_cors_middleware(app):
    """
    设置CORS中间件
    
    Args:
        app: FastAPI应用实例
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-Response-Time"]
    )


def setup_middleware(app):
    """
    设置所有中间件
    
    Args:
        app: FastAPI应用实例
    """
    # 错误处理中间件（最外层）
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 安全中间件
    app.add_middleware(SecurityMiddleware)
    
    # 性能监控中间件
    app.add_middleware(PerformanceMiddleware, slow_request_threshold=2.0)
    
    # 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 速率限制中间件
    if settings.ENVIRONMENT == "production":
        app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    
    # CORS中间件（最内层）
    setup_cors_middleware(app)