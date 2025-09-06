"""
数据库连接管理
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from typing import AsyncGenerator
import logging

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# 创建数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    """基础模型类"""
    pass

async def get_database():
    """获取数据库连接"""
    return DatabaseConnection()

class DatabaseConnection:
    """数据库连接管理类"""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
    
    async def connect(self) -> None:
        """连接数据库"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ 数据库连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    async def disconnect(self) -> None:
        """断开数据库连接"""
        try:
            await self.engine.dispose()
            logger.info("✅ 数据库连接已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭数据库连接失败: {e}")
    
    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        async with self.session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

# 依赖注入函数
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖函数"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# 全局数据库连接实例
db_connection = None

async def get_database():
    """获取全局数据库连接实例"""
    global db_connection
    if db_connection is None:
        db_connection = DatabaseConnection()
    return db_connection