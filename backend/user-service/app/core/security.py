#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 安全认证模块

提供JWT令牌管理、密码加密、权限验证等安全功能
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer 认证
security = HTTPBearer()


class SecurityManager:
    """
    安全管理器
    
    提供密码加密、JWT令牌管理、权限验证等功能
    """
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def hash_password(self, password: str) -> str:
        """
        加密密码
        
        Args:
            password: 明文密码
            
        Returns:
            str: 加密后的密码哈希
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 加密后的密码哈希
            
        Returns:
            bool: 密码是否正确
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        验证密码强度
        
        Args:
            password: 待验证的密码
            
        Returns:
            dict: 验证结果
        """
        errors = []
        
        # 检查长度
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"密码长度至少{settings.PASSWORD_MIN_LENGTH}位")
        
        # 检查大写字母
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("密码必须包含大写字母")
        
        # 检查小写字母
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("密码必须包含小写字母")
        
        # 检查数字
        if settings.PASSWORD_REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("密码必须包含数字")
        
        # 检查特殊字符
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码必须包含特殊字符")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength_score": self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> int:
        """
        计算密码强度分数
        
        Args:
            password: 密码
            
        Returns:
            int: 强度分数 (0-100)
        """
        score = 0
        
        # 长度分数
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # 字符类型分数
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 15
        
        # 复杂度分数
        unique_chars = len(set(password))
        if unique_chars >= len(password) * 0.7:
            score += 15
        
        return min(score, 100)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        
        Args:
            data: 令牌载荷数据
            expires_delta: 过期时间增量
            
        Returns:
            str: JWT访问令牌
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        创建刷新令牌
        
        Args:
            data: 令牌载荷数据
            
        Returns:
            str: JWT刷新令牌
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            token_type: 令牌类型 (access/refresh)
            
        Returns:
            dict: 令牌载荷数据
            
        Raises:
            HTTPException: 令牌无效或过期
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_current_user_id(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
        """
        从JWT令牌中获取当前用户ID
        
        Args:
            credentials: HTTP认证凭据
            
        Returns:
            int: 用户ID
            
        Raises:
            HTTPException: 认证失败
        """
        payload = self.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        return int(user_id)


# 创建全局安全管理器实例
security_manager = SecurityManager()

# 导出常用函数
hash_password = security_manager.hash_password
verify_password = security_manager.verify_password
validate_password_strength = security_manager.validate_password_strength
create_access_token = security_manager.create_access_token
create_refresh_token = security_manager.create_refresh_token
verify_token = security_manager.verify_token
get_current_user_id = security_manager.get_current_user_id


# 权限装饰器
def require_permissions(*permissions: str):
    """
    权限验证装饰器
    
    Args:
        permissions: 所需权限列表
        
    Returns:
        function: 装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # TODO: 实现权限验证逻辑
            # 当前版本暂时跳过权限检查
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 角色验证装饰器
def require_roles(*roles: str):
    """
    角色验证装饰器
    
    Args:
        roles: 所需角色列表
        
    Returns:
        function: 装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # TODO: 实现角色验证逻辑
            # 当前版本暂时跳过角色检查
            return await func(*args, **kwargs)
        return wrapper
    return decorator