from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime

from api.deps import get_exchanges
from app.adapters.exchanges.base import ExchangeAdapter

router = APIRouter()

@router.get("/api/v1/market/klines")
async def get_klines(
    exchange: str = Query(...),
    symbol: str = Query(...),
    timeframe: str = Query(...),
    start_time: Optional[int] = Query(default=None),
    end_time: Optional[int] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    exchanges = Depends(get_exchanges),
):
    mgr = exchanges
    adapter: ExchangeAdapter | None = mgr.get_exchange(exchange)
    if adapter is None:
        return {"code": 1003, "message": f"交易所未配置: {exchange}"}
    data = await adapter.get_klines(
        symbol=symbol,
        interval=timeframe,
        start_time=datetime.fromtimestamp(start_time) if start_time else None,
        end_time=datetime.fromtimestamp(end_time) if end_time else None,
        limit=limit,
    )
    # 直接返回适配器的标准化数据
    return {"code": 0, "message": "success", "data": [k.__dict__ for k in data]}

@router.get("/api/v1/market/orderbook")
async def get_orderbook(
    exchange: str = Query(...),
    symbol: str = Query(...),
    limit: int = Query(default=20, ge=1, le=200),
    exchanges = Depends(get_exchanges),
):
    mgr = exchanges
    adapter: ExchangeAdapter | None = mgr.get_exchange(exchange)
    if adapter is None:
        return {"code": 1003, "message": f"交易所未配置: {exchange}"}
    ob = await adapter.exchange.get_order_book(symbol, limit)
    return {"code": 0, "message": "success", "data": ob}