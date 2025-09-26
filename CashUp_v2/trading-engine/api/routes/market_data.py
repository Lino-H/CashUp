"""
市场数据API
基于Gate.io真实API的市场数据接口
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json

router = APIRouter(prefix="/market", tags=["市场数据"])

class GateIOClient:
    """Gate.io API客户端"""

    def __init__(self):
        self.base_url = "https://api.gateio.ws/api/v4"
        self.session = None

    async def __aenter__(self):
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_ticker(self, symbol: str):
        """获取行情数据"""
        async with self.session.get(f"{self.base_url}/spot/tickers", params={"currency_pair": symbol}) as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    return data[0]
            raise HTTPException(status_code=500, detail="获取行情数据失败")

    async def get_klines(self, symbol: str, interval: str, limit: int = 100):
        """获取K线数据"""
        params = {
            "currency_pair": symbol,
            "interval": interval,
            "limit": min(limit, 1000)
        }
        async with self.session.get(f"{self.base_url}/spot/candlesticks", params=params) as response:
            if response.status == 200:
                return await response.json()
            raise HTTPException(status_code=500, detail="获取K线数据失败")

    async def get_order_book(self, symbol: str, limit: int = 100):
        """获取订单簿"""
        params = {
            "currency_pair": symbol,
            "limit": limit
        }
        async with self.session.get(f"{self.base_url}/spot/order_book", params=params) as response:
            if response.status == 200:
                return await response.json()
            raise HTTPException(status_code=500, detail="获取订单簿失败")

    async def get_symbols(self):
        """获取交易对列表"""
        async with self.session.get(f"{self.base_url}/spot/currency_pairs") as response:
            if response.status == 200:
                return await response.json()
            raise HTTPException(status_code=500, detail="获取交易对列表失败")

# 全局客户端实例
market_client = GateIOClient()

@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str):
    """获取指定交易对的行情数据"""
    try:
        async with market_client:
            ticker = await market_client.get_ticker(symbol)

            return {
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "last_price": float(ticker.get("last", 0)),
                    "highest_bid": float(ticker.get("highest_bid", 0)),
                    "lowest_ask": float(ticker.get("lowest_ask", 0)),
                    "base_volume": float(ticker.get("base_volume", 0)),
                    "quote_volume": float(ticker.get("quote_volume", 0)),
                    "high_24h": float(ticker.get("high_24h", 0)),
                    "low_24h": float(ticker.get("low_24h", 0)),
                    "change": float(ticker.get("change", 0)),
                    "change_percentage": float(ticker.get("change_percentage", 0)),
                    "timestamp": datetime.now().isoformat()
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行情数据失败: {str(e)}")

@router.get("/klines/{symbol}")
async def get_klines(
    symbol: str,
    interval: str = Query("1h", description="时间间隔: 1m, 5m, 15m, 30m, 1h, 4h, 1d"),
    limit: int = Query(100, description="数据数量")
):
    """获取K线数据"""
    try:
        async with market_client:
            klines_data = await market_client.get_klines(symbol, interval, limit)

            klines = []
            for item in reversed(klines_data):
                kline = {
                    "timestamp": datetime.fromtimestamp(item[0]).isoformat(),
                    "open": float(item[1]),
                    "high": float(item[2]),
                    "low": float(item[3]),
                    "close": float(item[4]),
                    "volume": float(item[5]),
                    "quote_volume": float(item[6]),
                    "trades": 0,
                    "taker_buy_base_volume": 0,
                    "taker_buy_quote_volume": 0
                }
                klines.append(kline)

            return {
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "interval": interval,
                    "klines": klines,
                    "total": len(klines),
                    "timestamp": datetime.now().isoformat()
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")

@router.get("/orderbook/{symbol}")
async def get_order_book(
    symbol: str,
    limit: int = Query(100, description="深度数据数量")
):
    """获取订单簿数据"""
    try:
        async with market_client:
            orderbook_data = await market_client.get_order_book(symbol, limit)

            return {
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "bids": [[float(price), float(amount)] for price, amount in orderbook_data.get("bids", [])[:limit]],
                    "asks": [[float(price), float(amount)] for price, amount in orderbook_data.get("asks", [])[:limit]],
                    "timestamp": datetime.now().isoformat()
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单簿失败: {str(e)}")

@router.get("/symbols")
async def get_symbols():
    """获取所有支持的交易对"""
    try:
        async with market_client:
            symbols_data = await market_client.get_symbols()

            symbols = []
            for item in symbols_data:
                symbol_info = {
                    "symbol": item.get("id", ""),
                    "base_asset": item.get("base", ""),
                    "quote_asset": item.get("quote", ""),
                    "quote_precision": item.get("decimal_places", 8),
                    "amount_precision": item.get("amount_decimal_places", 8),
                    "min_amount": float(item.get("min_amount", "0")),
                    "max_amount": float(item.get("max_amount", "1000000")),
                    "min_price": float(item.get("min_price", "0.00000001")),
                    "max_price": float(item.get("max_price", "1000000")),
                    "status": item.get("status", "trading"),
                    "trading": item.get("trading", True),
                    "is_market_order_allowed": item.get("is_market_order_allowed", True),
                    "create_time": item.get("create_time", ""),
                    "update_time": item.get("update_time", "")
                }
                symbols.append(symbol_info)

            return {
                "status": "success",
                "data": {
                    "symbols": symbols,
                    "total": len(symbols),
                    "timestamp": datetime.now().isoformat()
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易对列表失败: {str(e)}")

@router.get("/overview")
async def get_market_overview():
    """获取市场概览数据"""
    try:
        # 获取主要交易对的行情数据
        major_symbols = ["BTC_USDT", "ETH_USDT", "BNB_USDT", "SOL_USDT"]

        overview_data = []
        total_volume_24h = 0
        price_changes = []

        async with market_client:
            for symbol in major_symbols:
                try:
                    ticker = await market_client.get_ticker(symbol)
                    symbol_name = symbol.replace("_", "/")

                    volume_24h = float(ticker.get("quote_volume", 0))
                    total_volume_24h += volume_24h

                    price_change = float(ticker.get("change_percentage", 0))
                    price_changes.append(price_change)

                    overview_data.append({
                        "symbol": symbol_name,
                        "last_price": float(ticker.get("last", 0)),
                        "price_change_24h": float(ticker.get("change", 0)),
                        "price_change_percentage": float(ticker.get("change_percentage", 0)),
                        "volume_24h": volume_24h,
                        "high_24h": float(ticker.get("high_24h", 0)),
                        "low_24h": float(ticker.get("low_24h", 0))
                    })
                except Exception as e:
                    print(f"获取 {symbol} 数据失败: {e}")
                    continue

        avg_price_change = sum(price_changes) / len(price_changes) if price_changes else 0

        return {
            "status": "success",
            "data": {
                "total_volume_24h": total_volume_24h,
                "average_price_change": avg_price_change,
                "active_symbols": len(overview_data),
                "timestamp": datetime.now().isoformat(),
                "major_symbols": overview_data
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场概览失败: {str(e)}")

@router.get("/stats/{symbol}")
async def get_symbol_stats(symbol: str):
    """获取交易对统计数据"""
    try:
        async with market_client:
            ticker = await market_client.get_ticker(symbol)

            return {
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "price": float(ticker.get("last", 0)),
                    "price_change_24h": float(ticker.get("change", 0)),
                    "price_change_percentage": float(ticker.get("change_percentage", 0)),
                    "volume_24h": float(ticker.get("base_volume", 0)),
                    "quote_volume_24h": float(ticker.get("quote_volume", 0)),
                    "high_24h": float(ticker.get("high_24h", 0)),
                    "low_24h": float(ticker.get("low_24h", 0)),
                    "timestamp": datetime.now().isoformat()
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")