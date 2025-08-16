#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis缓存管理

提供Redis连接管理、缓存操作、会话存储等功能，
支持策略数据缓存、回测结果缓存等。
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import redis
import logging

from .config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Redis缓存管理器
    
    提供Redis连接管理、数据缓存、会话管理等功能
    """
    
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """
        建立Redis连接
        """
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis连接建立成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            Any: 缓存值，不存在返回None
        """
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # 尝试JSON解析
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # 如果不是JSON，返回原始字符串
                return value
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）
            
        Returns:
            bool: 是否设置成功
        """
        try:
            # 序列化值
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, (int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            result = self.redis_client.set(key, serialized_value, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        try:
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"检查缓存存在性失败 {key}: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        设置缓存过期时间
        
        Args:
            key: 缓存键
            seconds: 过期时间（秒）
            
        Returns:
            bool: 是否设置成功
        """
        try:
            result = self.redis_client.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"设置缓存过期时间失败 {key}: {e}")
            return False
    
    def get_keys(self, pattern: str = "*") -> List[str]:
        """
        获取匹配模式的所有键
        
        Args:
            pattern: 匹配模式
            
        Returns:
            List[str]: 键列表
        """
        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"获取键列表失败 {pattern}: {e}")
            return []
    
    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            int: 删除的键数量
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"清除缓存失败 {pattern}: {e}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """
        Redis健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        try:
            info = self.redis_client.info()
            ping_result = self.redis_client.ping()
            
            return {
                "status": "healthy" if ping_result else "unhealthy",
                "version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
                "keyspace": info.get(f"db{settings.redis_db}", {})
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def close(self):
        """
        关闭Redis连接
        """
        if self.redis_client:
            self.redis_client.close()
            logger.info("Redis连接已关闭")


class StrategyCache:
    """
    策略专用缓存管理器
    
    提供策略数据、回测结果、性能指标等专用缓存功能
    """
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        self.prefix = "strategy:"
    
    def _make_key(self, key: str) -> str:
        """
        生成带前缀的缓存键
        
        Args:
            key: 原始键
            
        Returns:
            str: 带前缀的键
        """
        return f"{self.prefix}{key}"
    
    def cache_strategy_data(self, strategy_id: str, data: Dict[str, Any], expire: int = 3600) -> bool:
        """
        缓存策略数据
        
        Args:
            strategy_id: 策略ID
            data: 策略数据
            expire: 过期时间（秒）
            
        Returns:
            bool: 是否缓存成功
        """
        key = self._make_key(f"data:{strategy_id}")
        return self.redis.set(key, data, expire)
    
    def get_strategy_data(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """
        获取策略数据
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            Optional[Dict[str, Any]]: 策略数据
        """
        key = self._make_key(f"data:{strategy_id}")
        return self.redis.get(key)
    
    def cache_backtest_result(self, strategy_id: str, backtest_id: str, result: Dict[str, Any], expire: int = 86400) -> bool:
        """
        缓存回测结果
        
        Args:
            strategy_id: 策略ID
            backtest_id: 回测ID
            result: 回测结果
            expire: 过期时间（秒）
            
        Returns:
            bool: 是否缓存成功
        """
        key = self._make_key(f"backtest:{strategy_id}:{backtest_id}")
        return self.redis.set(key, result, expire)
    
    def get_backtest_result(self, strategy_id: str, backtest_id: str) -> Optional[Dict[str, Any]]:
        """
        获取回测结果
        
        Args:
            strategy_id: 策略ID
            backtest_id: 回测ID
            
        Returns:
            Optional[Dict[str, Any]]: 回测结果
        """
        key = self._make_key(f"backtest:{strategy_id}:{backtest_id}")
        return self.redis.get(key)
    
    def clear_strategy_cache(self, strategy_id: str) -> int:
        """
        清除策略相关缓存
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            int: 删除的缓存数量
        """
        pattern = self._make_key(f"*{strategy_id}*")
        return self.redis.clear_pattern(pattern)


# 全局Redis管理器实例
redis_manager = RedisManager()

# 全局策略缓存实例
strategy_cache = StrategyCache(redis_manager)


def get_redis() -> RedisManager:
    """
    获取Redis管理器实例
    
    Returns:
        RedisManager: Redis管理器
    """
    return redis_manager


def get_strategy_cache() -> StrategyCache:
    """
    获取策略缓存实例
    
    Returns:
        StrategyCache: 策略缓存管理器
    """
    return strategy_cache