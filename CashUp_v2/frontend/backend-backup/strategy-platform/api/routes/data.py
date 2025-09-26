"""
数据API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["data"])

@router.get("/symbols")
async def get_symbols():
    """获取支持的交易对列表"""
    try:
        symbols = [
            {"symbol": "BTCUSDT", "name": "Bitcoin/USDT", "type": "spot"},
            {"symbol": "ETHUSDT", "name": "Ethereum/USDT", "type": "spot"},
            {"symbol": "BNBUSDT", "name": "Binance Coin/USDT", "type": "spot"},
            {"symbol": "ADAUSDT", "name": "Cardano/USDT", "type": "spot"},
            {"symbol": "DOTUSDT", "name": "Polkadot/USDT", "type": "spot"},
        ]
        return {"data": symbols}
    except Exception as e:
        logger.error(f"获取交易对失败: {e}")
        raise HTTPException(status_code=500, detail="获取交易对失败")

@router.get("/timeframes")
async def get_timeframes():
    """获取支持的时间周期"""
    try:
        timeframes = [
            {"value": "1m", "label": "1分钟"},
            {"value": "5m", "label": "5分钟"},
            {"value": "15m", "label": "15分钟"},
            {"value": "1h", "label": "1小时"},
            {"value": "4h", "label": "4小时"},
            {"value": "1d", "label": "1天"},
        ]
        return {"data": timeframes}
    except Exception as e:
        logger.error(f"获取时间周期失败: {e}")
        raise HTTPException(status_code=500, detail="获取时间周期失败")

@router.get("/realtime/{symbol}")
async def get_realtime_data(symbol: str):
    """获取实时数据"""
    try:
        # 模拟实时数据
        import random
        price = random.uniform(40000, 45000)
        change_24h = random.uniform(-5, 5)
        
        data = {
            "symbol": symbol,
            "price": price,
            "change24h": change_24h,
            "changePercent24h": change_24h,
            "volume24h": random.uniform(1000000, 5000000),
            "high24h": price * (1 + abs(change_24h) / 100),
            "low24h": price * (1 - abs(change_24h) / 100),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return data
    except Exception as e:
        logger.error(f"获取实时数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取实时数据失败")

@router.get("/realtime")
async def get_multiple_realtime_data(symbols: str = Query(...)):
    """获取多个交易对的实时数据"""
    try:
        symbol_list = symbols.split(',')
        data = []
        for symbol in symbol_list:
            import random
            price = random.uniform(40000, 45000)
            change_24h = random.uniform(-5, 5)
            
            data.append({
                "symbol": symbol,
                "price": price,
                "change24h": change_24h,
                "changePercent24h": change_24h,
                "volume24h": random.uniform(1000000, 5000000),
                "high24h": price * (1 + abs(change_24h) / 100),
                "low24h": price * (1 - abs(change_24h) / 100),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        return {"data": data}
    except Exception as e:
        logger.error(f"获取多个实时数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取多个实时数据失败")

@router.get("/market/overview")
async def get_market_overview():
    """获取市场概览"""
    try:
        overview = {
            "totalMarketCap": 1500000000000,
            "24hVolume": 50000000000,
            "btcDominance": 45.5,
            "topGainers": [
                {"symbol": "BTCUSDT", "change": 3.5},
                {"symbol": "ETHUSDT", "change": 2.8},
            ],
            "topLosers": [
                {"symbol": "ADAUSDT", "change": -1.2},
                {"symbol": "DOTUSDT", "change": -0.8},
            ]
        }
        return overview
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        raise HTTPException(status_code=500, detail="获取市场概览失败")