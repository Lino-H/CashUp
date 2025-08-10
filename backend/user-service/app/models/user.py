#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 用户数据模型

定义用户、角色、权限等数据模型
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from app.core.database import Base


class UserRole(str, Enum):
    """
    用户角色枚举
    """
    TRADER = "trader"  # 交易员
    DEVELOPER = "developer"  # 策略开发者
    ADMIN = "admin"  # 系统管理员


class UserStatus(str, Enum):
    """
    用户状态枚举
    """
    ACTIVE = "active"  # 活跃
    INACTIVE = "inactive"  # 非活跃
    SUSPENDED = "suspended"  # 暂停
    LOCKED = "locked"  # 锁定


# 用户角色关联表
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)

# 角色权限关联表
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)


class User(Base):
    """
    用户模型
    
    存储用户基本信息、认证信息和状态
    """
    __tablename__ = "users"
    
    # 基本信息
    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        index=True, 
        nullable=False,
        comment="用户名"
    )
    email: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        index=True, 
        nullable=False,
        comment="邮箱地址"
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment="真实姓名"
    )
    
    # 认证信息
    hashed_password: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="加密密码"
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="邮箱是否已验证"
    )
    
    # 状态信息
    status: Mapped[UserStatus] = mapped_column(
        String(20), 
        default=UserStatus.ACTIVE,
        comment="用户状态"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="是否激活"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="是否超级用户"
    )
    
    # 登录信息
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        comment="最后登录时间"
    )
    login_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="登录次数"
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="失败登录尝试次数"
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        comment="锁定到期时间"
    )
    
    # 个人资料
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        comment="头像URL"
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="个人简介"
    )
    timezone: Mapped[str] = mapped_column(
        String(50), 
        default="UTC",
        comment="时区"
    )
    language: Mapped[str] = mapped_column(
        String(10), 
        default="zh-CN",
        comment="语言偏好"
    )
    
    # 邀请信息
    invited_by: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=True,
        comment="邀请人ID"
    )
    invitation_code: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True,
        comment="邀请码"
    )
    
    # 关联关系
    roles: Mapped[List["Role"]] = relationship(
        "Role", 
        secondary=user_roles, 
        back_populates="users",
        lazy="selectin"
    )
    inviter: Mapped[Optional["User"]] = relationship(
        "User", 
        remote_side=lambda: User.id,
        back_populates="invitees"
    )
    invitees: Mapped[List["User"]] = relationship(
        "User", 
        back_populates="inviter"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def is_locked(self) -> bool:
        """
        检查用户是否被锁定
        
        Returns:
            bool: 是否被锁定
        """
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def role_names(self) -> List[str]:
        """
        获取用户角色名称列表
        
        Returns:
            List[str]: 角色名称列表
        """
        return [role.name for role in self.roles]
    
    def has_role(self, role_name: str) -> bool:
        """
        检查用户是否具有指定角色
        
        Args:
            role_name: 角色名称
            
        Returns:
            bool: 是否具有角色
        """
        return role_name in self.role_names
    
    def has_permission(self, permission_name: str) -> bool:
        """
        检查用户是否具有指定权限
        
        Args:
            permission_name: 权限名称
            
        Returns:
            bool: 是否具有权限
        """
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False


class Role(Base):
    """
    角色模型
    
    定义系统角色和权限
    """
    __tablename__ = "roles"
    
    name: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False,
        comment="角色名称"
    )
    display_name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="显示名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="角色描述"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="是否激活"
    )
    
    # 关联关系
    users: Mapped[List[User]] = relationship(
        "User", 
        secondary=user_roles, 
        back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", 
        secondary=role_permissions, 
        back_populates="roles",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"
    
    @property
    def permission_names(self) -> List[str]:
        """
        获取角色权限名称列表
        
        Returns:
            List[str]: 权限名称列表
        """
        return [permission.name for permission in self.permissions]
    
    def has_permission(self, permission_name: str) -> bool:
        """
        检查角色是否具有指定权限
        
        Args:
            permission_name: 权限名称
            
        Returns:
            bool: 是否具有权限
        """
        return permission_name in self.permission_names


class Permission(Base):
    """
    权限模型
    
    定义系统权限
    """
    __tablename__ = "permissions"
    
    name: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False,
        comment="权限名称"
    )
    display_name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="显示名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="权限描述"
    )
    resource: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="资源类型"
    )
    action: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="操作类型"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="是否激活"
    )
    
    # 关联关系
    roles: Mapped[List[Role]] = relationship(
        "Role", 
        secondary=role_permissions, 
        back_populates="permissions"
    )
    
    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name='{self.name}')>"


class UserSession(Base):
    """
    用户会话模型
    
    记录用户登录会话信息
    """
    __tablename__ = "user_sessions"
    
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=False,
        comment="用户ID"
    )
    session_token: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False,
        comment="会话令牌"
    )
    refresh_token: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False,
        comment="刷新令牌"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), 
        nullable=True,
        comment="IP地址"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="用户代理"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False,
        comment="过期时间"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="是否激活"
    )
    
    # 关联关系
    user: Mapped[User] = relationship("User", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """
        检查会话是否过期
        
        Returns:
            bool: 是否过期
        """
        return datetime.utcnow() > self.expires_at