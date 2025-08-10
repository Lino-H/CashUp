#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易服务主应用

提供交易执行、订单管理、风险控制、持仓管理等核心交易功能
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis import redis_manager
from app.core.middleware import (
    LoggingMiddleware,
    PerformanceMiddleware,
    SecurityMiddleware
)
from app.core.logging import setup_logging
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
        
        print(f"Trading Service started on {settings.HOST}:{settings.PORT}")
        print(f"Debug mode: {settings.DEBUG}")
        print(f"Database: {settings.DATABASE_URL}")
        print(f"Redis: {settings.REDIS_URL}")
        
    except Exception as e:
        print(f"Failed to initialize trading service: {e}")
        raise
    
    yield
    
    # 关闭时清理
    try:
        await redis_manager.disconnect()
        await close_db()
        print("Trading Service shutdown completed")
    except Exception as e:
        print(f"Error during shutdown: {e}")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="CashUp量化交易系统 - 交易服务API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
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
                "type": "http_error"
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
                "message": "Internal server error" if not settings.DEBUG else str(exc),
                "type": "internal_error"
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


# 健康检查接口
@app.get("/health")
async def health_check():
    """
    健康检查接口
    
    Returns:
        dict: 服务健康状态
    """
    try:
        # 检查Redis连接
        redis_healthy = await redis_manager.health_check()
        
        return {
            "status": "healthy",
            "service": "trading-service",
            "version": settings.VERSION,
            "redis": "connected" if redis_healthy else "disconnected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "trading-service",
            "error": str(e)
        }


# 根路径
@app.get("/")
async def root():
    """
    根路径接口
    
    Returns:
        dict: 服务基本信息
    """
    return {
        "service": "CashUp Trading Service",
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )