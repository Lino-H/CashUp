#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - Gate.io交易所服务

提供Gate.io交易所的统一业务接口
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Callable

from shared.gateio import GateIOClient
from ..core.config import settings

logger = logging.getLogger(__name__)


class GateIOExchangeService:
    """
    Gate.io交易所服务
    
    提供统一的交易所业务接口，包括市场数据、交易执行、账户管理等功能
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: bool = False
    ):
        """
        初始化Gate.io交易所服务
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网
        """
        self.api_key = api_key or settings.GATEIO_API_KEY
        self.api_secret = api_secret or settings.GATEIO_API_SECRET
        self.testnet = testnet or settings.GATEIO_TESTNET
        
        # Gate.io客户端
        self.client: Optional[GateIOClient] = None
        
        # 市场数据缓存
        self.market_data_cache: Dict[str, Any] = {}
        
        # WebSocket回调函数
        self.ws_callbacks: Dict[str, List[Callable]] = {
            "ticker": [],
            "trades": [],
            "order_book": [],
            "orders": [],
            "positions": []
        }
    
    async def initialize(self):
        """
        初始化服务
        """
        try:
            self.client = GateIOClient(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=self.testnet
            )
            
            await self.client.__aenter__()
            
            logger.info("Gate.io交易所服务初始化完成")
            
        except Exception as e:
            logger.error(f"Gate.io交易所服务初始化失败: {e}")
            raise
    
    async def close(self):
        """
        关闭服务
        """
        if self.client:
            await self.client.close()
            self.client = None
        
        logger.info("Gate.io交易所服务已关闭")
    
    # ==================== 市场数据接口 ====================
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """
        获取交易所信息
        
        Returns:
            交易所基本信息
        """
        try:
            # 获取现货交易对
            spot_pairs = await self.client.rest.get_spot_currency_pairs()
            
            # 获取期货合约
            futures_contracts = await self.client.rest.get_futures_contracts()
            
            return {
                "exchange": "gateio",
                "spot_pairs": len(spot_pairs),
                "futures_contracts": len(futures_contracts),
                "spot_trading_pairs": [pair["id"] for pair in spot_pairs[:10]],  # 前10个
                "futures_contracts_list": [contract["name"] for contract in futures_contracts[:10]],  # 前10个
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取交易所信息失败: {e}")
            raise
    
    async def get_spot_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取现货行情数据
        
        Args:
            symbol: 交易对符号，如 BTC_USDT
            
        Returns:
            行情数据
        """
        try:
            ticker_data = await self.client.rest.get_spot_ticker(symbol)
            
            if ticker_data:
                ticker = ticker_data[0] if isinstance(ticker_data, list) else ticker_data
                
                return {
                    "symbol": symbol,
                    "price": float(ticker.get("last", 0)),
                    "bid_price": float(ticker.get("highest_bid", 0)),
                    "ask_price": float(ticker.get("lowest_ask", 0)),
                    "volume_24h": float(ticker.get("base_volume", 0)),
                    "quote_volume_24h": float(ticker.get("quote_volume", 0)),
                    "price_change_24h": float(ticker.get("change_percentage", 0)),
                    "high_24h": float(ticker.get("high_24h", 0)),
                    "low_24h": float(ticker.get("low_24h", 0)),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"获取现货行情失败 {symbol}: {e}")
            raise
    
    async def get_futures_ticker(self, symbol: str, settle: str = "usdt") -> Dict[str, Any]:
        """
        获取期货行情数据
        
        Args:
            symbol: 合约符号，如 BTC_USDT
            settle: 结算货币
            
        Returns:
            行情数据
        """
        try:
            ticker_data = await self.client.rest.get_futures_tickers(settle, symbol)
            
            if ticker_data:
                ticker = ticker_data[0] if isinstance(ticker_data, list) else ticker_data
                
                return {
                    "symbol": symbol,
                    "price": float(ticker.get("last", 0)),
                    "mark_price": float(ticker.get("mark_price", 0)),
                    "index_price": float(ticker.get("index_price", 0)),
                    "funding_rate": float(ticker.get("funding_rate", 0)),
                    "volume_24h": float(ticker.get("volume_24h", 0)),
                    "price_change_24h": float(ticker.get("change_percentage", 0)),
                    "high_24h": float(ticker.get("high_24h", 0)),
                    "low_24h": float(ticker.get("low_24h", 0)),
                    "open_interest": float(ticker.get("total_size", 0)),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"获取期货行情失败 {symbol}: {e}")
            raise
    
    async def get_order_book(self, symbol: str, market_type: str = "spot", limit: int = 20) -> Dict[str, Any]:
        """
        获取订单簿数据
        
        Args:
            symbol: 交易对/合约符号
            market_type: 市场类型 (spot/futures)
            limit: 深度限制
            
        Returns:
            订单簿数据
        """
        try:
            if market_type == "spot":
                order_book = await self.client.rest.get_spot_order_book(symbol, limit)
            else:
                order_book = await self.client.rest.get_futures_order_book("usdt", symbol, "0", limit)
            
            return {
                "symbol": symbol,
                "market_type": market_type,
                "bids": [[float(bid["price"]), float(bid["amount"])] for bid in order_book.get("bids", [])],
                "asks": [[float(ask["price"]), float(ask["amount"])] for ask in order_book.get("asks", [])],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取订单簿失败 {symbol}: {e}")
            raise
    
    async def get_recent_trades(self, symbol: str, market_type: str = "spot", limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取最近成交记录
        
        Args:
            symbol: 交易对/合约符号
            market_type: 市场类型 (spot/futures)
            limit: 记录数量限制
            
        Returns:
            成交记录列表
        """
        try:
            if market_type == "spot":
                trades = await self.client.rest.get_spot_trades(symbol, limit)
            else:
                trades = await self.client.rest.get_futures_trades("usdt", symbol, limit)
            
            return [
                {
                    "id": trade.get("id"),
                    "price": float(trade.get("price", 0)),
                    "amount": float(trade.get("amount", 0)),
                    "side": "buy" if float(trade.get("amount", 0)) > 0 else "sell",
                    "timestamp": trade.get("create_time_ms", trade.get("create_time", 0))
                }
                for trade in trades
            ]
            
        except Exception as e:
            logger.error(f"获取成交记录失败 {symbol}: {e}")
            raise
    
    async def get_klines(
        self,
        symbol: str,
        interval: str = "1m",
        market_type: str = "spot",
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对/合约符号
            interval: 时间间隔
            market_type: 市场类型 (spot/futures)
            limit: 数量限制
            start_time: 开始时间戳
            end_time: 结束时间戳
            
        Returns:
            K线数据列表
        """
        try:
            if market_type == "spot":
                klines = await self.client.rest.get_spot_candlesticks(
                    symbol, interval, limit, start_time, end_time
                )
            else:
                klines = await self.client.rest.get_futures_candlesticks(
                    "usdt", symbol, interval, limit, start_time, end_time
                )
            
            return [
                {
                    "timestamp": int(kline[0]),
                    "open": float(kline[5]),
                    "high": float(kline[3]),
                    "low": float(kline[4]),
                    "close": float(kline[2]),
                    "volume": float(kline[1]),
                    "quote_volume": float(kline[6]) if len(kline) > 6 else 0
                }
                for kline in klines
            ]
            
        except Exception as e:
            logger.error(f"获取K线数据失败 {symbol}: {e}")
            raise
    
    # ==================== 账户管理接口 ====================
    
    async def get_account_balance(self, market_type: str = "spot") -> Dict[str, Any]:
        """
        获取账户余额
        
        Args:
            market_type: 市场类型 (spot/futures)
            
        Returns:
            账户余额信息
        """
        try:
            if market_type == "spot":
                balances = await self.client.rest.get_spot_accounts()
                
                return {
                    "market_type": "spot",
                    "balances": [
                        {
                            "currency": balance.get("currency"),
                            "available": float(balance.get("available", 0)),
                            "locked": float(balance.get("locked", 0)),
                            "total": float(balance.get("available", 0)) + float(balance.get("locked", 0))
                        }
                        for balance in balances
                        if float(balance.get("available", 0)) > 0 or float(balance.get("locked", 0)) > 0
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                account = await self.client.rest.get_futures_accounts()
                
                return {
                    "market_type": "futures",
                    "total_balance": float(account.get("total", 0)),
                    "available_balance": float(account.get("available", 0)),
                    "position_margin": float(account.get("position_margin", 0)),
                    "order_margin": float(account.get("order_margin", 0)),
                    "unrealized_pnl": float(account.get("unrealised_pnl", 0)),
                    "currency": account.get("currency", "USDT"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"获取账户余额失败: {e}")
            raise
    
    async def get_positions(self, settle: str = "usdt") -> List[Dict[str, Any]]:
        """
        获取期货持仓信息
        
        Args:
            settle: 结算货币
            
        Returns:
            持仓信息列表
        """
        try:
            positions = await self.client.rest.get_futures_positions(settle)
            
            return [
                {
                    "contract": position.get("contract"),
                    "size": float(position.get("size", 0)),
                    "margin": float(position.get("margin", 0)),
                    "entry_price": float(position.get("entry_price", 0)),
                    "mark_price": float(position.get("mark_price", 0)),
                    "unrealized_pnl": float(position.get("unrealised_pnl", 0)),
                    "realized_pnl": float(position.get("realised_pnl", 0)),
                    "leverage": float(position.get("leverage", 0)),
                    "risk_limit": float(position.get("risk_limit", 0)),
                    "mode": position.get("mode"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                for position in positions
                if float(position.get("size", 0)) != 0
            ]
            
        except Exception as e:
            logger.error(f"获取持仓信息失败: {e}")
            raise
    
    # ==================== 交易执行接口 ====================
    
    async def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None,
        market_type: str = "spot",
        time_in_force: str = "gtc",
        reduce_only: bool = False,
        post_only: bool = False,
        client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建订单
        
        Args:
            symbol: 交易对/合约符号
            side: 买卖方向 (buy/sell)
            order_type: 订单类型 (limit/market)
            amount: 数量
            price: 价格（限价单必填）
            market_type: 市场类型 (spot/futures)
            time_in_force: 时效性
            reduce_only: 只减仓（期货）
            post_only: 只做maker
            client_order_id: 客户端订单ID
            
        Returns:
            订单信息
        """
        try:
            if market_type == "spot":
                # 现货订单
                order = await self.client.rest.create_spot_order(
                    currency_pair=symbol,
                    side=side,
                    amount=str(amount),
                    price=str(price) if price else None,
                    type_=order_type,
                    time_in_force=time_in_force,
                    text=client_order_id
                )
            else:
                # 期货订单
                size = int(amount) if side == "buy" else -int(amount)
                
                order = await self.client.rest.create_futures_order(
                    settle="usdt",
                    contract=symbol,
                    size=size,
                    price=str(price) if price else None,
                    tif=time_in_force,
                    reduce_only=reduce_only,
                    text=client_order_id
                )
            
            return {
                "order_id": order.get("id"),
                "client_order_id": order.get("text"),
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "amount": float(order.get("amount", amount)),
                "price": float(order.get("price", price or 0)),
                "status": order.get("status"),
                "filled_amount": float(order.get("filled_total", 0)),
                "remaining_amount": float(order.get("left", 0)),
                "create_time": order.get("create_time_ms", order.get("create_time")),
                "market_type": market_type
            }
            
        except Exception as e:
            logger.error(f"创建订单失败 {symbol}: {e}")
            raise
    
    async def cancel_order(
        self,
        order_id: str,
        symbol: str,
        market_type: str = "spot"
    ) -> Dict[str, Any]:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            symbol: 交易对/合约符号
            market_type: 市场类型 (spot/futures)
            
        Returns:
            取消结果
        """
        try:
            if market_type == "spot":
                result = await self.client.rest.cancel_spot_order(order_id, symbol)
            else:
                result = await self.client.rest.cancel_futures_order("usdt", order_id)
            
            return {
                "order_id": result.get("id"),
                "symbol": symbol,
                "status": result.get("status"),
                "market_type": market_type,
                "cancelled_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"取消订单失败 {order_id}: {e}")
            raise
    
    async def get_order(
        self,
        order_id: str,
        symbol: str,
        market_type: str = "spot"
    ) -> Dict[str, Any]:
        """
        获取订单详情
        
        Args:
            order_id: 订单ID
            symbol: 交易对/合约符号
            market_type: 市场类型 (spot/futures)
            
        Returns:
            订单详情
        """
        try:
            if market_type == "spot":
                order = await self.client.rest.get_spot_order(order_id, symbol)
            else:
                order = await self.client.rest.get_futures_order("usdt", order_id)
            
            return {
                "order_id": order.get("id"),
                "client_order_id": order.get("text"),
                "symbol": order.get("currency_pair", order.get("contract")),
                "side": order.get("side"),
                "type": order.get("type"),
                "amount": float(order.get("amount", 0)),
                "price": float(order.get("price", 0)),
                "status": order.get("status"),
                "filled_amount": float(order.get("filled_total", 0)),
                "remaining_amount": float(order.get("left", 0)),
                "average_price": float(order.get("avg_deal_price", 0)),
                "create_time": order.get("create_time_ms", order.get("create_time")),
                "update_time": order.get("update_time_ms", order.get("update_time")),
                "market_type": market_type
            }
            
        except Exception as e:
            logger.error(f"获取订单详情失败 {order_id}: {e}")
            raise
    
    async def get_orders(
        self,
        symbol: str,
        status: str = "open",
        market_type: str = "spot",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取订单列表
        
        Args:
            symbol: 交易对/合约符号
            status: 订单状态
            market_type: 市场类型 (spot/futures)
            limit: 数量限制
            
        Returns:
            订单列表
        """
        try:
            if market_type == "spot":
                orders = await self.client.rest.get_spot_orders(symbol, status, 1, limit)
            else:
                orders = await self.client.rest.get_futures_orders("usdt", symbol, status, limit)
            
            return [
                {
                    "order_id": order.get("id"),
                    "client_order_id": order.get("text"),
                    "symbol": order.get("currency_pair", order.get("contract")),
                    "side": order.get("side"),
                    "type": order.get("type"),
                    "amount": float(order.get("amount", 0)),
                    "price": float(order.get("price", 0)),
                    "status": order.get("status"),
                    "filled_amount": float(order.get("filled_total", 0)),
                    "remaining_amount": float(order.get("left", 0)),
                    "create_time": order.get("create_time_ms", order.get("create_time")),
                    "market_type": market_type
                }
                for order in orders
            ]
            
        except Exception as e:
            logger.error(f"获取订单列表失败 {symbol}: {e}")
            raise
    
    # ==================== WebSocket实时数据接口 ====================
    
    def add_ticker_callback(self, callback: Callable):
        """添加行情数据回调函数"""
        self.ws_callbacks["ticker"].append(callback)
    
    def add_trades_callback(self, callback: Callable):
        """添加成交数据回调函数"""
        self.ws_callbacks["trades"].append(callback)
    
    def add_order_book_callback(self, callback: Callable):
        """添加订单簿数据回调函数"""
        self.ws_callbacks["order_book"].append(callback)
    
    def add_orders_callback(self, callback: Callable):
        """添加订单更新回调函数"""
        self.ws_callbacks["orders"].append(callback)
    
    async def _handle_ticker_update(self, data: Dict[str, Any]):
        """处理行情更新"""
        for callback in self.ws_callbacks["ticker"]:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"行情回调函数执行失败: {e}")
    
    async def _handle_trades_update(self, data: Dict[str, Any]):
        """处理成交更新"""
        for callback in self.ws_callbacks["trades"]:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"成交回调函数执行失败: {e}")
    
    async def _handle_order_book_update(self, data: Dict[str, Any]):
        """处理订单簿更新"""
        for callback in self.ws_callbacks["order_book"]:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"订单簿回调函数执行失败: {e}")
    
    async def _handle_orders_update(self, data: Dict[str, Any]):
        """处理订单更新"""
        for callback in self.ws_callbacks["orders"]:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"订单回调函数执行失败: {e}")
    
    async def start_ticker_stream(self, symbols: List[str], market_type: str = "spot"):
        """
        启动行情数据流
        
        Args:
            symbols: 交易对/合约符号列表
            market_type: 市场类型 (spot/futures)
        """
        try:
            if market_type == "spot":
                await self.client.ws.start_spot()
                for symbol in symbols:
                    await self.client.ws.subscribe_spot_ticker(symbol, self._handle_ticker_update)
            else:
                await self.client.ws.start_futures()
                for symbol in symbols:
                    await self.client.ws.subscribe_futures_ticker(symbol, self._handle_ticker_update)
            
            logger.info(f"已启动{market_type}行情数据流: {symbols}")
            
        except Exception as e:
            logger.error(f"启动行情数据流失败: {e}")
            raise
    
    async def start_trades_stream(self, symbols: List[str], market_type: str = "spot"):
        """
        启动成交数据流
        
        Args:
            symbols: 交易对/合约符号列表
            market_type: 市场类型 (spot/futures)
        """
        try:
            if market_type == "spot":
                await self.client.ws.start_spot()
                for symbol in symbols:
                    await self.client.ws.subscribe_spot_trades(symbol, self._handle_trades_update)
            else:
                await self.client.ws.start_futures()
                for symbol in symbols:
                    await self.client.ws.subscribe_futures_trades(symbol, self._handle_trades_update)
            
            logger.info(f"已启动{market_type}成交数据流: {symbols}")
            
        except Exception as e:
            logger.error(f"启动成交数据流失败: {e}")
            raise
    
    async def start_order_book_stream(
        self,
        symbols: List[str],
        market_type: str = "spot",
        interval: str = "100ms",
        limit: int = 20
    ):
        """
        启动订单簿数据流
        
        Args:
            symbols: 交易对/合约符号列表
            market_type: 市场类型 (spot/futures)
            interval: 更新间隔
            limit: 深度限制
        """
        try:
            if market_type == "spot":
                await self.client.ws.start_spot()
                for symbol in symbols:
                    await self.client.ws.subscribe_spot_order_book(
                        symbol, interval, limit, self._handle_order_book_update
                    )
            else:
                await self.client.ws.start_futures()
                for symbol in symbols:
                    await self.client.ws.subscribe_futures_order_book(
                        symbol, interval, limit, self._handle_order_book_update
                    )
            
            logger.info(f"已启动{market_type}订单簿数据流: {symbols}")
            
        except Exception as e:
            logger.error(f"启动订单簿数据流失败: {e}")
            raise
    
    async def start_orders_stream(self, symbols: List[str], market_type: str = "spot"):
        """
        启动订单更新数据流（需要认证）
        
        Args:
            symbols: 交易对/合约符号列表
            market_type: 市场类型 (spot/futures)
        """
        try:
            if market_type == "spot":
                await self.client.ws.start_spot()
                await self.client.ws.subscribe_spot_orders(symbols, self._handle_orders_update)
            else:
                await self.client.ws.start_futures()
                await self.client.ws.subscribe_futures_orders(symbols, self._handle_orders_update)
            
            logger.info(f"已启动{market_type}订单更新数据流: {symbols}")
            
        except Exception as e:
            logger.error(f"启动订单更新数据流失败: {e}")
            raise


# 全局Gate.io交易所服务实例
gateio_service: Optional[GateIOExchangeService] = None


async def get_gateio_service() -> GateIOExchangeService:
    """
    获取Gate.io交易所服务实例
    
    Returns:
        Gate.io交易所服务实例
    """
    global gateio_service
    
    if not gateio_service:
        gateio_service = GateIOExchangeService()
        await gateio_service.initialize()
    
    return gateio_service


async def close_gateio_service():
    """
    关闭Gate.io交易所服务
    """
    global gateio_service
    
    if gateio_service:
        await gateio_service.close()
        gateio_service = None