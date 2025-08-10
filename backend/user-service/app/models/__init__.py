#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 数据模型包

定义数据库模型和ORM映射
"""

from .user import User, Role, Permission, UserSession, UserRole, UserStatus

__all__ = [
    "User",
    "Role", 
    "Permission",
    "UserSession",
    "UserRole",
    "UserStatus"
]

__version__ = "1.0.0"
__author__ = "CashUp Team"
__description__ = "User Service Models Package"