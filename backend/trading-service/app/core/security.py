#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易服务安全认证模块

提供JWT令牌验证、用户认证等安全功能
"""

from typing import Optional, Dict, Any
from datetime import datetime
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings


# HTTP Bearer 认证
security = HTTPBearer()


class SecurityManager:
    """
    安全管理器
    
    提供JWT令牌验证、用户认证等功能
    """
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            token_type: 令牌类型 (access/refresh)
            
        Returns:
            dict: 令牌载荷数据
            
        Raises:
            HTTPException: 令牌无效或过期
        """
        try:
            # 解码令牌
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # 检查令牌类型
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # 检查过期时间
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing expiration"
                )
            
            if datetime.utcnow().timestamp() > exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def extract_user_info(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        从令牌载荷中提取用户信息
        
        Args:
            payload: 令牌载荷
            
        Returns:
            dict: 用户信息
        """
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
            "is_superuser": payload.get("is_superuser", False)
        }


# 全局安全管理器实例
security_manager = SecurityManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    获取当前认证用户
    
    依赖注入函数，用于FastAPI路由中获取当前用户信息
    
    Args:
        credentials: HTTP Bearer 认证凭据
        
    Returns:
        dict: 当前用户信息
        
    Raises:
        HTTPException: 认证失败
    """
    try:
        # 验证令牌
        payload = security_manager.verify_token(credentials.credentials)
        
        # 提取用户信息
        user_info = security_manager.extract_user_info(payload)
        
        # 检查用户ID
        if not user_info["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token"
            )
        
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        dict: 当前活跃用户信息
        
    Raises:
        HTTPException: 用户未激活
    """
    # 这里可以添加额外的用户状态检查
    # 比如检查用户是否被禁用、是否需要重新验证等
    
    return current_user


async def require_roles(required_roles: list, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    要求特定角色权限
    
    Args:
        required_roles: 需要的角色列表
        current_user: 当前用户信息
        
    Returns:
        dict: 当前用户信息
        
    Raises:
        HTTPException: 权限不足
    """
    user_roles = current_user.get("roles", [])
    
    # 超级用户拥有所有权限
    if current_user.get("is_superuser", False):
        return current_user
    
    # 检查角色权限
    if not any(role in user_roles for role in required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return current_user


def require_trader_role(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    要求交易员角色
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        dict: 当前用户信息
    """
    return require_roles(["trader", "admin"], current_user)


def require_admin_role(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    要求管理员角色
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        dict: 当前用户信息
    """
    return require_roles(["admin"], current_user)