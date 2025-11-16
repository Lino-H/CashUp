"""
Redis连接管理
"""

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