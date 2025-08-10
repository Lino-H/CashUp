#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务主应用

提供订单生命周期管理、订单状态跟踪、订单历史查询等核心功能
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_database, close_database
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import (
    CashUpException,
    cashup_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.core.middleware import (
    RequestLoggingMiddleware,
    SecurityMiddleware,
    PerformanceMiddleware
)
from app.api.v1.router import api_router


# 设置日志
setup_logging()
logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    启动时创建数据库表，关闭时清理资源
    """
    try:
        # 启动时初始化数据库
        await init_database()
        logger.info("✅ 订单服务启动成功")
        logger.info(f"🌍 调试模式: {settings.DEBUG}")
        logger.info(f"🔗 数据库: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'SQLite'}")
        logger.info(f"📡 Redis: {settings.REDIS_URL}")
    except Exception as e:
        logger.error(f"❌ 订单服务启动失败: {str(e)}")
        raise
    
    yield
    
    try:
        # 关闭时清理资源
        await close_database()
        logger.info("👋 订单服务已关闭")
    except Exception as e:
        logger.error(f"❌ 订单服务关闭时发生错误: {str(e)}")


# 创建 FastAPI 应用实例
app = FastAPI(
    title="CashUp Order Service",
    description="CashUp量化交易系统 - 订单管理服务",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# 注册异常处理器
app.add_exception_handler(CashUpException, cashup_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# 添加中间件（注意顺序：后添加的先执行）
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(SecurityMiddleware)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """
    健康检查接口
    
    Returns:
        dict: 服务状态信息
    """
    return {
        "status": "healthy",
        "service": "order-service",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """
    根路径接口
    
    Returns:
        dict: 服务基本信息
    """
    return {
        "message": "CashUp Order Service",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=settings.DEBUG,
        log_level="info"
    )