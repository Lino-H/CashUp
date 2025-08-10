#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 用户服务层

提供用户管理、认证、权限等业务逻辑处理
"""

import secrets
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.user import User, Role, Permission, UserSession, UserStatus
from app.schemas.user import (
    UserCreate, UserUpdate, UserPasswordUpdate, UserLogin,
    UserResponse, UserProfile, LoginResponse, Token
)
from app.core.security import (
    hash_password, verify_password, validate_password_strength,
    create_access_token, create_refresh_token, verify_token
)
from app.core.redis import redis_manager
from app.core.config import settings


class UserService:
    """
    用户服务类
    
    提供用户管理相关的业务逻辑
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, user_data: UserCreate, invited_by: Optional[int] = None) -> UserResponse:
        """
        创建新用户
        
        Args:
            user_data: 用户创建数据
            invited_by: 邀请人ID
            
        Returns:
            UserResponse: 创建的用户信息
            
        Raises:
            HTTPException: 用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        existing_user = await self.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        existing_email = await self.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 验证密码强度
        password_check = validate_password_strength(user_data.password)
        if not password_check["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"密码强度不足: {', '.join(password_check['errors'])}"
            )
        
        # 验证邀请码（如果需要）
        if user_data.invitation_code and not invited_by:
            inviter = await self.verify_invitation_code(user_data.invitation_code)
            if inviter:
                invited_by = inviter.id
        
        # 创建用户
        hashed_password = hash_password(user_data.password)
        
        db_user = User(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            bio=user_data.bio,
            timezone=user_data.timezone,
            language=user_data.language,
            invited_by=invited_by,
            invitation_code=user_data.invitation_code
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        # 分配默认角色
        await self.assign_default_role(db_user.id)
        
        # 重新加载用户以获取角色信息
        user_with_roles = await self.get_user_by_id(db_user.id)
        
        return UserResponse(
            id=user_with_roles.id,
            username=user_with_roles.username,
            email=user_with_roles.email,
            full_name=user_with_roles.full_name,
            bio=user_with_roles.bio,
            timezone=user_with_roles.timezone,
            language=user_with_roles.language,
            status=user_with_roles.status,
            is_active=user_with_roles.is_active,
            is_email_verified=user_with_roles.is_email_verified,
            is_superuser=user_with_roles.is_superuser,
            last_login=user_with_roles.last_login,
            login_count=user_with_roles.login_count,
            avatar_url=user_with_roles.avatar_url,
            roles=user_with_roles.role_names,
            created_at=user_with_roles.created_at,
            updated_at=user_with_roles.updated_at
        )
    
    async def authenticate_user(self, login_data: UserLogin, ip_address: Optional[str] = None) -> LoginResponse:
        """
        用户认证登录
        
        Args:
            login_data: 登录数据
            ip_address: 客户端IP地址
            
        Returns:
            LoginResponse: 登录响应
            
        Raises:
            HTTPException: 认证失败
        """
        # 检查登录尝试次数
        identifier = login_data.username.lower()
        attempts = await redis_manager.get_login_attempts(identifier)
        
        if attempts >= settings.MAX_LOGIN_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"登录尝试次数过多，请{settings.ACCOUNT_LOCKOUT_DURATION}秒后重试"
            )
        
        # 获取用户
        user = await self.get_user_by_username_or_email(login_data.username)
        if not user:
            await redis_manager.increment_login_attempts(identifier)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被禁用"
            )
        
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被暂停"
            )
        
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被锁定"
            )
        
        # 验证密码
        if not verify_password(login_data.password, user.hashed_password):
            await redis_manager.increment_login_attempts(identifier)
            
            # 增加失败尝试次数
            user.failed_login_attempts += 1
            
            # 如果失败次数过多，锁定账户
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(seconds=settings.ACCOUNT_LOCKOUT_DURATION)
                user.status = UserStatus.LOCKED
            
            await self.db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 登录成功，重置失败尝试次数
        await redis_manager.reset_login_attempts(identifier)
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        user.login_count += 1
        
        if user.status == UserStatus.LOCKED:
            user.status = UserStatus.ACTIVE
            user.locked_until = None
        
        await self.db.commit()
        
        # 生成令牌
        token_data = {"sub": str(user.id), "username": user.username}
        
        # 根据记住我选项设置过期时间
        if login_data.remember_me:
            access_token_expires = timedelta(days=7)
        else:
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        access_token = create_access_token(token_data, access_token_expires)
        refresh_token = create_refresh_token(token_data)
        
        # 保存会话信息
        await self.create_user_session(
            user.id, access_token, refresh_token, ip_address
        )
        
        # 构建响应
        user_profile = UserProfile(
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
        
        token = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
        
        return LoginResponse(
            user=user_profile,
            token=token,
            message="登录成功"
        )
    
    async def refresh_token(self, refresh_token: str) -> Token:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            Token: 新的令牌信息
            
        Raises:
            HTTPException: 令牌无效
        """
        # 验证刷新令牌
        payload = verify_token(refresh_token, "refresh")
        user_id = int(payload.get("sub"))
        
        # 检查用户是否存在且活跃
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 检查会话是否存在
        session = await self.get_user_session_by_token(refresh_token)
        if not session or not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="会话已失效"
            )
        
        # 生成新的访问令牌
        token_data = {"sub": str(user.id), "username": user.username}
        access_token = create_access_token(token_data)
        
        # 更新会话令牌
        session.session_token = access_token
        await self.db.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            User: 用户对象
        """
        stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            User: 用户对象
        """
        stmt = select(User).options(selectinload(User.roles)).where(User.username == username.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            User: 用户对象
        """
        stmt = select(User).options(selectinload(User.roles)).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_username_or_email(self, identifier: str) -> Optional[User]:
        """
        根据用户名或邮箱获取用户
        
        Args:
            identifier: 用户名或邮箱
            
        Returns:
            User: 用户对象
        """
        identifier = identifier.lower()
        stmt = select(User).options(selectinload(User.roles)).where(
            or_(User.username == identifier, User.email == identifier)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            user_data: 更新数据
            
        Returns:
            UserResponse: 更新后的用户信息
            
        Raises:
            HTTPException: 用户不存在
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新字段
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            bio=user.bio,
            timezone=user.timezone,
            language=user.language,
            status=user.status,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            is_superuser=user.is_superuser,
            last_login=user.last_login,
            login_count=user.login_count,
            avatar_url=user.avatar_url,
            roles=user.role_names,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    async def update_password(self, user_id: int, password_data: UserPasswordUpdate) -> bool:
        """
        更新用户密码
        
        Args:
            user_id: 用户ID
            password_data: 密码更新数据
            
        Returns:
            bool: 是否更新成功
            
        Raises:
            HTTPException: 用户不存在或当前密码错误
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证当前密码
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        
        # 验证新密码强度
        password_check = validate_password_strength(password_data.new_password)
        if not password_check["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"密码强度不足: {', '.join(password_check['errors'])}"
            )
        
        # 更新密码
        user.hashed_password = hash_password(password_data.new_password)
        await self.db.commit()
        
        # 清除所有会话，强制重新登录
        await self.revoke_all_user_sessions(user_id)
        
        return True
    
    async def assign_default_role(self, user_id: int) -> bool:
        """
        为用户分配默认角色
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否分配成功
        """
        # 获取默认角色（交易员）
        stmt = select(Role).where(Role.name == "trader")
        result = await self.db.execute(stmt)
        default_role = result.scalar_one_or_none()
        
        if not default_role:
            # 如果默认角色不存在，创建它
            default_role = Role(
                name="trader",
                display_name="交易员",
                description="默认交易员角色"
            )
            self.db.add(default_role)
            await self.db.commit()
            await self.db.refresh(default_role)
        
        # 获取用户并分配角色
        user = await self.get_user_by_id(user_id)
        if user and default_role not in user.roles:
            user.roles.append(default_role)
            await self.db.commit()
        
        return True
    
    async def verify_invitation_code(self, code: str) -> Optional[User]:
        """
        验证邀请码
        
        Args:
            code: 邀请码
            
        Returns:
            User: 邀请人用户对象
        """
        # TODO: 实现邀请码验证逻辑
        # 当前版本暂时返回None
        return None
    
    async def create_user_session(
        self, 
        user_id: int, 
        session_token: str, 
        refresh_token: str, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """
        创建用户会话
        
        Args:
            user_id: 用户ID
            session_token: 会话令牌
            refresh_token: 刷新令牌
            ip_address: IP地址
            user_agent: 用户代理
            
        Returns:
            UserSession: 会话对象
        """
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def get_user_session_by_token(self, refresh_token: str) -> Optional[UserSession]:
        """
        根据刷新令牌获取会话
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            UserSession: 会话对象
        """
        stmt = select(UserSession).where(
            and_(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def revoke_all_user_sessions(self, user_id: int) -> bool:
        """
        撤销用户的所有会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否撤销成功
        """
        stmt = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()
        
        for session in sessions:
            session.is_active = False
        
        await self.db.commit()
        return True