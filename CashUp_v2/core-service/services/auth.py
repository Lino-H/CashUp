"""
认证服务层 - 简化版（基于会话）
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import uuid
import bcrypt
from passlib.context import CryptContext
import redis.asyncio as redis

from ..models.models import User
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """认证服务类"""
    
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户身份"""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # 更新最后登录时间
        await self.update_last_login(user.id)
        
        return user
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        from ..services.user import UserService
        user_service = UserService(self.db)
        return await user_service.get_user_by_username(username)
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        from ..services.user import UserService
        user_service = UserService(self.db)
        return await user_service.get_user_by_id(user_id)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)
    
    async def update_last_login(self, user_id: int) -> None:
        """更新最后登录时间"""
        from ..services.user import UserService
        user_service = UserService(self.db)
        await user_service.update_last_login(user_id)
    
    async def create_session(self, user_id: int) -> str:
        """创建用户会话"""
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_access": datetime.utcnow().isoformat()
        }
        
        # 会话有效期24小时
        await self.redis.setex(
            f"session:{session_id}", 
            24 * 3600,  # 24小时
            str(session_data)
        )
        
        return session_id
    
    async def validate_session(self, session_id: str) -> Optional[int]:
        """验证会话并返回用户ID"""
        try:
            session_data = await self.redis.get(f"session:{session_id}")
            if not session_data:
                return None
            
            # 更新最后访问时间
            await self.redis.expire(f"session:{session_id}", 24 * 3600)
            
            # 简单解析用户ID
            import json
            data = json.loads(session_data)
            return data.get("user_id")
            
        except Exception as e:
            logger.error(f"会话验证失败: {e}")
            return None
    
    async def destroy_session(self, session_id: str) -> bool:
        """销毁用户会话"""
        try:
            await self.redis.delete(f"session:{session_id}")
            return True
        except Exception as e:
            logger.error(f"会话销毁失败: {e}")
            return False
    
    async def create_user(self, username: str, email: str, password: str, full_name: str = None) -> User:
        """创建用户"""
        from ..services.user import UserService
        from ..schemas.user import UserCreate
        
        user_service = UserService(self.db)
        user_data = UserCreate(
            username=username,
            email=email,
            password=password,
            full_name=full_name
        )
        
        return await user_service.create_user(user_data)