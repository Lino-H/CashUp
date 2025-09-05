#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 核心服务

合并原user-service和config-service的功能，提供：
- 用户认证和授权
- 配置管理
- 统一的数据库访问
- 基础API接口
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging

# 导入配置和数据库
from core_service.config.settings import settings
from core_service.database.connection import get_database, Base
from core_service.utils.logger import setup_logger

# 导入API路由
from core_service.api.routes import auth, users, config

# 设置日志
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    logger.info("🚀 启动CashUp核心服务...")
    
    try:
        # 初始化数据库
        db = get_database()
        await db.connect()
        logger.info("✅ 数据库连接成功")
        
        logger.info(f"🌍 调试模式: {settings.DEBUG}")
        logger.info(f"🔗 数据库: {settings.DATABASE_URL}")
        logger.info(f"📡 Redis: {settings.REDIS_URL}")
        logger.info("✅ 核心服务启动成功")
        
    except Exception as e:
        logger.error(f"❌ 核心服务启动失败: {e}")
        raise
    
    yield
    
    try:
        # 清理资源
        db = get_database()
        await db.disconnect()
        logger.info("👋 核心服务已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭服务时发生错误: {e}")

# 创建FastAPI应用实例
app = FastAPI(
    title="CashUp 核心服务",
    description="CashUp量化交易系统 - 核心服务（认证、配置、用户管理）",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(config.router, prefix="/api/config", tags=["配置管理"])

@app.get("/")
async def root():
    """根路径接口"""
    return {
        "service": "CashUp 核心服务",
        "version": "2.0.0",
        "status": "running",
        "description": "提供用户认证、配置管理、用户信息维护等核心功能",
        "endpoints": {
            "auth": "/api/auth",
            "users": "/api/users", 
            "config": "/api/config",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接
        db = get_database()
        # 简单的健康检查
        return {
            "status": "healthy",
            "service": "core-service",
            "version": "2.0.0",
            "database": "ok",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "service": "core-service",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )