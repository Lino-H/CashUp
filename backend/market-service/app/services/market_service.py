#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 市场数据服务

提供统一的市场数据接口，包括行情、K线、订单簿等数据
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable

import numpy as np
import pandas as pd

from ..core.config import settings
from ..core.redis import get_redis
from shared.gateio import GateIOClient

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    市场数据服务
    
    提供统一的市场数据接口，支持多交易所数据聚合
    """
    
    def __init__(self):
        """
        初始化市场数据服务
        """
        self.gateio_client: Optional[GateIOClient] = None
        self.redis_manager = None
        
        # 数据缓存键前缀
        self.cache_prefix = "market_data"
        
        # 支持的交易对
        self.supported_pairs: Dict[str, List[str]] = {
            "spot": [],
            "futures": []
        }
        
        # WebSocket回调函数
        self.ws_callbacks: Dict[str, List[Callable]] = {
            "spot_ticker": [],
            "spot_trades": [],
            "spot_order_book": [],
            "futures_ticker": [],
            "futures_trades": [],
            "futures_order_book": []
        }
    
    async def initialize(self):
        """
        初始化服务
        """
        try:
            # 初始化Redis连接
            self.redis_manager = await get_redis()
            
            # 初始化Gate.io客户端
            self.gateio_client = GateIOClient(
                api_key=settings.GATEIO_API_KEY,
                api_secret=settings.GATEIO_API_SECRET,
                testnet=settings.GATEIO_TESTNET,
                timeout=settings.GATEIO_TIMEOUT
            )
            
            await self.gateio_client.rest_client.connect()
            
            # 获取支持的交易对
            await self._load_supported_pairs()
            
            # 启动WebSocket连接
            await self._start_websocket_streams()
            
            logger.info("市场数据服务初始化完成")
            
        except Exception as e:
            logger.error(f"市场数据服务初始化失败: {e}")
            raise
    
    async def close(self):
        """
        关闭服务
        """
        if self.gateio_client:
            await self.gateio_client.close()
        logger.info("市场数据服务已关闭")
    
    async def _load_supported_pairs(self):
        """
        加载支持的交易对
        """
        try:
            # 获取现货交易对
            spot_pairs = await self.gateio_client.rest.get_spot_currency_pairs()
            self.supported_pairs["spot"] = [pair["id"] for pair in spot_pairs if pair["trade_status"] == "tradable"]
            
            # 获取期货合约
            futures_contracts = await self.gateio_client.rest.get_futures_contracts()
            self.supported_pairs["futures"] = [contract["name"] for contract in futures_contracts if contract["type"] == "direct"]
            
            # 缓存到Redis
            await self.redis_manager.set(
                f"{self.cache_prefix}:supported_pairs",
                json.dumps(self.supported_pairs),
                ttl=3600  # 1小时过期
            )
            
            logger.info(f"已加载 {len(self.supported_pairs['spot'])} 个现货交易对，{len(self.supported_pairs['futures'])} 个期货合约")
            
        except Exception as e:
            logger.error(f"加载支持的交易对失败: {e}")
            raise
    
    async def _start_websocket_streams(self):
        """
        启动WebSocket数据流
        """
        try:
            # 启动现货和期货WebSocket
            await self.gateio_client.ws.start_spot()
            await self.gateio_client.ws.start_futures()
            
            # 订阅主要交易对的数据流
            await self._subscribe_major_pairs()
            
            logger.info("WebSocket数据流已启动")
            
        except Exception as e:
            logger.error(f"启动WebSocket数据流失败: {e}")
            raise
    
    async def _subscribe_major_pairs(self):
        """
        订阅主要交易对的数据流
        """
        # 主要现货交易对
        major_spot_pairs = ["BTC_USDT", "ETH_USDT", "BNB_USDT", "ADA_USDT", "SOL_USDT"]
        
        # 主要期货合约
        major_futures_contracts = ["BTC_USDT", "ETH_USDT", "BNB_USDT", "ADA_USDT", "SOL_USDT"]
        
        # 订阅现货数据
        for pair in major_spot_pairs:
            if pair in self.supported_pairs["spot"]:
                await self.gateio_client.ws.subscribe_spot_ticker(pair, self._handle_spot_ticker)
                await self.gateio_client.ws.subscribe_spot_trades(pair, self._handle_spot_trades)
                await self.gateio_client.ws.subscribe_spot_order_book(pair, "100ms", 20, self._handle_spot_order_book)
        
        # 订阅期货数据
        for contract in major_futures_contracts:
            if contract in self.supported_pairs["futures"]:
                await self.gateio_client.ws.subscribe_futures_ticker(contract, self._handle_futures_ticker)
                await self.gateio_client.ws.subscribe_futures_trades(contract, self._handle_futures_trades)
                await self.gateio_client.ws.subscribe_futures_order_book(contract, "100ms", 20, self._handle_futures_order_book)
    
    # ==================== WebSocket消息处理 ====================
    
    async def _handle_spot_ticker(self, data: Dict[str, Any]):
        """
        处理现货行情数据
        """
        try:
            result = data.get("result")
            if result:
                symbol = result.get("currency_pair")
                
                # 缓存到Redis
                cache_key = f"{self.cache_prefix}:spot:ticker:{symbol}"
                await self.redis_manager.set(
                    cache_key,
                    json.dumps(result),
                    ttl=60  # 1分钟过期
                )
                
                # 调用注册的回调函数
                for callback in self.ws_callbacks["spot_ticker"]:
                    try:
                        await callback(result)
                    except Exception as e:
                        logger.error(f"现货行情回调函数执行失败: {e}")
                        
        except Exception as e:
            logger.error(f"处理现货行情数据失败: {e}")
    
    async def _handle_spot_trades(self, data: Dict[str, Any]):
        """
        处理现货成交数据
        """
        try:
            result = data.get("result")
            if result:
                symbol = result.get("currency_pair")
                
                # 缓存最新成交记录
                cache_key = f"{self.cache_prefix}:spot:trades:{symbol}"
                await self.redis_manager.lpush(cache_key, json.dumps(result))
                await self.redis_manager.ltrim(cache_key, 0, 99)  # 保留最新100条
                await self.redis_manager.expire(cache_key, 3600)  # 1小时过期
                
                # 调用注册的回调函数
                for callback in self.ws_callbacks["spot_trades"]:
                    try:
                        await callback(result)
                    except Exception as e:
                        logger.error(f"现货成交回调函数执行失败: {e}")
                        
        except Exception as e:
            logger.error(f"处理现货成交数据失败: {e}")
    
    async def _handle_spot_order_book(self, data: Dict[str, Any]):
        """
        处理现货订单簿数据
        """
        try:
            result = data.get("result")
            if result:
                symbol = result.get("s")  # Gate.io订单簿更新中的symbol字段
                
                # 缓存订单簿数据
                cache_key = f"{self.cache_prefix}:spot:order_book:{symbol}"
                await self.redis_manager.set(
                    cache_key,
                    json.dumps(result),
                    ttl=60  # 1分钟过期
                )
                
                # 调用注册的回调函数
                for callback in self.ws_callbacks["spot_order_book"]:
                    try:
                        await callback(result)
                    except Exception as e:
                        logger.error(f"现货订单簿回调函数执行失败: {e}")
                        
        except Exception as e:
            logger.error(f"处理现货订单簿数据失败: {e}")
    
    async def _handle_futures_ticker(self, data: Dict[str, Any]):
        """
        处理期货行情数据
        """
        try:
            result = data.get("result")
            if result:
                symbol = result.get("contract")
                
                # 缓存到Redis
                cache_key = f"{self.cache_prefix}:futures:ticker:{symbol}"
                await self.redis_manager.set(
                    cache_key,
                    json.dumps(result),
                    ttl=60  # 1分钟过期
                )
                
                # 调用注册的回调函数
                for callback in self.ws_callbacks["futures_ticker"]:
                    try:
                        await callback(result)
                    except Exception as e:
                        logger.error(f"期货行情回调函数执行失败: {e}")
                        
        except Exception as e:
            logger.error(f"处理期货行情数据失败: {e}")
    
    async def _handle_futures_trades(self, data: Dict[str, Any]):
        """
        处理期货成交数据
        """
        try:
            result = data.get("result")
            if result:
                symbol = result.get("contract")
                
                # 缓存最新成交记录
                cache_key = f"{self.cache_prefix}:futures:trades:{symbol}"
                await self.redis_manager.lpush(cache_key, json.dumps(result))
                await self.redis_manager.ltrim(cache_key, 0, 99)  # 保留最新100条
                await self.redis_manager.expire(cache_key, 3600)  # 1小时过期
                
                # 调用注册的回调函数
                for callback in self.ws_callbacks["futures_trades"]:
                    try:
                        await callback(result)
                    except Exception as e:
                        logger.error(f"期货成交回调函数执行失败: {e}")
                        
        except Exception as e:
            logger.error(f"处理期货成交数据失败: {e}")
    
    async def _handle_futures_order_book(self, data: Dict[str, Any]):
        """
        处理期货订单簿数据
        """
        try:
            result = data.get("result")
            if result:
                symbol = result.get("s")  # Gate.io订单簿更新中的symbol字段
                
                # 缓存订单簿数据
                cache_key = f"{self.cache_prefix}:futures:order_book:{symbol}"
                await self.redis_manager.set(
                    cache_key,
                    json.dumps(result),
                    ttl=60  # 1分钟过期
                )
                
                # 调用注册的回调函数
                for callback in self.ws_callbacks["futures_order_book"]:
                    try:
                        await callback(result)
                    except Exception as e:
                        logger.error(f"期货订单簿回调函数执行失败: {e}")
                        
        except Exception as e:
            logger.error(f"处理期货订单簿数据失败: {e}")
    
    # ==================== 公共API接口 ====================
    
    async def get_supported_pairs(self, market_type: str = "all") -> Dict[str, List[str]]:
        """
        获取支持的交易对
        
        Args:
            market_type: 市场类型 (spot/futures/all)
            
        Returns:
            支持的交易对列表
        """
        if market_type == "all":
            return self.supported_pairs
        elif market_type in self.supported_pairs:
            return {market_type: self.supported_pairs[market_type]}
        else:
            raise ValueError(f"不支持的市场类型: {market_type}")
    
    async def get_ticker(self, symbol: str, market_type: str = "spot") -> Optional[Dict[str, Any]]:
        """
        获取行情数据
        
        Args:
            symbol: 交易对符号
            market_type: 市场类型 (spot/futures)
            
        Returns:
            行情数据
        """
        try:
            # 先从缓存获取
            cache_key = f"{self.cache_prefix}:{market_type}:ticker:{symbol}"
            cached_data = await self.redis_manager.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            # 缓存未命中，从API获取
            if market_type == "spot":
                data = await self.gateio_client.rest.get_spot_ticker(symbol)
            elif market_type == "futures":
                data = await self.gateio_client.rest.get_futures_tickers("usdt", symbol)
                data = data[0] if data else None
            else:
                raise ValueError(f"不支持的市场类型: {market_type}")
            
            # 缓存数据
            if data:
                await self.redis_manager.set(
                    cache_key,
                    json.dumps(data),
                    ttl=60
                )
            
            return data
            
        except Exception as e:
            logger.error(f"获取行情数据失败: {e}")
            return None
    
    async def get_order_book(self, symbol: str, market_type: str = "spot", limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        获取订单簿数据
        
        Args:
            symbol: 交易对符号
            market_type: 市场类型 (spot/futures)
            limit: 深度限制
            
        Returns:
            订单簿数据
        """
        try:
            # 先从缓存获取
            cache_key = f"{self.cache_prefix}:{market_type}:order_book:{symbol}"
            cached_data = await self.redis_manager.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            # 缓存未命中，从API获取
            if market_type == "spot":
                data = await self.gateio_client.rest.get_spot_order_book(symbol, limit)
            elif market_type == "futures":
                data = await self.gateio_client.rest.get_futures_order_book("usdt", symbol, "0", limit)
            else:
                raise ValueError(f"不支持的市场类型: {market_type}")
            
            # 缓存数据
            if data:
                await self.redis_manager.set(
                    cache_key,
                    json.dumps(data),
                    ttl=30  # 30秒过期
                )
            
            return data
            
        except Exception as e:
            logger.error(f"获取订单簿数据失败: {e}")
            return None
    
    async def get_trades(self, symbol: str, market_type: str = "spot", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        获取成交记录
        
        Args:
            symbol: 交易对符号
            market_type: 市场类型 (spot/futures)
            limit: 记录数量限制
            
        Returns:
            成交记录列表
        """
        try:
            # 先从缓存获取
            cache_key = f"{self.cache_prefix}:{market_type}:trades:{symbol}"
            cached_data = await self.redis_manager.lrange(cache_key, 0, limit - 1)
            
            if cached_data:
                return [json.loads(item) for item in cached_data]
            
            # 缓存未命中，从API获取
            if market_type == "spot":
                data = await self.gateio_client.rest.get_spot_trades(symbol, limit)
            elif market_type == "futures":
                data = await self.gateio_client.rest.get_futures_trades("usdt", symbol, limit)
            else:
                raise ValueError(f"不支持的市场类型: {market_type}")
            
            # 缓存数据
            if data:
                for trade in reversed(data):  # 反向插入保持时间顺序
                    await self.redis_manager.lpush(cache_key, json.dumps(trade))
                await self.redis_manager.ltrim(cache_key, 0, 99)
                await self.redis_manager.expire(cache_key, 3600)
            
            return data
            
        except Exception as e:
            logger.error(f"获取成交记录失败: {e}")
            return None
    
    async def get_candlesticks(
        self,
        symbol: str,
        interval: str = "1m",
        market_type: str = "spot",
        limit: int = 100,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None
    ) -> Optional[List[List]]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号
            interval: K线间隔
            market_type: 市场类型 (spot/futures)
            limit: 数量限制
            from_time: 开始时间戳
            to_time: 结束时间戳
            
        Returns:
            K线数据列表
        """
        try:
            # 构建缓存键
            cache_key = f"{self.cache_prefix}:{market_type}:klines:{symbol}:{interval}:{limit}"
            
            # 先从缓存获取
            cached_data = await self.redis_manager.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            # 缓存未命中，从API获取
            if market_type == "spot":
                data = await self.gateio_client.rest.get_spot_candlesticks(
                    symbol, interval, limit, from_time, to_time
                )
            elif market_type == "futures":
                data = await self.gateio_client.rest.get_futures_candlesticks(
                    "usdt", symbol, interval, limit, from_time, to_time
                )
            else:
                raise ValueError(f"不支持的市场类型: {market_type}")
            
            # 缓存数据
            if data:
                cache_expire = 300 if interval in ["1m", "5m"] else 600  # 短周期缓存时间更短
                await self.redis_manager.set(
                    cache_key,
                    json.dumps(data),
                    ttl=cache_expire
                )
            
            return data
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return None
    
    # ==================== 回调函数管理 ====================
    
    def register_callback(self, event_type: str, callback: Callable):
        """
        注册WebSocket事件回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self.ws_callbacks:
            self.ws_callbacks[event_type].append(callback)
            logger.info(f"已注册 {event_type} 事件回调函数")
        else:
            raise ValueError(f"不支持的事件类型: {event_type}")
    
    def unregister_callback(self, event_type: str, callback: Callable):
        """
        取消注册WebSocket事件回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self.ws_callbacks and callback in self.ws_callbacks[event_type]:
            self.ws_callbacks[event_type].remove(callback)
            logger.info(f"已取消注册 {event_type} 事件回调函数")
    
    # ==================== 技术指标计算 ====================
    
    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """
        计算简单移动平均线
        
        Args:
            prices: 价格列表
            period: 周期
            
        Returns:
            SMA值列表
        """
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = sum(prices[i - period + 1:i + 1]) / period
            sma_values.append(sma)
        
        return sma_values
    
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """
        计算指数移动平均线
        
        Args:
            prices: 价格列表
            period: 周期
            
        Returns:
            EMA值列表
        """
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema_values = [sum(prices[:period]) / period]  # 第一个EMA值使用SMA
        
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """
        计算相对强弱指数
        
        Args:
            prices: 价格列表
            period: 周期
            
        Returns:
            RSI值列表
        """
        if len(prices) < period + 1:
            return []
        
        # 计算价格变化
        price_changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        
        # 分离上涨和下跌
        gains = [change if change > 0 else 0 for change in price_changes]
        losses = [-change if change < 0 else 0 for change in price_changes]
        
        # 计算平均收益和损失
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        rsi_values = []
        
        for i in range(period, len(gains)):
            # 更新平均收益和损失
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            # 计算RSI
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values


# 全局市场数据服务实例
market_data_service = None


async def get_market_service() -> MarketDataService:
    """
    获取市场数据服务实例
    
    Returns:
        MarketDataService: 市场数据服务实例
    """
    global market_data_service
    if market_data_service is None:
        market_data_service = MarketDataService()
        await market_data_service.initialize()
    return market_data_service