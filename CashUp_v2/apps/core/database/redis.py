"""
Redis连接管理
函数集注释：
- RedisManager: 管理Redis连接的获取与关闭
- get_redis: FastAPI依赖函数，返回Redis客户端
- FakeRedis: 测试环境回退实现，提供最小化接口以避免外部依赖
"""

import os
import redis.asyncio as redis
from typing import Optional
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class RedisManager:
    """Redis连接管理器"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def get_redis_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self.redis_client is None:
            # 测试环境回退：当设置 TEST_FAKE_REDIS=true 时，使用内置的轻量客户端
            if str(os.getenv("TEST_FAKE_REDIS", "")).lower() in ("1", "true", "yes"):
                self.redis_client = FakeRedis()
            else:
                self.redis_client = redis.from_url(settings.REDIS_URL)
        return self.redis_client
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

# 全局Redis管理器实例
redis_manager = RedisManager()

async def get_redis() -> redis.Redis:
    """获取Redis连接的依赖函数"""
    return await redis_manager.get_redis_client()


class FakeRedis:
    """测试用轻量Redis客户端
    函数集注释：
    - get: 返回None
    - hgetall: 返回空dict
    - llen: 返回0
    - close: 关闭占位，无操作
    """
    async def get(self, key):
        return None

    async def hgetall(self, key):
        return {}

    async def llen(self, key):
        return 0

    async def close(self):
        return None