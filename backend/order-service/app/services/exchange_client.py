#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易所客户端服务

与交易所服务进行通信的客户端
"""

import logging
from typing import Dict, Any, Optional, List
import httpx
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ExchangeClient:
    """
    交易所客户端
    
    负责与exchange-service进行通信
    """
    
    def __init__(self):
        self.base_url = settings.EXCHANGE_SERVICE_URL
        self.timeout = 30.0
    
    async def create_order(self, exchange_name: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        在交易所创建订单
        
        Args:
            exchange_name: 交易所名称
            order_data: 订单数据
            
        Returns:
            Dict[str, Any]: 交易所响应
            
        Raises:
            Exception: 创建订单失败
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/trading/orders",
                    json={
                        "exchange_name": exchange_name,
                        **order_data
                    }
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating order on {exchange_name}: {str(e)}")
            raise Exception(f"Failed to create order: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating order on {exchange_name}: {str(e)}")
            raise
    
    async def cancel_order(self, exchange_name: str, order_id: str) -> Dict[str, Any]:
        """
        取消交易所订单
        
        Args:
            exchange_name: 交易所名称
            order_id: 订单ID
            
        Returns:
            Dict[str, Any]: 交易所响应
            
        Raises:
            Exception: 取消订单失败
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/api/v1/trading/orders/{order_id}",
                    params={"exchange_name": exchange_name}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error cancelling order {order_id} on {exchange_name}: {str(e)}")
            raise Exception(f"Failed to cancel order: {str(e)}")
        except Exception as e:
            logger.error(f"Error cancelling order {order_id} on {exchange_name}: {str(e)}")
            raise
    
    async def get_order_status(self, exchange_name: str, order_id: str) -> Dict[str, Any]:
        """
        获取订单状态
        
        Args:
            exchange_name: 交易所名称
            order_id: 订单ID
            
        Returns:
            Dict[str, Any]: 订单状态信息
            
        Raises:
            Exception: 获取订单状态失败
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/trading/orders/{order_id}",
                    params={"exchange_name": exchange_name}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting order status {order_id} on {exchange_name}: {str(e)}")
            raise Exception(f"Failed to get order status: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting order status {order_id} on {exchange_name}: {str(e)}")
            raise
    
    async def get_account_balance(self, exchange_name: str) -> Dict[str, Any]:
        """
        获取账户余额
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            Dict[str, Any]: 账户余额信息
            
        Raises:
            Exception: 获取余额失败
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/trading/balance",
                    params={"exchange_name": exchange_name}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting balance on {exchange_name}: {str(e)}")
            raise Exception(f"Failed to get balance: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting balance on {exchange_name}: {str(e)}")
            raise
    
    async def get_trading_pairs(self, exchange_name: str) -> List[Dict[str, Any]]:
        """
        获取交易对列表
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            List[Dict[str, Any]]: 交易对列表
            
        Raises:
            Exception: 获取交易对失败
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/market/symbols",
                    params={"exchange_name": exchange_name}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting trading pairs on {exchange_name}: {str(e)}")
            raise Exception(f"Failed to get trading pairs: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting trading pairs on {exchange_name}: {str(e)}")
            raise
    
    async def get_ticker(self, exchange_name: str, symbol: str) -> Dict[str, Any]:
        """
        获取交易对行情
        
        Args:
            exchange_name: 交易所名称
            symbol: 交易对符号
            
        Returns:
            Dict[str, Any]: 行情信息
            
        Raises:
            Exception: 获取行情失败
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/market/ticker/{symbol}",
                    params={"exchange_name": exchange_name}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting ticker {symbol} on {exchange_name}: {str(e)}")
            raise Exception(f"Failed to get ticker: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting ticker {symbol} on {exchange_name}: {str(e)}")
            raise
    
    async def validate_order(self, exchange_name: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证订单数据
        
        Args:
            exchange_name: 交易所名称
            order_data: 订单数据
            
        Returns:
            Dict[str, Any]: 验证结果
            
        Raises:
            Exception: 验证失败
        """
        try:
            # 获取交易对信息
            trading_pairs = await self.get_trading_pairs(exchange_name)
            symbol = order_data.get("symbol")
            
            # 检查交易对是否存在
            valid_symbols = [pair.get("symbol") for pair in trading_pairs]
            if symbol not in valid_symbols:
                raise ValueError(f"Invalid symbol: {symbol}")
            
            # 获取当前价格用于验证
            ticker = await self.get_ticker(exchange_name, symbol)
            current_price = float(ticker.get("price", 0))
            
            # 基本验证
            quantity = float(order_data.get("quantity", 0))
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            
            price = order_data.get("price")
            if price is not None:
                price = float(price)
                if price <= 0:
                    raise ValueError("Price must be positive")
                
                # 价格偏离检查（可选）
                if current_price > 0:
                    price_deviation = abs(price - current_price) / current_price
                    if price_deviation > 0.1:  # 10% 偏离警告
                        logger.warning(f"Order price {price} deviates {price_deviation:.2%} from current price {current_price}")
            
            return {
                "valid": True,
                "current_price": current_price,
                "message": "Order validation passed"
            }
            
        except ValueError as e:
            return {
                "valid": False,
                "error": str(e),
                "message": "Order validation failed"
            }
        except Exception as e:
            logger.error(f"Error validating order: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        检查交易所服务健康状态
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Exchange service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }