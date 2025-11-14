from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .manager import CompositeStrategy

async def run_backtest(db: AsyncSession, composite: CompositeStrategy, exchange: str, symbol: str, timeframe: str, start: str, end: str) -> Dict[str, Any]:
    q = text("""
        SELECT open_time, close FROM kline_data
        WHERE exchange=:exchange AND symbol=:symbol AND timeframe=:tf AND open_time BETWEEN :start AND :end
        ORDER BY open_time ASC
    """)
    rows = (await db.execute(q, {"exchange": exchange, "symbol": symbol, "tf": timeframe, "start": start, "end": end})).all()
    closes = [float(r.close) for r in rows]
    balance = 10000.0
    position = 0.0
    trades = 0
    for i in range(len(closes)):
        window = closes[:i+1]
        sig = composite.generate(window)
        price = closes[i]
        if sig["type"] == "buy" and position == 0:
            qty = balance / price
            position = qty
            balance = 0.0
            trades += 1
        elif sig["type"] == "sell" and position > 0:
            balance = position * price
            position = 0.0
            trades += 1
    final = balance + position * (closes[-1] if closes else 0.0)
    total_pnl = final - 10000.0
    return {"initial_balance": 10000.0, "final_balance": final, "total_pnl": total_pnl, "total_trades": trades}