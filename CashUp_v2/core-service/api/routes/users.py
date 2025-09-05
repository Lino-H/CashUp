"""
用户管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from ..schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from ..services.user import UserService
from ..database.connection import get_db
from ..utils.logger import get_logger
from ..auth.dependencies import get_current_user, get_current_active_user

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)

@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表"""
    try:
        user_service = UserService(db)
        users, total = await user_service.get_users(
            skip=skip, 
            limit=limit, 
            search=search, 
            role=role
        )
        
        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户详情"""
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查权限：用户只能查看自己的信息，管理员可以查看所有用户
        if current_user.id != user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此用户信息"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户详情失败"
        )

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建用户"""
    try:
        # 只有管理员可以创建用户
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权创建用户"
            )
        
        user_service = UserService(db)
        
        # 检查用户名是否已存在
        existing_user = await user_service.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        existing_email = await user_service.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        # 创建用户
        user = await user_service.create_user(user_data)
        
        logger.info(f"用户创建成功: {user.username}")
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户信息"""
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查权限：用户只能更新自己的信息，管理员可以更新所有用户
        if current_user.id != user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新此用户信息"
            )
        
        # 如果是普通用户，只能更新部分字段
        if current_user.role != "admin":
            # 过滤掉普通用户不能更新的字段
            update_data = user_data.dict(exclude={'role', 'status', 'is_verified'})
        else:
            update_data = user_data.dict()
        
        # 更新用户
        updated_user = await user_service.update_user(user_id, update_data)
        
        logger.info(f"用户更新成功: {updated_user.username}")
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户失败"
        )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除用户"""
    try:
        # 只有管理员可以删除用户
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除用户"
            )
        
        # 不能删除自己
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账户"
            )
        
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 删除用户
        await user_service.delete_user(user_id)
        
        logger.info(f"用户删除成功: {user.username}")
        return {"message": "用户删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新当前用户信息"""
    try:
        user_service = UserService(db)
        
        # 普通用户只能更新部分字段
        update_data = user_data.dict(exclude={'role', 'status', 'is_verified'})
        
        # 更新用户
        updated_user = await user_service.update_user(current_user.id, update_data)
        
        logger.info(f"当前用户更新成功: {updated_user.username}")
        return UserResponse.from_orm(updated_user)
        
    except Exception as e:
        logger.error(f"更新当前用户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )

@router.post("/me/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    try:
        user_service = UserService(db)
        
        # 验证旧密码
        if not await user_service.verify_password(current_user.id, old_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码错误"
            )
        
        # 更新密码
        await user_service.update_password(current_user.id, new_password)
        
        logger.info(f"用户密码修改成功: {current_user.username}")
        return {"message": "密码修改成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败"
        )