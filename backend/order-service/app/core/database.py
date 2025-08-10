#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务数据库配置

管理数据库连接、会话和模型基类
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

from .config import settings, get_database_config, get_database_url

logger = logging.getLogger(__name__)


# 数据库元数据配置
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)


class Base(DeclarativeBase):
    """
    数据库模型基类
    
    所有数据库模型都应该继承此类
    """
    metadata = metadata


# 全局数据库引擎和会话
engine: AsyncEngine = None
SessionLocal: async_sessionmaker[AsyncSession] = None


async def init_database() -> None:
    """
    初始化数据库连接
    
    创建数据库引擎、会话工厂，并创建所有表
    """
    global engine, SessionLocal
    
    try:
        # 获取数据库配置
        db_config = get_database_config()
        
        # 创建异步数据库引擎
        engine = create_async_engine(
            get_database_url(),
            echo=db_config["echo"],
            pool_size=db_config["pool_size"],
            max_overflow=db_config["max_overflow"],
            pool_timeout=db_config["pool_timeout"],
            pool_recycle=db_config["pool_recycle"]
        )
        
        # 创建会话工厂
        SessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # 创建所有表
        async with engine.begin() as conn:
            # 导入所有模型以确保它们被注册
            from ..models import order  # noqa: F401
            
            # 创建表
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ 订单服务数据库初始化成功")
        
    except Exception as e:
        logger.error(f"❌ 订单服务数据库初始化失败: {str(e)}")
        raise


async def close_database() -> None:
    """
    关闭数据库连接
    
    清理数据库资源
    """
    global engine
    
    if engine:
        await engine.dispose()
        logger.info("👋 订单服务数据库连接已关闭")


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    依赖注入函数，用于在API端点中获取数据库会话
    
    Yields:
        AsyncSession: 数据库会话
    """
    if not SessionLocal:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话异常: {str(e)}")
            raise
        finally:
            await session.close()


async def get_database_session_context() -> AsyncSession:
    """
    获取数据库会话（非依赖注入版本）
    
    用于在服务层直接获取数据库会话
    
    Returns:
        AsyncSession: 数据库会话
    """
    if not SessionLocal:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    
    return SessionLocal()


class DatabaseManager:
    """
    数据库管理器
    
    提供数据库操作的高级接口
    """
    
    def __init__(self):
        self.engine = engine
        self.session_factory = SessionLocal
    
    async def health_check(self) -> bool:
        """
        数据库健康检查
        
        Returns:
            bool: 数据库是否健康
        """
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"数据库健康检查失败: {str(e)}")
            return False
    
    async def get_connection_info(self) -> dict:
        """
        获取数据库连接信息
        
        Returns:
            dict: 连接信息
        """
        if not self.engine:
            return {"status": "disconnected"}
        
        return {
            "status": "connected",
            "url": str(self.engine.url).replace(self.engine.url.password or "", "***"),
            "pool_size": self.engine.pool.size(),
            "checked_in": self.engine.pool.checkedin(),
            "checked_out": self.engine.pool.checkedout(),
            "overflow": self.engine.pool.overflow()
        }


# 创建全局数据库管理器实例
db_manager = DatabaseManager()


# 健康检查函数
async def check_database_health() -> bool:
    """
    检查数据库健康状态
    
    Returns:
        bool: 数据库是否健康
    """
    return await db_manager.health_check()


# 获取数据库信息
async def get_database_info() -> dict:
    """
    获取数据库连接信息
    
    Returns:
        dict: 数据库信息
    """
    return await db_manager.get_connection_info()