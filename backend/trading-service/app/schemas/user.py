#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易服务用户模式

简化的用户模式，用于交易服务中的用户信息
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class UserStatus(str, Enum):
    """
    用户状态枚举
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserResponse(BaseModel):
    """
    用户响应模式（简化版）
    """
    id: int
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, description="真实姓名")
    status: UserStatus
    is_active: bool
    roles: List[str] = Field(default_factory=list, description="用户角色")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """
    用户个人资料模式（简化版）
    """
    id: int
    username: str
    email: str
    full_name: Optional[str]
    roles: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True