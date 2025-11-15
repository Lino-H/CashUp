"""
Bybit交易所客户端 - 只读适配器（行情/订单簿/K线）
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any

from .base import (
    ExchangeBase,
    Ticker,
    Kline,
    Balance,
    Order,
    Trade,
    OrderRequest,
    CancelOrderRequest,
    OrderStatus,
    Position,
    FundingRate,
)


class BybitExchange(ExchangeBase):
    """Bybit交易所客户端（只读）"""

    def __init__(self, config: Dict[str, Any]):
        """初始化客户端"""
        super().__init__(config)
        self.base_url = config.get("base_url", "https://api.bybit.com")
        self.stream_url = config.get("stream_url", "wss://stream.bybit.com")
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = asyncio.Semaphore(self.rate_limit)

    async def __aenter__(self):
        """进入异步上下文"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出异步上下文"""
        if self.session:
            await self.session.close()

    async def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送HTTP请求"""
        async with self.rate_limiter:
            url = f"{self.base_url}{endpoint}"
            params = params or {}
            headers = {}
            if not self.session:
                self.session = aiohttp.ClientSession()
            if method == "GET":
                async with self.session.get(url, params=params, headers=headers) as resp:
                    return await resp.json()
            elif method == "POST":
                async with self.session.post(url, json=params, headers=headers) as resp:
                    return await resp.json()
            else:
                async with self.session.request(method, url, json=params, headers=headers) as resp:
                    return await resp.json()

    def _map_interval(self, interval: str) -> str:
        """时间粒度转换到Bybit格式"""
        mapping = {
            "1m": "1",
            "3m": "3",
            "5m": "5",
            "15m": "15",
            "30m": "30",
            "1h": "60",
            "2h": "120",
            "4h": "240",
            "6h": "360",
            "12h": "720",
            "1d": "D",
            "1w": "W",
            "1M": "M",
        }
        return mapping.get(interval, "60")

    async def get_ticker(self, symbol: str) -> Ticker:
        """获取现货24小时行情"""
        data = await self._request(
            "GET",
            "/v5/market/tickers",
            {"category": "spot", "symbol": symbol},
        )
        item = (data.get("result", {}).get("list", []) or [{}])[0]
        now = datetime.now()
        return Ticker(
            symbol=item.get("symbol", symbol),
            last_price=float(item.get("lastPrice", 0) or 0),
            bid_price=float(item.get("bid1Price", 0) or 0),
            ask_price=float(item.get("ask1Price", 0) or 0),
            bid_volume=float(item.get("bid1Size", 0) or 0),
            ask_volume=float(item.get("ask1Size", 0) or 0),
            volume_24h=float(item.get("turnover24h", 0) or 0),
            high_24h=float(item.get("highPrice24h", 0) or 0),
            low_24h=float(item.get("lowPrice24h", 0) or 0),
            price_change_24h=float(item.get("priceChange24h", 0) or 0),
            price_change_percent_24h=float(item.get("priceChangeRate24h", 0) or 0),
            timestamp=now,
        )

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Kline]:
        """获取现货K线数据"""
        params: Dict[str, Any] = {
            "category": "spot",
            "symbol": symbol,
            "interval": self._map_interval(interval),
            "limit": min(limit, 1000),
        }
        if start_time:
            params["start"] = int(start_time.timestamp() * 1000)
        if end_time:
            params["end"] = int(end_time.timestamp() * 1000)
        data = await self._request("GET", "/v5/market/kline", params)
        rows = data.get("result", {}).get("list", []) or []
        klines: List[Kline] = []
        for item in rows:
            # Bybit返回数组: [start, open, high, low, close, volume, turnover]
            ot = datetime.fromtimestamp(int(item[0]) / 1000)
            # Bybit没有显式close_time，使用开时间加一个interval近似
            ct = ot
            klines.append(
                Kline(
                    symbol=symbol,
                    interval=interval,
                    open_time=ot,
                    close_time=ct,
                    open_price=float(item[1]),
                    high_price=float(item[2]),
                    low_price=float(item[3]),
                    close_price=float(item[4]),
                    volume=float(item[5]),
                    quote_volume=float(item[6]) if len(item) > 6 else 0.0,
                    trades_count=0,
                    taker_buy_volume=0.0,
                    taker_buy_quote_volume=0.0,
                )
            )
        return klines

    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """获取订单簿快照"""
        params = {"category": "spot", "symbol": symbol, "limit": min(limit, 200)}
        return await self._request("GET", "/v5/market/orderbook", params)

    async def get_balance(self) -> Dict[str, Balance]:
        """账户余额（未实现）"""
        pass

    async def get_orders(self, symbol: Optional[str] = None, status: Optional[OrderStatus] = None) -> List[Order]:
        """订单列表（未实现）"""
        pass

    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """单个订单（未实现）"""
        pass

    async def get_trades(
        self,
        symbol: str,
        order_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Trade]:
        """成交列表（未实现）"""
        pass

    async def place_order(self, request: OrderRequest) -> Order:
        """下单（未实现）"""
        pass

    async def cancel_order(self, request: CancelOrderRequest) -> bool:
        """取消订单（未实现）"""
        pass

    async def cancel_all_orders(self, symbol: str) -> List[Order]:
        """取消所有订单（未实现）"""
        pass

    async def get_server_time(self) -> datetime:
        """获取服务器时间"""
        data = await self._request("GET", "/v3/public/time")
        ts = float(data.get("timeNow", "0"))
        # timeNow为秒或毫秒字符串，做兼容处理
        if ts > 1e12:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts)

    async def get_symbols(self) -> List[Dict[str, Any]]:
        """获取现货交易对列表"""
        data = await self._request("GET", "/v5/market/instruments-info", {"category": "spot"})
        items = data.get("result", {}).get("list", []) or []
        symbols: List[Dict[str, Any]] = []
        for it in items:
            symbols.append(
                {
                    "symbol": it.get("symbol"),
                    "base_asset": it.get("baseCoin"),
                    "quote_asset": it.get("quoteCoin"),
                    "status": it.get("status", "TRADING"),
                }
            )
        return symbols

    async def get_exchange_info(self) -> Dict[str, Any]:
        """获取交易所信息（近似返回支持交易对）"""
        return {"name": "Bybit", "type": "spot", "symbols": await self.get_symbols()}

    async def get_futures_balance(self) -> Dict[str, Balance]:
        """永续合约余额（未实现）"""
        pass

    async def get_futures_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """永续持仓（未实现）"""
        pass

    async def get_funding_rate(self, symbol: str) -> FundingRate:
        """资金费率（未实现）"""
        pass

    async def get_funding_rate_history(
        self,
        symbol: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[FundingRate]:
        """资金费率历史（未实现）"""
        return []

    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """设置杠杆（未实现）"""
        pass

    async def get_leverage(self, symbol: str) -> int:
        """获取杠杆（未实现）"""
        pass

    async def subscribe_ticker(self, symbol: str, callback):
        """订阅行情（未实现）"""
        pass

    async def subscribe_kline(self, symbol: str, interval: str, callback):
        """订阅K线（未实现）"""
        pass

    async def subscribe_order_book(self, symbol: str, callback):
        """订阅订单簿（未实现）"""
        pass

    async def subscribe_trades(self, symbol: str, callback):
        """订阅成交（未实现）"""
        pass

    async def subscribe_user_data(self, callback):
        """订阅用户数据（未实现）"""
        pass

    async def subscribe_funding_rate(self, symbol: str, callback):
        """订阅资金费率（未实现）"""
        pass

    async def subscribe_mark_price(self, symbol: str, callback):
        """订阅标记价格（未实现）"""
        pass

    async def subscribe_liquidation_orders(self, callback):
        """订阅强平（未实现）"""
        pass