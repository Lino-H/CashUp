#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 配置服务缓存管理

管理Redis缓存连接、操作和健康检查
"""

import json
import logging
from typing import Optional, Any, Dict, List
from redis.asyncio import Redis, ConnectionPool
from contextlib import asynccontextmanager

from .config import get_redis_config, get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 全局变量
redis_client: Optional[Redis] = None
connection_pool: Optional[ConnectionPool] = None


async def init_redis() -> None:
    """
    初始化Redis连接
    
    创建Redis客户端和连接池
    """
    global redis_client, connection_pool
    
    try:
        # 获取Redis配置
        redis_config = get_redis_config()
        
        logger.info(f"Initializing Redis connection to: {redis_config['url']}")
        
        # 创建连接池
        connection_pool = ConnectionPool.from_url(
            redis_config["url"],
            encoding=redis_config["encoding"],
            decode_responses=redis_config["decode_responses"],
            socket_timeout=redis_config["socket_timeout"],
            socket_connect_timeout=redis_config["socket_connect_timeout"],
            retry_on_timeout=redis_config["retry_on_timeout"],
            max_connections=20
        )
        
        # 创建Redis客户端
        redis_client = Redis(connection_pool=connection_pool)
        
        # 测试连接
        await redis_client.ping()
        
        logger.info("Redis initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {str(e)}")
        raise


async def close_redis() -> None:
    """
    关闭Redis连接
    
    清理Redis资源
    """
    global redis_client, connection_pool
    
    try:
        if redis_client:
            await redis_client.close()
            
        if connection_pool:
            await connection_pool.disconnect()
            
        logger.info("Redis connection closed")
        
    except Exception as e:
        logger.error(f"Error closing Redis connection: {str(e)}")


async def get_redis_client() -> Redis:
    """
    获取Redis客户端
    
    Returns:
        Redis: Redis客户端实例
    """
    if not redis_client:
        raise RuntimeError("Redis not initialized")
    return redis_client


async def check_redis_health() -> bool:
    """
    检查Redis健康状态
    
    Returns:
        bool: Redis是否健康
    """
    try:
        if not redis_client:
            return False
        
        response = await redis_client.ping()
        return response is True
        
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return False


class ConfigCache:
    """
    配置缓存管理类
    
    提供配置的缓存操作功能
    """
    
    def __init__(self):
        self.prefix = "config:"
        self.version_prefix = "config_version:"
        self.lock_prefix = "config_lock:"
        self.default_ttl = settings.CONFIG_CACHE_TTL
    
    def _get_key(self, key: str) -> str:
        """
        获取缓存键名
        
        Args:
            key: 原始键名
            
        Returns:
            str: 带前缀的键名
        """
        return f"{self.prefix}{key}"
    
    def _get_version_key(self, key: str) -> str:
        """
        获取版本键名
        
        Args:
            key: 原始键名
            
        Returns:
            str: 版本键名
        """
        return f"{self.version_prefix}{key}"
    
    def _get_lock_key(self, key: str) -> str:
        """
        获取锁键名
        
        Args:
            key: 原始键名
            
        Returns:
            str: 锁键名
        """
        return f"{self.lock_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取配置
        
        Args:
            key: 配置键
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        try:
            client = await get_redis_client()
            cache_key = self._get_key(key)
            
            data = await client.get(cache_key)
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get config from cache: {key}, error: {str(e)}")
            return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        设置配置
        
        Args:
            key: 配置键
            value: 配置值
            ttl: 过期时间（秒）
            
        Returns:
            bool: 是否成功
        """
        try:
            client = await get_redis_client()
            cache_key = self._get_key(key)
            
            data = json.dumps(value, ensure_ascii=False)
            
            if ttl is None:
                ttl = self.default_ttl
            
            await client.setex(cache_key, ttl, data)
            
            # 更新版本号
            version_key = self._get_version_key(key)
            await client.incr(version_key)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set config to cache: {key}, error: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        删除配置
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否成功
        """
        try:
            client = await get_redis_client()
            cache_key = self._get_key(key)
            version_key = self._get_version_key(key)
            
            # 删除配置和版本
            await client.delete(cache_key, version_key)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete config from cache: {key}, error: {str(e)}")
            return False
    
    async def get_version(self, key: str) -> int:
        """
        获取配置版本号
        
        Args:
            key: 配置键
            
        Returns:
            int: 版本号
        """
        try:
            client = await get_redis_client()
            version_key = self._get_version_key(key)
            
            version = await client.get(version_key)
            return int(version) if version else 0
            
        except Exception as e:
            logger.error(f"Failed to get config version: {key}, error: {str(e)}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        检查配置是否存在
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否存在
        """
        try:
            client = await get_redis_client()
            cache_key = self._get_key(key)
            
            return await client.exists(cache_key) > 0
            
        except Exception as e:
            logger.error(f"Failed to check config existence: {key}, error: {str(e)}")
            return False
    
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """
        获取配置键列表
        
        Args:
            pattern: 匹配模式
            
        Returns:
            List[str]: 键列表
        """
        try:
            client = await get_redis_client()
            search_pattern = f"{self.prefix}{pattern}"
            
            keys = await client.keys(search_pattern)
            # 移除前缀
            return [key.replace(self.prefix, "") for key in keys]
            
        except Exception as e:
            logger.error(f"Failed to get config keys: {pattern}, error: {str(e)}")
            return []
    
    @asynccontextmanager
    async def lock(self, key: str, timeout: int = 30):
        """
        配置锁
        
        Args:
            key: 配置键
            timeout: 锁超时时间
        """
        client = await get_redis_client()
        lock_key = self._get_lock_key(key)
        
        try:
            # 获取锁
            acquired = await client.set(lock_key, "1", nx=True, ex=timeout)
            if not acquired:
                raise RuntimeError(f"Failed to acquire lock for config: {key}")
            
            yield
            
        finally:
            # 释放锁
            try:
                await client.delete(lock_key)
            except Exception as e:
                logger.error(f"Failed to release lock for config: {key}, error: {str(e)}")
    
    async def clear_all(self) -> bool:
        """
        清空所有配置缓存
        
        Returns:
            bool: 是否成功
        """
        try:
            client = await get_redis_client()
            
            # 获取所有配置键
            config_keys = await client.keys(f"{self.prefix}*")
            version_keys = await client.keys(f"{self.version_prefix}*")
            lock_keys = await client.keys(f"{self.lock_prefix}*")
            
            all_keys = config_keys + version_keys + lock_keys
            
            if all_keys:
                await client.delete(*all_keys)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear all config cache: {str(e)}")
            return False


# 创建全局缓存实例
config_cache = ConfigCache()


# 获取缓存实例
def get_config_cache() -> ConfigCache:
    """
    获取配置缓存实例
    
    Returns:
        ConfigCache: 缓存实例
    """
    return config_cache