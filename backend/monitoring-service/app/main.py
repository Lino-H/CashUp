#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 监控服务主应用

监控服务的FastAPI应用入口点
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn

from app.core.config import get_settings, validate_config, print_config
from app.core.database import init_database, close_database, create_tables
from app.core.cache import init_cache, close_cache
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import (
    monitoring_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.api import api_router
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityMiddleware
from app.middleware.monitoring import MonitoringMiddleware
from app.services.health_service import HealthService
from app.services.metrics_service import MetricsService
from app.core.exceptions import MonitoringException

# 获取配置
config = get_settings()

# 设置日志
setup_logging()
logger = get_logger(__name__)


class LifespanManager:
    """应用生命周期管理器"""
    
    def __init__(self):
        self.health_service = None
        self.metrics_service = None
        self.background_tasks = []
        self.shutdown_event = asyncio.Event()
    
    async def startup(self):
        """应用启动时的初始化"""
        try:
            logger.info("Starting CashUp Monitoring Service...")
            
            # 初始化数据库
            logger.info("Initializing database...")
            init_database()
            create_tables()
            
            # 初始化缓存
            logger.info("Initializing cache...")
            await init_cache()
            
            # 初始化服务
            logger.info("Initializing services...")
            from app.core.cache import get_cache_manager
            cache_manager = get_cache_manager()
            
            self.health_service = HealthService(cache_manager)
            self.metrics_service = MetricsService(cache_manager)
            
            # 启动后台任务
            logger.info("Starting background tasks...")
            await self._start_background_tasks()
            
            # 设置信号处理
            self._setup_signal_handlers()
            
            logger.info("CashUp Monitoring Service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start application: {e}", exc_info=True)
            raise
    
    async def shutdown(self):
        """应用关闭时的清理"""
        try:
            logger.info("Shutting down CashUp Monitoring Service...")
            
            # 设置关闭事件
            self.shutdown_event.set()
            
            # 停止后台任务
            logger.info("Stopping background tasks...")
            await self._stop_background_tasks()
            
            # 关闭服务
            if self.health_service:
                await self.health_service.stop_periodic_checks()
            
            # 关闭缓存
            logger.info("Closing cache...")
            await close_cache()
            
            # 关闭数据库
            logger.info("Closing database...")
            close_database()
            
            logger.info("CashUp Monitoring Service shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    async def _start_background_tasks(self):
        """启动后台任务"""
        try:
            # 启动健康检查任务
            if self.health_service:
                # 获取数据库会话
                from app.core.database import get_db
                db = next(get_db())
                try:
                    task = asyncio.create_task(
                        self.health_service.start_periodic_checks(db)
                    )
                    self.background_tasks.append(task)
                    logger.info("Health check task started")
                finally:
                    db.close()
            
            # 启动指标收集任务
            if self.metrics_service:
                task = asyncio.create_task(
                    self._periodic_metrics_collection()
                )
                self.background_tasks.append(task)
                logger.info("Metrics collection task started")
            
            # 启动数据清理任务
            task = asyncio.create_task(
                self._periodic_cleanup()
            )
            self.background_tasks.append(task)
            logger.info("Data cleanup task started")
            
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}", exc_info=True)
            raise
    
    async def _stop_background_tasks(self):
        """停止后台任务"""
        try:
            # 取消所有后台任务
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
            
            # 等待任务完成
            if self.background_tasks:
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
            self.background_tasks.clear()
            logger.info("All background tasks stopped")
            
        except Exception as e:
            logger.error(f"Error stopping background tasks: {e}", exc_info=True)
    
    async def _periodic_metrics_collection(self):
        """定期指标收集任务"""
        while not self.shutdown_event.is_set():
            try:
                # 触发指标收集
                if self.metrics_service:
                    from app.core.database import get_db
                    db = next(get_db())
                    try:
                        await self.metrics_service.trigger_collection(db)
                        logger.debug("Metrics collection completed")
                    finally:
                        db.close()
                
                # 等待下次收集（每5分钟一次）
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                logger.info("Metrics collection task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}", exc_info=True)
                await asyncio.sleep(60)  # 出错时等待1分钟再重试
    
    async def _periodic_cleanup(self):
        """定期数据清理任务"""
        while not self.shutdown_event.is_set():
            try:
                # 清理过期数据
                if self.metrics_service:
                    from app.core.database import get_db
                    db = next(get_db())
                    try:
                        await self.metrics_service.cleanup_expired_data(db)
                        logger.debug("Periodic cleanup completed")
                    finally:
                        db.close()
                
                # 等待下次清理（每小时一次）
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}", exc_info=True)
                await asyncio.sleep(300)  # 出错时等待5分钟再重试
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


