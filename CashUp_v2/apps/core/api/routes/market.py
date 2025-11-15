from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime

from api.deps import get_exchanges
from app.adapters.exchanges.base import ExchangeAdapter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database.connection import get_db
from database.redis import get_redis

router = APIRouter()

@router.get("/api/v1/market/klines")
async def get_klines(
    exchange: str = Query(...),
    symbol: str = Query(...),
    timeframe: str = Query(...),
    start_time: Optional[int] = Query(default=None),
    end_time: Optional[int] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    persist: bool = Query(default=False),
    exchanges = Depends(get_exchanges),
    db: AsyncSession = Depends(get_db),
):
    mgr = exchanges
    # 缓存读取
    try:
        r = await get_redis()
        ck = f"klines:{exchange}:{symbol}:{timeframe}:{limit}"
        cached = await r.get(ck)
        if cached:
            import json
            return {"code": 0, "message": "cache", "data": json.loads(cached)}
    except Exception:
        pass
    adapter: ExchangeAdapter | None = mgr.get_exchange(exchange)
    if adapter is None:
        # 回退到数据库历史
        rows = (await db.execute(text("SELECT open_time, open, high, low, close, volume FROM kline_data WHERE exchange=:ex AND symbol=:sym AND timeframe=:tf ORDER BY open_time DESC LIMIT :limit").bindparams(limit=limit), {"ex": exchange, "sym": symbol, "tf": timeframe})).fetchall()
        data = [{"open_time": r.open_time.isoformat() if hasattr(r.open_time, 'isoformat') else r.open_time, "open": float(r.open or 0), "high": float(r.high or 0), "low": float(r.low or 0), "close": float(r.close or 0), "volume": float(r.volume or 0)} for r in rows]
        return {"code": 0, "message": "success", "data": data}
    try:
        data = await adapter.get_klines(
            symbol=symbol,
            interval=timeframe,
            start_time=datetime.fromtimestamp(start_time) if start_time else None,
            end_time=datetime.fromtimestamp(end_time) if end_time else None,
            limit=limit,
        )
        payload = [k.__dict__ for k in data]
        if persist and payload:
            try:
                rows = [
                    {
                        "ex": exchange,
                        "sym": symbol,
                        "tf": timeframe,
                        "ot": k.open_time,
                        "o": k.open_price,
                        "h": k.high_price,
                        "l": k.low_price,
                        "c": k.close_price,
                        "v": k.volume,
                    }
                    for k in data
                ]
                await db.execute(
                    text(
                        """
                        INSERT INTO kline_data (exchange, symbol, timeframe, open_time, open, high, low, close, volume)
                        VALUES (:ex, :sym, :tf, :ot, :o, :h, :l, :c, :v)
                        ON CONFLICT (exchange, symbol, timeframe, open_time)
                        DO UPDATE SET open=:o, high=:h, low=:l, close=:c, volume=:v
                        """
                    ),
                    rows,
                )
                await db.commit()
            except Exception as e:
                try:
                    r2 = await get_redis()
                    await r2.set("market:persist:error:last", str(e))
                except Exception:
                    pass
        try:
            r = await get_redis()
            import json
            ck = f"klines:{exchange}:{symbol}:{timeframe}:{limit}"
            # 缓存 TTL 读取自 system_configs，默认 30
            ttl = 30
            try:
                res = await db.execute(text("SELECT config_value FROM system_configs WHERE config_key='market.cache.ttl'"))
                rv = res.first()
                if rv and rv.config_value:
                    ttl = int(str(rv.config_value).strip('"'))
            except Exception:
                ttl = 30
            await r.setex(ck, ttl, json.dumps(payload))
        except Exception:
            pass
        return {"code": 0, "message": "success", "data": payload}
    except Exception as e:
        # 二级回退：数据库历史
        rows = (await db.execute(text("SELECT open_time, open, high, low, close, volume FROM kline_data WHERE exchange=:ex AND symbol=:sym AND timeframe=:tf ORDER BY open_time DESC LIMIT :limit").bindparams(limit=limit), {"ex": exchange, "sym": symbol, "tf": timeframe})).fetchall()
        data = [{"open_time": r.open_time.isoformat() if hasattr(r.open_time, 'isoformat') else r.open_time, "open": float(r.open or 0), "high": float(r.high or 0), "low": float(r.low or 0), "close": float(r.close or 0), "volume": float(r.volume or 0)} for r in rows]
        return {"code": 0, "message": "fallback", "data": data}

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
    try:
        ob = await adapter.exchange.get_order_book(symbol, limit)
        return {"code": 0, "message": "success", "data": ob}
    except Exception as e:
        return {"code": 1002, "message": f"获取订单簿失败: {str(e)}", "data": {}}