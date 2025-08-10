import time
import json
from typing import Dict, List, Optional, Any, Callable
from decimal import Decimal
from .base import (
    BaseExchange, ExchangeInfo, ExchangeType, OrderType, OrderSide, OrderStatus,
    Symbol, Ticker, OrderBook, Trade, Kline, Balance, Order, Position
)
from ..gateio.gateio_client import GateIOClient
import logging

logger = logging.getLogger(__name__)


class GateIOExchange(BaseExchange):
    """Gate.io交易所插件"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False, **kwargs):
        super().__init__(api_key, api_secret, testnet, **kwargs)
        self.client: Optional[GateIOClient] = None
        self.timeout = kwargs.get('timeout', 30)
    
    async def connect(self) -> None:
        """连接到Gate.io"""
        self.client = GateIOClient(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=self.testnet,
            timeout=self.timeout
        )
        await self.client.rest.connect()
        logger.info(f"已连接到Gate.io {'测试网' if self.testnet else '主网'}")
    
    async def disconnect(self) -> None:
        """断开连接"""
        if self.client:
            await self.client.close()
            self.client = None
        logger.info("已断开Gate.io连接")
    
    def get_exchange_info(self) -> ExchangeInfo:
        """获取Gate.io交易所信息"""
        return ExchangeInfo(
            name="gateio",
            display_name="Gate.io",
            supported_types=[ExchangeType.SPOT, ExchangeType.FUTURES],
            api_version="v4",
            testnet_available=True,
            rate_limits={
                "spot_public": 900,  # 每分钟900次
                "spot_private": 900,  # 每分钟900次
                "futures_public": 900,  # 每分钟900次
                "futures_private": 900,  # 每分钟900次
            },
            description="Gate.io是全球领先的数字资产交易平台，支持现货和期货交易"
        )
    
    def _ensure_connected(self):
        """确保已连接"""
        if not self.client:
            raise RuntimeError("未连接到Gate.io，请先调用connect()方法")
    
    def _convert_order_type(self, order_type: OrderType) -> str:
        """转换订单类型"""
        mapping = {
            OrderType.MARKET: "market",
            OrderType.LIMIT: "limit",
            OrderType.STOP: "stop",
            OrderType.STOP_LIMIT: "stop_limit"
        }
        return mapping.get(order_type, "limit")
    
    def _convert_order_side(self, side: OrderSide) -> str:
        """转换订单方向"""
        return side.value
    
    def _convert_order_status(self, status: str) -> OrderStatus:
        """转换订单状态"""
        mapping = {
            "open": OrderStatus.OPEN,
            "closed": OrderStatus.FILLED,
            "cancelled": OrderStatus.CANCELLED,
            "pending": OrderStatus.PENDING,
            "rejected": OrderStatus.REJECTED
        }
        return mapping.get(status, OrderStatus.PENDING)
    
    def _parse_symbol_info(self, data: Dict) -> Symbol:
        """解析交易对信息"""
        return Symbol(
            symbol=data.get("id", ""),
            base_asset=data.get("base", ""),
            quote_asset=data.get("quote", ""),
            status=data.get("trade_status", "tradable"),
            min_qty=float(data.get("min_base_amount", "0")),
            max_qty=float(data.get("max_base_amount", "0")),
            step_size=float(data.get("amount_precision", "0.000001")),
            min_price=float(data.get("min_quote_amount", "0")),
            max_price=float(data.get("max_quote_amount", "0")),
            tick_size=float(data.get("precision", "0.000001")),
            min_notional=float(data.get("min_quote_amount", "0"))
        )
    
    def _parse_ticker(self, data: Dict, symbol: str = "") -> Ticker:
        """解析行情数据"""
        return Ticker(
            symbol=symbol or data.get("currency_pair", ""),
            last_price=float(data.get("last", "0")),
            bid_price=float(data.get("highest_bid", "0")),
            ask_price=float(data.get("lowest_ask", "0")),
            bid_qty=0.0,  # Gate.io API不提供
            ask_qty=0.0,  # Gate.io API不提供
            volume_24h=float(data.get("base_volume", "0")),
            change_24h=float(data.get("change_percentage", "0")),
            high_24h=float(data.get("high_24h", "0")),
            low_24h=float(data.get("low_24h", "0")),
            timestamp=int(time.time() * 1000)
        )
    
    def _parse_order_book(self, data: Dict, symbol: str) -> OrderBook:
        """解析订单簿数据"""
        return OrderBook(
            symbol=symbol,
            bids=[[float(bid[0]), float(bid[1])] for bid in data.get("bids", [])],
            asks=[[float(ask[0]), float(ask[1])] for ask in data.get("asks", [])],
            timestamp=int(time.time() * 1000)
        )
    
    def _parse_trade(self, data: Dict, symbol: str = "") -> Trade:
        """解析成交记录"""
        return Trade(
            id=str(data.get("id", "")),
            symbol=symbol or data.get("currency_pair", ""),
            price=float(data.get("price", "0")),
            qty=float(data.get("amount", "0")),
            side=OrderSide.BUY if data.get("side") == "buy" else OrderSide.SELL,
            timestamp=int(data.get("create_time", 0)) * 1000
        )
    
    def _parse_kline(self, data: List, symbol: str) -> Kline:
        """解析K线数据"""
        return Kline(
            symbol=symbol,
            open_time=int(data[0]) * 1000,
            close_time=int(data[0]) * 1000 + 60000,  # 假设1分钟K线
            open_price=float(data[5]),
            high_price=float(data[3]),
            low_price=float(data[4]),
            close_price=float(data[2]),
            volume=float(data[1]),
            quote_volume=float(data[1]) * float(data[2]),
            trades_count=0  # Gate.io API不提供
        )
    
    def _parse_balance(self, data: Dict) -> Balance:
        """解析余额数据"""
        return Balance(
            asset=data.get("currency", ""),
            free=float(data.get("available", "0")),
            locked=float(data.get("locked", "0")),
            total=float(data.get("available", "0")) + float(data.get("locked", "0"))
        )
    
    def _parse_order(self, data: Dict) -> Order:
        """解析订单数据"""
        return Order(
            id=str(data.get("id", "")),
            client_order_id=data.get("text", ""),
            symbol=data.get("currency_pair", ""),
            side=OrderSide.BUY if data.get("side") == "buy" else OrderSide.SELL,
            type=OrderType.LIMIT if data.get("type") == "limit" else OrderType.MARKET,
            qty=float(data.get("amount", "0")),
            price=float(data.get("price", "0")) if data.get("price") else None,
            status=self._convert_order_status(data.get("status", "open")),
            filled_qty=float(data.get("filled_amount", "0")),
            remaining_qty=float(data.get("left", "0")),
            avg_price=float(data.get("avg_deal_price", "0")) if data.get("avg_deal_price") else None,
            create_time=int(data.get("create_time", 0)) * 1000,
            update_time=int(data.get("update_time", 0)) * 1000
        )
    
    def _parse_position(self, data: Dict) -> Position:
        """解析持仓数据"""
        return Position(
            symbol=data.get("contract", ""),
            side="long" if float(data.get("size", "0")) > 0 else "short",
            size=abs(float(data.get("size", "0"))),
            entry_price=float(data.get("entry_price", "0")),
            mark_price=float(data.get("mark_price", "0")),
            unrealized_pnl=float(data.get("unrealised_pnl", "0")),
            realized_pnl=float(data.get("realised_pnl", "0")),
            margin=float(data.get("margin", "0")),
            percentage=float(data.get("unrealised_pnl", "0")) / float(data.get("margin", "1")) * 100,
            timestamp=int(time.time() * 1000)
        )
    
    # 市场数据接口实现
    async def get_symbols(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Symbol]:
        """获取交易对列表"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.get_spot_currency_pairs()
        elif exchange_type == ExchangeType.FUTURES:
            data = await self.client.rest.get_futures_contracts("usdt")
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
        
        return [self._parse_symbol_info(item) for item in data]
    
    async def get_ticker(self, symbol: str, exchange_type: ExchangeType = ExchangeType.SPOT) -> Ticker:
        """获取单个交易对行情"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.get_spot_ticker(symbol)
        elif exchange_type == ExchangeType.FUTURES:
            data = await self.client.rest.get_futures_ticker("usdt", symbol)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
        
        return self._parse_ticker(data, symbol)
    
    async def get_tickers(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Ticker]:
        """获取所有交易对行情"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.get_spot_tickers()
            return [self._parse_ticker(item) for item in data]
        elif exchange_type == ExchangeType.FUTURES:
            data = await self.client.rest.get_futures_tickers("usdt")
            return [self._parse_ticker(item) for item in data]
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
    
    async def get_order_book(self, symbol: str, limit: int = 100, exchange_type: ExchangeType = ExchangeType.SPOT) -> OrderBook:
        """获取订单簿"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.get_spot_order_book(symbol, limit=limit)
        elif exchange_type == ExchangeType.FUTURES:
            data = await self.client.rest.get_futures_order_book("usdt", symbol, limit=limit)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
        
        return self._parse_order_book(data, symbol)
    
    async def get_trades(self, symbol: str, limit: int = 100, exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Trade]:
        """获取成交记录"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.get_spot_trades(symbol, limit=limit)
        elif exchange_type == ExchangeType.FUTURES:
            data = await self.client.rest.get_futures_trades("usdt", symbol, limit=limit)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
        
        return [self._parse_trade(item, symbol) for item in data]
    
    async def get_klines(self, symbol: str, interval: str, limit: int = 100,
                        start_time: Optional[int] = None, end_time: Optional[int] = None,
                        exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Kline]:
        """获取K线数据"""
        self._ensure_connected()
        
        # 转换时间戳（毫秒转秒）
        from_time = start_time // 1000 if start_time else None
        to_time = end_time // 1000 if end_time else None
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.get_spot_candlesticks(
                symbol, interval, limit=limit, from_time=from_time, to_time=to_time
            )
        elif exchange_type == ExchangeType.FUTURES:
            data = await self.client.rest.get_futures_candlesticks(
                "usdt", symbol, interval, limit=limit, from_time=from_time, to_time=to_time
            )
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
        
        return [self._parse_kline(item, symbol) for item in data]
    
    # 账户接口实现
    async def get_account_info(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> Dict[str, Any]:
        """获取账户信息"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            return await self.client.rest.get_spot_accounts()
        elif exchange_type == ExchangeType.FUTURES:
            return await self.client.rest.get_futures_account("usdt")
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
    
    async def get_balances(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Balance]:
        """获取账户余额"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.get_spot_accounts()
            return [self._parse_balance(item) for item in data]
        elif exchange_type == ExchangeType.FUTURES:
            account_info = await self.client.rest.get_futures_account("usdt")
            # 期货账户结构不同，需要特殊处理
            balance_data = {
                "currency": "USDT",
                "available": account_info.get("available", "0"),
                "locked": str(float(account_info.get("total", "0")) - float(account_info.get("available", "0")))
            }
            return [self._parse_balance(balance_data)]
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
    
    # 交易接口实现
    async def create_order(self, symbol: str, side: OrderSide, order_type: OrderType,
                          qty: float, price: Optional[float] = None,
                          client_order_id: Optional[str] = None,
                          exchange_type: ExchangeType = ExchangeType.SPOT,
                          **kwargs) -> Order:
        """创建订单"""
        self._ensure_connected()
        
        order_data = {
            "currency_pair": symbol,
            "side": self._convert_order_side(side),
            "type": self._convert_order_type(order_type),
            "amount": str(qty)
        }
        
        if price is not None:
            order_data["price"] = str(price)
        
        if client_order_id:
            order_data["text"] = client_order_id
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.create_spot_order(**order_data)
        elif exchange_type == ExchangeType.FUTURES:
            order_data["contract"] = symbol
            order_data["settle"] = "usdt"
            del order_data["currency_pair"]
            data = await self.client.rest.create_futures_order(**order_data)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
        
        return self._parse_order(data)
    
    async def cancel_order(self, symbol: str, order_id: str,
                          exchange_type: ExchangeType = ExchangeType.SPOT) -> Order:
        """取消订单"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.cancel_spot_order(order_id, symbol)
        elif exchange_type == ExchangeType.FUTURES:
            data = await self.client.rest.cancel_futures_order("usdt", order_id)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
        
        return self._parse_order(data)
    
    async def get_order(self, symbol: str, order_id: str,
                       exchange_type: ExchangeType = ExchangeType.SPOT) -> Order:
        """获取订单信息"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.get_spot_order(order_id, symbol)
        elif exchange_type == ExchangeType.FUTURES:
            data = await self.client.rest.get_futures_order("usdt", order_id)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
        
        return self._parse_order(data)
    
    async def get_open_orders(self, symbol: Optional[str] = None,
                             exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Order]:
        """获取未成交订单"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.get_spot_open_orders(currency_pair=symbol)
        elif exchange_type == ExchangeType.FUTURES:
            data = await self.client.rest.get_futures_orders("usdt", status="open", contract=symbol)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
        
        return [self._parse_order(item) for item in data]
    
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100,
                               exchange_type: ExchangeType = ExchangeType.SPOT) -> List[Order]:
        """获取历史订单"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            data = await self.client.rest.get_spot_orders(currency_pair=symbol, status="finished", limit=limit)
        elif exchange_type == ExchangeType.FUTURES:
            data = await self.client.rest.get_futures_orders("usdt", status="finished", contract=symbol, limit=limit)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
        
        return [self._parse_order(item) for item in data]
    
    # 期货特有接口
    async def get_positions(self) -> List[Position]:
        """获取持仓信息（期货）"""
        self._ensure_connected()
        data = await self.client.rest.get_futures_positions("usdt")
        return [self._parse_position(item) for item in data]
    
    async def get_position(self, symbol: str) -> Position:
        """获取单个持仓信息（期货）"""
        self._ensure_connected()
        data = await self.client.rest.get_futures_position("usdt", symbol)
        return self._parse_position(data)
    
    # WebSocket接口实现
    async def subscribe_ticker(self, symbol: str, callback: Callable,
                              exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """订阅行情数据"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            await self.client.ws.subscribe_spot_ticker(symbol, callback)
        elif exchange_type == ExchangeType.FUTURES:
            await self.client.ws.subscribe_futures_ticker(symbol, callback)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
    
    async def subscribe_order_book(self, symbol: str, callback: Callable,
                                  exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """订阅订单簿数据"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            await self.client.ws.subscribe_spot_order_book(symbol, "1000ms", 20, callback)
        elif exchange_type == ExchangeType.FUTURES:
            await self.client.ws.subscribe_futures_order_book(symbol, "1000ms", 20, callback)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
    
    async def subscribe_trades(self, symbol: str, callback: Callable,
                              exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """订阅成交数据"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            await self.client.ws.subscribe_spot_trades(symbol, callback)
        elif exchange_type == ExchangeType.FUTURES:
            await self.client.ws.subscribe_futures_trades(symbol, callback)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
    
    async def subscribe_orders(self, callback: Callable,
                              exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """订阅订单更新"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            await self.client.ws.subscribe_spot_orders([], callback)
        elif exchange_type == ExchangeType.FUTURES:
            await self.client.ws.subscribe_futures_orders([], callback)
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
    
    async def start_websocket(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """启动WebSocket连接"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            await self.client.ws.start_spot()
        elif exchange_type == ExchangeType.FUTURES:
            await self.client.ws.start_futures()
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")
    
    async def stop_websocket(self, exchange_type: ExchangeType = ExchangeType.SPOT) -> None:
        """停止WebSocket连接"""
        self._ensure_connected()
        
        if exchange_type == ExchangeType.SPOT:
            await self.client.ws.stop_spot()
        elif exchange_type == ExchangeType.FUTURES:
            await self.client.ws.stop_futures()
        else:
            raise ValueError(f"不支持的交易类型: {exchange_type}")