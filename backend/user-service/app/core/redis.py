#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - Redis连接管理

提供Redis连接、缓存管理、会话存储等功能
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
    
    提供Redis连接管理、缓存操作、会话存储等功能
    """
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.password = settings.REDIS_PASSWORD
        self._redis: Optional[Redis] = None
        self._connection_pool = None
    
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
                print("Redis connected successfully")
                
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
    
    async def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 键是否存在
        """
        try:
            redis_client = await self.get_redis()
            return await redis_client.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        设置键的过期时间
        
        Args:
            key: 缓存键
            seconds: 过期时间(秒)
            
        Returns:
            bool: 是否设置成功
        """
        try:
            redis_client = await self.get_redis()
            return await redis_client.expire(key, seconds)
        except Exception as e:
            print(f"Redis expire error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间
        
        Args:
            key: 缓存键
            
        Returns:
            int: 剩余时间(秒)，-1表示永不过期，-2表示键不存在
        """
        try:
            redis_client = await self.get_redis()
            return await redis_client.ttl(key)
        except Exception as e:
            print(f"Redis ttl error: {e}")
            return -2
    
    # 会话管理方法
    async def set_user_session(self, user_id: int, session_data: Dict[str, Any], expire: int = 3600) -> bool:
        """
        设置用户会话
        
        Args:
            user_id: 用户ID
            session_data: 会话数据
            expire: 过期时间(秒)
            
        Returns:
            bool: 是否设置成功
        """
        session_key = f"user_session:{user_id}"
        return await self.set(session_key, session_data, expire)
    
    async def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 会话数据
        """
        session_key = f"user_session:{user_id}"
        return await self.get(session_key)
    
    async def delete_user_session(self, user_id: int) -> bool:
        """
        删除用户会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        session_key = f"user_session:{user_id}"
        return await self.delete(session_key) > 0
    
    # 登录尝试管理
    async def increment_login_attempts(self, identifier: str) -> int:
        """
        增加登录尝试次数
        
        Args:
            identifier: 标识符(用户名或IP)
            
        Returns:
            int: 当前尝试次数
        """
        key = f"login_attempts:{identifier}"
        redis_client = await self.get_redis()
        
        attempts = await redis_client.incr(key)
        if attempts == 1:
            # 设置过期时间
            await redis_client.expire(key, settings.ACCOUNT_LOCKOUT_DURATION)
        
        return attempts
    
    async def get_login_attempts(self, identifier: str) -> int:
        """
        获取登录尝试次数
        
        Args:
            identifier: 标识符(用户名或IP)
            
        Returns:
            int: 尝试次数
        """
        key = f"login_attempts:{identifier}"
        attempts = await self.get(key, 0)
        return int(attempts) if attempts else 0
    
    async def reset_login_attempts(self, identifier: str) -> bool:
        """
        重置登录尝试次数
        
        Args:
            identifier: 标识符(用户名或IP)
            
        Returns:
            bool: 是否重置成功
        """
        key = f"login_attempts:{identifier}"
        return await self.delete(key) > 0


# 创建全局Redis管理器实例
redis_manager = RedisManager()


# 依赖注入函数
async def get_redis() -> Redis:
    """
    获取Redis连接的依赖注入函数
    
    Returns:
        Redis: Redis连接实例
    """
    return await redis_manager.get_redis()