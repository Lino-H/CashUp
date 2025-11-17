"""
数据库连接和会话管理
函数集注释：
- Database: 异步数据库引擎与会话管理
- get_database: 获取全局数据库实例
- get_db: FastAPI依赖，返回会话或测试替身
- FakeSession/FakeResult: 测试环境下的最小化会话实现
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import asynccontextmanager
import asyncio

from config.settings import settings

USE_FAKE_DB = str(os.getenv("TEST_FAKE_DB", "")).lower() in ("1", "true", "yes")

# 创建异步数据库引擎（测试环境可跳过）
engine = None
AsyncSessionLocal = None
if not USE_FAKE_DB:
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
            if self._engine is None:
                return
            async with self._engine.begin() as conn:
                pass
            print("数据库连接成功")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self._engine is None:
            return
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
    """FastAPI依赖注入 - 获取数据库会话或测试替身"""
    if USE_FAKE_DB:
        yield FakeSession()
        return
    async with get_database().session() as session:
        yield session


class FakeResult:
    def __init__(self):
        self._rows = []
    def fetchall(self):
        return []
    def first(self):
        return None

class FakeSession:
    async def execute(self, *_args, **_kwargs):
        return FakeResult()
    async def commit(self):
        return None
    async def close(self):
        return None