"""
交易所抽象层 - 统一的交易所接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    POST_ONLY = "post_only"
    FOK = "fill_or_kill"
    IOC = "immediate_or_cancel"

class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REJECTED = "rejected"

class ContractType(Enum):
    """合约类型"""
    PERPETUAL = "perpetual"
    FUTURES = "futures"
    SPOT = "spot"

class PositionSide(Enum):
    """持仓方向"""
    LONG = "long"
    SHORT = "short"
    BOTH = "both"

class TimeInForce(Enum):
    """时间有效性"""
    GTC = "good_till_cancelled"  # 撤销前有效
    IOC = "immediate_or_cancel"  # 立即成交或撤销
    FOK = "fill_or_kill"         # 全部成交或撤销
    DAY = "day"                  # 当日有效

@dataclass
class Ticker:
    """行情信息"""
    symbol: str
    last_price: float
    bid_price: float
    ask_price: float
    bid_volume: float
    ask_volume: float
    volume_24h: float
    high_24h: float
    low_24h: float
    price_change_24h: float
    price_change_percent_24h: float
    timestamp: datetime

@dataclass
class Balance:
    """账户余额"""
    asset: str
    free: float
    used: float
    total: float

@dataclass
class Order:
    """订单信息"""
    id: str
    client_order_id: Optional[str]
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    time_in_force: TimeInForce
    status: OrderStatus
    filled_quantity: float
    remaining_quantity: float
    average_price: Optional[float]
    commission: float
    created_at: datetime
    updated_at: datetime
    exchange: str

@dataclass
class Trade:
    """成交信息"""
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float
    commission_asset: str
    timestamp: datetime
    exchange: str

@dataclass
class Kline:
    """K线数据"""
    symbol: str
    interval: str
    open_time: datetime
    close_time: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float
    trades_count: int
    taker_buy_volume: float
    taker_buy_quote_volume: float

@dataclass
class Position:
    """持仓信息"""
    symbol: str
    side: PositionSide
    size: float
    entry_price: float
    mark_price: float
    liquidation_price: float
    unrealized_pnl: float
    realized_pnl: float
    leverage: int
    margin_used: float
    timestamp: datetime
    exchange: str

@dataclass
class FundingRate:
    """资金费率信息"""
    symbol: str
    funding_rate: float
    funding_rate_8h: float
    next_funding_time: datetime
    mark_price: float
    index_price: float
    timestamp: datetime
    exchange: str

@dataclass
class OrderRequest:
    """下单请求"""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    client_order_id: Optional[str] = None
    iceberg_quantity: Optional[float] = None
    post_only: bool = False
    reduce_only: bool = False
    contract_type: ContractType = ContractType.PERPETUAL

@dataclass
class CancelOrderRequest:
    """取消订单请求"""
    symbol: str
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None

class ExchangeBase(ABC):
    """交易所基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'Unknown')
        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')
        self.passphrase = config.get('passphrase', '')
        self.sandbox = config.get('sandbox', False)
        self.rate_limit = config.get('rate_limit', 10)  # 每秒请求数
        
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """获取行情信息"""
        pass
    
    @abstractmethod
    async def get_klines(self, symbol: str, interval: str, 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: int = 100) -> List[Kline]:
        """获取K线数据"""
        pass
    
    @abstractmethod
    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """获取订单簿"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, Balance]:
        """获取账户余额"""
        pass
    
    @abstractmethod
    async def get_orders(self, symbol: Optional[str] = None, 
                        status: Optional[OrderStatus] = None) -> List[Order]:
        """获取订单列表"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """获取单个订单信息"""
        pass
    
    @abstractmethod
    async def get_trades(self, symbol: str, order_id: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: int = 100) -> List[Trade]:
        """获取成交记录"""
        pass
    
    @abstractmethod
    async def place_order(self, request: OrderRequest) -> Order:
        """下单"""
        pass
    
    @abstractmethod
    async def cancel_order(self, request: CancelOrderRequest) -> bool:
        """取消订单"""
        pass
    
    @abstractmethod
    async def cancel_all_orders(self, symbol: str) -> List[Order]:
        """取消所有订单"""
        pass
    
    @abstractmethod
    async def get_server_time(self) -> datetime:
        """获取服务器时间"""
        pass
    
    @abstractmethod
    async def get_symbols(self) -> List[Dict[str, Any]]:
        """获取交易对信息"""
        pass
    
    @abstractmethod
    async def get_exchange_info(self) -> Dict[str, Any]:
        """获取交易所信息"""
        pass

    # 永续合约相关方法
    @abstractmethod
    async def get_futures_balance(self) -> Dict[str, Balance]:
        """获取永续合约账户余额"""
        pass

    @abstractmethod
    async def get_futures_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """获取永续合约持仓信息"""
        pass

    @abstractmethod
    async def get_funding_rate(self, symbol: str) -> FundingRate:
        """获取资金费率信息"""
        pass

    @abstractmethod
    async def get_funding_rate_history(self, symbol: str,
                                     start_time: Optional[datetime] = None,
                                     end_time: Optional[datetime] = None,
                                     limit: int = 100) -> List[FundingRate]:
        """获取资金费率历史"""
        pass

    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """设置杠杆"""
        pass

    @abstractmethod
    async def get_leverage(self, symbol: str) -> int:
        """获取当前杠杆"""
        pass
    
    # WebSocket相关方法
    @abstractmethod
    async def subscribe_ticker(self, symbol: str, callback):
        """订阅行情推送"""
        pass

    @abstractmethod
    async def subscribe_kline(self, symbol: str, interval: str, callback):
        """订阅K线推送"""
        pass

    @abstractmethod
    async def subscribe_order_book(self, symbol: str, callback):
        """订阅订单簿推送"""
        pass

    @abstractmethod
    async def subscribe_trades(self, symbol: str, callback):
        """订阅成交推送"""
        pass

    @abstractmethod
    async def subscribe_user_data(self, callback):
        """订阅用户数据推送"""
        pass

    # 永续合约WebSocket方法
    @abstractmethod
    async def subscribe_funding_rate(self, symbol: str, callback):
        """订阅资金费率推送"""
        pass

    @abstractmethod
    async def subscribe_mark_price(self, symbol: str, callback):
        """订阅标记价格推送"""
        pass

    @abstractmethod
    async def subscribe_liquidation_orders(self, callback):
        """订阅强制平仓推送"""
        pass
    
    # 工具方法
    def parse_symbol(self, symbol: str) -> Dict[str, str]:
        """解析交易对"""
        # 默认实现，子类可以重写
        return {'base': '', 'quote': ''}
    
    def format_symbol(self, base: str, quote: str) -> str:
        """格式化交易对"""
        # 默认实现，子类可以重写
        return f"{base}/{quote}"
    
    def get_interval_minutes(self, interval: str) -> int:
        """获取时间间隔（分钟）"""
        interval_map = {
            '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '6h': 360, '8h': 480, '12h': 720,
            '1d': 1440, '3d': 4320, '1w': 10080, '1M': 43200
        }
        return interval_map.get(interval, 60)
    
    def validate_symbol(self, symbol: str) -> bool:
        """验证交易对格式"""
        # 默认实现，子类可以重写
        return len(symbol) > 0
    
    def validate_order_request(self, request: OrderRequest) -> bool:
        """验证下单请求"""
        if not self.validate_symbol(request.symbol):
            return False
        
        if request.quantity <= 0:
            return False
        
        if request.type in [OrderType.LIMIT, OrderType.STOP_LIMIT, OrderType.STOP]:
            if request.price is None or request.price <= 0:
                return False
        
        if request.type == OrderType.STOP_LIMIT:
            if request.stop_price is None or request.stop_price <= 0:
                return False
        
        return True
    
    async def test_connectivity(self) -> bool:
        """测试连接"""
        try:
            await self.get_server_time()
            return True
        except Exception:
            return False
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """获取速率限制状态"""
        return {
            'requests_used': 0,
            'requests_remaining': self.rate_limit,
            'reset_time': datetime.now() + timedelta(seconds=60)
        }

class ExchangeAdapter:
    """交易所适配器"""
    
    def __init__(self, exchange_config: Dict[str, Any]):
        self.config = exchange_config
        self.exchange = self._create_exchange()
        self.name = self.exchange.name
        self.symbols_cache = {}
        self.last_update = datetime.now()
    
    def _create_exchange(self) -> ExchangeBase:
        """根据配置创建交易所实例"""
        exchange_type = self.config.get('type')
        
        if exchange_type == 'binance':
            from .binance import BinanceExchange
            return BinanceExchange(self.config)
        elif exchange_type == 'gateio':
            from .gateio import GateIOExchange
            return GateIOExchange(self.config)
        elif exchange_type == 'okx':
            from .okx import OKXExchange
            return OKXExchange(self.config)
        elif exchange_type == 'huobi':
            from .huobi import HuobiExchange
            return HuobiExchange(self.config)
        elif exchange_type == 'bybit':
            from .bybit import BybitExchange
            return BybitExchange(self.config)
        elif exchange_type == 'kraken':
            from .kraken import KrakenExchange
            return KrakenExchange(self.config)
        else:
            raise ValueError(f"不支持的交易所类型: {exchange_type}")
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """获取行情信息"""
        return await self.exchange.get_ticker(symbol)
    
    async def get_klines(self, symbol: str, interval: str,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: int = 100) -> List[Kline]:
        """获取K线数据"""
        return await self.exchange.get_klines(symbol, interval, start_time, end_time, limit)
    
    async def get_balance(self) -> Dict[str, Balance]:
        """获取账户余额"""
        return await self.exchange.get_balance()
    
    async def place_order(self, request: OrderRequest) -> Order:
        """下单"""
        if not self.exchange.validate_order_request(request):
            raise ValueError("无效的下单请求")
        
        return await self.exchange.place_order(request)
    
    async def cancel_order(self, request: CancelOrderRequest) -> bool:
        """取消订单"""
        return await self.exchange.cancel_order(request)
    
    async def get_orders(self, symbol: Optional[str] = None,
                        status: Optional[OrderStatus] = None) -> List[Order]:
        """获取订单列表"""
        return await self.exchange.get_orders(symbol, status)
    
    async def get_symbols(self) -> List[Dict[str, Any]]:
        """获取交易对信息"""
        # 使用缓存
        now = datetime.now()
        if (now - self.last_update).seconds < 3600 and self.symbols_cache:
            return list(self.symbols_cache.values())
        
        symbols = await self.exchange.get_symbols()
        self.symbols_cache = {s['symbol']: s for s in symbols}
        self.last_update = now
        return symbols
    
    async def test_connection(self) -> bool:
        """测试连接"""
        return await self.exchange.test_connectivity()
    
    def get_info(self) -> Dict[str, Any]:
        """获取适配器信息"""
        return {
            'name': self.name,
            'type': self.config.get('type'),
            'sandbox': self.config.get('sandbox', False),
            'symbols_count': len(self.symbols_cache),
            'last_update': self.last_update.isoformat()
        }

class ExchangeManager:
    """交易所管理器"""
    
    def __init__(self):
        self.exchanges: Dict[str, ExchangeAdapter] = {}
        self.primary_exchange: Optional[str] = None
    
    def add_exchange(self, name: str, config: Dict[str, Any]) -> bool:
        """添加交易所"""
        try:
            adapter = ExchangeAdapter(config)
            self.exchanges[name] = adapter
            
            if self.primary_exchange is None:
                self.primary_exchange = name
            
            return True
        except Exception as e:
            print(f"添加交易所 {name} 失败: {e}")
            return False
    
    def remove_exchange(self, name: str) -> bool:
        """移除交易所"""
        if name in self.exchanges:
            del self.exchanges[name]
            
            if self.primary_exchange == name:
                self.primary_exchange = next(iter(self.exchanges.keys()), None)
            
            return True
        return False
    
    def get_exchange(self, name: Optional[str] = None) -> Optional[ExchangeAdapter]:
        """获取交易所适配器"""
        if name is None:
            name = self.primary_exchange
        
        return self.exchanges.get(name)
    
    def get_all_exchanges(self) -> Dict[str, ExchangeAdapter]:
        """获取所有交易所"""
        return self.exchanges.copy()
    
    def get_exchange_names(self) -> List[str]:
        """获取交易所名称列表"""
        return list(self.exchanges.keys())
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """测试所有交易所连接"""
        results = {}
        
        for name, adapter in self.exchanges.items():
            results[name] = await adapter.test_connection()
        
        return results
    
    def get_exchange_summary(self) -> List[Dict[str, Any]]:
        """获取交易所摘要信息"""
        summary = []
        
        for name, adapter in self.exchanges.items():
            info = adapter.get_info()
            info['is_primary'] = (name == self.primary_exchange)
            summary.append(info)
        
        return summary
    
    def set_primary_exchange(self, name: str) -> bool:
        """设置主交易所"""
        if name in self.exchanges:
            self.primary_exchange = name
            return True
        return False