"""
Kraken交易所客户端 - 只读适配器（行情/订单簿/K线）
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


class KrakenExchange(ExchangeBase):
    """Kraken交易所客户端（只读）"""

    def __init__(self, config: Dict[str, Any]):
        """初始化客户端"""
        super().__init__(config)
        self.base_url = config.get("base_url", "https://api.kraken.com")
        self.stream_url = config.get("stream_url", "wss://ws.kraken.com")
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

    def _map_symbol(self, symbol: str) -> str:
        """转换通用交易对到Kraken的pair标识"""
        base = symbol[:-4]
        quote = symbol[-4:]
        if base.upper() == "BTC":
            base = "XBT"
        return f"{base}{quote}".upper()

    def _map_interval(self, interval: str) -> int:
        """时间粒度转换到Kraken分钟制"""
        mapping = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
            "1w": 10080,
        }
        return mapping.get(interval, 60)

    async def get_ticker(self, symbol: str) -> Ticker:
        """获取现货24小时行情"""
        pair = self._map_symbol(symbol)
        data = await self._request("GET", "/0/public/Ticker", {"pair": pair})
        result = data.get("result", {})
        # Kraken返回的键名不固定，取第一个键
        key = next(iter(result.keys()), pair)
        item = result.get(key, {})
        now = datetime.now()
        return Ticker(
            symbol=symbol,
            last_price=float((item.get("c") or [0])[0] or 0),
            bid_price=float((item.get("b") or [0])[0] or 0),
            ask_price=float((item.get("a") or [0])[0] or 0),
            bid_volume=0.0,
            ask_volume=0.0,
            volume_24h=float((item.get("v") or [0])[1] or 0),
            high_24h=float((item.get("h") or [0])[1] or 0),
            low_24h=float((item.get("l") or [0])[1] or 0),
            price_change_24h=0.0,
            price_change_percent_24h=0.0,
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
        """获取现货OHLC数据"""
        pair = self._map_symbol(symbol)
        params: Dict[str, Any] = {"pair": pair, "interval": self._map_interval(interval)}
        if start_time:
            params["since"] = int(start_time.timestamp())
        data = await self._request("GET", "/0/public/OHLC", params)
        result = data.get("result", {})
        key = next((k for k in result.keys() if k != "last"), pair)
        rows = result.get(key, [])
        klines: List[Kline] = []
        for item in rows[:limit]:
            # Kraken: [time, open, high, low, close, vwap, volume, count]
            ot = datetime.fromtimestamp(item[0])
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
                    volume=float(item[6]),
                    quote_volume=float(item[5]),
                    trades_count=int(item[7]),
                    taker_buy_volume=0.0,
                    taker_buy_quote_volume=0.0,
                )
            )
        return klines

    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """获取订单簿快照"""
        pair = self._map_symbol(symbol)
        data = await self._request("GET", "/0/public/Depth", {"pair": pair, "count": min(limit, 200)})
        return data.get("result", {})

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
        data = await self._request("GET", "/0/public/Time")
        ts = int(data.get("result", {}).get("unixtime", 0))
        return datetime.fromtimestamp(ts)

    async def get_symbols(self) -> List[Dict[str, Any]]:
        """获取现货交易对列表"""
        data = await self._request("GET", "/0/public/AssetPairs")
        result = data.get("result", {})
        symbols: List[Dict[str, Any]] = []
        for _, it in result.items():
            symbols.append(
                {
                    "symbol": it.get("altname"),
                    "base_asset": it.get("base"),
                    "quote_asset": it.get("quote"),
                    "status": "TRADING",
                }
            )
        return symbols

    async def get_exchange_info(self) -> Dict[str, Any]:
        """获取交易所信息（近似返回支持交易对）"""
        return {"name": "Kraken", "type": "spot", "symbols": await self.get_symbols()}

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