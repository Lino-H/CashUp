#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 用户API路由

提供用户注册、登录、管理等API接口
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id, validate_password_strength
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate, UserUpdate, UserPasswordUpdate, UserLogin,
    UserResponse, UserProfile, LoginResponse, Token, TokenRefresh,
    MessageResponse, PasswordStrengthResponse
)


router = APIRouter(prefix="/users", tags=["用户管理"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册
    
    创建新用户账户，支持邀请码注册
    
    - **username**: 用户名 (3-50字符，只能包含字母、数字、下划线和连字符)
    - **email**: 邮箱地址
    - **password**: 密码 (至少8位，包含大小写字母和数字)
    - **full_name**: 真实姓名 (可选)
    - **invitation_code**: 邀请码 (可选)
    """
    user_service = UserService(db)
    
    try:
        # 获取邀请人信息（如果有）
        invited_by = None
        if hasattr(request.state, 'current_user_id'):
            invited_by = request.state.current_user_id
        
        user = await user_service.create_user(user_data, invited_by)
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    验证用户凭据并返回访问令牌
    
    - **username**: 用户名或邮箱地址
    - **password**: 密码
    - **remember_me**: 是否记住登录状态
    """
    user_service = UserService(db)
    
    try:
        # 获取客户端IP地址
        ip_address = request.client.host if request.client else None
        
        login_response = await user_service.authenticate_user(login_data, ip_address)
        return login_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌
    
    使用刷新令牌获取新的访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    user_service = UserService(db)
    
    try:
        new_token = await user_service.refresh_token(token_data.refresh_token)
        return new_token
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失败: {str(e)}"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户信息
    
    返回当前登录用户的详细信息
    """
    user_service = UserService(db)
    
    try:
        user = await user_service.get_user_by_id(current_user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserProfile(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            bio=user.bio,
            avatar_url=user.avatar_url,
            timezone=user.timezone,
            language=user.language,
            is_email_verified=user.is_email_verified,
            roles=user.role_names,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户信息
    
    更新当前登录用户的个人信息
    
    - **full_name**: 真实姓名
    - **bio**: 个人简介
    - **avatar_url**: 头像URL
    - **timezone**: 时区
    - **language**: 语言偏好
    """
    user_service = UserService(db)
    
    try:
        updated_user = await user_service.update_user(current_user_id, user_data)
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户信息失败: {str(e)}"
        )


@router.put("/me/password", response_model=MessageResponse)
async def update_current_user_password(
    password_data: UserPasswordUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户密码
    
    修改当前登录用户的密码
    
    - **current_password**: 当前密码
    - **new_password**: 新密码
    - **confirm_password**: 确认新密码
    """
    user_service = UserService(db)
    
    try:
        success = await user_service.update_password(current_user_id, password_data)
        
        if success:
            return MessageResponse(
                message="密码更新成功，请重新登录",
                success=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码更新失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码更新失败: {str(e)}"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout_user(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登出
    
    撤销当前用户的所有会话令牌
    """
    user_service = UserService(db)
    
    try:
        success = await user_service.revoke_all_user_sessions(current_user_id)
        
        if success:
            return MessageResponse(
                message="登出成功",
                success=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="登出失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserProfile)
async def get_user_by_id(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    根据ID获取用户信息
    
    获取指定用户的公开信息
    
    - **user_id**: 用户ID
    """
    user_service = UserService(db)
    
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 只返回公开信息
        return UserProfile(
            id=user.id,
            username=user.username,
            email=user.email if user.id == current_user_id else "",  # 只有本人能看到邮箱
            full_name=user.full_name,
            bio=user.bio,
            avatar_url=user.avatar_url,
            timezone=user.timezone,
            language=user.language,
            is_email_verified=user.is_email_verified,
            roles=user.role_names,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


# 工具接口
@router.post("/check-password-strength", response_model=PasswordStrengthResponse)
async def check_password_strength(password: str):
    """
    检查密码强度
    
    验证密码是否符合安全要求
    
    - **password**: 待检查的密码
    """
    try:
        result = validate_password_strength(password)
        
        # 生成改进建议
        suggestions = []
        if result["strength_score"] < 60:
            suggestions.append("建议使用更复杂的密码")
        if len(password) < 12:
            suggestions.append("建议密码长度至少12位")
        if not any(c.isupper() for c in password):
            suggestions.append("建议包含大写字母")
        if not any(c.islower() for c in password):
            suggestions.append("建议包含小写字母")
        if not any(c.isdigit() for c in password):
            suggestions.append("建议包含数字")
        if not any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
            suggestions.append("建议包含特殊字符")
        
        return PasswordStrengthResponse(
            is_valid=result["is_valid"],
            strength_score=result["strength_score"],
            errors=result["errors"],
            suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码强度检查失败: {str(e)}"
        )


@router.get("/username/{username}/available")
async def check_username_availability(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """
    检查用户名是否可用
    
    验证用户名是否已被注册
    
    - **username**: 待检查的用户名
    """
    user_service = UserService(db)
    
    try:
        existing_user = await user_service.get_user_by_username(username)
        
        return {
            "username": username,
            "available": existing_user is None,
            "message": "用户名可用" if existing_user is None else "用户名已被使用"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查用户名可用性失败: {str(e)}"
        )


@router.get("/email/{email}/available")
async def check_email_availability(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    检查邮箱是否可用
    
    验证邮箱是否已被注册
    
    - **email**: 待检查的邮箱地址
    """
    user_service = UserService(db)
    
    try:
        existing_user = await user_service.get_user_by_email(email)
        
        return {
            "email": email,
            "available": existing_user is None,
            "message": "邮箱可用" if existing_user is None else "邮箱已被注册"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查邮箱可用性失败: {str(e)}"
        )