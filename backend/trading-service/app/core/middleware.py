#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易服务中间件

提供请求日志、性能监控、安全检查等中间件功能
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from .config import settings


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录所有HTTP请求的详细信息
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("cashup.trading.middleware")
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        处理请求并记录日志
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        start_time = time.time()
        
        # 记录请求开始
        self.logger.info(
            f"请求开始: {request.method} {request.url.path}"
        )
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录请求完成
        self.logger.info(
            f"请求完成: {request.method} {request.url.path} - "
            f"{response.status_code} - {process_time:.3f}s"
        )
        
        return response


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件
    
    监控请求处理时间并添加性能头
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        处理请求并添加性能监控
        
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
        
        # 添加性能头
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Service"] = "trading-service"
        
        # 如果处理时间过长，记录警告
        if process_time > 1.0:  # 超过1秒
            logging.getLogger("cashup.trading.performance").warning(
                f"Slow request: {request.method} {request.url.path} - {process_time:.3f}s"
            )
        
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    安全中间件
    
    添加安全头和基本安全检查
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        处理请求并添加安全检查
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        # 处理请求
        response = await call_next(request)
        
        # 添加安全头
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response: Response) -> None:
        """
        添加安全响应头
        
        Args:
            response: HTTP响应
        """
        # 基本安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 生产环境额外安全头
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    限流中间件
    
    基于IP地址的简单限流实现
    """
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}  # 简单内存存储，生产环境应使用Redis
        self.logger = logging.getLogger("cashup.trading.ratelimit")
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        处理请求并检查限流
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 检查限流
        if await self._is_rate_limited(client_ip):
            self.logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # 记录请求
        await self._record_request(client_ip)
        
        # 处理请求
        response = await call_next(request)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址
        
        Args:
            request: HTTP请求
            
        Returns:
            str: 客户端IP地址
        """
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直接连接IP
        return request.client.host if request.client else "unknown"
    
    async def _is_rate_limited(self, client_ip: str) -> bool:
        """
        检查是否超过限流
        
        Args:
            client_ip: 客户端IP
            
        Returns:
            bool: 是否被限流
        """
        current_time = time.time()
        
        # 清理过期记录
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                timestamp for timestamp in self.request_counts[client_ip]
                if current_time - timestamp < self.window_seconds
            ]
        
        # 检查请求数量
        request_count = len(self.request_counts.get(client_ip, []))
        return request_count >= self.max_requests
    
    async def _record_request(self, client_ip: str) -> None:
        """
        记录请求时间
        
        Args:
            client_ip: 客户端IP
        """
        current_time = time.time()
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        self.request_counts[client_ip].append(current_time)