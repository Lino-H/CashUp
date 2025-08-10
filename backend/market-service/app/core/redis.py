#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 市场数据服务Redis配置

配置Redis连接和缓存管理
"""

import json
import logging
from typing import Any, Optional, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from .config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Redis连接管理器
    
    提供Redis连接池管理和常用操作方法
    """
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
    
    async def init_redis(self):
        """
        初始化Redis连接
        """
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # 测试连接
            await self.redis_client.ping()
            logger.info("Redis连接初始化成功")
            
        except Exception as e:
            logger.error(f"Redis连接初始化失败: {e}")
            raise
    
    async def close(self):
        """
        关闭Redis连接
        """
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Redis连接已关闭")
    
    async def ping(self) -> bool:
        """
        检查Redis连接状态
        
        Returns:
            bool: 连接是否正常
        """
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            return False
        except Exception as e:
            logger.error(f"Redis ping失败: {e}")
            return False
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)
            
        Returns:
            bool: 是否设置成功
        """
        try:
            if self.redis_client:
                # 序列化值
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                elif not isinstance(value, str):
                    value = str(value)
                
                await self.redis_client.set(key, value, ex=ttl)
                return True
            return False
        except Exception as e:
            logger.error(f"Redis set失败 {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或None
        """
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    # 尝试反序列化JSON
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value
            return None
        except Exception as e:
            logger.error(f"Redis get失败 {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if self.redis_client:
                result = await self.redis_client.delete(key)
                return result > 0
            return False
        except Exception as e:
            logger.error(f"Redis delete失败 {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 键是否存在
        """
        try:
            if self.redis_client:
                result = await self.redis_client.exists(key)
                return result > 0
            return False
        except Exception as e:
            logger.error(f"Redis exists失败 {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        设置键的过期时间
        
        Args:
            key: 缓存键
            ttl: 过期时间(秒)
            
        Returns:
            bool: 是否设置成功
        """
        try:
            if self.redis_client:
                result = await self.redis_client.expire(key, ttl)
                return result
            return False
        except Exception as e:
            logger.error(f"Redis expire失败 {key}: {e}")
            return False
    
    async def hset(
        self,
        name: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置哈希表字段值
        
        Args:
            name: 哈希表名
            key: 字段名
            value: 字段值
            ttl: 过期时间(秒)
            
        Returns:
            bool: 是否设置成功
        """
        try:
            if self.redis_client:
                # 序列化值
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                elif not isinstance(value, str):
                    value = str(value)
                
                await self.redis_client.hset(name, key, value)
                
                # 设置过期时间
                if ttl:
                    await self.redis_client.expire(name, ttl)
                
                return True
            return False
        except Exception as e:
            logger.error(f"Redis hset失败 {name}.{key}: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """
        获取哈希表字段值
        
        Args:
            name: 哈希表名
            key: 字段名
            
        Returns:
            字段值或None
        """
        try:
            if self.redis_client:
                value = await self.redis_client.hget(name, key)
                if value:
                    # 尝试反序列化JSON
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value
            return None
        except Exception as e:
            logger.error(f"Redis hget失败 {name}.{key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> dict:
        """
        获取哈希表所有字段
        
        Args:
            name: 哈希表名
            
        Returns:
            字段字典
        """
        try:
            if self.redis_client:
                result = await self.redis_client.hgetall(name)
                # 尝试反序列化JSON值
                for key, value in result.items():
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        pass
                return result
            return {}
        except Exception as e:
            logger.error(f"Redis hgetall失败 {name}: {e}")
            return {}
    
    async def lpush(self, key: str, *values: Any) -> bool:
        """
        向列表左侧推入值
        
        Args:
            key: 列表键
            values: 要推入的值
            
        Returns:
            bool: 是否推入成功
        """
        try:
            if self.redis_client:
                # 序列化值
                serialized_values = []
                for value in values:
                    if isinstance(value, (dict, list)):
                        serialized_values.append(json.dumps(value, ensure_ascii=False))
                    else:
                        serialized_values.append(str(value))
                
                await self.redis_client.lpush(key, *serialized_values)
                return True
            return False
        except Exception as e:
            logger.error(f"Redis lpush失败 {key}: {e}")
            return False
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """
        获取列表范围内的元素
        
        Args:
            key: 列表键
            start: 开始索引
            end: 结束索引
            
        Returns:
            元素列表
        """
        try:
            if self.redis_client:
                values = await self.redis_client.lrange(key, start, end)
                # 尝试反序列化JSON值
                result = []
                for value in values:
                    try:
                        result.append(json.loads(value))
                    except (json.JSONDecodeError, TypeError):
                        result.append(value)
                return result
            return []
        except Exception as e:
            logger.error(f"Redis lrange失败 {key}: {e}")
            return []
    
    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """
        修剪列表，只保留指定范围内的元素
        
        Args:
            key: 列表键
            start: 开始索引
            end: 结束索引
            
        Returns:
            bool: 是否修剪成功
        """
        try:
            if self.redis_client:
                await self.redis_client.ltrim(key, start, end)
                return True
            return False
        except Exception as e:
            logger.error(f"Redis ltrim失败 {key}: {e}")
            return False


# 全局Redis管理器实例
redis_manager: Optional[RedisManager] = None


async def get_redis() -> RedisManager:
    """
    获取Redis管理器实例
    
    Returns:
        RedisManager: Redis管理器实例
    """
    global redis_manager
    
    if not redis_manager:
        redis_manager = RedisManager()
        await redis_manager.init_redis()
    
    return redis_manager