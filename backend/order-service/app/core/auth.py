#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务认证模块

处理用户认证和授权
"""

import jwt
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
security = HTTPBearer()


class AuthenticationError(Exception):
    """
    认证异常
    """
    pass


class AuthorizationError(Exception):
    """
    授权异常
    """
    pass


async def verify_token(token: str) -> Dict[str, Any]:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        Dict[str, Any]: 解码后的用户信息
        
    Raises:
        AuthenticationError: 令牌验证失败
    """
    try:
        # 尝试本地验证JWT
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 检查令牌是否过期
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            raise AuthenticationError("Token has expired")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        # 如果本地验证失败，尝试通过用户服务验证
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{settings.USER_SERVICE_URL}/api/v1/auth/verify",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise AuthenticationError("Invalid token")
                    
        except httpx.RequestError:
            logger.error("Failed to verify token with user service")
            raise AuthenticationError("Token verification failed")
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise AuthenticationError("Token verification failed")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    获取当前用户信息
    
    Args:
        credentials: HTTP认证凭据
        
    Returns:
        Dict[str, Any]: 用户信息
        
    Raises:
        HTTPException: 认证失败时抛出401异常
    """
    try:
        token = credentials.credentials
        user_info = await verify_token(token)
        
        # 检查必要的用户信息
        if not user_info.get("user_id"):
            raise AuthenticationError("Invalid user information")
        
        return user_info
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取当前活跃用户信息
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        Dict[str, Any]: 活跃用户信息
        
    Raises:
        HTTPException: 用户未激活时抛出403异常
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user


def require_permissions(required_permissions: list[str]):
    """
    权限检查装饰器
    
    Args:
        required_permissions: 需要的权限列表
        
    Returns:
        function: 权限检查函数
    """
    async def check_permissions(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """
        检查用户权限
        
        Args:
            current_user: 当前用户信息
            
        Returns:
            Dict[str, Any]: 用户信息
            
        Raises:
            HTTPException: 权限不足时抛出403异常
        """
        user_permissions = current_user.get("permissions", [])
        user_roles = current_user.get("roles", [])
        
        # 检查是否为管理员
        if "admin" in user_roles or "super_admin" in user_roles:
            return current_user
        
        # 检查具体权限
        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required"
                )
        
        return current_user
    
    return check_permissions


def require_roles(required_roles: list[str]):
    """
    角色检查装饰器
    
    Args:
        required_roles: 需要的角色列表
        
    Returns:
        function: 角色检查函数
    """
    async def check_roles(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """
        检查用户角色
        
        Args:
            current_user: 当前用户信息
            
        Returns:
            Dict[str, Any]: 用户信息
            
        Raises:
            HTTPException: 角色不匹配时抛出403异常
        """
        user_roles = current_user.get("roles", [])
        
        # 检查是否有任一所需角色
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: one of {required_roles}"
            )
        
        return current_user
    
    return check_roles


async def create_service_token(service_name: str, permissions: list[str]) -> str:
    """
    创建服务间通信令牌
    
    Args:
        service_name: 服务名称
        permissions: 权限列表
        
    Returns:
        str: JWT令牌
    """
    payload = {
        "service": service_name,
        "permissions": permissions,
        "iat": datetime.utcnow().timestamp(),
        "exp": (datetime.utcnow().timestamp() + 3600)  # 1小时过期
    }
    
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token


async def verify_service_token(token: str) -> Dict[str, Any]:
    """
    验证服务间通信令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        Dict[str, Any]: 服务信息
        
    Raises:
        AuthenticationError: 令牌验证失败
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 检查是否为服务令牌
        if not payload.get("service"):
            raise AuthenticationError("Invalid service token")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Service token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid service token")
    except Exception as e:
        logger.error(f"Service token verification error: {str(e)}")
        raise AuthenticationError("Service token verification failed")


# 常用权限常量
class Permissions:
    """
    权限常量
    """
    ORDER_CREATE = "order:create"
    ORDER_READ = "order:read"
    ORDER_UPDATE = "order:update"
    ORDER_DELETE = "order:delete"
    ORDER_CANCEL = "order:cancel"
    ORDER_ADMIN = "order:admin"


# 权限常量实例（用于向后兼容）
PERMISSIONS = Permissions()


# 常用角色常量
class Roles:
    """
    角色常量
    """
    USER = "user"
    TRADER = "trader"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    SERVICE = "service"


# 角色常量实例（用于向后兼容）
ROLES = Roles()