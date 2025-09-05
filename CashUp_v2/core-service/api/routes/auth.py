"""
认证路由 - 简化版（基于会话）
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from ..services.auth import AuthService
from ..database.connection import get_db
from ..database.redis import get_redis
from ..utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """用户登录"""
    auth_service = AuthService(db, redis_client)
    
    try:
        user = await auth_service.authenticate_user(request.username, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 创建会话
        session_id = await auth_service.create_session(user.id)
        
        # 设置HttpOnly Cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,  # 开发环境设为False，生产环境设为True
            samesite="lax",
            max_age=24 * 3600  # 24小时
        )
        
        return LoginResponse(
            session_id=session_id,
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
    from ..database.redis import get_redis
    
    auth_service = AuthService(db, await get_redis())
    
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

@router.post("/logout")
async def logout(
    response: Response,
    session_id: Optional[str] = None,
    authorization: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """用户登出"""
    auth_service = AuthService(db, redis_client)
    
    try:
        # 获取session_id
        if not session_id and authorization:
            if authorization.startswith("Bearer "):
                session_id = authorization[7:]
            else:
                session_id = authorization
        
        # 销毁会话
        if session_id:
            await auth_service.destroy_session(session_id)
        
        # 清除Cookie
        response.delete_cookie("session_id")
        
        return {"message": "登出成功"}
        
    except Exception as e:
        logger.error(f"登出失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """获取当前用户信息"""
    return UserResponse.from_orm(current_user)