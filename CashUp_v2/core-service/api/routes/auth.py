"""
认证路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional

from ..schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from ..services.auth import AuthService
from ..database.connection import get_db
from ..utils.logger import get_logger

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.authenticate_user(request.username, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 生成访问令牌
        access_token = auth_service.create_access_token(data={"sub": user.username})
        refresh_token = auth_service.create_refresh_token(data={"sub": user.username})
        
        # 更新最后登录时间
        await auth_service.update_last_login(user.id)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )

@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    auth_service = AuthService(db)
    
    try:
        # 检查用户名是否已存在
        existing_user = await auth_service.get_user_by_username(request.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        existing_email = await auth_service.get_user_by_email(request.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        # 创建用户
        user = await auth_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        return UserResponse.from_orm(user)
        
    except Exception as e:
        logger.error(f"注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败"
        )

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """刷新令牌"""
    auth_service = AuthService(db)
    
    try:
        # 验证刷新令牌
        username = auth_service.verify_token(credentials.credentials)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌"
            )
        
        # 获取用户信息
        user = await auth_service.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        # 生成新的访问令牌
        access_token = auth_service.create_access_token(data={"sub": user.username})
        refresh_token = auth_service.create_refresh_token(data={"sub": user.username})
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except Exception as e:
        logger.error(f"令牌刷新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户信息"""
    auth_service = AuthService(db)
    
    try:
        # 验证访问令牌
        username = auth_service.verify_token(credentials.credentials)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌"
            )
        
        # 获取用户信息
        user = await auth_service.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        return UserResponse.from_orm(user)
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )