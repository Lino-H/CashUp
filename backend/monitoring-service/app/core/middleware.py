#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 监控服务中间件

定义请求处理中间件，包括日志、指标收集、限流等
"""

import time
import logging
import asyncio
from typing import Dict, Optional, Callable
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Prometheus指标
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'http_active_requests',
    'Number of active HTTP requests'
)

request_size = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

response_size = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录所有HTTP请求的详细信息
    """
    
    def __init__(self, app, log_body: bool = False):
        super().__init__(app)
        self.log_body = log_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录日志
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            Response: 响应对象
        """
        start_time = time.time()
        request_id = id(request)
        
        # 记录请求开始
        logger.info(
            f"Request started - ID: {request_id}, "
            f"Method: {request.method}, "
            f"URL: {request.url}, "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # 记录请求体（如果启用）
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    logger.debug(f"Request body - ID: {request_id}, Body: {body.decode('utf-8')[:1000]}")
            except Exception as e:
                logger.warning(f"Failed to read request body - ID: {request_id}, Error: {e}")
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求完成
            logger.info(
                f"Request completed - ID: {request_id}, "
                f"Status: {response.status_code}, "
                f"Duration: {process_time:.3f}s"
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = str(request_id)
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录异常
            process_time = time.time() - start_time
            logger.error(
                f"Request failed - ID: {request_id}, "
                f"Error: {str(e)}, "
                f"Duration: {process_time:.3f}s",
                exc_info=True
            )
            raise


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    指标收集中间件
    
    收集HTTP请求的Prometheus指标
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并收集指标
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            Response: 响应对象
        """
        start_time = time.time()
        method = request.method
        endpoint = self._get_endpoint(request)
        
        # 增加活跃请求数
        active_requests.inc()
        
        # 记录请求大小
        if hasattr(request, 'content_length') and request.content_length:
            request_size.labels(method=method, endpoint=endpoint).observe(request.content_length)
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            duration = time.time() - start_time
            
            # 记录指标
            request_count.labels(
                method=method,
                endpoint=endpoint,
                status_code=response.status_code
            ).inc()
            
            request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # 记录响应大小
            if hasattr(response, 'content_length') and response.content_length:
                response_size.labels(method=method, endpoint=endpoint).observe(response.content_length)
            
            return response
            
        except Exception as e:
            # 记录错误指标
            duration = time.time() - start_time
            request_count.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()
            
            request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            raise
        
        finally:
            # 减少活跃请求数
            active_requests.dec()
    
    def _get_endpoint(self, request: Request) -> str:
        """
        获取端点路径
        
        Args:
            request: 请求对象
            
        Returns:
            str: 端点路径
        """
        if hasattr(request, 'scope') and 'route' in request.scope:
            route = request.scope['route']
            if hasattr(route, 'path'):
                return route.path
        
        # 回退到URL路径
        return request.url.path


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件
    
    基于IP地址的请求速率限制
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.clients: Dict[str, deque] = defaultdict(deque)
        self.cleanup_interval = 300  # 5分钟清理一次
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并检查速率限制
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            Response: 响应对象
        """
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 检查速率限制
        if not self._check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute.",
                        "type": "rate_limit_error"
                    }
                }
            )
        
        # 记录请求
        self._record_request(client_ip)
        
        # 定期清理过期记录
        await self._cleanup_if_needed()
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址
        
        Args:
            request: 请求对象
            
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
        
        # 使用直接连接IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """
        检查客户端是否超过速率限制
        
        Args:
            client_ip: 客户端IP地址
            
        Returns:
            bool: 是否允许请求
        """
        now = time.time()
        minute_ago = now - 60
        
        # 获取客户端请求记录
        requests = self.clients[client_ip]
        
        # 移除过期请求
        while requests and requests[0] < minute_ago:
            requests.popleft()
        
        # 检查是否超过限制
        return len(requests) < self.requests_per_minute
    
    def _record_request(self, client_ip: str) -> None:
        """
        记录客户端请求
        
        Args:
            client_ip: 客户端IP地址
        """
        now = time.time()
        self.clients[client_ip].append(now)
        
        # 限制队列大小
        if len(self.clients[client_ip]) > self.burst_size:
            self.clients[client_ip].popleft()
    
    async def _cleanup_if_needed(self) -> None:
        """
        定期清理过期的客户端记录
        """
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            await self._cleanup_expired_clients()
            self.last_cleanup = now
    
    async def _cleanup_expired_clients(self) -> None:
        """
        清理过期的客户端记录
        """
        now = time.time()
        minute_ago = now - 60
        
        # 找到需要清理的客户端
        clients_to_remove = []
        for client_ip, requests in self.clients.items():
            # 移除过期请求
            while requests and requests[0] < minute_ago:
                requests.popleft()
            
            # 如果没有活跃请求，标记为删除
            if not requests:
                clients_to_remove.append(client_ip)
        
        # 删除空的客户端记录
        for client_ip in clients_to_remove:
            del self.clients[client_ip]
        
        if clients_to_remove:
            logger.debug(f"Cleaned up {len(clients_to_remove)} expired client records")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全头中间件
    
    添加安全相关的HTTP头
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并添加安全头
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            Response: 响应对象
        """
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response