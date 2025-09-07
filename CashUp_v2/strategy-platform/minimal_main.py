#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp策略平台最小版本
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title="CashUp 策略平台",
    description="CashUp量化交易系统 - 策略开发和回测平台（最小版）",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径接口
@app.get("/")
async def root():
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

# 健康检查接口
@app.get("/health")
async def health_check():
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
        "message": "策略平台API正常工作（最小版）"
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
            "message": "市场概览API正常工作（最小版）"
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
        "message": f"实时数据API正常工作（最小版）- {symbol}"
    }

if __name__ == "__main__":
    uvicorn.run(
        "minimal_main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )