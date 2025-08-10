#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 缓存管理

Redis缓存管理和操作
"""

import json
import pickle
import logging
import asyncio
from typing import Any, Optional, Union, List, Dict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis, ConnectionPool
    from redis.exceptions import RedisError, ConnectionError, TimeoutError
except ImportError:
    import redis
    from redis import Redis, ConnectionPool
    from redis.exceptions import RedisError, ConnectionError, TimeoutError
    
    # 为同步版本创建异步包装器
    class AsyncRedisWrapper:
        def __init__(self, redis_client):
            self._client = redis_client
        
        async def get(self, key):
            return self._client.get(key)
        
        async def set(self, key, value, ex=None):
            return self._client.set(key, value, ex=ex)
        
        async def delete(self, *keys):
            return self._client.delete(*keys)
        
        async def exists(self, key):
            return self._client.exists(key)
        
        async def expire(self, key, time):
            return self._client.expire(key, time)
        
        async def ttl(self, key):
            return self._client.ttl(key)
        
        async def keys(self, pattern):
            return self._client.keys(pattern)
        
        async def flushdb(self):
            return self._client.flushdb()
        
        async def ping(self):
            return self._client.ping()
        
        async def info(self, section=None):
            return self._client.info(section)
        
        async def close(self):
            if hasattr(self._client, 'close'):
                self._client.close()

from .config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_url: str = None, password: str = None, db: int = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.password = password or settings.REDIS_PASSWORD
        self.db = db or settings.REDIS_DB
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[Redis] = None
        self._connected = False
        
        # 缓存配置
        self.default_ttl = settings.CACHE_TTL_DEFAULT
        self.short_ttl = settings.CACHE_TTL_SHORT
        self.long_ttl = settings.CACHE_TTL_LONG
        
        # 序列化配置
        self.serializers = {
            'json': {
                'dumps': json.dumps,
                'loads': json.loads
            },
            'pickle': {
                'dumps': pickle.dumps,
                'loads': pickle.loads
            }
        }
        self.default_serializer = 'json'
    
    async def connect(self):
        """连接到Redis"""
        try:
            if self._connected:
                return
            
            # 创建连接池
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                password=self.password,
                db=self.db,
                max_connections=settings.REDIS_POOL_SIZE,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # 创建Redis客户端
            if hasattr(redis, 'Redis'):
                # 异步版本
                self.client = redis.Redis(connection_pool=self.pool)
            else:
                # 同步版本，使用包装器
                sync_client = redis.Redis(connection_pool=self.pool)
                self.client = AsyncRedisWrapper(sync_client)
            
            # 测试连接
            await self.client.ping()
            self._connected = True
            
            logger.info(f"Connected to Redis: {self.redis_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """断开Redis连接"""
        try:
            if self.client:
                await self.client.close()
            if self.pool:
                await self.pool.disconnect()
            
            self._connected = False
            logger.info("Disconnected from Redis")
            
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")
    
    async def _ensure_connected(self):
        """确保Redis连接"""
        if not self._connected:
            await self.connect()
    
    def _serialize(self, value: Any, serializer: str = None) -> bytes:
        """序列化值"""
        serializer = serializer or self.default_serializer
        
        if serializer not in self.serializers:
            raise ValueError(f"Unknown serializer: {serializer}")
        
        try:
            if isinstance(value, (str, bytes)):
                return value.encode() if isinstance(value, str) else value
            
            serialized = self.serializers[serializer]['dumps'](value)
            return serialized.encode() if isinstance(serialized, str) else serialized
            
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize(self, value: bytes, serializer: str = None) -> Any:
        """反序列化值"""
        if value is None:
            return None
        
        serializer = serializer or self.default_serializer
        
        if serializer not in self.serializers:
            raise ValueError(f"Unknown serializer: {serializer}")
        
        try:
            if isinstance(value, bytes):
                value = value.decode()
            
            return self.serializers[serializer]['loads'](value)
            
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            # 如果反序列化失败，尝试返回原始字符串
            return value.decode() if isinstance(value, bytes) else value
    
    def _make_key(self, key: str, namespace: str = None) -> str:
        """生成缓存键"""
        if namespace:
            return f"{namespace}:{key}"
        return key
    
    async def get(self, key: str, namespace: str = None, serializer: str = None) -> Any:
        """获取缓存值"""
        try:
            await self._ensure_connected()
            
            cache_key = self._make_key(key, namespace)
            value = await self.client.get(cache_key)
            
            if value is None:
                return None
            
            return self._deserialize(value, serializer)
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = None, 
        namespace: str = None, 
        serializer: str = None
    ) -> bool:
        """设置缓存值"""
        try:
            await self._ensure_connected()
            
            cache_key = self._make_key(key, namespace)
            serialized_value = self._serialize(value, serializer)
            ttl = ttl or self.default_ttl
            
            result = await self.client.set(cache_key, serialized_value, ex=ttl)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str, namespace: str = None) -> bool:
        """删除缓存值"""
        try:
            await self._ensure_connected()
            
            cache_key = self._make_key(key, namespace)
            result = await self.client.delete(cache_key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str, namespace: str = None) -> bool:
        """检查缓存键是否存在"""
        try:
            await self._ensure_connected()
            
            cache_key = self._make_key(key, namespace)
            result = await self.client.exists(cache_key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int, namespace: str = None) -> bool:
        """设置缓存键过期时间"""
        try:
            await self._ensure_connected()
            
            cache_key = self._make_key(key, namespace)
            result = await self.client.expire(cache_key, ttl)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str, namespace: str = None) -> int:
        """获取缓存键剩余过期时间"""
        try:
            await self._ensure_connected()
            
            cache_key = self._make_key(key, namespace)
            result = await self.client.ttl(cache_key)
            return result
            
        except Exception as e:
            logger.error(f"Cache ttl error for key {key}: {e}")
            return -1
    
    async def keys(self, pattern: str, namespace: str = None) -> List[str]:
        """获取匹配模式的缓存键"""
        try:
            await self._ensure_connected()
            
            search_pattern = self._make_key(pattern, namespace)
            keys = await self.client.keys(search_pattern)
            
            # 移除命名空间前缀
            if namespace:
                prefix = f"{namespace}:"
                return [key.decode().replace(prefix, '', 1) if isinstance(key, bytes) else key.replace(prefix, '', 1) for key in keys]
            
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
            
        except Exception as e:
            logger.error(f"Cache keys error for pattern {pattern}: {e}")
            return []
    
    async def clear_namespace(self, namespace: str) -> int:
        """清除命名空间下的所有缓存"""
        try:
            keys = await self.keys("*", namespace)
            if not keys:
                return 0
            
            # 删除所有键
            cache_keys = [self._make_key(key, namespace) for key in keys]
            result = await self.client.delete(*cache_keys)
            return result
            
        except Exception as e:
            logger.error(f"Cache clear namespace error for {namespace}: {e}")
            return 0
    
    async def flush_all(self) -> bool:
        """清除所有缓存"""
        try:
            await self._ensure_connected()
            
            result = await self.client.flushdb()
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache flush all error: {e}")
            return False
    
    async def get_info(self) -> Dict[str, Any]:
        """获取Redis信息"""
        try:
            await self._ensure_connected()
            
            info = await self.client.info()
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
            
        except Exception as e:
            logger.error(f"Cache info error: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            await self._ensure_connected()
            
            # 测试连接
            start_time = datetime.now()
            await self.client.ping()
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 获取基本信息
            info = await self.get_info()
            
            # 计算命中率
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
            
            status = "healthy"
            if response_time > 0.1:  # 100ms
                status = "warning"
            if response_time > 1.0:  # 1s
                status = "unhealthy"
            
            return {
                "status": status,
                "response_time": response_time,
                "hit_rate": hit_rate,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "Unknown"),
                "uptime": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"Cache health check error: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # 高级缓存操作
    async def get_or_set(
        self, 
        key: str, 
        factory_func, 
        ttl: int = None, 
        namespace: str = None, 
        serializer: str = None
    ) -> Any:
        """获取缓存值，如果不存在则通过工厂函数生成并缓存"""
        # 尝试获取缓存值
        value = await self.get(key, namespace, serializer)
        if value is not None:
            return value
        
        # 生成新值
        try:
            if asyncio.iscoroutinefunction(factory_func):
                new_value = await factory_func()
            else:
                new_value = factory_func()
            
            # 缓存新值
            await self.set(key, new_value, ttl, namespace, serializer)
            return new_value
            
        except Exception as e:
            logger.error(f"Factory function error for key {key}: {e}")
            raise
    
    async def increment(self, key: str, amount: int = 1, namespace: str = None) -> int:
        """递增计数器"""
        try:
            await self._ensure_connected()
            
            cache_key = self._make_key(key, namespace)
            result = await self.client.incr(cache_key, amount)
            return result
            
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    async def decrement(self, key: str, amount: int = 1, namespace: str = None) -> int:
        """递减计数器"""
        try:
            await self._ensure_connected()
            
            cache_key = self._make_key(key, namespace)
            result = await self.client.decr(cache_key, amount)
            return result
            
        except Exception as e:
            logger.error(f"Cache decrement error for key {key}: {e}")
            return 0
    
    @asynccontextmanager
    async def lock(self, key: str, timeout: int = 10, namespace: str = None):
        """分布式锁"""
        lock_key = self._make_key(f"lock:{key}", namespace)
        lock_value = f"{datetime.now().timestamp()}"
        acquired = False
        
        try:
            await self._ensure_connected()
            
            # 尝试获取锁
            result = await self.client.set(lock_key, lock_value, nx=True, ex=timeout)
            acquired = bool(result)
            
            if not acquired:
                raise RuntimeError(f"Failed to acquire lock for key: {key}")
            
            yield
            
        finally:
            if acquired:
                try:
                    await self.client.delete(lock_key)
                except Exception as e:
                    logger.error(f"Error releasing lock for key {key}: {e}")
    
    # 批量操作
    async def mget(self, keys: List[str], namespace: str = None, serializer: str = None) -> Dict[str, Any]:
        """批量获取缓存值"""
        try:
            await self._ensure_connected()
            
            cache_keys = [self._make_key(key, namespace) for key in keys]
            values = await self.client.mget(cache_keys)
            
            result = {}
            for i, key in enumerate(keys):
                if values[i] is not None:
                    result[key] = self._deserialize(values[i], serializer)
                else:
                    result[key] = None
            
            return result
            
        except Exception as e:
            logger.error(f"Cache mget error: {e}")
            return {key: None for key in keys}
    
    async def mset(self, mapping: Dict[str, Any], ttl: int = None, namespace: str = None, serializer: str = None) -> bool:
        """批量设置缓存值"""
        try:
            await self._ensure_connected()
            
            # 序列化所有值
            cache_mapping = {}
            for key, value in mapping.items():
                cache_key = self._make_key(key, namespace)
                cache_mapping[cache_key] = self._serialize(value, serializer)
            
            # 批量设置
            result = await self.client.mset(cache_mapping)
            
            # 如果指定了TTL，需要单独设置过期时间
            if ttl and result:
                for cache_key in cache_mapping.keys():
                    await self.client.expire(cache_key, ttl)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            return False


# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例（单例模式）"""
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager()
    
    return _cache_manager


# 便捷函数
async def init_cache():
    """初始化缓存"""
    cache = get_cache_manager()
    await cache.connect()
    logger.info("Cache initialized successfully")


async def close_cache():
    """关闭缓存连接"""
    cache = get_cache_manager()
    await cache.disconnect()
    logger.info("Cache closed successfully")


# 装饰器
def cached(ttl: int = None, namespace: str = None, key_func=None):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 尝试从缓存获取
            result = await cache.get(cache_key, namespace)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await cache.set(cache_key, result, ttl, namespace)
            return result
        
        return wrapper
    return decorator