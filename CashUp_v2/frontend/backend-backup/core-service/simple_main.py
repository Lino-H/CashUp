#!/usr/bin/env python3
"""
简化版核心服务 - 绕过数据库依赖，用于前端测试
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime, timezone
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="CashUp 核心服务 (简化版)",
    description="用于前端测试的简化版本",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/")
async def root():
    return {"message": "CashUp 核心服务 (简化版)", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "core-service", "timestamp": datetime.now().isoformat()}

@app.get("/api/core/health")
async def api_health():
    return {"status": "ok", "message": "核心服务运行正常", "timestamp": datetime.now().isoformat()}

# 简化的认证端点
@app.post("/api/auth/login")
async def login():
    return {
        "access_token": "mock_token_for_testing",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": "mock_user_id",
            "username": "admin",
            "email": "admin@cashup.com",
            "role": "admin"
        }
    }

@app.post("/api/auth/register")
async def register():
    return {"message": "注册功能暂未开放"}

# 简化的配置端点
@app.get("/api/config/settings")
async def get_settings():
    return {
        "app_name": "CashUp 量化交易平台",
        "version": "2.0.0",
        "theme": "light",
        "language": "zh-CN",
        "timezone": "Asia/Shanghai",
        "currency": "USDT"
    }

@app.get("/api/config/exchanges")
async def get_exchanges():
    return {
        "exchanges": [
            {
                "id": "gateio",
                "name": "Gate.io",
                "enabled": True,
                "sandbox": True,
                "symbols": ["BTC/USDT", "ETH/USDT"]
            },
            {
                "id": "binance",
                "name": "Binance",
                "enabled": True,
                "sandbox": True,
                "symbols": ["BTCUSDT", "ETHUSDT"]
            }
        ]
    }

# 用户端点
@app.get("/api/users/me")
async def get_current_user():
    return {
        "id": "mock_user_id",
        "username": "admin",
        "email": "admin@cashup.com",
        "role": "admin",
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }

# 异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"error": exc.detail, "status_code": exc.status_code}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return {"error": "请求验证失败", "details": exc.errors}

@app.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(request, exc):
    return {"error": "HTTP错误", "status_code": exc.status_code}

if __name__ == "__main__":
    logger.info("🚀 启动CashUp核心服务 (简化版)...")
    logger.info("📍 服务地址: http://0.0.0.0:8001")
    logger.info("📖 API文档: http://0.0.0.0:8001/docs")
    logger.info("🏥 健康检查: http://0.0.0.0:8001/health")

    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )