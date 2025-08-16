#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知服务主应用程序

通知服务的FastAPI应用程序入口点
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .core.config import settings
from .core.database import init_database
# from .core.logging import setup_logging
from .api.v1 import api_router
from .services import (
    notification_service,
    template_service,
    channel_service,
    sender_service,
    websocket_service,
    scheduler_service
)

import time
import uuid

# 设置日志
# setup_logging()
logger = logging.getLogger(__name__)

# 获取配置
config = settings


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 记录请求开始
        start_time = time.time()
        logger.info(
            f"Request started - ID: {request_id}, Method: {request.method}, "
            f"URL: {request.url}, Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 记录请求完成
            process_time = time.time() - start_time
            logger.info(
                f"Request completed - ID: {request_id}, Status: {response.status_code}, "
                f"Time: {process_time:.3f}s"
            )
            
            # 添加请求ID到响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录请求错误
            process_time = time.time() - start_time
            logger.error(
                f"Request failed - ID: {request_id}, Error: {str(e)}, "
                f"Time: {process_time:.3f}s"
            )
            raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用程序生命周期管理
    
    Args:
        app: FastAPI应用实例
    """
    logger.info("Starting notification service...")
    
    try:
        # 初始化数据库
        logger.info("Initializing database...")
        await init_database()
        
        # 初始化服务
        logger.info("Initializing services...")
        await _initialize_services()
        
        logger.info("Notification service started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start notification service: {str(e)}")
        raise
    finally:
        # 清理资源
        logger.info("Shutting down notification service...")
        await _cleanup_services()
        logger.info("Notification service stopped")


async def _initialize_services():
    """
    初始化所有服务
    """
    try:
        # 初始化WebSocket服务
        logger.info("Initializing WebSocket service...")
        # WebSocket服务通常不需要特殊初始化
        
        # 初始化调度服务
        logger.info("Initializing scheduler service...")
        await scheduler_service.start()
        
        # 初始化发送服务
        logger.info("Initializing sender service...")
        # 发送服务通常不需要特殊初始化
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise


async def _cleanup_services():
    """
    清理所有服务
    """
    try:
        # 停止调度服务
        logger.info("Stopping scheduler service...")
        await scheduler_service.stop()
        
        # 清理WebSocket连接
        logger.info("Cleaning up WebSocket connections...")
        await websocket_service.cleanup_expired_connections()
        
        # 关闭发送服务的HTTP会话
        logger.info("Closing sender service sessions...")
        await sender_service.close()
        
        logger.info("All services cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Error during service cleanup: {str(e)}")


# 创建FastAPI应用
app = FastAPI(
    title="CashUp通知服务",
    description="CashUp量化交易系统的通知服务API",
    version="1.0.0",
    docs_url="/docs" if config.DEBUG else None,
    redoc_url="/redoc" if config.DEBUG else None,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加可信主机中间件
if config.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=config.ALLOWED_HOSTS
    )

# 添加请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 注册API路由
app.include_router(
    api_router,
    prefix="/api/v1"
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
    logger.warning(
        f"HTTP exception - Status: {exc.status_code}, Detail: {exc.detail}, "
        f"URL: {request.url}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_exception"
            },
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    请求验证异常处理器
    
    Args:
        request: 请求对象
        exc: 验证异常
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.warning(
        f"Validation error - URL: {request.url}, Errors: {exc.errors()}"
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Validation error",
                "type": "validation_error",
                "details": exc.errors()
            },
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Starlette HTTP异常处理器
    
    Args:
        request: 请求对象
        exc: Starlette HTTP异常
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.error(
        f"Starlette HTTP exception - Status: {exc.status_code}, Detail: {exc.detail}, "
        f"URL: {request.url}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "starlette_exception"
            },
            "timestamp": time.time(),
            "path": str(request.url.path)
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
    logger.error(
        f"Unhandled exception - Type: {type(exc).__name__}, Message: {str(exc)}, "
        f"URL: {request.url}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error" if not config.DEBUG else str(exc),
                "type": "internal_error"
            },
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )


# 根路径
@app.get("/")
async def root():
    """
    根路径处理器
    
    Returns:
        dict: 服务信息
    """
    return {
        "service": "CashUp通知服务",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if config.DEBUG else "disabled",
        "api": "/api/v1"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """
    简单健康检查
    
    Returns:
        dict: 健康状态
    """
    return {
        "status": "healthy",
        "service": "notification-service",
        "version": "1.0.0",
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    
    # 开发环境运行
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
        log_level="info" if not config.DEBUG else "debug"
    )