"""
用户数据模型定义
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """用户角色枚举"""
    USER = "USER"
    ADMIN = "ADMIN"
    TRADER = "TRADER"

class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    is_verified: bool = False

class UserCreate(UserBase):
    """创建用户模型"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度不能少于6位')
        if len(v) > 50:
            raise ValueError('密码长度不能超过50位')
        return v

class UserUpdate(BaseModel):
    """更新用户模型"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_verified: Optional[bool] = None

class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserResponse]
    total: int
    skip: int
    limit: int

class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度不能少于6位')
        if len(v) > 50:
            raise ValueError('密码长度不能超过50位')
        return v