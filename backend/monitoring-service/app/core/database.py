#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 数据库连接管理

数据库连接池和会话管理
"""

import logging
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError

from .config import settings

logger = logging.getLogger(__name__)

# 创建基础模型类
Base = declarative_base()

# 数据库引擎
engine: Optional[Engine] = None

# 会话工厂
SessionLocal: Optional[sessionmaker] = None


def create_database_engine() -> Engine:
    """创建数据库引擎"""
    try:
        # 数据库连接配置
        engine_config = {
            "url": settings.DATABASE_URL,
            "poolclass": QueuePool,
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
            "pool_recycle": settings.DATABASE_POOL_RECYCLE,
            "pool_pre_ping": True,  # 连接前检查
            "echo": settings.DEBUG,  # 开发环境下打印SQL
            "echo_pool": settings.DEBUG,  # 开发环境下打印连接池信息
        }
        
        # 创建引擎
        db_engine = create_engine(**engine_config)
        
        # 添加事件监听器
        setup_engine_events(db_engine)
        
        logger.info(f"Database engine created successfully: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
        return db_engine
        
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


def setup_engine_events(db_engine: Engine):
    """设置数据库引擎事件监听器"""
    
    @event.listens_for(db_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """SQLite特定配置"""
        if "sqlite" in str(db_engine.url):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()
    
    @event.listens_for(db_engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        """连接检出事件"""
        logger.debug("Database connection checked out")
    
    @event.listens_for(db_engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        """连接检入事件"""
        logger.debug("Database connection checked in")
    
    @event.listens_for(db_engine, "invalidate")
    def receive_invalidate(dbapi_connection, connection_record, exception):
        """连接失效事件"""
        logger.warning(f"Database connection invalidated: {exception}")
    
    @event.listens_for(db_engine, "soft_invalidate")
    def receive_soft_invalidate(dbapi_connection, connection_record, exception):
        """连接软失效事件"""
        logger.warning(f"Database connection soft invalidated: {exception}")


def create_session_factory(db_engine: Engine) -> sessionmaker:
    """创建会话工厂"""
    return sessionmaker(
        bind=db_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )


def init_database():
    """初始化数据库连接"""
    global engine, SessionLocal
    
    try:
        # 创建数据库引擎
        engine = create_database_engine()
        
        # 创建会话工厂
        SessionLocal = create_session_factory(engine)
        
        # 测试连接
        test_database_connection()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def test_database_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            result.fetchone()
        logger.info("Database connection test successful")
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（依赖注入）"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database session: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话（上下文管理器）"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database session: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """创建数据库表"""
    try:
        if engine is None:
            raise RuntimeError("Database engine not initialized")
        
        # 导入所有模型以确保它们被注册
        from app.models import *  # noqa
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_tables():
    """删除数据库表"""
    try:
        if engine is None:
            raise RuntimeError("Database engine not initialized")
        
        # 导入所有模型以确保它们被注册
        from app.models import *  # noqa
        
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
        
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def get_database_info() -> dict:
    """获取数据库信息"""
    try:
        if engine is None:
            raise RuntimeError("Database engine not initialized")
        
        info = {
            "url": str(engine.url).replace(engine.url.password or "", "***") if engine.url.password else str(engine.url),
            "driver": engine.url.drivername,
            "database": engine.url.database,
            "host": engine.url.host,
            "port": engine.url.port,
            "pool_size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "invalid": engine.pool.invalid()
        }
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {}


def check_database_health() -> dict:
    """检查数据库健康状态"""
    try:
        if engine is None:
            return {
                "status": "error",
                "message": "Database engine not initialized"
            }
        
        # 测试连接
        with engine.connect() as connection:
            start_time = time.time()
            result = connection.execute("SELECT 1")
            result.fetchone()
            response_time = time.time() - start_time
        
        # 获取连接池状态
        pool_status = {
            "size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "invalid": engine.pool.invalid()
        }
        
        # 计算健康状态
        status = "healthy"
        if pool_status["checked_out"] / pool_status["size"] > 0.8:
            status = "warning"  # 连接池使用率过高
        if response_time > 1.0:
            status = "warning"  # 响应时间过长
        
        return {
            "status": status,
            "response_time": response_time,
            "pool_status": pool_status,
            "message": "Database is healthy"
        }
        
    except DisconnectionError as e:
        logger.error(f"Database disconnection error: {e}")
        return {
            "status": "error",
            "message": f"Database disconnected: {e}"
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return {
            "status": "error",
            "message": f"Database error: {e}"
        }
    except Exception as e:
        logger.error(f"Unexpected database health check error: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {e}"
        }


def close_database():
    """关闭数据库连接"""
    global engine, SessionLocal
    
    try:
        if engine:
            engine.dispose()
            logger.info("Database engine disposed")
        
        engine = None
        SessionLocal = None
        
    except Exception as e:
        logger.error(f"Error closing database: {e}")


# 数据库操作辅助函数
def execute_raw_sql(sql: str, params: dict = None) -> list:
    """执行原始SQL查询"""
    try:
        with get_db_session() as db:
            result = db.execute(sql, params or {})
            return result.fetchall()
    except Exception as e:
        logger.error(f"Failed to execute raw SQL: {e}")
        raise


def get_table_row_count(table_name: str) -> int:
    """获取表行数"""
    try:
        sql = f"SELECT COUNT(*) FROM {table_name}"
        result = execute_raw_sql(sql)
        return result[0][0] if result else 0
    except Exception as e:
        logger.error(f"Failed to get table row count: {e}")
        return 0


def get_database_size() -> dict:
    """获取数据库大小信息"""
    try:
        if "postgresql" in str(engine.url):
            # PostgreSQL
            sql = """
            SELECT 
                pg_size_pretty(pg_database_size(current_database())) as database_size,
                pg_database_size(current_database()) as database_size_bytes
            """
            result = execute_raw_sql(sql)
            if result:
                return {
                    "size": result[0][0],
                    "size_bytes": result[0][1]
                }
        elif "mysql" in str(engine.url):
            # MySQL
            sql = """
            SELECT 
                ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb,
                SUM(data_length + index_length) AS size_bytes
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
            """
            result = execute_raw_sql(sql)
            if result:
                return {
                    "size": f"{result[0][0]} MB",
                    "size_bytes": result[0][1]
                }
        elif "sqlite" in str(engine.url):
            # SQLite
            import os
            db_path = engine.url.database
            if os.path.exists(db_path):
                size_bytes = os.path.getsize(db_path)
                size_mb = size_bytes / 1024 / 1024
                return {
                    "size": f"{size_mb:.2f} MB",
                    "size_bytes": size_bytes
                }
        
        return {"size": "Unknown", "size_bytes": 0}
        
    except Exception as e:
        logger.error(f"Failed to get database size: {e}")
        return {"size": "Error", "size_bytes": 0}


# 导入time模块
import time


# 在应用启动时自动初始化数据库
if not engine:
    try:
        init_database()
    except Exception as e:
        logger.warning(f"Failed to auto-initialize database: {e}")