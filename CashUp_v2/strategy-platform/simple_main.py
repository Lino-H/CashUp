#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp策略平台简化版本
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 启动CashUp策略平台（简化版）...")
    logger.info("✅ 策略平台启动成功")
    yield
    logger.info("👋 策略平台已关闭")

# 创建FastAPI应用实例
app = FastAPI(
    title="CashUp 策略平台",
    description="CashUp量化交易系统 - 策略开发和回测平台（简化版）",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
import os
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost,http://localhost:3000,http://localhost:80")
if isinstance(allowed_origins, str):
    allowed_origins = allowed_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 简化的API路由
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
            "data": "/api/data",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "strategy-platform",
        "version": "2.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# 策略管理API
@app.get("/api/strategies")
async def get_strategies():
    """获取策略列表"""
    return {
        "strategies": [],
        "total": 0,
        "message": "策略平台API正常工作（简化版）"
    }

# 数据管理API
@app.get("/api/data/market/overview")
async def get_market_overview():
    """获取市场概览"""
    return {
        "market_overview": {
            "total_markets": 10,
            "active_markets": 8,
            "total_volume": "1000000",
            "message": "市场概览API正常工作（简化版）"
        }
    }

@app.get("/api/data/realtime/{symbol}")
async def get_realtime_data(symbol: str):
    """获取实时数据"""
    return {
        "symbol": symbol,
        "price": "50000.00",
        "volume": "1000",
        "timestamp": "2024-01-01T00:00:00Z",
        "message": f"实时数据API正常工作（简化版）- {symbol}"
    }

if __name__ == "__main__":
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )