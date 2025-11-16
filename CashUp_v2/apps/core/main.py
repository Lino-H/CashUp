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
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone

# 导入配置和数据库
from config.settings import settings
from fastapi import Request
from database.connection import get_database, Base
from utils.logger import setup_logger

# 导入API路由
from api.routes import config, news, market, trading, strategies, reporting
from api.routes import keys as keys_routes
from api.routes import admin_configs
from api.routes import seed as seed_routes
from api.routes import exchanges as exchanges_routes
from api.routes import scheduler as scheduler_routes
from api.routes import rss as rss_routes
from database.redis import get_redis

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

# 禁用认证时提供默认用户上下文
@app.middleware("http")
async def default_user_middleware(request: Request, call_next):
    if not settings.ENABLE_AUTH:
        try:
            request.state.user = {"id": "dev", "username": "developer", "role": "admin"}
        except Exception:
            request.state.user = None
    response = await call_next(request)
    return response

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(config.router, prefix="/api/config", tags=["配置管理"])
app.include_router(news.router, prefix="/api", tags=["新闻"])
app.include_router(market.router, tags=["行情"])
app.include_router(trading.router, tags=["交易"])
app.include_router(strategies.router, tags=["策略"])
app.include_router(keys_routes.router, tags=["密钥管理"])
app.include_router(admin_configs.router, tags=["系统配置"])
app.include_router(seed_routes.router, tags=["初始化"])
app.include_router(exchanges_routes.router, tags=["交易所"])
app.include_router(scheduler_routes.router, tags=["调度"])
app.include_router(rss_routes.router, tags=["RSS"])
app.include_router(reporting.router, tags=["报表"])

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
        db = get_database()
        return {
            "status": "healthy",
            "service": "core-service",
            "version": "2.0.0",
            "database": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "service": "core-service",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/metrics")
async def metrics():
    """Prometheus 指标导出端点"""
    try:
        r = await get_redis()
        import time
        def _int(v):
            try:
                if v is None:
                    return 0
                s = v.decode() if isinstance(v, (bytes, bytearray)) else str(v)
                return int(s)
            except Exception:
                return 0
        last_rss_fetch = _int(await r.get("sched:last:rss.fetch"))
        last_rss_analyze = _int(await r.get("sched:last:rss.analyze"))
        last_rss_corr = _int(await r.get("sched:last:rss.correlation"))
        last_trading_sync = _int(await r.get("sched:last:trading.sync"))
        last_market_collect = _int(await r.get("sched:last:market.collect"))
        rss_error_total = _int(await r.get("rss:error_total"))
        market_error_last = _int(await r.get("market:error:last"))
        sched_hist_len = await r.llen("sched:history") if hasattr(r, "llen") else 0
        feed_err = {}
        try:
            feed_err_raw = await r.hgetall("rss:error:feed")
            if isinstance(feed_err_raw, dict):
                for k, v in feed_err_raw.items():
                    kk = k.decode() if isinstance(k, (bytes, bytearray)) else str(k)
                    vv = _int(v)
                    feed_err[kk] = vv
        except Exception:
            feed_err = {}
        lines = []
        lines.append("# HELP cashup_sched_last_timestamp Last run timestamp for scheduled tasks")
        lines.append("# TYPE cashup_sched_last_timestamp gauge")
        lines.append(f"cashup_sched_last_timestamp{{task=\"rss.fetch\"}} {last_rss_fetch}")
        lines.append(f"cashup_sched_last_timestamp{{task=\"rss.analyze\"}} {last_rss_analyze}")
        lines.append(f"cashup_sched_last_timestamp{{task=\"rss.correlation\"}} {last_rss_corr}")
        lines.append(f"cashup_sched_last_timestamp{{task=\"trading.sync\"}} {last_trading_sync}")
        lines.append(f"cashup_sched_last_timestamp{{task=\"market.collect\"}} {last_market_collect}")
        lines.append("# HELP cashup_rss_error_total Total RSS errors")
        lines.append("# TYPE cashup_rss_error_total counter")
        lines.append(f"cashup_rss_error_total {rss_error_total}")
        lines.append("# HELP cashup_rss_error_feed_total RSS errors by feed id")
        lines.append("# TYPE cashup_rss_error_feed_total counter")
        for fid, cnt in (feed_err or {}).items():
            lines.append(f"cashup_rss_error_feed_total{{feed=\"{fid}\"}} {cnt}")
        lines.append("# HELP cashup_market_error_last Last market error timestamp")
        lines.append("# TYPE cashup_market_error_last gauge")
        lines.append(f"cashup_market_error_last {market_error_last}")
        lines.append("# HELP cashup_sched_history_len Scheduler history list length")
        lines.append("# TYPE cashup_sched_history_len gauge")
        lines.append(f"cashup_sched_history_len {int(sched_hist_len or 0)}")
        from fastapi import Response
        return Response("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4; charset=utf-8")
    except Exception:
        from fastapi import Response
        return Response("", media_type="text/plain")
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "service": "core-service",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

class NewsWSManager:
    """新闻WebSocket连接管理器"""
    def __init__(self):
        self.active = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.add(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict):
        for ws in list(self.active):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)


news_ws_manager = NewsWSManager()


@app.websocket("/ws/news")
async def news_ws(websocket: WebSocket):
    await news_ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        news_ws_manager.disconnect(websocket)