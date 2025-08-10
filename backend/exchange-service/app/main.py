from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import List, Optional, Dict, Any

from .api import exchanges, market, trading
from .core.config import settings
from .core.exchange_pool import exchange_pool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("Exchange Service 启动中...")
    
    # 这里可以添加启动时的初始化逻辑
    # 比如预加载一些交易所连接等
    
    yield
    
    # 关闭时清理
    logger.info("Exchange Service 关闭中...")
    await exchange_pool.close_all()


# 创建FastAPI应用
app = FastAPI(
    title="Exchange Service",
    description="统一的交易所服务API",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(exchanges.router, prefix="/api/v1/exchanges", tags=["exchanges"])
app.include_router(market.router, prefix="/api/v1/market", tags=["market"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["trading"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Exchange Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "exchange-service"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    )