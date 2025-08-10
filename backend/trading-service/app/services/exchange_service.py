#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易所服务

提供统一的交易所业务接口，通过exchange-service实现
"""

import logging
from typing import Dict, List, Optional, Any

from ..clients.exchange_client import ExchangeClient
from ..core.config import settings

logger = logging.getLogger(__name__)


class ExchangeService:
    """
    交易所服务
    
    提供统一的交易所业务接口，通过exchange-service实现多交易所支持
    """
    
    def __init__(self, exchange_service_url: Optional[str] = None):
        """
        初始化交易所服务
        
        Args:
            exchange_service_url: exchange-service的URL
        """
        self.exchange_service_url = exchange_service_url or settings.EXCHANGE_SERVICE_URL
        self.client: Optional[ExchangeClient] = None
        self.connected_exchanges: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self):
        """
        初始化服务
        """
        try:
            self.client = ExchangeClient(self.exchange_service_url)
            await self.client.__aenter__()
            
            logger.info("交易所服务初始化完成")
            
        except Exception as e:
            logger.error(f"交易所服务初始化失败: {e}")
            raise
    
    async def close(self):
        """
        关闭服务
        """
        if self.client:
            await self.client.__aexit__(None, None, None)
            self.client = None
        
        logger.info("交易所服务已关闭")
    
    # ==================== 交易所管理接口 ====================
    
    async def get_available_exchanges(self) -> List[Dict[str, Any]]:
        """
        获取可用交易所列表
        
        Returns:
            交易所列表
        """
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_available_exchanges()
    
    async def get_exchange_info(self, exchange_name: str) -> Dict[str, Any]:
        """
        获取指定交易所信息
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            交易所信息
        """
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_exchange_info(exchange_name)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        result = await self.client.connect_exchange(
            exchange_name, api_key, api_secret, testnet
        )
        
        # 记录连接的交易所
        self.connected_exchanges[exchange_name] = {
            "api_key": api_key,
            "testnet": testnet,
            "connected_at": result.get("timestamp")
        }
        
        return result
    
    async def disconnect_exchange(self, exchange_name: str) -> Dict[str, Any]:
        """
        断开交易所连接
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            断开结果
        """
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        result = await self.client.disconnect_exchange(exchange_name)
        
        # 移除连接记录
        self.connected_exchanges.pop(exchange_name, None)
        
        return result
    
    def is_exchange_connected(self, exchange_name: str) -> bool:
        """
        检查交易所是否已连接
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            是否已连接
        """
        return exchange_name in self.connected_exchanges
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_symbols(exchange_name, market_type)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_ticker(exchange_name, symbol, market_type)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_tickers(exchange_name, market_type)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_order_book(exchange_name, symbol, market_type, limit)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_trades(exchange_name, symbol, market_type, limit)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_klines(
            exchange_name, symbol, interval, market_type, limit, start_time, end_time
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_account_info(exchange_name, market_type)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_balances(exchange_name, market_type)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.create_order(
            exchange_name, symbol, side, order_type, amount, price, market_type, **kwargs
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.cancel_order(exchange_name, order_id, symbol, market_type)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_order(exchange_name, order_id, symbol, market_type)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_open_orders(exchange_name, symbol, market_type)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_order_history(exchange_name, symbol, market_type, limit)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_positions(exchange_name, settle)
    
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
        if not self.client:
            raise RuntimeError("Exchange service not initialized")
        
        return await self.client.get_position(exchange_name, contract, settle)


# 全局交易所服务实例
_exchange_service: Optional[ExchangeService] = None


async def get_exchange_service() -> ExchangeService:
    """
    获取交易所服务实例
    
    Returns:
        交易所服务实例
    """
    global _exchange_service
    
    if _exchange_service is None:
        _exchange_service = ExchangeService()
        await _exchange_service.initialize()
    
    return _exchange_service


async def close_exchange_service():
    """
    关闭交易所服务
    """
    global _exchange_service
    
    if _exchange_service:
        await _exchange_service.close()
        _exchange_service = None