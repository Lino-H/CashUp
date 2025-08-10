#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易所服务客户端

提供与exchange-service通信的客户端
"""

import logging
from typing import Dict, List, Optional, Any

import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ExchangeClient:
    """
    交易所服务客户端
    
    提供与exchange-service通信的接口
    """
    
    def __init__(self, base_url: str = "http://exchange-service:8003"):
        """
        初始化交易所服务客户端
        
        Args:
            base_url: exchange-service的基础URL
        """
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: 查询参数
            json_data: JSON数据
            headers: 请求头
            
        Returns:
            响应数据
        """
        if not self.session:
            raise RuntimeError("Client session not initialized")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers
            ) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {method} {url} - {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    # ==================== 交易所管理接口 ====================
    
    async def get_available_exchanges(self) -> List[Dict[str, Any]]:
        """
        获取可用交易所列表
        
        Returns:
            交易所列表
        """
        return await self._request("GET", "/api/v1/exchanges")
    
    async def get_exchange_info(self, exchange_name: str) -> Dict[str, Any]:
        """
        获取指定交易所信息
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            交易所信息
        """
        return await self._request("GET", f"/api/v1/exchanges/{exchange_name}")
    
    async def connect_exchange(
        self,
        exchange_name: str,
        api_key: str,
        api_secret: str,
        testnet: bool = False
    ) -> Dict[str, Any]:
        """
        连接交易所
        
        Args:
            exchange_name: 交易所名称
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网
            
        Returns:
            连接结果
        """
        return await self._request(
            "POST",
            f"/api/v1/exchanges/{exchange_name}/connect",
            json_data={
                "api_key": api_key,
                "api_secret": api_secret,
                "testnet": testnet
            }
        )
    
    async def disconnect_exchange(self, exchange_name: str) -> Dict[str, Any]:
        """
        断开交易所连接
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            断开结果
        """
        return await self._request("POST", f"/api/v1/exchanges/{exchange_name}/disconnect")
    
    # ==================== 市场数据接口 ====================
    
    async def get_symbols(
        self,
        exchange_name: str,
        market_type: str = "spot"
    ) -> List[Dict[str, Any]]:
        """
        获取交易对列表
        
        Args:
            exchange_name: 交易所名称
            market_type: 市场类型
            
        Returns:
            交易对列表
        """
        return await self._request(
            "GET",
            f"/api/v1/market/{exchange_name}/symbols",
            params={"market_type": market_type}
        )
    
    async def get_ticker(
        self,
        exchange_name: str,
        symbol: str,
        market_type: str = "spot"
    ) -> Dict[str, Any]:
        """
        获取行情数据
        
        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号
            market_type: 市场类型
            
        Returns:
            行情数据
        """
        return await self._request(
            "GET",
            f"/api/v1/market/{exchange_name}/ticker/{symbol}",
            params={"market_type": market_type}
        )
    
    async def get_tickers(
        self,
        exchange_name: str,
        market_type: str = "spot"
    ) -> List[Dict[str, Any]]:
        """
        获取所有行情数据
        
        Args:
            exchange_name: 交易所名称
            market_type: 市场类型
            
        Returns:
            行情数据列表
        """
        return await self._request(
            "GET",
            f"/api/v1/market/{exchange_name}/tickers",
            params={"market_type": market_type}
        )
    
    async def get_order_book(
        self,
        exchange_name: str,
        symbol: str,
        market_type: str = "spot",
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取订单簿
        
        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号
            market_type: 市场类型
            limit: 深度限制
            
        Returns:
            订单簿数据
        """
        return await self._request(
            "GET",
            f"/api/v1/market/{exchange_name}/orderbook/{symbol}",
            params={"market_type": market_type, "limit": limit}
        )
    
    async def get_trades(
        self,
        exchange_name: str,
        symbol: str,
        market_type: str = "spot",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取成交记录
        
        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号
            market_type: 市场类型
            limit: 记录数量限制
            
        Returns:
            成交记录列表
        """
        return await self._request(
            "GET",
            f"/api/v1/market/{exchange_name}/trades/{symbol}",
            params={"market_type": market_type, "limit": limit}
        )
    
    async def get_klines(
        self,
        exchange_name: str,
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
            exchange_name: 交易所名称
            symbol: 交易对符号
            interval: 时间间隔
            market_type: 市场类型
            limit: 数量限制
            start_time: 开始时间戳
            end_time: 结束时间戳
            
        Returns:
            K线数据列表
        """
        params = {
            "interval": interval,
            "market_type": market_type,
            "limit": limit
        }
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        
        return await self._request(
            "GET",
            f"/api/v1/market/{exchange_name}/klines/{symbol}",
            params=params
        )
    
    # ==================== 账户接口 ====================
    
    async def get_account_info(
        self,
        exchange_name: str,
        market_type: str = "spot"
    ) -> Dict[str, Any]:
        """
        获取账户信息
        
        Args:
            exchange_name: 交易所名称
            market_type: 市场类型
            
        Returns:
            账户信息
        """
        return await self._request(
            "GET",
            f"/api/v1/trading/{exchange_name}/account",
            params={"market_type": market_type}
        )
    
    async def get_balances(
        self,
        exchange_name: str,
        market_type: str = "spot"
    ) -> List[Dict[str, Any]]:
        """
        获取账户余额
        
        Args:
            exchange_name: 交易所名称
            market_type: 市场类型
            
        Returns:
            余额列表
        """
        return await self._request(
            "GET",
            f"/api/v1/trading/{exchange_name}/balances",
            params={"market_type": market_type}
        )
    
    # ==================== 交易接口 ====================
    
    async def create_order(
        self,
        exchange_name: str,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None,
        market_type: str = "spot",
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建订单
        
        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号
            side: 买卖方向
            order_type: 订单类型
            amount: 数量
            price: 价格
            market_type: 市场类型
            **kwargs: 其他参数
            
        Returns:
            订单信息
        """
        order_data = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "amount": amount,
            "market_type": market_type,
            **kwargs
        }
        if price is not None:
            order_data["price"] = price
        
        return await self._request(
            "POST",
            f"/api/v1/trading/{exchange_name}/orders",
            json_data=order_data
        )
    
    async def cancel_order(
        self,
        exchange_name: str,
        order_id: str,
        symbol: str,
        market_type: str = "spot"
    ) -> Dict[str, Any]:
        """
        取消订单
        
        Args:
            exchange_name: 交易所名称
            order_id: 订单ID
            symbol: 交易对符号
            market_type: 市场类型
            
        Returns:
            取消结果
        """
        return await self._request(
            "DELETE",
            f"/api/v1/trading/{exchange_name}/orders/{order_id}",
            params={"symbol": symbol, "market_type": market_type}
        )
    
    async def get_order(
        self,
        exchange_name: str,
        order_id: str,
        symbol: str,
        market_type: str = "spot"
    ) -> Dict[str, Any]:
        """
        获取订单信息
        
        Args:
            exchange_name: 交易所名称
            order_id: 订单ID
            symbol: 交易对符号
            market_type: 市场类型
            
        Returns:
            订单信息
        """
        return await self._request(
            "GET",
            f"/api/v1/trading/{exchange_name}/orders/{order_id}",
            params={"symbol": symbol, "market_type": market_type}
        )
    
    async def get_open_orders(
        self,
        exchange_name: str,
        symbol: Optional[str] = None,
        market_type: str = "spot"
    ) -> List[Dict[str, Any]]:
        """
        获取未成交订单
        
        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号（可选）
            market_type: 市场类型
            
        Returns:
            订单列表
        """
        params = {"market_type": market_type}
        if symbol:
            params["symbol"] = symbol
        
        return await self._request(
            "GET",
            f"/api/v1/trading/{exchange_name}/orders/open",
            params=params
        )
    
    async def get_order_history(
        self,
        exchange_name: str,
        symbol: Optional[str] = None,
        market_type: str = "spot",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取历史订单
        
        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号（可选）
            market_type: 市场类型
            limit: 数量限制
            
        Returns:
            订单列表
        """
        params = {"market_type": market_type, "limit": limit}
        if symbol:
            params["symbol"] = symbol
        
        return await self._request(
            "GET",
            f"/api/v1/trading/{exchange_name}/orders/history",
            params=params
        )
    
    # ==================== 期货特有接口 ====================
    
    async def get_positions(
        self,
        exchange_name: str,
        settle: str = "usdt"
    ) -> List[Dict[str, Any]]:
        """
        获取持仓信息
        
        Args:
            exchange_name: 交易所名称
            settle: 结算货币
            
        Returns:
            持仓列表
        """
        return await self._request(
            "GET",
            f"/api/v1/trading/{exchange_name}/positions",
            params={"settle": settle}
        )
    
    async def get_position(
        self,
        exchange_name: str,
        contract: str,
        settle: str = "usdt"
    ) -> Dict[str, Any]:
        """
        获取单个持仓信息
        
        Args:
            exchange_name: 交易所名称
            contract: 合约名称
            settle: 结算货币
            
        Returns:
            持仓信息
        """
        return await self._request(
            "GET",
            f"/api/v1/trading/{exchange_name}/positions/{contract}",
            params={"settle": settle}
        )