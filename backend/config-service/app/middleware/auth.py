#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 认证中间件

提供JWT认证和权限控制功能
"""

import uuid
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_settings

security = HTTPBearer(auto_error=False)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.excluded_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/info",
            "/api/v1/"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        """
        # 检查是否为排除路径
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # 获取Authorization头
        authorization = request.headers.get("Authorization")
        if not authorization:
            # 对于某些接口，允许匿名访问
            if self._is_anonymous_allowed(request.url.path):
                return await call_next(request)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少认证信息",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        try:
            # 解析JWT token
            token = authorization.replace("Bearer ", "")
            payload = self._decode_token(token)
            
            # 将用户信息添加到请求状态
            request.state.user_id = payload.get("user_id")
            request.state.username = payload.get("username")
            request.state.roles = payload.get("roles", [])
            request.state.permissions = payload.get("permissions", [])
            
            # 检查权限
            if not self._check_permission(request.url.path, request.method, payload):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的Token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"认证失败: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return await call_next(request)
    
    def _decode_token(self, token: str) -> Dict[str, Any]:
        """
        解码JWT token
        """
        return jwt.decode(
            token,
            self.settings.JWT_SECRET_KEY,
            algorithms=[self.settings.JWT_ALGORITHM]
        )
    
    def _is_anonymous_allowed(self, path: str) -> bool:
        """
        检查是否允许匿名访问
        """
        anonymous_paths = [
            "/api/v1/configs/key/",  # 允许匿名获取某些全局配置
        ]
        return any(path.startswith(p) for p in anonymous_paths)
    
    def _check_permission(self, path: str, method: str, payload: Dict[str, Any]) -> bool:
        """
        检查用户权限
        """
        # 超级管理员拥有所有权限
        if "admin" in payload.get("roles", []):
            return True
        
        # 基于路径和方法的权限检查
        permissions = payload.get("permissions", [])
        
        # 配置相关权限
        if path.startswith("/api/v1/configs"):
            if method == "GET":
                return "config:read" in permissions
            elif method == "POST":
                return "config:create" in permissions
            elif method == "PUT" or method == "PATCH":
                return "config:update" in permissions
            elif method == "DELETE":
                return "config:delete" in permissions
        
        # 模板相关权限
        if path.startswith("/api/v1/templates"):
            if method == "GET":
                return "template:read" in permissions
            elif method == "POST":
                return "template:create" in permissions
            elif method == "PUT" or method == "PATCH":
                return "template:update" in permissions
            elif method == "DELETE":
                return "template:delete" in permissions
        
        # 默认拒绝
        return False


class JWTAuth:
    """
    JWT认证工具类
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    def create_access_token(
        self,
        user_id: uuid.UUID,
        username: str,
        roles: list = None,
        permissions: list = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建访问令牌
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "user_id": str(user_id),
            "username": username,
            "roles": roles or [],
            "permissions": permissions or [],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(
            payload,
            self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM
        )
    
    def create_refresh_token(
        self,
        user_id: uuid.UUID,
        username: str
    ) -> str:
        """
        创建刷新令牌
        """
        expire = datetime.utcnow() + timedelta(days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "user_id": str(user_id),
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(
            payload,
            self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM
        )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        验证令牌
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的Token"
            )
    
    def get_current_user_id(self, token: str) -> Optional[uuid.UUID]:
        """
        从token中获取当前用户ID
        """
        try:
            payload = self.verify_token(token)
            user_id_str = payload.get("user_id")
            return uuid.UUID(user_id_str) if user_id_str else None
        except Exception:
            return None


# 全局JWT认证实例
jwt_auth = JWTAuth()


def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = security) -> Optional[Dict[str, Any]]:
    """
    从token中获取当前用户信息
    """
    if not credentials:
        return None
    
    try:
        payload = jwt_auth.verify_token(credentials.credentials)
        return {
            "user_id": uuid.UUID(payload["user_id"]),
            "username": payload["username"],
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", [])
        }
    except Exception:
        return None


def require_permission(permission: str):
    """
    权限装饰器
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 这里可以实现权限检查逻辑
            return func(*args, **kwargs)
        return wrapper
    return decorator