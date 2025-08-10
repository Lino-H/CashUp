#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 依赖注入模块

提供FastAPI依赖注入函数
"""

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from .database import get_db
from .redis import get_redis, RedisManager
from .security import verify_token, get_current_user_id
from .exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    PermissionDeniedError,
    UserNotFoundError
)
from .logging import get_logger
from ..models.user import User, UserRole, UserStatus
from ..services.user_service import UserService

logger = get_logger("dependencies")

# HTTP Bearer Token 方案
security = HTTPBearer(auto_error=False)


async def get_user_service(
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis)
) -> UserService:
    """
    获取用户服务实例
    
    Args:
        db: 数据库会话
        redis: Redis管理器
    
    Returns:
        UserService: 用户服务实例
    """
    return UserService(db, redis)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """
    获取当前认证用户
    
    Args:
        credentials: HTTP认证凭据
        db: 数据库会话
        user_service: 用户服务
    
    Returns:
        User: 当前用户对象
    
    Raises:
        HTTPException: 认证失败时抛出
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # 验证令牌
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise InvalidTokenError()
        
        # 获取用户信息
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)
        
        # 检查用户状态
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被禁用"
            )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except (InvalidTokenError, TokenExpiredError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
) -> Optional[User]:
    """
    获取当前认证用户（可选）
    
    如果没有提供令牌或令牌无效，返回None而不是抛出异常
    
    Args:
        credentials: HTTP认证凭据
        db: 数据库会话
        user_service: 用户服务
    
    Returns:
        Optional[User]: 当前用户对象或None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db, user_service)
    except HTTPException:
        return None


def require_roles(*required_roles: UserRole):
    """
    角色权限装饰器工厂
    
    Args:
        *required_roles: 需要的角色列表
    
    Returns:
        Callable: 依赖函数
    """
    async def check_roles(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        检查用户角色权限
        
        Args:
            current_user: 当前用户
        
        Returns:
            User: 当前用户对象
        
        Raises:
            HTTPException: 权限不足时抛出
        """
        user_roles = [role.name for role in current_user.roles]
        
        # 检查是否有任一所需角色
        has_required_role = any(
            role.value in user_roles for role in required_roles
        )
        
        if not has_required_role:
            logger.warning(f"用户 {current_user.id} 尝试访问需要角色 {[r.value for r in required_roles]} 的资源")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join([r.value for r in required_roles])}"
            )
        
        return current_user
    
    return check_roles


def require_permissions(*required_permissions: str):
    """
    权限检查装饰器工厂
    
    Args:
        *required_permissions: 需要的权限列表
    
    Returns:
        Callable: 依赖函数
    """
    async def check_permissions(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        检查用户权限
        
        Args:
            current_user: 当前用户
        
        Returns:
            User: 当前用户对象
        
        Raises:
            HTTPException: 权限不足时抛出
        """
        # 获取用户所有权限
        user_permissions = set()
        for role in current_user.roles:
            for permission in role.permissions:
                user_permissions.add(permission.name)
        
        # 检查是否有所有所需权限
        missing_permissions = set(required_permissions) - user_permissions
        
        if missing_permissions:
            logger.warning(f"用户 {current_user.id} 缺少权限: {missing_permissions}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return check_permissions


async def get_admin_user(
    current_user: User = Depends(require_roles(UserRole.ADMIN))
) -> User:
    """
    获取管理员用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        User: 管理员用户对象
    """
    return current_user


async def get_trader_user(
    current_user: User = Depends(require_roles(UserRole.TRADER, UserRole.ADMIN))
) -> User:
    """
    获取交易员用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        User: 交易员用户对象
    """
    return current_user


async def get_analyst_user(
    current_user: User = Depends(require_roles(UserRole.ANALYST, UserRole.ADMIN))
) -> User:
    """
    获取分析师用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        User: 分析师用户对象
    """
    return current_user


async def get_client_ip(request: Request) -> str:
    """
    获取客户端IP地址
    
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


async def get_request_id(request: Request) -> str:
    """
    获取请求ID
    
    Args:
        request: FastAPI请求对象
    
    Returns:
        str: 请求ID
    """
    return getattr(request.state, "request_id", "unknown")


class PaginationParams:
    """
    分页参数类
    """
    
    def __init__(
        self,
        page: int = 1,
        size: int = 20,
        max_size: int = 100
    ):
        self.page = max(1, page)
        self.size = min(max(1, size), max_size)
        self.offset = (self.page - 1) * self.size
        self.limit = self.size


def get_pagination_params(
    page: int = 1,
    size: int = 20
) -> PaginationParams:
    """
    获取分页参数
    
    Args:
        page: 页码（从1开始）
        size: 每页大小
    
    Returns:
        PaginationParams: 分页参数对象
    """
    return PaginationParams(page=page, size=size)


class SortParams:
    """
    排序参数类
    """
    
    def __init__(
        self,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()
        self.is_desc = self.sort_order == "desc"


def get_sort_params(
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> SortParams:
    """
    获取排序参数
    
    Args:
        sort_by: 排序字段
        sort_order: 排序顺序（asc/desc）
    
    Returns:
        SortParams: 排序参数对象
    """
    return SortParams(sort_by=sort_by, sort_order=sort_order)