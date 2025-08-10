#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 配置服务数据库配置

管理数据库连接、会话和健康检查
"""

import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from contextlib import asynccontextmanager

from .config import get_database_config, get_database_url

logger = logging.getLogger(__name__)

# 全局变量
engine: Optional[AsyncEngine] = None
SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


class Base(DeclarativeBase):
    """
    SQLAlchemy声明式基类
    
    所有数据库模型都应该继承此类
    """
    pass


async def init_database() -> None:
    """
    初始化数据库连接
    
    创建数据库引擎和会话工厂
    """
    global engine, SessionLocal
    
    try:
        # 获取数据库配置
        db_config = get_database_config()
        database_url = get_database_url()
        
        logger.info(f"Initializing database connection to: {database_url}")
        
        # 创建异步引擎
        engine = create_async_engine(
            database_url,
            echo=db_config["echo"],
            pool_size=db_config["pool_size"],
            max_overflow=db_config["max_overflow"],
            pool_timeout=db_config["pool_timeout"],
            pool_recycle=db_config["pool_recycle"],
            future=True
        )
        
        # 创建会话工厂
        SessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # 创建数据库表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def close_database() -> None:
    """
    关闭数据库连接
    
    清理数据库资源
    """
    global engine
    
    if engine:
        try:
            await engine.dispose()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    依赖注入函数，用于FastAPI路由
    
    Yields:
        AsyncSession: 数据库会话
    """
    if not SessionLocal:
        raise RuntimeError("Database not initialized")
    
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_database_transaction():
    """
    获取数据库事务会话
    
    用于需要事务控制的操作
    
    Yields:
        AsyncSession: 数据库会话
    """
    if not SessionLocal:
        raise RuntimeError("Database not initialized")
    
    async with SessionLocal() as session:
        async with session.begin():
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database transaction error: {str(e)}")
                raise


async def check_database_health() -> bool:
    """
    检查数据库健康状态
    
    Returns:
        bool: 数据库是否健康
    """
    try:
        if not engine:
            return False
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
            
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False


async def execute_raw_sql(sql: str, params: Optional[dict] = None) -> any:
    """
    执行原生SQL语句
    
    Args:
        sql: SQL语句
        params: 参数字典
        
    Returns:
        any: 执行结果
    """
    if not engine:
        raise RuntimeError("Database not initialized")
    
    try:
        async with engine.begin() as conn:
            if params:
                result = await conn.execute(text(sql), params)
            else:
                result = await conn.execute(text(sql))
            return result
            
    except Exception as e:
        logger.error(f"Failed to execute SQL: {sql}, error: {str(e)}")
        raise


async def get_database_info() -> dict:
    """
    获取数据库信息
    
    Returns:
        dict: 数据库信息
    """
    try:
        if not engine:
            return {"status": "not_initialized"}
        
        async with engine.begin() as conn:
            # 获取数据库版本
            version_result = await conn.execute(text("SELECT version()"))
            version = version_result.scalar()
            
            # 获取连接池信息
            pool = engine.pool
            
            return {
                "status": "connected",
                "version": version,
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
            
    except Exception as e:
        logger.error(f"Failed to get database info: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


# 数据库依赖
DatabaseDep = get_database_session