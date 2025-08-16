#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入模块

提供FastAPI依赖注入函数，包括用户认证、权限验证等。
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import logging
from datetime import datetime

from .config import settings
from .database import get_db

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取当前用户信息
    
    Args:
        credentials: HTTP Bearer认证凭据
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 用户信息
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    try:
        # 解码JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # 检查token是否过期
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 提取用户信息
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 构建用户信息
        user_info = {
            "id": int(user_id),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
            "exp": exp
        }
        
        logger.debug(f"用户认证成功: {user_id}")
        return user_info
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token已过期")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT token无效: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"用户认证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    获取可选的当前用户信息（允许匿名访问）
    
    Args:
        credentials: HTTP Bearer认证凭据（可选）
        db: 数据库会话
        
    Returns:
        Optional[Dict[str, Any]]: 用户信息或None
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None


def require_permissions(*required_permissions: str):
    """
    权限验证装饰器
    
    Args:
        *required_permissions: 需要的权限列表
        
    Returns:
        function: 依赖函数
    """
    def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """
        检查用户权限
        
        Args:
            current_user: 当前用户信息
            
        Returns:
            Dict[str, Any]: 用户信息
            
        Raises:
            HTTPException: 权限不足时抛出异常
        """
        user_permissions = set(current_user.get("permissions", []))
        required_permissions_set = set(required_permissions)
        
        # 检查是否有管理员权限
        if "admin" in current_user.get("roles", []):
            return current_user
        
        # 检查是否有所需权限
        if not required_permissions_set.issubset(user_permissions):
            missing_permissions = required_permissions_set - user_permissions
            logger.warning(
                f"用户 {current_user['id']} 缺少权限: {missing_permissions}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker


def require_roles(*required_roles: str):
    """
    角色验证装饰器
    
    Args:
        *required_roles: 需要的角色列表
        
    Returns:
        function: 依赖函数
    """
    def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """
        检查用户角色
        
        Args:
            current_user: 当前用户信息
            
        Returns:
            Dict[str, Any]: 用户信息
            
        Raises:
            HTTPException: 角色不符时抛出异常
        """
        user_roles = set(current_user.get("roles", []))
        required_roles_set = set(required_roles)
        
        # 检查是否有所需角色
        if not required_roles_set.intersection(user_roles):
            logger.warning(
                f"用户 {current_user['id']} 角色不符: 需要 {required_roles}, 拥有 {user_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker


def get_pagination_params(
    page: int = 1,
    size: int = 20,
    max_size: int = 100
) -> Dict[str, int]:
    """
    获取分页参数
    
    Args:
        page: 页码
        size: 每页大小
        max_size: 最大每页大小
        
    Returns:
        Dict[str, int]: 分页参数
        
    Raises:
        HTTPException: 参数无效时抛出异常
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="页码必须大于0"
        )
    
    if size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="每页大小必须大于0"
        )
    
    if size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"每页大小不能超过{max_size}"
        )
    
    return {
        "page": page,
        "size": size,
        "offset": (page - 1) * size
    }


def validate_strategy_access(
    strategy_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    验证策略访问权限
    
    Args:
        strategy_id: 策略ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 用户信息
        
    Raises:
        HTTPException: 无权限访问时抛出异常
    """
    try:
        from ..models.strategy import Strategy
        
        # 查询策略
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        # 检查是否是策略所有者或管理员
        if strategy.user_id != current_user["id"] and "admin" not in current_user.get("roles", []):
            logger.warning(
                f"用户 {current_user['id']} 尝试访问不属于自己的策略 {strategy_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此策略"
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证策略访问权限失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证权限失败"
        )


def get_rate_limiter():
    """
    获取速率限制器（占位符实现）
    
    Returns:
        function: 速率限制检查函数
    """
    def rate_limit_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """
        检查速率限制
        
        Args:
            current_user: 当前用户
            
        Returns:
            Dict[str, Any]: 用户信息
        """
        # TODO: 实现实际的速率限制逻辑
        # 可以使用Redis或内存缓存来跟踪用户请求频率
        return current_user
    
    return rate_limit_checker


def get_api_key_user(
    api_key: str,
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    通过API Key获取用户信息（用于API访问）
    
    Args:
        api_key: API密钥
        db: 数据库会话
        
    Returns:
        Optional[Dict[str, Any]]: 用户信息或None
    """
    try:
        # TODO: 实现API Key验证逻辑
        # 这里应该查询数据库中的API Key记录
        # 并返回对应的用户信息
        
        # 占位符实现
        if api_key == settings.api_master_key:
            return {
                "id": 0,
                "username": "api_user",
                "email": "api@cashup.com",
                "roles": ["api"],
                "permissions": ["read", "write"]
            }
        
        return None
        
    except Exception as e:
        logger.error(f"API Key验证失败: {e}")
        return None


def get_service_account() -> Dict[str, Any]:
    """
    获取服务账户信息（用于内部服务调用）
    
    Returns:
        Dict[str, Any]: 服务账户信息
    """
    return {
        "id": -1,
        "username": "service_account",
        "email": "service@cashup.com",
        "roles": ["service"],
        "permissions": ["read", "write", "admin"]
    }