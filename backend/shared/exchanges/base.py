from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum


class ExchangeType(Enum):
    """交易所类型"""
    SPOT = "spot"  # 现货
    FUTURES = "futures"  # 期货
    OPTIONS = "options"  # 期权


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"  # 市价单
    LIMIT = "limit"  # 限价单
    STOP = "stop"  # 止损单
    STOP_LIMIT = "stop_limit"  # 止损限价单


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"  # 待成交
    OPEN = "open"  # 部分成交
    FILLED = "filled"  # 完全成交
    CANCELLED = "cancelled"  # 已取消
    REJECTED = "rejected"  # 已拒绝


@dataclass
class ExchangeInfo:
    """交易所信息"""
    name: str  # 交易所名称
    display_name: str  # 显示名称
    supported_types: List[ExchangeType]  # 支持的交易类型
    api_version: str  # API版本
    testnet_available: bool  # 是否支持测试网
    rate_limits: Dict[str, int]  # 速率限制
    description: str  # 描述


@dataclass
class Symbol:
    """交易对信息"""
    symbol: str  # 交易对符号
    base_asset: str  # 基础资产
    quote_asset: str  # 计价资产
    status: str  # 状态
    min_qty: float  # 最小数量
    max_qty: float  # 最大数量
    step_size: float  # 数量步长
    min_price: float  # 最小价格
    max_price: float  # 最大价格
    tick_size: float  # 价格步长
    min_notional: float  # 最小名义价值


@dataclass
class Ticker:
    """行情数据"""
    symbol: str  # 交易对
    last_price: float  # 最新价格
    bid_price: float  # 买一价
    ask_price: float  # 卖一价
    bid_qty: float  # 买一量
    ask_qty: float  # 卖一量
    volume_24h: float  # 24小时成交量
    change_24h: float  # 24小时涨跌幅
    high_24h: float  # 24小时最高价
    low_24h: float  # 24小时最低价
    timestamp: int  # 时间戳


@dataclass
class OrderBook:
    """订单簿"""
    symbol: str  # 交易对
    bids: List[List[float]]  # 买单 [[价格, 数量], ...]
    asks: List[List[float]]  # 卖单 [[价格, 数量], ...]
    timestamp: int  # 时间戳


@dataclass
class Trade:
    """成交记录"""
    id: str  # 成交ID
    symbol: str  # 交易对
    price: float  # 成交价格
    qty: float  # 成交数量
    side: OrderSide  # 成交方向
    timestamp: int  # 成交时间


@dataclass
class Kline:
    """K线数据"""
    symbol: str  # 交易对
    open_time: int  # 开盘时间
    close_time: int  # 收盘时间
    open_price: float  # 开盘价
    high_price: float  # 最高价
    low_price: float  # 最低价
    close_price: float  # 收盘价
    volume: float  # 成交量
    quote_volume: float  # 成交额
    trades_count: int  # 成交笔数


@dataclass
class Balance:
    """账户余额"""
    asset: str  # 资产
    free: float  # 可用余额
    locked: float  # 冻结余额
    total: float  # 总余额


@dataclass
class Order:
    """订单信息"""
    id: str  # 订单ID
    client_order_id: str  # 客户端订单ID
    symbol: str  # 交易对
    side: OrderSide  # 订单方向
    type: OrderType  # 订单类型
    qty: float  # 订单数量
    price: Optional[float]  # 订单价格
    status: OrderStatus  # 订单状态
    filled_qty: float  # 已成交数量
    remaining_qty: float  # 剩余数量
    avg_price: Optional[float]  # 平均成交价格
    create_time: int  # 创建时间
    update_time: int  # 更新时间


@dataclass
class Position:
    """持仓信息（期货）"""
    symbol: str  # 合约符号
    side: str  # 持仓方向 (long/short)
    size: float  # 持仓数量
    entry_price: float  # 开仓价格
    mark_price: float  # 标记价格
    unrealized_pnl: float  # 未实现盈亏
    realized_pnl: float  # 已实现盈亏
    margin: float  # 保证金
    percentage: float  # 盈亏比例
    timestamp: int  # 时间戳


class BaseExchange(ABC):
    """交易所基础抽象类"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False, **kwargs):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.extra_params = kwargs
    
    @abstractmethod
    async def connect(self) -> None:
        """连接到交易所"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    def get_exchange_info(self) -> ExchangeInfo:
        """获取交易所信息"""
        pass
    
    # 市场数据接口
    @abstractmethod
    async def get_symbols(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Symbol]:
        """获取交易对列表"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str, exchange_type: ExchangeType = ExchangeType.SPOT) -> Ticker:
        """获取单个交易对行情"""
        pass
    
    @abstractmethod
    async def get_tickers(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Ticker]:
        """获取所有交易对行情"""
        pass
    
    @abstractmethod
    async def get_order_book(self, symbol: str, limit: int = 100, exchange_type: ExchangeType = ExchangeType.SPOT) -> OrderBook:
        """获取订单簿"""
        pass
    
    @abstractmethod
    async def get_trades(self, symbol: str, limit: int = 100, exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Trade]:
        """获取成交记录"""
        pass
    
    @abstractmethod
    async def get_klines(self, symbol: str, interval: str, limit: int = 100, 
                        start_time: Optional[int] = None, end_time: Optional[int] = None,
                        exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Kline]:
        """获取K线数据"""
        pass
    
    # 账户接口
    @abstractmethod
    async def get_account_info(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> Dict[str, Any]:
        """获取账户信息"""
        pass
    
    @abstractmethod
    async def get_balances(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Balance]:
        """获取账户余额"""
        pass
    
    # 交易接口
    @abstractmethod
    async def create_order(self, symbol: str, side: OrderSide, order_type: OrderType,
                          qty: float, price: Optional[float] = None,
                          client_order_id: Optional[str] = None,
                          exchange_type: ExchangeType = ExchangeType.SPOT,
                          **kwargs) -> Order:
        """创建订单"""
        pass
    
    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str,
                          exchange_type: ExchangeType = ExchangeType.SPOT) -> Order:
        """取消订单"""
        pass
    
    @abstractmethod
    async def get_order(self, symbol: str, order_id: str,
                       exchange_type: ExchangeType = ExchangeType.SPOT) -> Order:
        """获取订单信息"""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None,
                             exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Order]:
        """获取未成交订单"""
        pass
    
    @abstractmethod
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100,
                               exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Order]:
        """获取历史订单"""
        pass
    
    # 期货特有接口
    async def get_positions(self) -> List[Position]:
        """获取持仓信息（期货）"""
        raise NotImplementedError("This exchange does not support futures trading")
    
    async def get_position(self, symbol: str) -> Position:
        """获取单个持仓信息（期货）"""
        raise NotImplementedError("This exchange does not support futures trading")
    
    # WebSocket接口
    async def subscribe_ticker(self, symbol: str, callback: Callable,
                              exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """订阅行情数据"""
        raise NotImplementedError("WebSocket not implemented")
    
    async def subscribe_order_book(self, symbol: str, callback: Callable,
                                  exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """订阅订单簿数据"""
        raise NotImplementedError("WebSocket not implemented")
    
    async def subscribe_trades(self, symbol: str, callback: Callable,
                              exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """订阅成交数据"""
        raise NotImplementedError("WebSocket not implemented")
    
    async def subscribe_orders(self, callback: Callable,
                              exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """订阅订单更新"""
        raise NotImplementedError("WebSocket not implemented")
    
    async def start_websocket(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """启动WebSocket连接"""
        raise NotImplementedError("WebSocket not implemented")
    
    async def stop_websocket(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """停止WebSocket连接"""
        raise NotImplementedError("WebSocket not implemented")