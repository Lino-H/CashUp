#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp交易引擎主应用
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from typing import List, Dict, Any
from dataclasses import asdict

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入路由
from api.routes.strategies import router as strategies_router
from api.routes.trading import router as trading_router

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

# 包含API路由
app.include_router(strategies_router)
app.include_router(trading_router)

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
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# 策略管理API
@app.get("/api/v1/strategies/status")
async def get_strategies_status():
    """获取所有策略状态"""
    try:
        from strategies.strategy_manager import get_strategy_manager
        strategy_manager = await get_strategy_manager()
        status = await strategy_manager.get_strategy_status()
        return {
            "status": "success",
            "strategies": status,
            "total_strategies": len(status)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略状态失败: {str(e)}")

@app.post("/api/v1/strategies/{strategy_name}/start")
async def start_strategy(strategy_name: str):
    """启动指定策略"""
    try:
        from strategies.strategy_manager import get_strategy_manager
        strategy_manager = await get_strategy_manager()

        success = await strategy_manager.start_strategy(strategy_name)

        if success:
            return {
                "status": "success",
                "message": f"策略 {strategy_name} 启动成功"
            }
        else:
            raise HTTPException(status_code=400, detail=f"策略 {strategy_name} 启动失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动策略失败: {str(e)}")

@app.post("/api/v1/strategies/{strategy_name}/stop")
async def stop_strategy(strategy_name: str):
    """停止单个策略"""
    try:
        from strategies.strategy_manager import get_strategy_manager
        strategy_manager = await get_strategy_manager()

        success = await strategy_manager.stop_strategy(strategy_name)

        if success:
            return {
                "status": "success",
                "message": f"策略 {strategy_name} 停止成功"
            }
        else:
            raise HTTPException(status_code=400, detail=f"策略 {strategy_name} 停止失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止策略失败: {str(e)}")

@app.post("/api/v1/strategies/start-all")
async def start_all_strategies():
    """启动所有策略"""
    try:
        from strategies.strategy_manager import get_strategy_manager
        strategy_manager = await get_strategy_manager()

        await strategy_manager.start_all_strategies()

        return {
            "status": "success",
            "message": "所有策略启动成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动所有策略失败: {str(e)}")

@app.post("/api/v1/strategies/stop-all")
async def stop_all_strategies():
    """停止所有策略"""
    try:
        from strategies.strategy_manager import get_strategy_manager
        strategy_manager = await get_strategy_manager()

        await strategy_manager.stop_all_strategies()

        return {
            "status": "success",
            "message": "所有策略停止成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止所有策略失败: {str(e)}")

@app.get("/api/v1/strategies/{strategy_name}/signals")
async def get_strategy_signals(strategy_name: str, limit: int = 10):
    """获取策略交易信号"""
    try:
        from strategies.strategy_manager import get_strategy_manager
        strategy_manager = await get_strategy_manager()

        signals = await strategy_manager.get_strategy_signals(strategy_name, limit)

        return {
            "status": "success",
            "strategy_name": strategy_name,
            "signals": [asdict(signal) for signal in signals],
            "count": len(signals)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略信号失败: {str(e)}")

@app.get("/api/v1/strategies/{strategy_name}/positions")
async def get_strategy_positions(strategy_name: str):
    """获取策略持仓"""
    try:
        from strategies.strategy_manager import get_strategy_manager
        strategy_manager = await get_strategy_manager()

        positions = await strategy_manager.get_strategy_positions(strategy_name)

        return {
            "status": "success",
            "strategy_name": strategy_name,
            "positions": [asdict(position) for position in positions],
            "count": len(positions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略持仓失败: {str(e)}")

@app.put("/api/v1/strategies/{strategy_name}/config")
async def update_strategy_config(strategy_name: str, config: Dict[str, Any]):
    """更新策略配置"""
    try:
        from strategies.strategy_manager import get_strategy_manager
        strategy_manager = await get_strategy_manager()

        success = await strategy_manager.update_strategy_config(strategy_name, config)

        if success:
            return {
                "status": "success",
                "message": f"策略 {strategy_name} 配置更新成功"
            }
        else:
            raise HTTPException(status_code=400, detail=f"策略 {strategy_name} 不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新策略配置失败: {str(e)}")

# 交易管理API
# 交易管理API (保持向后兼容)
@app.get("/api/v1/orders")
async def get_orders():
    """获取订单列表"""
    try:
        from api.routes.trading import get_order_history
        result = await get_order_history()
        return result["data"]
    except Exception as e:
        return {"orders": [], "error": f"获取订单失败: {str(e)}"}

@app.post("/api/v1/orders")
async def create_order(order_data: dict):
    """创建订单"""
    try:
        from api.routes.trading import router as trading_router
        # 这里应该调用trading路由的创建订单功能
        order_id = f"order_{int(datetime.now().timestamp())}"
        return {
            "order_id": order_id,
            "status": "success",
            "message": "订单创建成功",
            "order": {
                **order_data,
                "id": order_id,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建订单失败: {str(e)}")

@app.get("/api/v1/positions")
async def get_positions():
    """获取持仓列表"""
    try:
        from api.routes.trading import get_all_positions
        result = await get_all_positions()
        return result["data"]
    except Exception as e:
        return {"positions": [], "error": f"获取持仓失败: {str(e)}"}

@app.get("/api/v1/balances")
async def get_balances():
    """获取账户余额"""
    from api.routes.trading import get_account_summary
    result = await get_account_summary()
    summary = result["data"]
    return {
        "balances": [
            {
                "asset": "USDT",
                "free": summary["available_balance"],
                "used": summary["total_margin_used"],
                "total": summary["total_balance"]
            }
        ],
        "total_value_usd": summary["total_balance"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/account/info")
async def get_account_info():
    """获取账户信息"""
    from api.routes.trading import get_account_summary
    result = await get_account_summary()
    return result["data"]

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )