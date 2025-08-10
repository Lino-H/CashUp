# 交易所插件系统
from .base import (
    BaseExchange, ExchangeInfo, ExchangeType, OrderType, OrderSide, OrderStatus,
    Symbol, Ticker, OrderBook, Trade, Kline, Balance, Order, Position
)
from .manager import ExchangeManager, exchange_manager, register_exchange, get_exchange_manager
from .gateio_exchange import GateIOExchange

# 自动注册Gate.io交易所
register_exchange(GateIOExchange)

__all__ = [
    # 基础类
    "BaseExchange",
    "ExchangeInfo",
    "ExchangeType",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "Symbol",
    "Ticker",
    "OrderBook",
    "Trade",
    "Kline",
    "Balance",
    "Order",
    "Position",
    # 管理器
    "ExchangeManager",
    "exchange_manager",
    "register_exchange",
    "get_exchange_manager",
    # 交易所实现
    "GateIOExchange",
]