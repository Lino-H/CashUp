import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
import asyncio
from api import router as notify_router

"""
通知服务入口
函数集注释：
- lifespan: 可选启动 RabbitMQ 消费任务，默认禁用以适配 Redis-only
"""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    enable_consumer = os.getenv("ENABLE_RABBITMQ_CONSUMER", "false").lower() == "true"
    task = None
    if enable_consumer:
        from consumer import consume
        task = asyncio.create_task(consume())
    yield
    if task:
        task.cancel()

app = FastAPI(
    title="CashUp 通知服务",
    description="CashUp量化交易系统 - 消息通知服务",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

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
    return {
        "status": "healthy",
        "service": "notification-service",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

app.include_router(notify_router, tags=["通知"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )