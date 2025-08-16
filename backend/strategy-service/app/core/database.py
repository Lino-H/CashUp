#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接管理

提供PostgreSQL数据库连接池管理，包括会话创建、
事务管理和连接池配置。
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# 数据库引擎配置
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug
)

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 基础模型类
Base = declarative_base()

# 元数据
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    Yields:
        Session: SQLAlchemy数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """
    创建所有数据库表
    """
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.warning(f"创建数据库表时出现警告: {e}")
        # 不抛出异常，因为表可能已经存在


def drop_tables():
    """
    删除所有数据库表（谨慎使用）
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("数据库表已删除")
    except Exception as e:
        logger.error(f"删除数据库表失败: {e}")
        raise


def check_connection() -> bool:
    """
    检查数据库连接状态
    
    Returns:
        bool: 连接是否正常
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False


class DatabaseManager:
    """
    数据库管理器
    
    提供数据库连接池管理、健康检查等功能
    """
    
    def __init__(self):
        self.engine = engine
        self.session_factory = SessionLocal
    
    def get_session(self) -> Session:
        """
        获取新的数据库会话
        
        Returns:
            Session: 数据库会话
        """
        return self.session_factory()
    
    def health_check(self) -> dict:
        """
        数据库健康检查
        
        Returns:
            dict: 健康检查结果
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute("SELECT version()")
                version = result.fetchone()[0]
                
            pool = self.engine.pool
            
            return {
                "status": "healthy",
                "database_version": version,
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def close(self):
        """
        关闭数据库连接池
        """
        self.engine.dispose()
        logger.info("数据库连接池已关闭")


# 全局数据库管理器实例
db_manager = DatabaseManager()