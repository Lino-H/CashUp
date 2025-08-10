#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 限流中间件

基于Redis的API限流中间件
"""

import time
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.core.cache import get_cache_manager
from app.core.logging import get_logger
from app.core.security import get_client_ip

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(
        self,
        app,
        calls: int = 100,
        period: int = 60,
        key_func: Optional[Callable[[Request], str]] = None
    ):
        """
        初始化限流中间件
        
        Args:
            app: FastAPI应用实例
            calls: 时间窗口内允许的请求次数
            period: 时间窗口大小（秒）
            key_func: 生成限流键的函数，默认使用客户端IP
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.key_func = key_func or self._default_key_func
        self.cache_manager = get_cache_manager()
    
    def _default_key_func(self, request: Request) -> str:
        """默认的限流键生成函数"""
        client_ip = get_client_ip(request)
        return f"rate_limit:{client_ip}"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 跳过健康检查等端点
        if request.url.path in ["/health", "/ready", "/live", "/metrics"]:
            return await call_next(request)
        
        try:
            # 生成限流键
            rate_limit_key = self.key_func(request)
            
            # 检查限流
            allowed, remaining, reset_time = await self._check_rate_limit(rate_limit_key)
            
            if not allowed:
                # 超出限流，返回429错误
                logger.warning(
                    f"Rate limit exceeded",
                    extra={
                        'rate_limit_key': rate_limit_key,
                        'method': request.method,
                        'url': str(request.url),
                        'client_ip': get_client_ip(request)
                    }
                )
                
                return JSONResponse(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {self.calls} per {self.period} seconds",
                        "retry_after": reset_time
                    },
                    headers={
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(reset_time)
                    }
                )
            
            # 处理请求
            response = await call_next(request)
            
            # 添加限流信息到响应头
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            
            return response
            
        except Exception as e:
            logger.error(
                f"Rate limit middleware error: {e}",
                extra={
                    'method': request.method,
                    'url': str(request.url)
                },
                exc_info=True
            )
            # 限流中间件出错时，允许请求通过
            return await call_next(request)
    
    async def _check_rate_limit(self, key: str) -> tuple[bool, int, int]:
        """
        检查限流状态
        
        Returns:
            tuple: (是否允许请求, 剩余请求数, 重置时间戳)
        """
        try:
            current_time = int(time.time())
            window_start = current_time - (current_time % self.period)
            window_key = f"{key}:{window_start}"
            
            # 获取当前窗口的请求计数
            current_count = await self.cache_manager.get(window_key)
            if current_count is None:
                current_count = 0
            else:
                current_count = int(current_count)
            
            # 检查是否超出限制
            if current_count >= self.calls:
                remaining = 0
                reset_time = window_start + self.period
                return False, remaining, reset_time
            
            # 增加计数
            new_count = await self.cache_manager.increment(window_key)
            if new_count == 1:
                # 设置过期时间
                await self.cache_manager.expire(window_key, self.period)
            
            remaining = max(0, self.calls - new_count)
            reset_time = window_start + self.period
            
            return True, remaining, reset_time
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}", exc_info=True)
            # 出错时允许请求通过
            return True, self.calls, int(time.time()) + self.period


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """高级限流中间件，支持多种限流策略"""
    
    def __init__(
        self,
        app,
        default_calls: int = 100,
        default_period: int = 60,
        endpoint_limits: Optional[dict] = None,
        user_limits: Optional[dict] = None,
        key_func: Optional[Callable[[Request], str]] = None
    ):
        """
        初始化高级限流中间件
        
        Args:
            app: FastAPI应用实例
            default_calls: 默认请求次数限制
            default_period: 默认时间窗口
            endpoint_limits: 端点特定限制 {"endpoint": {"calls": 10, "period": 60}}
            user_limits: 用户特定限制 {"user_type": {"calls": 1000, "period": 60}}
            key_func: 生成限流键的函数
        """
        super().__init__(app)
        self.default_calls = default_calls
        self.default_period = default_period
        self.endpoint_limits = endpoint_limits or {}
        self.user_limits = user_limits or {}
        self.key_func = key_func or self._default_key_func
        self.cache_manager = get_cache_manager()
    
    def _default_key_func(self, request: Request) -> str:
        """默认的限流键生成函数"""
        client_ip = get_client_ip(request)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"rate_limit:user:{user_id}"
        return f"rate_limit:ip:{client_ip}"
    
    def _get_rate_limit_config(self, request: Request) -> tuple[int, int]:
        """获取请求的限流配置"""
        # 检查端点特定限制
        endpoint = request.url.path
        if endpoint in self.endpoint_limits:
            config = self.endpoint_limits[endpoint]
            return config.get("calls", self.default_calls), config.get("period", self.default_period)
        
        # 检查用户特定限制
        user_type = getattr(request.state, 'user_type', None)
        if user_type and user_type in self.user_limits:
            config = self.user_limits[user_type]
            return config.get("calls", self.default_calls), config.get("period", self.default_period)
        
        return self.default_calls, self.default_period
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 跳过健康检查等端点
        if request.url.path in ["/health", "/ready", "/live", "/metrics"]:
            return await call_next(request)
        
        try:
            # 获取限流配置
            calls, period = self._get_rate_limit_config(request)
            
            # 生成限流键
            rate_limit_key = self.key_func(request)
            
            # 检查限流
            allowed, remaining, reset_time = await self._check_rate_limit(
                rate_limit_key, calls, period
            )
            
            if not allowed:
                logger.warning(
                    f"Advanced rate limit exceeded",
                    extra={
                        'rate_limit_key': rate_limit_key,
                        'method': request.method,
                        'url': str(request.url),
                        'calls': calls,
                        'period': period,
                        'client_ip': get_client_ip(request)
                    }
                )
                
                return JSONResponse(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {calls} per {period} seconds",
                        "retry_after": reset_time
                    },
                    headers={
                        "X-RateLimit-Limit": str(calls),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(reset_time)
                    }
                )
            
            # 处理请求
            response = await call_next(request)
            
            # 添加限流信息到响应头
            response.headers["X-RateLimit-Limit"] = str(calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            
            return response
            
        except Exception as e:
            logger.error(
                f"Advanced rate limit middleware error: {e}",
                extra={
                    'method': request.method,
                    'url': str(request.url)
                },
                exc_info=True
            )
            return await call_next(request)
    
    async def _check_rate_limit(self, key: str, calls: int, period: int) -> tuple[bool, int, int]:
        """
        检查限流状态
        
        Returns:
            tuple: (是否允许请求, 剩余请求数, 重置时间戳)
        """
        try:
            current_time = int(time.time())
            window_start = current_time - (current_time % period)
            window_key = f"{key}:{window_start}"
            
            # 获取当前窗口的请求计数
            current_count = await self.cache_manager.get(window_key)
            if current_count is None:
                current_count = 0
            else:
                current_count = int(current_count)
            
            # 检查是否超出限制
            if current_count >= calls:
                remaining = 0
                reset_time = window_start + period
                return False, remaining, reset_time
            
            # 增加计数
            new_count = await self.cache_manager.increment(window_key)
            if new_count == 1:
                # 设置过期时间
                await self.cache_manager.expire(window_key, period)
            
            remaining = max(0, calls - new_count)
            reset_time = window_start + period
            
            return True, remaining, reset_time
            
        except Exception as e:
            logger.error(f"Advanced rate limit check failed: {e}", exc_info=True)
            return True, calls, int(time.time()) + period