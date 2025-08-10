#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 用户数据模式

定义用户相关的 Pydantic 模式，用于API请求和响应验证
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    """
    用户基础模式
    """
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    timezone: str = Field(default="UTC", description="时区")
    language: str = Field(default="zh-CN", description="语言偏好")


class UserCreate(UserBase):
    """
    用户创建模式
    """
    password: str = Field(..., min_length=8, max_length=50, description="密码")
    invitation_code: Optional[str] = Field(None, description="邀请码")
    
    @validator('username')
    def validate_username(cls, v):
        """
        验证用户名格式
        """
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        """
        验证密码强度
        """
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('密码必须包含大写字母、小写字母和数字')
        
        return v


class UserUpdate(BaseModel):
    """
    用户更新模式
    """
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    timezone: Optional[str] = Field(None, description="时区")
    language: Optional[str] = Field(None, description="语言偏好")


class UserPasswordUpdate(BaseModel):
    """
    用户密码更新模式
    """
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=50, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """
        验证密码确认
        """
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v


class UserLogin(BaseModel):
    """
    用户登录模式
    """
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(default=False, description="记住我")


class UserResponse(UserBase):
    """
    用户响应模式
    """
    id: int
    status: UserStatus
    is_active: bool
    is_email_verified: bool
    is_superuser: bool
    last_login: Optional[datetime]
    login_count: int
    avatar_url: Optional[str]
    roles: List[str] = Field(default_factory=list, description="用户角色")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """
    用户个人资料模式
    """
    id: int
    username: str
    email: str
    full_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    timezone: str
    language: str
    is_email_verified: bool
    roles: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """
    用户列表响应模式
    """
    id: int
    username: str
    email: str
    full_name: Optional[str]
    status: UserStatus
    is_active: bool
    last_login: Optional[datetime]
    roles: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# 认证相关模式
class Token(BaseModel):
    """
    令牌模式
    """
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")


class TokenRefresh(BaseModel):
    """
    令牌刷新模式
    """
    refresh_token: str = Field(..., description="刷新令牌")


class LoginResponse(BaseModel):
    """
    登录响应模式
    """
    user: UserProfile
    token: Token
    message: str = Field(default="登录成功", description="响应消息")


# 角色和权限模式
class RoleBase(BaseModel):
    """
    角色基础模式
    """
    name: str = Field(..., max_length=50, description="角色名称")
    display_name: str = Field(..., max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="角色描述")


class RoleCreate(RoleBase):
    """
    角色创建模式
    """
    permissions: List[int] = Field(default_factory=list, description="权限ID列表")


class RoleUpdate(BaseModel):
    """
    角色更新模式
    """
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: Optional[bool] = Field(None, description="是否激活")
    permissions: Optional[List[int]] = Field(None, description="权限ID列表")


class RoleResponse(RoleBase):
    """
    角色响应模式
    """
    id: int
    is_active: bool
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PermissionBase(BaseModel):
    """
    权限基础模式
    """
    name: str = Field(..., max_length=100, description="权限名称")
    display_name: str = Field(..., max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="权限描述")
    resource: str = Field(..., max_length=50, description="资源类型")
    action: str = Field(..., max_length=50, description="操作类型")


class PermissionCreate(PermissionBase):
    """
    权限创建模式
    """
    pass


class PermissionUpdate(BaseModel):
    """
    权限更新模式
    """
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="权限描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class PermissionResponse(PermissionBase):
    """
    权限响应模式
    """
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 通用响应模式
class MessageResponse(BaseModel):
    """
    消息响应模式
    """
    message: str = Field(..., description="响应消息")
    success: bool = Field(default=True, description="是否成功")
    data: Optional[dict] = Field(None, description="附加数据")


class PaginatedResponse(BaseModel):
    """
    分页响应模式
    """
    items: List[dict] = Field(..., description="数据项列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


# 密码强度验证模式
class PasswordStrengthResponse(BaseModel):
    """
    密码强度响应模式
    """
    is_valid: bool = Field(..., description="密码是否有效")
    strength_score: int = Field(..., description="强度分数(0-100)")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")


# 邮箱验证模式
class EmailVerificationRequest(BaseModel):
    """
    邮箱验证请求模式
    """
    email: str = Field(..., description="邮箱地址")


class EmailVerificationConfirm(BaseModel):
    """
    邮箱验证确认模式
    """
    token: str = Field(..., description="验证令牌")


# 密码重置模式
class PasswordResetRequest(BaseModel):
    """
    密码重置请求模式
    """
    email: str = Field(..., description="邮箱地址")


class PasswordResetConfirm(BaseModel):
    """
    密码重置确认模式
    """
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=50, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """
        验证密码确认
        """
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v