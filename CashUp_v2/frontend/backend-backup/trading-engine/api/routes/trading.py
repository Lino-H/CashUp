"""
交易服务
为前端提供交易管理相关的API接口
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime, timedelta

router = APIRouter(prefix="/trading", tags=["交易管理"])

@router.get("/orders/history")
async def get_order_history(
    symbol: str = None,
    status: str = None,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 100,
    offset: int = 0
):
    """获取订单历史"""
    # 模拟订单历史数据
    mock_orders = [
        {
            "id": "order_001",
            "symbol": "BTC/USDT",
            "side": "buy",
            "type": "limit",
            "quantity": 0.1,
            "price": 30000.0,
            "status": "filled",
            "filled_quantity": 0.1,
            "average_price": 30000.0,
            "commission": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "strategy": "grid"
        },
        {
            "id": "order_002",
            "symbol": "ETH/USDT",
            "side": "sell",
            "type": "limit",
            "quantity": 1.0,
            "price": 2000.0,
            "status": "cancelled",
            "filled_quantity": 0.0,
            "average_price": 0.0,
            "commission": 0.0,
            "created_at": (datetime.now() - timedelta(hours=1)).isoformat(),
            "updated_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "strategy": "trend"
        }
    ]

    # 过滤条件
    if symbol:
        mock_orders = [o for o in mock_orders if o["symbol"] == symbol]

    if status:
        mock_orders = [o for o in mock_orders if o["status"] == status]

    # 分页
    paginated_orders = mock_orders[offset:limit + offset]

    return {
        "status": "success",
        "data": {
            "orders": paginated_orders,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(mock_orders)
            },
            "filters": {
                "symbol": symbol,
                "status": status,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None
            }
        }
    }

@router.post("/orders/cancel/{order_id}")
async def cancel_order(order_id: str):
    """取消订单"""
    try:
        # 模拟取消订单逻辑
        return {
            "status": "success",
            "message": f"订单 {order_id} 取消成功",
            "data": {
                "order_id": order_id,
                "cancelled_at": datetime.now().isoformat(),
                "status": "cancelled"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消订单失败: {str(e)}")

@router.get("/positions")
async def get_all_positions():
    """获取所有持仓"""
    mock_positions = [
        {
            "symbol": "BTC/USDT",
            "side": "long",
            "size": 0.1,
            "entry_price": 30000.0,
            "mark_price": 31000.0,
            "unrealized_pnl": 100.0,
            "realized_pnl": 0.0,
            "leverage": 3,
            "margin_used": 1000.0,
            "percentage": 3.33,
            "strategy": "grid",
            "created_at": datetime.now().isoformat()
        },
        {
            "symbol": "ETH/USDT",
            "side": "short",
            "size": -2.0,
            "entry_price": 2000.0,
            "mark_price": 1950.0,
            "unrealized_pnl": 100.0,
            "realized_pnl": 0.0,
            "leverage": 3,
            "margin_used": 1333.33,
            "percentage": 3.33,
            "strategy": "trend",
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat()
        }
    ]

    return {
        "status": "success",
        "data": {
            "positions": mock_positions,
            "total_positions": len(mock_positions),
            "total_unrealized_pnl": sum(p["unrealized_pnl"] for p in mock_positions),
            "total_margin_used": sum(p["margin_used"] for p in mock_positions)
        }
    }

@router.get("/positions/{symbol}")
async def get_position_by_symbol(symbol: str):
    """获取指定交易对的持仓"""
    # 获取所有持仓，然后过滤
    all_positions = await get_all_positions()
    symbol_positions = [p for p in all_positions["data"]["positions"] if p["symbol"] == symbol]

    return {
        "status": "success",
        "data": {
            "symbol": symbol,
            "positions": symbol_positions,
            "total_positions": len(symbol_positions),
            "total_unrealized_pnl": sum(p["unrealized_pnl"] for p in symbol_positions),
            "total_margin_used": sum(p["margin_used"] for p in symbol_positions)
        }
    }

@router.post("/positions/close/{symbol}")
async def close_position(symbol: str):
    """平仓指定交易对的持仓"""
    try:
        # 模拟平仓逻辑
        return {
            "status": "success",
            "message": f"交易对 {symbol} 平仓成功",
            "data": {
                "symbol": symbol,
                "closed_at": datetime.now().isoformat(),
                "realized_pnl": 150.0,
                "closed_positions": 2
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"平仓失败: {str(e)}")

@router.get("/account/summary")
async def get_account_summary():
    """获取账户摘要"""
    mock_summary = {
        "total_balance": 11500.0,
        "available_balance": 8000.0,
        "margin_balance": 11500.0,
        "unrealized_pnl": 1500.0,
        "realized_pnl": 500.0,
        "total_margin_used": 2333.33,
        "free_margin": 9166.67,
        "margin_ratio": 20.3,
        "equity": 13000.0,
        "risk_level": "low",
        "leverage": 3,
        "account_type": "futures",
        "trading_enabled": True,
        "timestamp": datetime.now().isoformat()
    }

    return {
        "status": "success",
        "data": mock_summary
    }

@router.get("/account/pnl")
async def get_pnl_history(
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 100
):
    """获取盈亏历史"""
    mock_pnl_history = [
        {
            "id": "pnl_001",
            "type": "realized",
            "symbol": "BTC/USDT",
            "quantity": 0.1,
            "entry_price": 29000.0,
            "exit_price": 30000.0,
            "pnl": 100.0,
            "commission": 0.0,
            "strategy": "grid",
            "created_at": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        {
            "id": "pnl_002",
            "type": "realized",
            "symbol": "ETH/USDT",
            "quantity": 1.0,
            "entry_price": 2100.0,
            "exit_price": 2000.0,
            "pnl": -100.0,
            "commission": 0.0,
            "strategy": "trend",
            "created_at": (datetime.now() - timedelta(hours=3)).isoformat()
        }
    ]

    # 过滤
    if start_time:
        mock_pnl_history = [p for p in mock_pnl_history if datetime.fromisoformat(p["created_at"]) >= start_time]

    if end_time:
        mock_pnl_history = [p for p in mock_pnl_history if datetime.fromisoformat(p["created_at"]) <= end_time]

    # 分页
    paginated_pnl = mock_pnl_history[:limit]

    return {
        "status": "success",
        "data": {
            "pnl_history": paginated_pnl,
            "total_pnl": sum(p["pnl"] for p in mock_pnl_history),
            "winning_trades": len([p for p in mock_pnl_history if p["pnl"] > 0]),
            "losing_trades": len([p for p in mock_pnl_history if p["pnl"] < 0]),
            "total_trades": len(mock_pnl_history),
            "win_rate": 50.0,  # 模拟胜率
            "risk_reward_ratio": 1.5,  # 模拟盈亏比
            "pagination": {
                "limit": limit,
                "total": len(mock_pnl_history)
            }
        }
    }

@router.get("/symbols")
async def get_available_symbols():
    """获取可用交易对"""
    mock_symbols = [
        {
            "symbol": "BTC/USDT",
            "base_asset": "BTC",
            "quote_asset": "USDT",
            "price_precision": 2,
            "quantity_precision": 6,
            "min_quantity": 0.0001,
            "max_quantity": 100.0,
            "min_price": 0.01,
            "max_price": 1000000.0,
            "status": "trading",
            "funding_rate": 0.0001,
            "funding_rate_8h": 0.0008,
            "leverage": 3,
            "market_cap": 1000000000.0,
            "volume_24h": 50000000.0,
            "last_price": 31000.0,
            "price_change_24h": 2.5,
            "timestamp": datetime.now().isoformat()
        },
        {
            "symbol": "ETH/USDT",
            "base_asset": "ETH",
            "quote_asset": "USDT",
            "price_precision": 2,
            "quantity_precision": 6,
            "min_quantity": 0.001,
            "max_quantity": 1000.0,
            "min_price": 0.01,
            "max_price": 100000.0,
            "status": "trading",
            "funding_rate": -0.0001,
            "funding_rate_8h": -0.0008,
            "leverage": 3,
            "market_cap": 400000000.0,
            "volume_24h": 30000000.0,
            "last_price": 1950.0,
            "price_change_24h": -1.2,
            "timestamp": datetime.now().isoformat()
        }
    ]

    return {
        "status": "success",
        "data": {
            "symbols": mock_symbols,
            "total_symbols": len(mock_symbols)
        }
    }

@router.get("/fees")
async def get_trading_fees():
    """获取交易费率"""
    mock_fees = {
        "spot_trading": {
            "maker_fee": 0.001,
            "taker_fee": 0.002,
            "fee_currency": "USDT"
        },
        "futures_trading": {
            "maker_fee": 0.002,
            "taker_fee": 0.003,
            "fee_currency": "USDT"
        },
        "funding_rate": {
            "long_rate": 0.0001,
            "short_rate": -0.0001,
            "funding_interval": "8h",
            "next_funding_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
    }

    return {
        "status": "success",
        "data": mock_fees
    }