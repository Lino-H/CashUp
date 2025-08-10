#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知服务主应用

通知服务负责处理系统中的所有通知需求，包括：
- 多渠道消息推送（邮件、短信、WebSocket、系统通知）
- 通知模板管理
- 批量发送和定时发送
- 通知状态跟踪
- 实时推送功能
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
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middleware
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
    
    启动时初始化数据库连接和其他资源
    关闭时清理资源
    """
    try:
        # 启动时初始化
        logger.info("Starting CashUp Notification Service...")
        await init_database()
        logger.info("Database initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    finally:
        # 关闭时清理
        logger.info("Shutting down CashUp Notification Service...")
        await close_database()
        logger.info("Database connections closed")


# 创建FastAPI应用实例
app = FastAPI(
    title="CashUp Notification Service",
    description="CashUp量化交易系统 - 通知服务API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# 设置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置受信任主机中间件
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# 设置异常处理器
setup_exception_handlers(app)

# 设置自定义中间件
setup_middleware(app)

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
        "service": "CashUp Notification Service",
        "version": "1.0.0",
        "status": "running",
        "description": "多渠道通知服务，支持邮件、短信、WebSocket推送等"
    }


@app.get("/health")
async def health_check():
    """
    健康检查接口
    
    Returns:
        dict: 服务健康状态
    """
    try:
        # 这里可以添加数据库连接检查等
        return {
            "status": "healthy",
            "service": "notification-service",
            "timestamp": "2024-12-19T10:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "notification-service",
                "error": str(e)
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