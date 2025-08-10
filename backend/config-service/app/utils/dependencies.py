#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 依赖注入

提供FastAPI依赖注入函数
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from ..core.database import get_database_session
from ..core.cache import get_redis_client
from ..services.config_service import ConfigService
from ..services.template_service import TemplateService
from ..middleware.auth import get_current_user_from_token


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    """
    async with get_database_session() as session:
        yield session


async def get_redis() -> Redis:
    """
    获取Redis客户端
    """
    redis_client = await get_redis_client()
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis服务不可用"
        )
    return redis_client


async def get_config_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> ConfigService:
    """
    获取配置服务实例
    """
    return ConfigService(db=db, redis=redis)


async def get_template_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> TemplateService:
    """
    获取模板服务实例
    """
    return TemplateService(db=db, redis=redis)


async def get_current_user(
    token: str = Depends(get_current_user_from_token)
) -> Optional[dict]:
    """
    获取当前用户信息
    """
    # 这里可以根据token获取用户详细信息
    # 目前返回基本的用户信息
    if not token:
        return None
    
    # TODO: 从用户服务获取完整的用户信息
    return {
        "user_id": token.get("user_id"),
        "username": token.get("username"),
        "email": token.get("email"),
        "roles": token.get("roles", []),
        "permissions": token.get("permissions", [])
    }


async def require_auth(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    要求用户认证
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要用户认证",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user


async def require_admin(
    current_user: dict = Depends(require_auth)
) -> dict:
    """
    要求管理员权限
    """
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles and "super_admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def require_permission(permission: str):
    """
    要求特定权限
    """
    async def check_permission(
        current_user: dict = Depends(require_auth)
    ) -> dict:
        user_permissions = current_user.get("permissions", [])
        user_roles = current_user.get("roles", [])
        
        # 超级管理员拥有所有权限
        if "super_admin" in user_roles:
            return current_user
        
        # 检查是否有特定权限
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要权限: {permission}"
            )
        
        return current_user
    
    return check_permission


# 权限常量
class Permissions:
    # 配置权限
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"
    CONFIG_DELETE = "config:delete"
    CONFIG_ADMIN = "config:admin"
    
    # 模板权限
    TEMPLATE_READ = "template:read"
    TEMPLATE_WRITE = "template:write"
    TEMPLATE_DELETE = "template:delete"
    TEMPLATE_ADMIN = "template:admin"
    
    # 系统权限
    SYSTEM_ADMIN = "system:admin"
    AUDIT_READ = "audit:read"
    
    # 批量操作权限
    BATCH_OPERATION = "batch:operation"
    
    # 导入导出权限
    IMPORT_EXPORT = "import:export"


# 预定义的权限依赖
require_config_read = require_permission(Permissions.CONFIG_READ)
require_config_write = require_permission(Permissions.CONFIG_WRITE)
require_config_delete = require_permission(Permissions.CONFIG_DELETE)
require_config_admin = require_permission(Permissions.CONFIG_ADMIN)

require_template_read = require_permission(Permissions.TEMPLATE_READ)
require_template_write = require_permission(Permissions.TEMPLATE_WRITE)
require_template_delete = require_permission(Permissions.TEMPLATE_DELETE)
require_template_admin = require_permission(Permissions.TEMPLATE_ADMIN)

require_system_admin = require_permission(Permissions.SYSTEM_ADMIN)
require_audit_read = require_permission(Permissions.AUDIT_READ)
require_batch_operation = require_permission(Permissions.BATCH_OPERATION)
require_import_export = require_permission(Permissions.IMPORT_EXPORT)


async def get_optional_user(
    token: str = Depends(get_current_user_from_token)
) -> Optional[dict]:
    """
    获取可选的用户信息（不要求认证）
    """
    try:
        return await get_current_user(token)
    except:
        return None


async def validate_service_health(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> dict:
    """
    验证服务健康状态
    """
    health_status = {
        "database": False,
        "redis": False,
        "overall": False
    }
    
    try:
        # 检查数据库连接
        await db.execute("SELECT 1")
        health_status["database"] = True
    except Exception:
        pass
    
    try:
        # 检查Redis连接
        await redis.ping()
        health_status["redis"] = True
    except Exception:
        pass
    
    health_status["overall"] = health_status["database"] and health_status["redis"]
    
    if not health_status["overall"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务不健康"
        )
    
    return health_status


class RateLimiter:
    """
    简单的速率限制器
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    async def check_rate_limit(self, identifier: str) -> bool:
        """
        检查速率限制
        """
        import time
        
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        # 清理过期的请求记录
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
        else:
            self.requests[identifier] = []
        
        # 检查是否超过限制
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # 记录当前请求
        self.requests[identifier].append(current_time)
        return True


# 全局速率限制器实例
default_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
strict_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


async def apply_rate_limit(
    request,
    rate_limiter: RateLimiter = default_rate_limiter
):
    """
    应用速率限制
    """
    # 使用客户端IP作为标识符
    client_ip = request.client.host
    
    if not await rate_limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试"
        )


async def apply_strict_rate_limit(request):
    """
    应用严格的速率限制
    """
    await apply_rate_limit(request, strict_rate_limiter)