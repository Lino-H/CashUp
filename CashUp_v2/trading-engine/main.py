#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp交易引擎主应用
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
    logger.info("🚀 启动CashUp交易引擎...")
    logger.info("✅ 交易引擎启动成功")
    yield
    logger.info("👋 交易引擎已关闭")

# 创建FastAPI应用实例
app = FastAPI(
    title="CashUp 交易引擎",
    description="CashUp量化交易系统 - 交易执行引擎",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径接口"""
    return {
        "service": "CashUp 交易引擎",
        "version": "2.0.0",
        "status": "running",
        "description": "交易执行引擎服务",
        "endpoints": {
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "trading-engine",
        "version": "2.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )