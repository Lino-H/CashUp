#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 配置管理服务

提供系统配置、用户配置、策略配置等的统一管理
支持配置版本控制、热更新、权限控制等功能
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import get_settings
from app.core.database import init_database, close_database
from app.core.cache import init_redis, close_redis
from app.core.exceptions import setup_exception_handlers
from app.middleware.logging import LoggingMiddleware
from app.middleware.auth import AuthMiddleware
from app.api.v1.router import api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    管理应用启动和关闭时的资源初始化和清理
    """
    # 启动时初始化
    logger.info("Starting CashUp Config Service...")
    
    try:
        # 初始化数据库
        await init_database()
        logger.info("Database initialized successfully")
        
        # 初始化Redis缓存
        await init_redis()
        logger.info("Redis cache initialized successfully")
        
        logger.info("Config Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Config Service: {str(e)}")
        raise
    
    yield
    
    # 关闭时清理资源
    logger.info("Shutting down Config Service...")
    
    try:
        await close_redis()
        logger.info("Redis connection closed")
        
        await close_database()
        logger.info("Database connection closed")
        
        logger.info("Config Service shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# 创建FastAPI应用实例
app = FastAPI(
    title="CashUp Config Service",
    description="CashUp量化交易系统配置管理服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加受信任主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 添加自定义中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)

# 设置异常处理器
setup_exception_handlers(app)

# 注册API路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    根路径接口
    
    Returns:
        dict: 服务基本信息
    """
    return {
        "service": "CashUp Config Service",
        "version": "1.0.0",
        "status": "running",
        "description": "配置管理服务 - 提供系统配置、用户配置、策略配置的统一管理"
    }


@app.get("/health")
async def health_check():
    """
    健康检查接口
    
    Returns:
        dict: 服务健康状态
    """
    from app.core.database import check_database_health
    from app.core.cache import check_redis_health
    
    try:
        # 检查数据库连接
        db_healthy = await check_database_health()
        
        # 检查Redis连接
        redis_healthy = await check_redis_health()
        
        # 整体健康状态
        healthy = db_healthy and redis_healthy
        
        return {
            "status": "healthy" if healthy else "unhealthy",
            "database": "ok" if db_healthy else "error",
            "redis": "ok" if redis_healthy else "error",
            "timestamp": "2024-12-19T10:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-12-19T10:00:00Z"
            }
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )