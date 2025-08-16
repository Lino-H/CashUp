#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易服务Redis连接管理

提供Redis连接、缓存管理、实时数据存储等功能
"""

import json
import asyncio
from typing import Optional, Any, Dict, List
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio import Redis

from .config import settings


class RedisManager:
    """
    Redis管理器
    
    提供Redis连接管理、缓存操作、实时数据存储等功能
    """
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.password = settings.REDIS_PASSWORD
        self._redis: Optional[Redis] = None
        self._connection_pool = None
    
    async def init_redis(self) -> Redis:
        """
        初始化Redis连接
        
        Returns:
            Redis: Redis连接实例
        """
        return await self.connect()
    
    async def connect(self) -> Redis:
        """
        建立Redis连接
        
        Returns:
            Redis: Redis连接实例
        """
        if self._redis is None:
            try:
                # 创建连接池
                self._connection_pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    password=self.password,
                    decode_responses=True,
                    max_connections=20,
                    retry_on_timeout=True
                )
                
                # 创建Redis实例
                self._redis = redis.Redis(connection_pool=self._connection_pool)
                
                # 测试连接
                await self._redis.ping()
                print("Trading Service Redis connected successfully")
                
            except Exception as e:
                print(f"Failed to connect to Redis: {e}")
                raise
        
        return self._redis
    
    async def disconnect(self) -> None:
        """
        断开Redis连接
        """
        if self._redis:
            await self._redis.close()
            self._redis = None
        
        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._connection_pool = None
    
    async def get_redis(self) -> Redis:
        """
        获取Redis连接
        
        Returns:
            Redis: Redis连接实例
        """
        if self._redis is None:
            await self.connect()
        return self._redis
    
    async def health_check(self) -> bool:
        """
        Redis健康检查
        
        Returns:
            bool: Redis是否正常
        """
        try:
            redis_client = await self.get_redis()
            await redis_client.ping()
            return True
        except Exception as e:
            print(f"Redis health check failed: {e}")
            return False
    
    # 缓存操作方法
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间(秒)
            
        Returns:
            bool: 是否设置成功
        """
        try:
            redis_client = await self.get_redis()
            
            # 序列化值
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            elif not isinstance(value, str):
                value = str(value)
            
            if expire:
                return await redis_client.setex(key, expire, value)
            else:
                return await redis_client.set(key, value)
                
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            Any: 缓存值
        """
        try:
            redis_client = await self.get_redis()
            value = await redis_client.get(key)
            
            if value is None:
                return default
            
            # 尝试反序列化JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            print(f"Redis get error: {e}")
            return default
    
    async def delete(self, *keys: str) -> int:
        """
        删除缓存键
        
        Args:
            keys: 要删除的键列表
            
        Returns:
            int: 删除的键数量
        """
        try:
            redis_client = await self.get_redis()
            return await redis_client.delete(*keys)
        except Exception as e:
            print(f"Redis delete error: {e}")
            return 0
    
    # 实时数据相关方法
    async def publish_market_data(self, symbol: str, data: dict) -> bool:
        """
        发布市场数据
        
        Args:
            symbol: 交易对符号
            data: 市场数据
            
        Returns:
            bool: 是否发布成功
        """
        try:
            redis_client = await self.get_redis()
            channel = f"market_data:{symbol}"
            message = json.dumps(data, ensure_ascii=False)
            await redis_client.publish(channel, message)
            return True
        except Exception as e:
            print(f"Failed to publish market data: {e}")
            return False
    
    async def publish_order_update(self, user_id: int, order_data: dict) -> bool:
        """
        发布订单更新
        
        Args:
            user_id: 用户ID
            order_data: 订单数据
            
        Returns:
            bool: 是否发布成功
        """
        try:
            redis_client = await self.get_redis()
            channel = f"order_updates:{user_id}"
            message = json.dumps(order_data, ensure_ascii=False)
            await redis_client.publish(channel, message)
            return True
        except Exception as e:
            print(f"Failed to publish order update: {e}")
            return False
    
    async def publish_position_update(self, user_id: int, position_data: dict) -> bool:
        """
        发布持仓更新
        
        Args:
            user_id: 用户ID
            position_data: 持仓数据
            
        Returns:
            bool: 是否发布成功
        """
        try:
            redis_client = await self.get_redis()
            channel = f"position_updates:{user_id}"
            message = json.dumps(position_data, ensure_ascii=False)
            await redis_client.publish(channel, message)
            return True
        except Exception as e:
            print(f"Failed to publish position update: {e}")
            return False
    
    # 缓存持仓和订单数据
    async def cache_user_positions(self, user_id: int, positions: List[dict], expire: int = 300) -> bool:
        """
        缓存用户持仓数据
        
        Args:
            user_id: 用户ID
            positions: 持仓列表
            expire: 过期时间(秒)
            
        Returns:
            bool: 是否缓存成功
        """
        key = f"user_positions:{user_id}"
        return await self.set(key, positions, expire)
    
    async def get_user_positions(self, user_id: int) -> List[dict]:
        """
        获取用户持仓数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[dict]: 持仓列表
        """
        key = f"user_positions:{user_id}"
        return await self.get(key, [])
    
    async def cache_user_orders(self, user_id: int, orders: List[dict], expire: int = 300) -> bool:
        """
        缓存用户订单数据
        
        Args:
            user_id: 用户ID
            orders: 订单列表
            expire: 过期时间(秒)
            
        Returns:
            bool: 是否缓存成功
        """
        key = f"user_orders:{user_id}"
        return await self.set(key, orders, expire)
    
    async def get_user_orders(self, user_id: int) -> List[dict]:
        """
        获取用户订单数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[dict]: 订单列表
        """
        key = f"user_orders:{user_id}"
        return await self.get(key, [])


# 全局Redis管理器实例
redis_manager = RedisManager()