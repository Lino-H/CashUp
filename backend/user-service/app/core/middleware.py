#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 中间件模块

提供请求日志、安全和性能监控中间件
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging import get_logger, log_api_request, log_security_event
from .config import settings

logger = get_logger("middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    记录所有API请求的详细信息
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 获取客户端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 记录请求开始
        start_time = time.time()
        
        logger.info(f"请求开始: {request.method} {request.url.path}", extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": client_ip,
            "user_agent": user_agent
        })
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求完成
            logger.info(f"请求完成: {request.method} {request.url.path} - {response.status_code}", extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "client_ip": client_ip
            })
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求异常
            logger.error(f"请求异常: {request.method} {request.url.path} - {str(e)}", extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "process_time": round(process_time, 4),
                "client_ip": client_ip
            })
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实IP地址
        
        Args:
            request: FastAPI请求对象
        
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
        
        # 返回直接连接的IP
        return request.client.host if request.client else "unknown"


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    安全中间件
    
    提供基础的安全防护功能
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit_storage = {}  # 简单的内存存储，生产环境应使用Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 检查IP黑名单（示例）
        if self._is_blocked_ip(client_ip):
            log_security_event(
                "IP地址被阻止",
                severity="WARNING",
                ip=client_ip,
                details={"reason": "IP在黑名单中"}
            )
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error_code": "IP_BLOCKED",
                    "message": "访问被拒绝",
                    "details": {},
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            )
        
        # 简单的速率限制检查
        if self._is_rate_limited(client_ip, request.url.path):
            log_security_event(
                "请求频率超限",
                severity="WARNING",
                ip=client_ip,
                details={"path": request.url.path}
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "请求过于频繁，请稍后再试",
                    "details": {"retry_after": 60},
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            )
        
        # 处理请求
        response = await call_next(request)
        
        # 添加安全头
        self._add_security_headers(response)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实IP地址
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_blocked_ip(self, ip: str) -> bool:
        """
        检查IP是否在黑名单中
        
        Args:
            ip: 客户端IP地址
        
        Returns:
            bool: 是否被阻止
        """
        # 示例黑名单，实际应从数据库或配置文件读取
        blocked_ips = []
        return ip in blocked_ips
    
    def _is_rate_limited(self, ip: str, path: str) -> bool:
        """
        检查是否触发速率限制
        
        Args:
            ip: 客户端IP地址
            path: 请求路径
        
        Returns:
            bool: 是否触发限制
        """
        # 简单的速率限制实现
        # 生产环境应使用Redis实现分布式速率限制
        current_time = time.time()
        key = f"{ip}:{path}"
        
        if key not in self.rate_limit_storage:
            self.rate_limit_storage[key] = []
        
        # 清理过期记录（1分钟前的记录）
        self.rate_limit_storage[key] = [
            timestamp for timestamp in self.rate_limit_storage[key]
            if current_time - timestamp < 60
        ]
        
        # 检查请求数量
        if len(self.rate_limit_storage[key]) >= 100:  # 每分钟最多100次请求
            return True
        
        # 记录当前请求
        self.rate_limit_storage[key].append(current_time)
        return False
    
    def _add_security_headers(self, response: Response) -> None:
        """
        添加安全响应头
        
        Args:
            response: FastAPI响应对象
        """
        # 防止点击劫持
        response.headers["X-Frame-Options"] = "DENY"
        
        # 防止MIME类型嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS保护
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # 严格传输安全（仅HTTPS）
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # 内容安全策略
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # 引用策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 权限策略
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件
    
    监控API响应时间和性能指标
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.slow_request_threshold = 2.0  # 慢请求阈值（秒）
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录慢请求
        if process_time > self.slow_request_threshold:
            logger.warning(f"慢请求检测: {request.method} {request.url.path}", extra={
                "method": request.method,
                "path": request.url.path,
                "process_time": round(process_time, 4),
                "threshold": self.slow_request_threshold,
                "status_code": response.status_code
            })
        
        # 添加性能头
        response.headers["X-Response-Time"] = str(round(process_time * 1000, 2))  # 毫秒
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """
    自定义CORS中间件
    
    提供更精细的CORS控制
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.allowed_origins = settings.ALLOWED_HOSTS
        self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.allowed_headers = [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-Request-ID"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")
        
        # 处理预检请求
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, origin)
            return response
        
        # 处理实际请求
        response = await call_next(request)
        self._add_cors_headers(response, origin)
        
        return response
    
    def _add_cors_headers(self, response: Response, origin: str = None) -> None:
        """
        添加CORS头
        
        Args:
            response: FastAPI响应对象
            origin: 请求来源
        """
        # 检查来源是否被允许
        if origin and ("*" in self.allowed_origins or origin in self.allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"  # 24小时