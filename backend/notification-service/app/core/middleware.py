#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知服务中间件

定义和配置各种中间件
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录所有HTTP请求的详细信息
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """
        处理请求并记录日志
        
        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            StarletteResponse: HTTP响应
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent", "")
            }
        )
        
        # 将请求ID添加到请求状态中
        request.state.request_id = request_id
        
        try:
            # 调用下一个中间件或路由处理器
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4)
                }
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录异常信息
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "process_time": round(process_time, 4)
                },
                exc_info=True
            )
            
            # 重新抛出异常
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全头中间件
    
    添加安全相关的HTTP头
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """
        添加安全头到响应中
        
        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            StarletteResponse: 带有安全头的HTTP响应
        """
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件
    
    简单的内存速率限制实现
    """
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        """
        初始化速率限制中间件
        
        Args:
            app: FastAPI应用实例
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # 存储客户端请求记录
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """
        检查速率限制
        
        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            StarletteResponse: HTTP响应
        """
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 获取当前时间
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_expired_requests(current_time)
        
        # 检查客户端请求记录
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        client_requests = self.requests[client_ip]
        
        # 过滤时间窗口内的请求
        window_start = current_time - self.window_seconds
        recent_requests = [req_time for req_time in client_requests if req_time > window_start]
        
        # 检查是否超过限制
        if len(recent_requests) >= self.max_requests:
            logger.warning(
                f"Rate limit exceeded for client {client_ip}",
                extra={
                    "client_ip": client_ip,
                    "requests_count": len(recent_requests),
                    "max_requests": self.max_requests
                }
            )
            
            return Response(
                content='{"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"}}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + self.window_seconds))
                }
            )
        
        # 记录当前请求
        recent_requests.append(current_time)
        self.requests[client_ip] = recent_requests
        
        # 处理请求
        response = await call_next(request)
        
        # 添加速率限制头
        remaining = self.max_requests - len(recent_requests)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))
        
        return response
    
    def _cleanup_expired_requests(self, current_time: float):
        """
        清理过期的请求记录
        
        Args:
            current_time: 当前时间戳
        """
        window_start = current_time - self.window_seconds
        
        for client_ip in list(self.requests.keys()):
            # 过滤掉过期的请求
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] 
                if req_time > window_start
            ]
            
            # 如果没有请求记录，删除客户端记录
            if not self.requests[client_ip]:
                del self.requests[client_ip]


def setup_middleware(app: FastAPI):
    """
    设置中间件
    
    Args:
        app: FastAPI应用实例
    """
    # 添加请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 添加安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 添加速率限制中间件（每分钟最多100个请求）
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
    
    logger.info("Middleware setup completed")