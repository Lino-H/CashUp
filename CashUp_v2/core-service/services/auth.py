"""
认证服务层
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
import jwt
import bcrypt
from passlib.context import CryptContext

from ..models.models import User
from ..schemas.auth import TokenData
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """认证服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
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
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        from ..config.settings import settings
        
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """创建刷新令牌"""
        from ..config.settings import settings
        
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """验证令牌"""
        from ..config.settings import settings
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            
            if username is None or user_id is None:
                return None
            
            return TokenData(username=username, user_id=user_id)
        
        except jwt.PyJWTError:
            return None
    
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