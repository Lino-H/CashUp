#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp策略平台主应用

提供策略开发、回测、管理等功能
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入配置和数据库
from config.settings import settings
from utils.logger import setup_logger

# 导入API路由
from api.routes import strategies, backtest, data

# 设置日志
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    logger.info("🚀 启动CashUp策略平台...")
    
    try:
        # 初始化数据管理器
        from data.manager import DataManager
        data_manager = DataManager()
        
        # 初始化策略管理器
        from strategies.manager import StrategyManager
        strategy_manager = StrategyManager()
        
        # 发现可用策略
        available_strategies = strategy_manager.discover_strategies()
        logger.info(f"✅ 发现 {len(available_strategies)} 个策略")
        
        # 初始化回测引擎
        from backtest.engine import BacktestEngine
        backtest_engine = BacktestEngine(data_manager)
        
        logger.info(f"🌍 调试模式: {settings.DEBUG}")
        logger.info(f"📊 数据目录: {settings.DATA_DIR}")
        logger.info(f"📁 策略目录: {settings.STRATEGIES_DIR}")
        logger.info("✅ 策略平台启动成功")
        
    except Exception as e:
        logger.error(f"❌ 策略平台启动失败: {e}")
        raise
    
    yield
    
    try:
        # 清理资源
        logger.info("👋 策略平台已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭服务时发生错误: {e}")

# 创建FastAPI应用实例
app = FastAPI(
    title="CashUp 策略平台",
    description="CashUp量化交易系统 - 策略开发和回测平台",
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
app.include_router(strategies.router, prefix="/api/strategies", tags=["策略管理"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["回测引擎"])
app.include_router(data.router, prefix="/api/data", tags=["数据管理"])

@app.get("/")
async def root():
    """根路径接口"""
    return {
        "service": "CashUp 策略平台",
        "version": "2.0.0",
        "status": "running",
        "description": "提供策略开发、回测、管理等功能",
        "endpoints": {
            "strategies": "/api/strategies",
            "backtest": "/api/backtest",
            "data": "/api/data",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查数据管理器
        from data.manager import DataManager
        data_manager = DataManager()
        
        # 检查策略管理器
        from strategies.manager import StrategyManager
        strategy_manager = StrategyManager()
        
        return {
            "status": "healthy",
            "service": "strategy-platform",
            "version": "2.0.0",
            "data_manager": "ok",
            "strategy_manager": "ok",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "service": "strategy-platform",
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