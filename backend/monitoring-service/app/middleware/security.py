#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 安全中间件

提供安全相关的中间件功能
"""

import time
import hashlib
import secrets
from typing import Callable, Optional, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST

from app.core.config import get_config
from app.core.logging import get_logger
from app.core.security import get_client_ip, verify_csrf_token
from app.core.cache import get_cache_manager

logger = get_logger(__name__)
config = get_config()


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""
    
    def __init__(
        self,
        app,
        enable_csrf: bool = True,
        enable_xss_protection: bool = True,
        enable_content_type_options: bool = True,
        enable_frame_options: bool = True,
        enable_hsts: bool = True,
        blocked_user_agents: Optional[List[str]] = None,
        blocked_ips: Optional[List[str]] = None
    ):
        """
        初始化安全中间件
        
        Args:
            app: FastAPI应用实例
            enable_csrf: 是否启用CSRF保护
            enable_xss_protection: 是否启用XSS保护
            enable_content_type_options: 是否启用内容类型选项
            enable_frame_options: 是否启用框架选项
            enable_hsts: 是否启用HSTS
            blocked_user_agents: 被阻止的用户代理列表
            blocked_ips: 被阻止的IP地址列表
        """
        super().__init__(app)
        self.enable_csrf = enable_csrf
        self.enable_xss_protection = enable_xss_protection
        self.enable_content_type_options = enable_content_type_options
        self.enable_frame_options = enable_frame_options
        self.enable_hsts = enable_hsts
        self.blocked_user_agents = blocked_user_agents or []
        self.blocked_ips = blocked_ips or []
        self.cache_manager = get_cache_manager()
        
        # CSRF保护的安全方法
        self.csrf_safe_methods = {"GET", "HEAD", "OPTIONS", "TRACE"}
        
        # 跳过安全检查的路径
        self.skip_paths = {
            "/health",
            "/ready",
            "/live",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        try:
            # 跳过特定路径的安全检查
            if request.url.path in self.skip_paths:
                response = await call_next(request)
                return self._add_security_headers(response)
            
            # 检查被阻止的IP
            if not await self._check_ip_allowed(request):
                logger.warning(
                    f"Blocked IP access attempt",
                    extra={
                        'client_ip': get_client_ip(request),
                        'method': request.method,
                        'url': str(request.url)
                    }
                )
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN,
                    content={"error": "Access denied"}
                )
            
            # 检查被阻止的用户代理
            if not await self._check_user_agent_allowed(request):
                logger.warning(
                    f"Blocked user agent access attempt",
                    extra={
                        'user_agent': request.headers.get('user-agent', ''),
                        'client_ip': get_client_ip(request),
                        'method': request.method,
                        'url': str(request.url)
                    }
                )
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN,
                    content={"error": "Access denied"}
                )
            
            # CSRF保护
            if self.enable_csrf and not await self._check_csrf_protection(request):
                logger.warning(
                    f"CSRF protection triggered",
                    extra={
                        'client_ip': get_client_ip(request),
                        'method': request.method,
                        'url': str(request.url)
                    }
                )
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN,
                    content={"error": "CSRF token missing or invalid"}
                )
            
            # 检查请求大小
            if not await self._check_request_size(request):
                logger.warning(
                    f"Request size limit exceeded",
                    extra={
                        'client_ip': get_client_ip(request),
                        'method': request.method,
                        'url': str(request.url),
                        'content_length': request.headers.get('content-length', 'unknown')
                    }
                )
                return JSONResponse(
                    status_code=HTTP_400_BAD_REQUEST,
                    content={"error": "Request too large"}
                )
            
            # 检查可疑活动
            await self._check_suspicious_activity(request)
            
            # 处理请求
            response = await call_next(request)
            
            # 添加安全头
            response = self._add_security_headers(response)
            
            return response
            
        except Exception as e:
            logger.error(
                f"Security middleware error: {e}",
                extra={
                    'method': request.method,
                    'url': str(request.url)
                },
                exc_info=True
            )
            # 安全中间件出错时，拒绝请求
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"error": "Security check failed"}
            )
    
    async def _check_ip_allowed(self, request: Request) -> bool:
        """检查IP是否被允许"""
        if not self.blocked_ips:
            return True
        
        client_ip = get_client_ip(request)
        return client_ip not in self.blocked_ips
    
    async def _check_user_agent_allowed(self, request: Request) -> bool:
        """检查用户代理是否被允许"""
        if not self.blocked_user_agents:
            return True
        
        user_agent = request.headers.get('user-agent', '').lower()
        for blocked_ua in self.blocked_user_agents:
            if blocked_ua.lower() in user_agent:
                return False
        
        return True
    
    async def _check_csrf_protection(self, request: Request) -> bool:
        """检查CSRF保护"""
        # 安全方法不需要CSRF保护
        if request.method in self.csrf_safe_methods:
            return True
        
        # 检查CSRF令牌
        csrf_token = request.headers.get('X-CSRF-Token')
        if not csrf_token:
            # 尝试从表单数据获取
            if request.headers.get('content-type', '').startswith('application/x-www-form-urlencoded'):
                form_data = await request.form()
                csrf_token = form_data.get('csrf_token')
        
        if not csrf_token:
            return False
        
        # 验证CSRF令牌
        return verify_csrf_token(csrf_token)
    
    async def _check_request_size(self, request: Request) -> bool:
        """检查请求大小"""
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                max_size = config.security.max_request_size
                return size <= max_size
            except ValueError:
                return False
        
        return True
    
    async def _check_suspicious_activity(self, request: Request):
        """检查可疑活动"""
        try:
            client_ip = get_client_ip(request)
            current_time = int(time.time())
            
            # 检查请求频率
            request_key = f"security:requests:{client_ip}:{current_time // 60}"  # 每分钟
            request_count = await self.cache_manager.increment(request_key)
            await self.cache_manager.expire(request_key, 60)
            
            # 如果请求频率过高，记录可疑活动
            if request_count > 100:  # 每分钟超过100个请求
                logger.warning(
                    f"High request frequency detected",
                    extra={
                        'client_ip': client_ip,
                        'request_count': request_count,
                        'method': request.method,
                        'url': str(request.url)
                    }
                )
                
                # 记录到可疑活动日志
                await self._log_suspicious_activity(
                    client_ip,
                    "high_request_frequency",
                    {
                        'request_count': request_count,
                        'method': request.method,
                        'url': str(request.url)
                    }
                )
            
            # 检查异常路径访问
            suspicious_patterns = [
                '/admin', '/.env', '/config', '/backup',
                '/wp-admin', '/phpmyadmin', '/mysql',
                '/../', '/..\\', '/etc/passwd'
            ]
            
            path = request.url.path.lower()
            for pattern in suspicious_patterns:
                if pattern in path:
                    logger.warning(
                        f"Suspicious path access",
                        extra={
                            'client_ip': client_ip,
                            'path': request.url.path,
                            'pattern': pattern,
                            'method': request.method
                        }
                    )
                    
                    await self._log_suspicious_activity(
                        client_ip,
                        "suspicious_path_access",
                        {
                            'path': request.url.path,
                            'pattern': pattern,
                            'method': request.method
                        }
                    )
                    break
            
        except Exception as e:
            logger.error(f"Error checking suspicious activity: {e}", exc_info=True)
    
    async def _log_suspicious_activity(self, client_ip: str, activity_type: str, details: dict):
        """记录可疑活动"""
        try:
            activity_data = {
                'client_ip': client_ip,
                'activity_type': activity_type,
                'details': details,
                'timestamp': int(time.time())
            }
            
            # 存储到缓存中，用于后续分析
            activity_key = f"security:suspicious:{client_ip}:{int(time.time())}"
            await self.cache_manager.set(
                activity_key,
                activity_data,
                expire=86400  # 保存24小时
            )
            
        except Exception as e:
            logger.error(f"Error logging suspicious activity: {e}", exc_info=True)
    
    def _add_security_headers(self, response: Response) -> Response:
        """添加安全头"""
        # X-Content-Type-Options
        if self.enable_content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        if self.enable_frame_options:
            response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        if self.enable_xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Strict-Transport-Security (HSTS)
        if self.enable_hsts and config.security.use_https:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content-Security-Policy
        if config.security.content_security_policy:
            response.headers["Content-Security-Policy"] = config.security.content_security_policy
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Server header removal
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP白名单中间件"""
    
    def __init__(self, app, whitelist: List[str], skip_paths: Optional[List[str]] = None):
        """
        初始化IP白名单中间件
        
        Args:
            app: FastAPI应用实例
            whitelist: 允许的IP地址列表
            skip_paths: 跳过检查的路径列表
        """
        super().__init__(app)
        self.whitelist = set(whitelist)
        self.skip_paths = set(skip_paths or ["/health", "/ready", "/live"])
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 跳过特定路径
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        client_ip = get_client_ip(request)
        
        if client_ip not in self.whitelist:
            logger.warning(
                f"IP not in whitelist",
                extra={
                    'client_ip': client_ip,
                    'method': request.method,
                    'url': str(request.url)
                }
            )
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"error": "Access denied"}
            )
        
        return await call_next(request)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API密钥中间件"""
    
    def __init__(
        self,
        app,
        api_keys: List[str],
        header_name: str = "X-API-Key",
        skip_paths: Optional[List[str]] = None
    ):
        """
        初始化API密钥中间件
        
        Args:
            app: FastAPI应用实例
            api_keys: 有效的API密钥列表
            header_name: API密钥头名称
            skip_paths: 跳过检查的路径列表
        """
        super().__init__(app)
        self.api_keys = set(api_keys)
        self.header_name = header_name
        self.skip_paths = set(skip_paths or ["/health", "/ready", "/live", "/docs", "/redoc"])
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 跳过特定路径
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        api_key = request.headers.get(self.header_name)
        
        if not api_key or api_key not in self.api_keys:
            logger.warning(
                f"Invalid or missing API key",
                extra={
                    'client_ip': get_client_ip(request),
                    'method': request.method,
                    'url': str(request.url),
                    'has_api_key': bool(api_key)
                }
            )
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"error": "Invalid or missing API key"}
            )
        
        return await call_next(request)