"""
用户服务层
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional, Tuple
from datetime import datetime
import bcrypt

from models.models import User
from schemas.user import UserCreate, UserUpdate
from utils.logger import get_logger

logger = get_logger(__name__)

class UserService:
    """用户服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None, 
        role: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """获取用户列表"""
        query = select(User)
        
        if search:
            query = query.where(
                User.username.ilike(f"%{search}%") | 
                User.email.ilike(f"%{search}%") |
                User.full_name.ilike(f"%{search}%")
            )
        
        if role:
            query = query.where(User.role == role)
        
        # 获取总数
        count_query = select(User.__table__)
        if search:
            count_query = count_query.where(
                User.username.ilike(f"%{search}%") | 
                User.email.ilike(f"%{search}%") |
                User.full_name.ilike(f"%{search}%")
            )
        if role:
            count_query = count_query.where(User.role == role)
        
        count_result = await self.db.execute(count_query)
        total = len(count_result.fetchall())
        
        # 分页查询
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return list(users), total
    
    async def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        # 密码加密
        hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            password_hash=hashed_password.decode('utf-8'),
            role=user_data.role,
            status=user_data.status,
            is_verified=user_data.is_verified
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def update_user(self, user_id: int, update_data: dict) -> User:
        """更新用户信息"""
        query = update(User).where(User.id == user_id).values(**update_data)
        await self.db.execute(query)
        await self.db.commit()
        
        updated_user = await self.get_user_by_id(user_id)
        return updated_user
    
    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        query = delete(User).where(User.id == user_id)
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def verify_password(self, user_id: int, password: str) -> bool:
        """验证密码"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        return bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
    
    async def update_password(self, user_id: int, new_password: str) -> bool:
        """更新密码"""
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        query = update(User).where(User.id == user_id).values(
            password_hash=hashed_password.decode('utf-8'),
            updated_at=datetime.utcnow()
        )
        await self.db.execute(query)
        await self.db.commit()
        
        return True
    
    async def update_last_login(self, user_id: int) -> bool:
        """更新最后登录时间"""
        query = update(User).where(User.id == user_id).values(
            last_login=datetime.utcnow()
        )
        await self.db.execute(query)
        await self.db.commit()
        
        return True