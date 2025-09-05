"""
认证依赖模块
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database.connection import get_db
from ..services.auth import AuthService
from ..schemas.auth import TokenData
from ..utils.logger import get_logger

logger = get_logger(__name__)

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        auth_service = AuthService(db)
        token_data = auth_service.verify_token(credentials.credentials)
        
        if token_data is None:
            raise credentials_exception
        
        user = await auth_service.get_user_by_id(token_data.user_id)
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """获取可选的当前用户（用于公开接口）"""
    if credentials is None:
        return None
    
    try:
        auth_service = AuthService(db)
        token_data = auth_service.verify_token(credentials.credentials)
        
        if token_data is None:
            return None
        
        user = await auth_service.get_user_by_id(token_data.user_id)
        return user
    
    except Exception:
        return None