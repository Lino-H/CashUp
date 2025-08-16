#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 市场数据服务主应用

提供实时市场数据、历史数据和技术指标计算的FastAPI应用
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db
from app.core.redis import RedisManager
from app.services.market_service import get_market_service
from app.api.market_data import router as market_router
from app.api.indicators import router as indicators_router

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理
    
    在应用启动时初始化数据库和Redis连接
    在应用关闭时清理资源
    """
    # 启动时执行
    logger.info("启动市场数据服务...")
    
    try:
        # 初始化数据库
        await init_db()
        logger.info("数据库初始化完成")
        
        # 初始化Redis连接
        redis_manager = RedisManager()
        await redis_manager.init_redis()
        logger.info("Redis连接初始化完成")
        
        # 存储Redis管理器到应用状态
        app.state.redis_manager = redis_manager
        
        # 初始化数据库
        await init_db()
        
        # 初始化市场数据服务
        market_service = await get_market_service()
        
        logger.info("市场数据服务启动完成")
        
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise
    
    yield
    
    # 关闭时执行
    logger.info("关闭市场数据服务...")
    
    try:
        # 关闭市场数据服务
        market_service = get_market_service()
        await market_service.stop_websocket_streams()
        logger.info("市场数据服务已关闭")
        
        # 关闭Redis连接
        if hasattr(app.state, 'redis_manager'):
            await app.state.redis_manager.close()
            logger.info("Redis连接已关闭")
        
        logger.info("市场数据服务已关闭")
        
    except Exception as e:
        logger.error(f"服务关闭异常: {e}")





# 创建FastAPI应用
app = FastAPI(
    title="CashUp Market Service",
    description="CashUp量化交易系统 - 市场数据服务API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)


# 中间件配置

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 可信主机中间件
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    # 生成请求ID
    request_id = str(uuid.uuid4())
    
    # 记录请求开始
    start_time = time.time()
    logger.info(
        f"请求开始: {request_id} {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    # 处理请求
    response = await call_next(request)
    
    # 记录请求结束
    process_time = time.time() - start_time
    logger.info(
        f"请求完成: {request_id} {response.status_code} {process_time:.3f}s",
        extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time": process_time
        }
    )
    
    # 添加响应头
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# 异常处理器

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理"""
    logger.warning(
        f"HTTP异常: {exc.status_code} {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理"""
    logger.warning(
        f"请求验证失败: {exc.errors()}",
        extra={
            "errors": exc.errors(),
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "请求参数验证失败",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(
        f"未处理异常: {type(exc).__name__}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": request.url.path
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            "message": "服务器内部错误" if not settings.DEBUG else str(exc)
        }
    )


# 健康检查
@app.get("/health", tags=["health"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "market-service",
        "version": "1.0.0",
        "timestamp": time.time()
    }


@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """就绪检查接口"""
    try:
        # 检查数据库连接
        from app.core.database import get_db
        async for db in get_db():
            await db.execute("SELECT 1")
            break
        
        # 检查Redis连接
        if hasattr(app.state, 'redis_manager'):
            await app.state.redis_manager.ping()
        
        # 检查市场数据服务
        market_service = get_market_service()
        exchange_info = await market_service.get_exchange_info()
        
        return {
            "status": "ready",
            "service": "market-service",
            "checks": {
                "database": "ok",
                "redis": "ok",
                "gateio": "ok",
                "exchange_pairs": exchange_info.get("spot_pairs", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"就绪检查失败: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "error": str(e)
            }
        )


# 注册路由
app.include_router(market_router, prefix="/api/v1")
app.include_router(indicators_router, prefix="/api/v1")


# 根路径
@app.get("/", tags=["root"])
async def root():
    """根路径"""
    return {
        "service": "CashUp Market Service",
        "version": "1.0.0",
        "description": "CashUp量化交易系统 - 市场数据服务API",
        "docs_url": "/docs" if settings.DEBUG else None
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8004,
        reload=settings.DEBUG,
        log_config=None  # 使用我们自己的日志配置
    )