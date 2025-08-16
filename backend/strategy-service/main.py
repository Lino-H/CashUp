#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp策略服务主入口

提供策略管理、回测和风险评估功能的微服务。
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.database import db_manager as database_manager
from app.core.cache import get_redis as get_redis_manager
from app.middleware import (
    setup_cors,
    setup_logging_middleware,
    setup_error_handlers,
    setup_security_middleware
)
from app.api.v1 import api_v1_router

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format,
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    Args:
        app: FastAPI应用实例
    """
    # 启动时初始化
    logger.info("策略服务启动中...")
    
    try:
        # 检查数据库连接
        try:
            db_health = database_manager.health_check()
            if db_health["status"] == "healthy":
                logger.info("数据库连接已建立")
            else:
                logger.error(f"数据库连接失败: {db_health.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
        
        # 创建数据库表
        from app.core.database import create_tables
        create_tables()
        logger.info("数据库表已创建")
        
        # 检查Redis连接
        redis_manager = get_redis_manager()
        redis_health = redis_manager.health_check()
        if redis_health["status"] == "healthy":
            logger.info("Redis连接已建立")
        else:
            logger.error(f"Redis连接失败: {redis_health.get('error', 'Unknown error')}")
        
        # 检查服务健康状态
        db_health = database_manager.health_check()
        db_healthy = db_health["status"] == "healthy"
        redis_health = redis_manager.health_check()
        redis_healthy = redis_health["status"] == "healthy"
        
        if not db_healthy:
            logger.error("数据库健康检查失败")
        if not redis_healthy:
            logger.error("Redis健康检查失败")
        
        logger.info("策略服务启动完成")
        
    except Exception as e:
        logger.error(f"策略服务启动失败: {e}")
        raise
    
    yield
    
    # 关闭时清理
    logger.info("策略服务关闭中...")
    
    try:
        # 关闭Redis连接
        redis_manager = get_redis_manager()
        redis_manager.close()
        logger.info("Redis连接已关闭")
        
        # 关闭数据库连接
        database_manager.close()
        logger.info("数据库连接已关闭")
        
        logger.info("策略服务已关闭")
        
    except Exception as e:
        logger.error(f"策略服务关闭失败: {e}")


# 创建FastAPI应用
app = FastAPI(
    title="CashUp策略服务",
    description="提供策略管理、回测和风险评估功能的微服务",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# 设置中间件
setup_cors(app)
setup_logging_middleware(app)
setup_error_handlers(app)
setup_security_middleware(app)

# 注册路由
app.include_router(api_v1_router, prefix="/api")


@app.get("/health")
async def health_check():
    """
    健康检查
    
    Returns:
        dict: 健康状态
    """
    try:
        # 检查数据库连接
        db_health = database_manager.health_check()
        db_healthy = db_health["status"] == "healthy"
        
        # 检查Redis连接
        redis_manager = get_redis_manager()
        redis_health = redis_manager.health_check()
        redis_healthy = redis_health["status"] == "healthy"
        
        # 整体健康状态
        overall_healthy = db_healthy and redis_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
        )


@app.get("/")
async def root():
    """
    根路径
    
    Returns:
        dict: 服务信息
    """
    return {
        "service": "CashUp策略服务",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled"
    }


@app.get("/metrics")
async def metrics():
    """
    服务指标
    
    Returns:
        dict: 服务指标信息
    """
    try:
        # 获取数据库连接池状态
        db_pool_status = database_manager.health_check()
        
        # 获取Redis连接状态
        redis_manager = get_redis_manager()
        redis_status = redis_manager.health_check()
        
        return {
            "database": db_pool_status,
            "redis": redis_status,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error(f"获取服务指标失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "获取服务指标失败",
                "details": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )