#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全中间件

提供应用程序安全相关的中间件功能。
"""

import time
import hashlib
import logging
from typing import Callable, Dict, Set
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import ipaddress

from ..core.config import settings
from .logging import get_request_id

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全头部中间件
    
    添加各种安全相关的HTTP头部。
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并添加安全头部
        
        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: 添加了安全头部的HTTP响应
        """
        response = await call_next(request)
        
        # 添加安全头部
        security_headers = {
            # 防止点击劫持
            "X-Frame-Options": "DENY",
            # 防止MIME类型嗅探
            "X-Content-Type-Options": "nosniff",
            # XSS保护
            "X-XSS-Protection": "1; mode=block",
            # 引用者策略
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # 权限策略
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            # 严格传输安全（仅HTTPS）
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            # 内容安全策略
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件
    
    基于IP地址和用户的请求速率限制。
    """
    
    def __init__(self, app: FastAPI, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, Dict[str, int]] = {}
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并检查速率限制
        
        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应或速率限制错误响应
        """
        # 获取客户端标识
        client_id = self._get_client_id(request)
        current_minute = int(time.time() // 60)
        
        # 清理过期的计数器
        self._cleanup_old_counts(current_minute)
        
        # 检查速率限制
        if self._is_rate_limited(client_id, current_minute):
            request_id = get_request_id(request)
            
            logger.warning(
                f"速率限制触发 - ID: {request_id}, "
                f"客户端: {client_id}, "
                f"路径: {request.url.path}"
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "请求过于频繁，请稍后再试",
                    "retry_after": 60,
                    "request_id": request_id,
                    "timestamp": time.time()
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str((current_minute + 1) * 60)
                }
            )
        
        # 增加请求计数
        self._increment_count(client_id, current_minute)
        
        # 处理请求
        response = await call_next(request)
        
        # 添加速率限制头部
        remaining = max(0, self.requests_per_minute - 
                       self.request_counts.get(client_id, {}).get(str(current_minute), 0))
        
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str((current_minute + 1) * 60)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """
        获取客户端标识
        
        Args:
            request: HTTP请求对象
            
        Returns:
            str: 客户端标识
        """
        # 优先使用用户ID（如果已认证）
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # 使用IP地址
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def _is_rate_limited(self, client_id: str, current_minute: int) -> bool:
        """
        检查是否触发速率限制
        
        Args:
            client_id: 客户端标识
            current_minute: 当前分钟
            
        Returns:
            bool: 是否触发速率限制
        """
        if client_id not in self.request_counts:
            return False
        
        current_count = self.request_counts[client_id].get(str(current_minute), 0)
        return current_count >= self.requests_per_minute
    
    def _increment_count(self, client_id: str, current_minute: int) -> None:
        """
        增加请求计数
        
        Args:
            client_id: 客户端标识
            current_minute: 当前分钟
        """
        if client_id not in self.request_counts:
            self.request_counts[client_id] = {}
        
        minute_key = str(current_minute)
        self.request_counts[client_id][minute_key] = (
            self.request_counts[client_id].get(minute_key, 0) + 1
        )
    
    def _cleanup_old_counts(self, current_minute: int) -> None:
        """
        清理过期的计数器
        
        Args:
            current_minute: 当前分钟
        """
        # 每5分钟清理一次
        if time.time() - self.last_cleanup < 300:
            return
        
        cutoff_minute = current_minute - 5  # 保留最近5分钟的数据
        
        for client_id in list(self.request_counts.keys()):
            client_counts = self.request_counts[client_id]
            
            # 删除过期的分钟计数
            for minute_key in list(client_counts.keys()):
                if int(minute_key) < cutoff_minute:
                    del client_counts[minute_key]
            
            # 如果客户端没有任何计数，删除整个记录
            if not client_counts:
                del self.request_counts[client_id]
        
        self.last_cleanup = time.time()


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    IP白名单中间件
    
    限制只有白名单中的IP地址可以访问。
    """
    
    def __init__(self, app: FastAPI, whitelist: Set[str] = None):
        super().__init__(app)
        self.whitelist = whitelist or set()
        self.whitelist_networks = self._parse_networks()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并检查IP白名单
        
        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应或访问拒绝错误响应
        """
        # 如果没有配置白名单，直接通过
        if not self.whitelist:
            return await call_next(request)
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 检查IP是否在白名单中
        if not self._is_ip_allowed(client_ip):
            request_id = get_request_id(request)
            
            logger.warning(
                f"IP访问被拒绝 - ID: {request_id}, "
                f"IP: {client_ip}, "
                f"路径: {request.url.path}"
            )
            
            return JSONResponse(
                status_code=403,
                content={
                    "error": "ACCESS_DENIED",
                    "message": "访问被拒绝",
                    "request_id": request_id,
                    "timestamp": time.time()
                }
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址
        
        Args:
            request: HTTP请求对象
            
        Returns:
            str: 客户端IP地址
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _parse_networks(self) -> list:
        """
        解析网络地址
        
        Returns:
            list: 网络对象列表
        """
        networks = []
        for addr in self.whitelist:
            try:
                if "/" in addr:
                    networks.append(ipaddress.ip_network(addr, strict=False))
                else:
                    networks.append(ipaddress.ip_address(addr))
            except ValueError:
                logger.warning(f"无效的IP地址或网络: {addr}")
        
        return networks
    
    def _is_ip_allowed(self, ip: str) -> bool:
        """
        检查IP是否被允许
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 是否被允许
        """
        try:
            client_ip = ipaddress.ip_address(ip)
            
            for network in self.whitelist_networks:
                if isinstance(network, ipaddress.IPv4Network) or isinstance(network, ipaddress.IPv6Network):
                    if client_ip in network:
                        return True
                elif client_ip == network:
                    return True
            
            return False
            
        except ValueError:
            logger.warning(f"无效的客户端IP地址: {ip}")
            return False


def setup_security_middleware(app: FastAPI) -> None:
    """
    设置安全中间件
    
    Args:
        app: FastAPI应用实例
    """
    try:
        # 添加安全头部中间件
        app.add_middleware(SecurityHeadersMiddleware)
        
        # 添加速率限制中间件
        if settings.enable_rate_limit:
            app.add_middleware(
                RateLimitMiddleware,
                requests_per_minute=settings.rate_limit_requests_per_minute
            )
        
        # 添加IP白名单中间件（如果配置了白名单）
        if settings.ip_whitelist:
            app.add_middleware(
                IPWhitelistMiddleware,
                whitelist=set(settings.ip_whitelist)
            )
        
        logger.info("安全中间件设置完成")
        
    except Exception as e:
        logger.error(f"设置安全中间件失败: {e}")
        raise


def generate_csrf_token() -> str:
    """
    生成CSRF令牌
    
    Returns:
        str: CSRF令牌
    """
    import secrets
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, expected_token: str) -> bool:
    """
    验证CSRF令牌
    
    Args:
        token: 提供的令牌
        expected_token: 期望的令牌
        
    Returns:
        bool: 验证结果
    """
    import hmac
    return hmac.compare_digest(token, expected_token)


def hash_password(password: str) -> str:
    """
    哈希密码
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 验证结果
    """
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))