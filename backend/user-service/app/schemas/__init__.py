#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 数据模式包

定义API请求和响应的数据模式
"""

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserLogin,
    UserResponse,
    UserProfile,
    UserListResponse,
    Token,
    TokenRefresh,
    LoginResponse,
    RoleResponse,
    PermissionResponse,
    MessageResponse,
    PaginatedResponse,
    PasswordStrengthResponse,
    EmailVerificationRequest,
    EmailVerificationConfirm,
    PasswordResetRequest,
    PasswordResetConfirm
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPasswordUpdate",
    "UserLogin",
    "UserResponse",
    "UserProfile",
    "UserListResponse",
    "Token",
    "TokenRefresh",
    "LoginResponse",
    "RoleResponse",
    "PermissionResponse",
    "MessageResponse",
    "PaginatedResponse",
    "PasswordStrengthCheck",
    "EmailVerification",
    "PasswordReset"
]

__version__ = "1.0.0"
__author__ = "CashUp Team"
__description__ = "User Service Schemas Package"