# 创建生命周期管理器
lifespan_manager = LifespanManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    await lifespan_manager.startup()
    yield
    # 关闭
    await lifespan_manager.shutdown()


# 创建FastAPI应用
app = FastAPI(
    title="CashUp Monitoring Service",
    description="CashUp量化交易系统监控服务API",
    version="1.0.0",
    docs_url="/docs" if config.DEBUG else None,
    redoc_url="/redoc" if config.DEBUG else None,
    openapi_url="/openapi.json" if config.DEBUG else None,
    lifespan=lifespan
)


# ==================== 中间件配置 ====================

# 请求ID中间件
app.add_middleware(RequestIDMiddleware)

# 安全中间件
app.add_middleware(SecurityMiddleware)

# 监控中间件
app.add_middleware(MonitoringMiddleware)

# 限流中间件
if config.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        calls=config.RATE_LIMIT_REQUESTS,
        period=config.RATE_LIMIT_WINDOW
    )

# GZIP压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 信任主机中间件
if config.ALLOWED_HOSTS and config.ALLOWED_HOSTS != ["*"]:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=config.ALLOWED_HOSTS
    )

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ==================== 异常处理器 ====================

# 自定义异常处理器
app.add_exception_handler(MonitoringException, monitoring_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# ==================== 路由配置 ====================

# 注册API路由
app.include_router(
    api_router,
    prefix=config.API_V1_STR
)


# ==================== 健康检查端点 ====================

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "monitoring-service",
        "version": "1.0.0",
        "timestamp": asyncio.get_event_loop().time()
    }


@app.get("/ready")
async def readiness_check():
    """就绪检查端点"""
    try:
        # 检查数据库连接
        from app.core.database import test_connection
        db_healthy = await test_connection()
        
        # 检查缓存连接
        from app.core.cache import get_cache_manager
        cache_manager = get_cache_manager()
        cache_healthy = await cache_manager.health_check()
        
        if db_healthy and cache_healthy:
            return {
                "status": "ready",
                "database": "healthy",
                "cache": "healthy"
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not ready",
                    "database": "healthy" if db_healthy else "unhealthy",
                    "cache": "healthy" if cache_healthy else "unhealthy"
                }
            )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "error": str(e)
            }
        )


@app.get("/live")
async def liveness_check():
    """存活检查端点"""
    return {
        "status": "alive",
        "timestamp": asyncio.get_event_loop().time()
    }


# ==================== Prometheus指标 ====================

if config.PROMETHEUS_ENABLED:
    # 初始化Prometheus指标收集器
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/ready", "/live", "/metrics"]
    )
    
    # 添加自定义指标
    instrumentator.add(
        lambda info: info.modified_duration < 0.1,
        "fast_requests_total",
        "Total number of fast requests (< 100ms)"
    )
    
    # 启用指标收集
    instrumentator.instrument(app)
    
    # 暴露指标端点
    instrumentator.expose(app, endpoint="/metrics")


# ==================== 启动函数 ====================

def create_app() -> FastAPI:
    """创建应用实例"""
    return app


def main():
    """主函数"""
    try:
        # 验证配置
        errors = validate_config()
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            sys.exit(1)
        
        # 打印配置信息
        if config.DEBUG:
            print_config()
        
        # 启动服务器
        uvicorn.run(
            "app.main:app",
            host=config.HOST,
            port=config.PORT,
            reload=config.DEBUG,
            workers=1 if config.DEBUG else config.WORKER_PROCESSES,
            log_level=config.LOG_LEVEL.lower(),
            access_log=True,
            use_colors=True,
            server_header=False,
            date_header=False
        )
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()