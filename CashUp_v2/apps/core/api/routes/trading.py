from fastapi import APIRouter, Depends, Query
from typing import Optional

from api.deps import get_exchanges
from app.adapters.exchanges.base import ExchangeAdapter, OrderRequest, OrderSide, OrderType, CancelOrderRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database.connection import get_db
from events.notifications import publish
from events.rabbitmq import publish_event

router = APIRouter()

@router.post("/api/v1/trading/orders")
async def create_order(
    exchange: str,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    time_in_force: str = "GTC",
    client_order_id: Optional[str] = None,
    exchanges = Depends(get_exchanges),
    db: AsyncSession = Depends(get_db),
):
    mgr = exchanges
    adapter: ExchangeAdapter | None = mgr.get_exchange(exchange)
    if adapter is None:
        return {"code": 1003, "message": f"交易所未配置: {exchange}"}
    req = OrderRequest(
        symbol=symbol,
        side=OrderSide(side),
        type=OrderType(order_type),
        quantity=quantity,
        price=price,
        client_order_id=client_order_id,
    )
    order = await adapter.place_order(req)
    await db.execute(text(
        """
        INSERT INTO orders (user_id, strategy_instance_id, exchange, symbol, client_order_id, exchange_order_id, order_type, side, price, quantity, filled_quantity, status, fee, created_at)
        VALUES (1, NULL, :exchange, :symbol, :client_id, :exchange_id, :type, :side, :price, :qty, :filled, :status, 0, NOW())
        """
    ), {
        "exchange": exchange,
        "symbol": symbol,
        "client_id": client_order_id or order.client_order_id,
        "exchange_id": order.id,
        "type": order.type.value,
        "side": order.side.value,
        "price": order.price or 0,
        "qty": order.quantity,
        "filled": order.filled_quantity,
        "status": order.status.value,
    })
    await publish("order.created", {"symbol": symbol, "side": side, "quantity": quantity})
    await publish_event("order.created", {"symbol": symbol, "side": side, "quantity": quantity})
    if order.status.value in ("filled", "partially_filled"):
        await publish("order.filled", {"symbol": symbol, "side": side, "quantity": order.filled_quantity})
        await publish_event("order.filled", {"symbol": symbol, "side": side, "quantity": order.filled_quantity})
    return {"code": 0, "message": "订单创建成功", "data": order.__dict__}

@router.get("/api/v1/trading/positions")
async def list_positions(exchange: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    q = "SELECT id, user_id, strategy_instance_id, exchange, symbol, side, quantity, entry_price, mark_price, liquidation_price, unrealized_pnl, realized_pnl, leverage, status, updated_at FROM positions"
    params = {}
    if exchange:
        q += " WHERE exchange=:exchange"
        params["exchange"] = exchange
    q += " ORDER BY updated_at DESC"
    res = await db.execute(text(q), params)
    rows = res.fetchall()
    items = []
    for r in rows:
        items.append({
            "id": r.id,
            "exchange": r.exchange,
            "symbol": r.symbol,
            "side": r.side,
            "quantity": float(r.quantity or 0),
            "entry_price": float(r.entry_price or 0),
            "mark_price": float(r.mark_price or 0),
            "realized_pnl": float(r.realized_pnl or 0),
            "unrealized_pnl": float(r.unrealized_pnl or 0),
            "status": r.status,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })
    return {"code": 0, "message": "success", "data": items}

@router.get("/api/v1/trading/balance")
async def get_balance(exchange: str, exchanges = Depends(get_exchanges)):
    adapter: ExchangeAdapter | None = exchanges.get_exchange(exchange)
    if adapter is None:
        return {"code": 1003, "message": f"交易所未配置: {exchange}"}
    bal = await adapter.get_balance()
    # 映射为可序列化结构
    data = {k: v.__dict__ for k, v in bal.items()}
    total = sum(b.total for b in bal.values()) if bal else 0
    available = sum(b.free for b in bal.values()) if bal else 0
    return {"code": 0, "message": "success", "data": {"total_balance": total, "available": available, "assets": data}}

@router.post("/api/v1/trading/orders/cancel")
async def cancel_order(exchange: str, symbol: str, order_id: Optional[str] = None, client_order_id: Optional[str] = None, exchanges = Depends(get_exchanges)):
    adapter: ExchangeAdapter | None = exchanges.get_exchange(exchange)
    if adapter is None:
        return {"code": 1003, "message": f"交易所未配置: {exchange}"}
    ok = await adapter.cancel_order(CancelOrderRequest(symbol=symbol, order_id=order_id, client_order_id=client_order_id))
    return {"code": 0 if ok else 1005, "message": "success" if ok else "取消失败"}