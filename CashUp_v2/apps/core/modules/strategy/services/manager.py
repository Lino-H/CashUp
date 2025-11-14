import asyncio
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.adapters.exchanges.base import ExchangeAdapter, OrderRequest, OrderSide, OrderType
from ..factors.base import FactorBase

class CompositeStrategy:
    def __init__(self, name: str, factors: List[FactorBase]):
        self.name = name
        self.factors = factors
        self.weights = {f.name: 1.0 for f in factors}
        self.mode = "weighted"

    def set_weight(self, factor_name: str, weight: float):
        self.weights[factor_name] = weight

    def generate(self, closes: List[float]) -> Dict[str, Any]:
        signals = []
        for f in self.factors:
            s = f.get_signal(closes)
            if s["type"] != "none" and s["strength"] > 0:
                s["strength"] *= self.weights.get(f.name, 1.0)
                signals.append(s)
        if self.mode == "vote":
            buys = len([1 for s in signals if s["type"] == "buy"])
            sells = len([1 for s in signals if s["type"] == "sell"])
            if buys > sells and buys >= 2:
                return {"type": "buy", "strength": 0.7}
            if sells > buys and sells >= 2:
                return {"type": "sell", "strength": 0.7}
        else:
            buy = sum(s["strength"] for s in signals if s["type"] == "buy")
            sell = sum(s["strength"] for s in signals if s["type"] == "sell")
            if buy > sell and buy > 0.5:
                return {"type": "buy", "strength": min(buy, 1.0)}
            if sell > buy and sell > 0.5:
                return {"type": "sell", "strength": min(sell, 1.0)}
        return {"type": "none", "strength": 0.0}

class StrategyLifecycle:
    def __init__(self):
        self.active: Dict[int, asyncio.Task] = {}

    async def start(self, strategy_id: int, adapter: ExchangeAdapter, symbol: str, timeframe: str, composite: CompositeStrategy, db: AsyncSession | None = None, risk: Dict[str, Any] | None = None):
        task = asyncio.create_task(self._loop(strategy_id, adapter, symbol, timeframe, composite, db, risk or {}))
        self.active[strategy_id] = task
        return True

    async def stop(self, strategy_id: int):
        t = self.active.get(strategy_id)
        if t:
            t.cancel()
            self.active.pop(strategy_id, None)
        return True

    async def _loop(self, strategy_id: int, adapter: ExchangeAdapter, symbol: str, timeframe: str, composite: CompositeStrategy, db: AsyncSession | None, risk: Dict[str, Any]):
        try:
            max_pos = float(risk.get("max_position_size", 0))
            stop_loss = float(risk.get("stop_loss", 0))
            take_profit = float(risk.get("take_profit", 0))
            position_qty = 0.0
            entry_price = 0.0
            while True:
                klines = await adapter.get_klines(symbol, timeframe, limit=100)
                closes = [k.close_price for k in klines] if klines else []
                sig = composite.generate(closes)
                price = closes[-1] if closes else 0.0
                if db:
                    await db.execute(text("INSERT INTO strategy_signals (strategy_instance_id, signal_type, signal_data, price, executed, created_at) VALUES (:sid, :type, :data, :price, false, NOW())"), {"sid": strategy_id, "type": sig["type"], "data": {}, "price": price})
                if sig["type"] == "buy" and position_qty == 0.0:
                    qty = max_pos if max_pos > 0 else 0.0
                    if qty > 0:
                        req = OrderRequest(symbol=symbol, side=OrderSide.BUY, type=OrderType.MARKET, quantity=qty)
                        await adapter.place_order(req)
                        position_qty = qty
                        entry_price = price
                        if db:
                            await db.execute(text("UPDATE strategy_signals SET executed=true, executed_at=NOW() WHERE strategy_instance_id=:sid AND price=:price AND executed=false"), {"sid": strategy_id, "price": price})
                            await db.execute(text("INSERT INTO positions (user_id, strategy_instance_id, exchange, symbol, side, quantity, entry_price, mark_price, status, updated_at) VALUES (1, :sid, :exchange, :symbol, 'long', :qty, :price, :price, 'open', NOW()) ON CONFLICT DO NOTHING"), {"sid": strategy_id, "exchange": adapter.name, "symbol": symbol, "qty": qty, "price": price})
                if sig["type"] == "sell" and position_qty > 0.0:
                    req = OrderRequest(symbol=symbol, side=OrderSide.SELL, type=OrderType.MARKET, quantity=position_qty)
                    await adapter.place_order(req)
                    position_qty = 0.0
                    if db:
                        await db.execute(text("UPDATE strategy_signals SET executed=true, executed_at=NOW() WHERE strategy_instance_id=:sid AND price=:price AND executed=false"), {"sid": strategy_id, "price": price})
                        await db.execute(text("UPDATE positions SET status='closed', mark_price=:price, updated_at=NOW() WHERE strategy_instance_id=:sid AND symbol=:symbol AND status='open'"), {"sid": strategy_id, "symbol": symbol, "price": price})
                if position_qty > 0.0 and entry_price > 0.0 and price > 0.0:
                    change = (price - entry_price) / entry_price
                    if stop_loss > 0 and change <= -stop_loss:
                        req = OrderRequest(symbol=symbol, side=OrderSide.SELL, type=OrderType.MARKET, quantity=position_qty)
                        await adapter.place_order(req)
                        position_qty = 0.0
                        if db:
                            await db.execute(text("UPDATE positions SET status='closed', mark_price=:price, updated_at=NOW() WHERE strategy_instance_id=:sid AND symbol=:symbol AND status='open'"), {"sid": strategy_id, "symbol": symbol, "price": price})
                    if take_profit > 0 and change >= take_profit:
                        req = OrderRequest(symbol=symbol, side=OrderSide.SELL, type=OrderType.MARKET, quantity=position_qty)
                        await adapter.place_order(req)
                        position_qty = 0.0
                        if db:
                            await db.execute(text("UPDATE positions SET status='closed', mark_price=:price, updated_at=NOW() WHERE strategy_instance_id=:sid AND symbol=:symbol AND status='open'"), {"sid": strategy_id, "symbol": symbol, "price": price})
                await asyncio.sleep(adapter.exchange.get_interval_minutes(timeframe) * 60)
        except asyncio.CancelledError:
            return

lifecycle = StrategyLifecycle()