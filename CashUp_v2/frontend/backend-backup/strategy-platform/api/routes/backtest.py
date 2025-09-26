"""
回测API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

@router.get("/")
async def get_backtests():
    """获取回测列表"""
    try:
        backtests = [
            {
                "id": "1",
                "name": "BTC MA策略回测",
                "symbol": "BTCUSDT",
                "status": "completed",
                "startTime": "2024-01-01T00:00:00Z",
                "endTime": "2024-01-31T23:59:59Z",
                "totalReturn": 15.5,
                "sharpeRatio": 1.8,
                "maxDrawdown": -8.2
            },
            {
                "id": "2", 
                "name": "ETH RSI策略回测",
                "symbol": "ETHUSDT",
                "status": "running",
                "startTime": "2024-01-01T00:00:00Z",
                "endTime": None,
                "totalReturn": None,
                "sharpeRatio": None,
                "maxDrawdown": None
            }
        ]
        return {"data": backtests}
    except Exception as e:
        logger.error(f"获取回测列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取回测列表失败")

@router.get("/{backtest_id}")
async def get_backtest(backtest_id: str):
    """获取回测详情"""
    try:
        # 模拟回测详情
        backtest = {
            "id": backtest_id,
            "name": "BTC MA策略回测",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "startTime": "2024-01-01T00:00:00Z",
            "endTime": "2024-01-31T23:59:59Z",
            "status": "completed",
            "performance": {
                "totalReturn": 15.5,
                "annualReturn": 186.0,
                "sharpeRatio": 1.8,
                "maxDrawdown": -8.2,
                "winRate": 65.2,
                "totalTrades": 45,
                "profitFactor": 2.1
            },
            "config": {
                "strategy": "Moving Average",
                "parameters": {
                    "fastPeriod": 10,
                    "slowPeriod": 30,
                    "riskPerTrade": 2.0
                }
            }
        }
        return backtest
    except Exception as e:
        logger.error(f"获取回测详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取回测详情失败")

@router.post("/")
async def create_backtest(backtest_data: dict):
    """创建回测"""
    try:
        # 返回创建的回测信息
        backtest = {
            "id": "3",
            "name": backtest_data.get("name", "新回测"),
            "symbol": backtest_data.get("symbol", "BTCUSDT"),
            "status": "pending",
            "startTime": None,
            "endTime": None,
            "totalReturn": None,
            "sharpeRatio": None,
            "maxDrawdown": None
        }
        return backtest
    except Exception as e:
        logger.error(f"创建回测失败: {e}")
        raise HTTPException(status_code=500, detail="创建回测失败")