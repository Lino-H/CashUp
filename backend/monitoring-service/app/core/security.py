#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 安全认证

JWT认证、密码加密和权限管理
"""

import jwt
import bcrypt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings
from .exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Token数据模型"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = []
    permissions: List[str] = []
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None


class User(BaseModel):
    """用户模型"""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    roles: List[str] = []
    permissions: List[str] = []
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Token响应模型"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: User


# 密码相关函数
def hash_password(password: str) -> str:
    """加密密码"""
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def generate_password(length: int = 12) -> str:
    """生成随机密码"""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# JWT相关函数
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    try:
        to_encode = data.copy()
        
        # 设置过期时间
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        # 生成JWT
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise AuthenticationError("Failed to create access token")


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建刷新令牌"""
    try:
        to_encode = data.copy()
        
        # 设置过期时间
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        # 生成JWT
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Refresh token creation error: {e}")
        raise AuthenticationError("Failed to create refresh token")


def verify_token(token: str) -> TokenData:
    """验证令牌"""
    try:
        # 解码JWT
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # 检查令牌类型
        token_type = payload.get("type")
        if token_type not in ["access", "refresh"]:
            raise AuthenticationError("Invalid token type")
        
        # 提取用户信息
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
        
        # 创建TokenData对象
        token_data = TokenData(
            user_id=user_id,
            username=payload.get("username"),
            email=payload.get("email"),
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
            exp=datetime.fromtimestamp(payload.get("exp", 0)),
            iat=datetime.fromtimestamp(payload.get("iat", 0))
        )
        
        return token_data
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.JWTError as e:
        logger.error(f"JWT verification error: {e}")
        raise AuthenticationError("Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise AuthenticationError("Token verification failed")


def refresh_access_token(refresh_token: str) -> str:
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        token_data = verify_token(refresh_token)
        
        # 检查是否为刷新令牌
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")
        
        # 创建新的访问令牌
        access_token_data = {
            "sub": token_data.user_id,
            "username": token_data.username,
            "email": token_data.email,
            "roles": token_data.roles,
            "permissions": token_data.permissions
        }
        
        return create_access_token(access_token_data)
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise AuthenticationError("Failed to refresh token")


# 用户认证函数
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """获取当前用户"""
    if not credentials:
        raise AuthenticationError("Authentication credentials required")
    
    try:
        # 验证令牌
        token_data = verify_token(credentials.credentials)
        
        # 这里应该从数据库获取用户信息
        # 示例实现
        user = User(
            id=token_data.user_id,
            username=token_data.username or "unknown",
            email=token_data.email or "unknown@example.com",
            roles=token_data.roles,
            permissions=token_data.permissions
        )
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        return user
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise AuthenticationError("Failed to get current user")


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise AuthenticationError("User account is disabled")
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise AuthorizationError("Superuser access required")
    return current_user


# 权限检查函数
def check_permission(user: User, permission: str) -> bool:
    """检查用户权限"""
    if user.is_superuser:
        return True
    
    return permission in user.permissions


def check_role(user: User, role: str) -> bool:
    """检查用户角色"""
    if user.is_superuser:
        return True
    
    return role in user.roles


def require_permission(permission: str):
    """权限检查装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从参数中获取用户对象
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            if not user:
                # 从kwargs中查找
                for value in kwargs.values():
                    if isinstance(value, User):
                        user = value
                        break
            
            if not user:
                raise AuthenticationError("User not found in function arguments")
            
            if not check_permission(user, permission):
                raise AuthorizationError(
                    f"Permission '{permission}' required",
                    action=permission
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role: str):
    """角色检查装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从参数中获取用户对象
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            if not user:
                # 从kwargs中查找
                for value in kwargs.values():
                    if isinstance(value, User):
                        user = value
                        break
            
            if not user:
                raise AuthenticationError("User not found in function arguments")
            
            if not check_role(user, role):
                raise AuthorizationError(
                    f"Role '{role}' required",
                    resource=role
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# 权限依赖注入
def RequirePermission(permission: str):
    """权限依赖注入"""
    async def permission_checker(current_user: User = Depends(get_current_user)):
        if not check_permission(current_user, permission):
            raise AuthorizationError(
                f"Permission '{permission}' required",
                action=permission
            )
        return current_user
    
    return permission_checker


def RequireRole(role: str):
    """角色依赖注入"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if not check_role(current_user, role):
            raise AuthorizationError(
                f"Role '{role}' required",
                resource=role
            )
        return current_user
    
    return role_checker


# API密钥相关
def generate_api_key() -> str:
    """生成API密钥"""
    return secrets.token_urlsafe(32)


def verify_api_key(api_key: str) -> bool:
    """验证API密钥"""
    # 这里应该从数据库验证API密钥
    # 示例实现
    valid_api_keys = [
        "demo_api_key_123",
        "test_api_key_456"
    ]
    return api_key in valid_api_keys


# 安全工具函数
def generate_csrf_token() -> str:
    """生成CSRF令牌"""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, expected_token: str) -> bool:
    """验证CSRF令牌"""
    return secrets.compare_digest(token, expected_token)


def generate_session_id() -> str:
    """生成会话ID"""
    return secrets.token_urlsafe(32)


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """掩码敏感数据"""
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


# 安全配置验证
def validate_security_config() -> List[str]:
    """验证安全配置"""
    errors = []
    
    # 检查密钥强度
    if len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY should be at least 32 characters long")
    
    if settings.SECRET_KEY == "your-secret-key-here-change-in-production":
        errors.append("SECRET_KEY must be changed from default value")
    
    # 检查令牌过期时间
    if settings.ACCESS_TOKEN_EXPIRE_MINUTES > 1440:  # 24小时
        errors.append("ACCESS_TOKEN_EXPIRE_MINUTES should not exceed 24 hours")
    
    if settings.REFRESH_TOKEN_EXPIRE_DAYS > 30:
        errors.append("REFRESH_TOKEN_EXPIRE_DAYS should not exceed 30 days")
    
    return errors


# 安全中间件辅助函数
def get_client_ip(request) -> str:
    """获取客户端IP地址"""
    # 检查代理头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def is_safe_url(url: str, allowed_hosts: List[str]) -> bool:
    """检查URL是否安全"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # 检查是否为相对URL
        if not parsed.netloc:
            return True
        
        # 检查主机是否在允许列表中
        return parsed.netloc in allowed_hosts
        
    except Exception:
        return False


# 审计日志
def log_security_event(
    event_type: str,
    user_id: str = None,
    ip_address: str = None,
    details: Dict[str, Any] = None
):
    """记录安全事件"""
    logger.info(
        f"Security event: {event_type}",
        extra={
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# 权限常量
class Permissions:
    """权限常量"""
    
    # 指标权限
    METRICS_READ = "metrics:read"
    METRICS_WRITE = "metrics:write"
    METRICS_DELETE = "metrics:delete"
    
    # 告警权限
    ALERTS_READ = "alerts:read"
    ALERTS_WRITE = "alerts:write"
    ALERTS_DELETE = "alerts:delete"
    ALERTS_MANAGE = "alerts:manage"
    
    # 健康检查权限
    HEALTH_READ = "health:read"
    HEALTH_WRITE = "health:write"
    HEALTH_DELETE = "health:delete"
    
    # 仪表板权限
    DASHBOARD_READ = "dashboard:read"
    DASHBOARD_WRITE = "dashboard:write"
    DASHBOARD_DELETE = "dashboard:delete"
    DASHBOARD_SHARE = "dashboard:share"
    
    # 系统权限
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_ADMIN = "system:admin"
    
    # 用户管理权限
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    USER_ADMIN = "user:admin"


class Roles:
    """角色常量"""
    
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    GUEST = "guest"


# 默认角色权限映射
DEFAULT_ROLE_PERMISSIONS = {
    Roles.ADMIN: [
        Permissions.METRICS_READ, Permissions.METRICS_WRITE, Permissions.METRICS_DELETE,
        Permissions.ALERTS_READ, Permissions.ALERTS_WRITE, Permissions.ALERTS_DELETE, Permissions.ALERTS_MANAGE,
        Permissions.HEALTH_READ, Permissions.HEALTH_WRITE, Permissions.HEALTH_DELETE,
        Permissions.DASHBOARD_READ, Permissions.DASHBOARD_WRITE, Permissions.DASHBOARD_DELETE, Permissions.DASHBOARD_SHARE,
        Permissions.SYSTEM_READ, Permissions.SYSTEM_WRITE, Permissions.SYSTEM_ADMIN,
        Permissions.USER_READ, Permissions.USER_WRITE, Permissions.USER_DELETE, Permissions.USER_ADMIN
    ],
    Roles.OPERATOR: [
        Permissions.METRICS_READ, Permissions.METRICS_WRITE,
        Permissions.ALERTS_READ, Permissions.ALERTS_WRITE, Permissions.ALERTS_MANAGE,
        Permissions.HEALTH_READ, Permissions.HEALTH_WRITE,
        Permissions.DASHBOARD_READ, Permissions.DASHBOARD_WRITE, Permissions.DASHBOARD_SHARE,
        Permissions.SYSTEM_READ
    ],
    Roles.VIEWER: [
        Permissions.METRICS_READ,
        Permissions.ALERTS_READ,
        Permissions.HEALTH_READ,
        Permissions.DASHBOARD_READ,
        Permissions.SYSTEM_READ
    ],
    Roles.GUEST: [
        Permissions.DASHBOARD_READ
    ]
}