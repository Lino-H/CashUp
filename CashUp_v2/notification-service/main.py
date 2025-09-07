#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp通知服务主应用
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
    logger.info("🚀 启动CashUp通知服务...")
    logger.info("✅ 通知服务启动成功")
    yield
    logger.info("👋 通知服务已关闭")

# 创建FastAPI应用实例
app = FastAPI(
    title="CashUp 通知服务",
    description="CashUp量化交易系统 - 消息通知服务",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS - 生产环境只允许特定域名
import os
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost,http://localhost:3000,http://localhost:80,https://cashup.com,https://www.cashup.com").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径接口"""
    return {
        "service": "CashUp 通知服务",
        "version": "2.0.0",
        "status": "running",
        "description": "消息通知服务",
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
        "service": "notification-service",
        "version": "2.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )