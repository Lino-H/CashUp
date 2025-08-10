#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 策略服务主应用

提供量化策略管理、回测、执行和性能分析功能
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis import redis_manager
from app.core.logging import setup_logging
from app.core.middleware import (
    LoggingMiddleware,
    PerformanceMiddleware,
    SecurityMiddleware
)
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    处理应用启动和关闭时的初始化和清理工作
    """
    # 启动时初始化
    try:
        # 初始化日志
        setup_logging()
        
        # 初始化数据库
        await init_db()
        print("Database initialized successfully")
        
        # 初始化Redis连接
        await redis_manager.connect()
        print("Redis connected successfully")
        
        print(f"Strategy Service started on {settings.HOST}:{settings.PORT}")
        
    except Exception as e:
        print(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # 关闭时清理
    try:
        await redis_manager.disconnect()
        await close_db()
        print("Application shutdown completed")
    except Exception as e:
        print(f"Error during shutdown: {e}")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="CashUp量化交易系统策略服务，提供策略管理、回测、执行和性能分析功能",
    lifespan=lifespan,
    debug=settings.DEBUG
)


# 异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP异常处理器
    
    Args:
        request: 请求对象
        exc: HTTP异常
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "HTTPException"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    通用异常处理器
    
    Args:
        request: 请求对象
        exc: 异常
        
    Returns:
        JSONResponse: 错误响应
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "InternalError"
            }
        }
    )


# 添加中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(SecurityMiddleware)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """
    健康检查接口
    
    Returns:
        dict: 服务状态信息
    """
    # 检查数据库连接
    try:
        from app.core.database import get_db_manager
        db_manager = get_db_manager()
        db_healthy = await db_manager.health_check()
    except Exception:
        db_healthy = False
    
    # 检查Redis连接
    redis_healthy = await redis_manager.health_check()
    
    status = "healthy" if db_healthy and redis_healthy else "unhealthy"
    
    return {
        "status": status,
        "service": "strategy-service",
        "version": settings.VERSION,
        "database": "connected" if db_healthy else "disconnected",
        "redis": "connected" if redis_healthy else "disconnected",
        "debug_mode": settings.DEBUG
    }


@app.get("/")
async def root():
    """
    根路径接口
    
    Returns:
        dict: 服务基本信息
    """
    return {
        "message": "CashUp Strategy Service",
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    # 启动服务
    print(f"Starting {settings.APP_NAME}...")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Database: {settings.DATABASE