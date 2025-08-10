#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知服务数据库配置

管理数据库连接、会话和基础模型
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    create_async_engine, 
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from sqlalchemy import event

from .config import get_settings, get_database_url

logger = logging.getLogger(__name__)
settings = get_settings()


class Base(DeclarativeBase):
    """
    数据库模型基类
    
    所有数据库模型都应该继承此类
    """
    pass


# 全局数据库引擎和会话工厂
engine: AsyncEngine = None
SessionLocal: async_sessionmaker[AsyncSession] = None


def get_engine() -> AsyncEngine:
    """
    获取数据库引擎
    
    Returns:
        AsyncEngine: 数据库引擎实例
    """
    global engine
    if engine is None:
        database_url = get_database_url()
        
        # 根据数据库类型设置不同的配置
        if "sqlite" in database_url:
            # SQLite配置
            engine = create_async_engine(
                database_url,
                echo=settings.DEBUG,
                poolclass=NullPool,
                connect_args={"check_same_thread": False}
            )
        else:
            # PostgreSQL配置
            engine = create_async_engine(
                database_url,
                echo=settings.DEBUG,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600
            )
        
        # 添加连接事件监听器
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """为SQLite设置PRAGMA"""
            if "sqlite" in database_url:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    return engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    获取会话工厂
    
    Returns:
        async_sessionmaker[AsyncSession]: 会话工厂
    """
    global SessionLocal
    if SessionLocal is None:
        engine = get_engine()
        SessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    return SessionLocal


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    这是一个依赖注入函数，用于FastAPI的Depends
    
    Yields:
        AsyncSession: 数据库会话
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """
    初始化数据库
    
    创建所有表和初始数据
    """
    try:
        engine = get_engine()
        
        # 导入所有模型以确保它们被注册
        from ..models import notification, template, channel
        
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def close_database():
    """
    关闭数据库连接
    
    清理数据库资源
    """
    global engine, SessionLocal
    
    try:
        if engine:
            await engine.dispose()
            engine = None
        
        SessionLocal = None
        logger.info("Database connections closed successfully")
        
    except Exception as e:
        logger.error(f"Failed to close database connections: {str(e)}")
        raise


async def check_database_health() -> bool:
    """
    检查数据库健康状态
    
    Returns:
        bool: 数据库是否健康
    """
    try:
        session_factory = get_session_factory()
        async with session_