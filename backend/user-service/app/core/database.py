#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 数据库连接管理

提供异步数据库连接、会话管理和基础模型类
"""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, DateTime, func
from datetime import datetime

from .config import settings


# 全局变量，延迟初始化
engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None


class Base(DeclarativeBase):
    """
    数据库模型基类
    
    提供通用字段和方法
    """
    
    # 主键ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, comment="主键ID")
    
    # 时间戳字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    
    def __repr__(self) -> str:
        """
        模型字符串表示
        
        Returns:
            str: 模型描述
        """
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self) -> dict:
        """
        将模型转换为字典
        
        Returns:
            dict: 模型字典表示
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


def init_database() -> None:
    """
    初始化数据库连接
    
    创建数据库引擎和会话工厂
    """
    global engine, AsyncSessionLocal
    
    if engine is None:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20
        )
    
    if AsyncSessionLocal is None:
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    依赖注入函数，用于FastAPI路由中获取数据库会话
    
    Yields:
        AsyncSession: 异步数据库会话
    """
    if AsyncSessionLocal is None:
        init_database()
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    初始化数据库
    
    创建所有表结构
    """
    if engine is None:
        init_database()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    关闭数据库连接
    
    清理数据库连接池
    """
    if engine is not None:
        await engine.dispose()


class DatabaseManager:
    """
    数据库管理器
    
    提供数据库连接管理和健康检查功能
    """
    
    def __init__(self):
        if engine is None or AsyncSessionLocal is None:
            init_database()
        self.engine = engine
        self.session_factory = AsyncSessionLocal
    
    async def health_check(self) -> bool:
        """
        数据库健康检查
        
        Returns:
            bool: 数据库是否正常
        """
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False
    
    async def get_connection_info(self) -> dict:
        """
        获取数据库连接信息
        
        Returns:
            dict: 连接信息
        """
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }


# 全局数据库管理器实例，延迟初始化
db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager