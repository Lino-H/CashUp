"""
认证依赖模块 - 简化版（基于会话）
"""

from fastapi import Depends, HTTPException, status, Cookie, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database.connection import get_db
from ..database.redis import get_redis
from ..services.auth import AuthService
from ..utils.logger import get_logger

logger = get_logger(__name__)

async def get_current_user(
    session_id: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
    )
    
    try:
        # 优先从Cookie获取session_id
        if not session_id and authorization:
            # 从Authorization头获取session_id
            if authorization.startswith("Bearer "):
                session_id = authorization[7:]
            else:
                session_id = authorization
        
        if not session_id:
            raise credentials_exception
        
        auth_service = AuthService(db, redis_client)
        user_id = await auth_service.validate_session(session_id)
        
        if user_id is None:
            raise credentials_exception
        
        user = await auth_service.get_user_by_id(user_id)
        if user is None:
            raise credentials_exception
        
        return user
    
    except Exception as e:
        logger.error(f"认证失败: {e}")
        raise credentials_exception

async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """获取当前活跃用户"""
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    return current_user

async def get_current_admin_user(
    current_user = Depends(get_current_active_user)
):
    """获取当前管理员用户"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

async def get_optional_current_user(
    session_id: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """获取可选的当前用户（用于公开接口）"""
    if not session_id and authorization:
        if authorization.startswith("Bearer "):
            session_id = authorization[7:]
        else:
            session_id = authorization
    
    if not session_id:
        return None
    
    try:
        auth_service = AuthService(db, redis_client)
        user_id = await auth_service.validate_session(session_id)
        
        if user_id is None:
            return None
        
        user = await auth_service.get_user_by_id(user_id)
        return user
    
    except Exception:
        return None