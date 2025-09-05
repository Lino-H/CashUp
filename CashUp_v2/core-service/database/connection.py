"""
数据库连接和会话管理
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import asynccontextmanager
import asyncio

from config.settings import settings

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 创建基础模型类
Base = declarative_base()

class Database:
    """数据库管理类"""
    
    def __init__(self):
        self._engine = engine
        self._session_factory = AsyncSessionLocal
    
    async def connect(self):
        """连接数据库"""
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("数据库连接成功")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        await self._engine.dispose()
        print("数据库连接已关闭")
    
    @asynccontextmanager
    async def session(self):
        """创建数据库会话上下文"""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

# 全局数据库实例
_database_instance = None

def get_database() -> Database:
    """获取数据库实例"""
    global _database_instance
    if _database_instance is None:
        _database_instance = Database()
    return _database_instance

async def get_db_session():
    """获取数据库会话依赖"""
    async with get_database().session() as session:
        yield session

# 依赖注入函数
async def get_db():
    """FastAPI依赖注入 - 获取数据库会话"""
    async with get_database().session() as session:
        yield session