from typing import Dict, Optional, Any
import asyncio
import logging
from contextlib import asynccontextmanager

from shared.exchanges import BaseExchange, get_exchange_manager, ExchangeType
from .config import settings

logger = logging.getLogger(__name__)


class ExchangePool:
    """交易所连接池
    
    管理多个交易所的连接实例，提供连接复用和自动管理功能
    """
    
    def __init__(self):
        self._connections: Dict[str, BaseExchange] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self.exchange_manager = get_exchange_manager()
    
    def _get_connection_key(self, exchange_name: str, api_key: str, testnet: bool = False) -> str:
        """生成连接键"""
        return f"{exchange_name}:{api_key[:8]}:{'testnet' if testnet else 'mainnet'}"
    
    async def get_exchange(self, exchange_name: str, api_key: str, api_secret: str,
                          testnet: bool = False, **kwargs) -> BaseExchange:
        """获取交易所实例
        
        Args:
            exchange_name: 交易所名称
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网
            **kwargs: 其他参数
            
        Returns:
            交易所实例
        """
        connection_key = self._get_connection_key(exchange_name, api_key, testnet)
        
        # 获取或创建锁
        if connection_key not in self._locks:
            self._locks[connection_key] = asyncio.Lock()
        
        async with self._locks[connection_key]:
            # 检查是否已存在连接
            if connection_key in self._connections:
                return self._connections[connection_key]
            
            # 创建新连接
            exchange = self.exchange_manager.create_exchange(
                exchange_name, api_key, api_secret, testnet, **kwargs
            )
            
            # 连接到交易所
            await exchange.connect()
            
            # 存储连接
            self._connections[connection_key] = exchange
            
            logger.info(f"已创建交易所连接: {exchange_name} ({'测试网' if testnet else '主网'})")
            
            return exchange
    
    @asynccontextmanager
    async def get_exchange_context(self, exchange_name: str, api_key: str, api_secret: str,
                                  testnet: bool = False, **kwargs):
        """获取交易所上下文管理器
        
        使用完毕后不会关闭连接，连接会保留在池中供复用
        """
        exchange = await self.get_exchange(exchange_name, api_key, api_secret, testnet, **kwargs)
        try:
            yield exchange
        except Exception as e:
            logger.error(f"交易所操作异常: {e}")
            raise
    
    async def close_exchange(self, exchange_name: str, api_key: str, testnet: bool = False) -> bool:
        """关闭指定的交易所连接
        
        Args:
            exchange_name: 交易所名称
            api_key: API密钥
            testnet: 是否使用测试网
            
        Returns:
            是否成功关闭
        """
        connection_key = self._get_connection_key(exchange_name, api_key, testnet)
        
        if connection_key in self._connections:
            exchange = self._connections[connection_key]
            await exchange.disconnect()
            del self._connections[connection_key]
            
            if connection_key in self._locks:
                del self._locks[connection_key]
            
            logger.info(f"已关闭交易所连接: {exchange_name}")
            return True
        
        return False
    
    async def close_all(self) -> None:
        """关闭所有交易所连接"""
        for connection_key, exchange in list(self._connections.items()):
            try:
                await exchange.disconnect()
                logger.info(f"已关闭连接: {connection_key}")
            except Exception as e:
                logger.error(f"关闭连接失败 {connection_key}: {e}")
        
        self._connections.clear()
        self._locks.clear()
        logger.info("已关闭所有交易所连接")
    
    def get_active_connections(self) -> Dict[str, str]:
        """获取活跃连接信息
        
        Returns:
            连接信息字典
        """
        return {
            key: exchange.get_exchange_info().display_name
            for key, exchange in self._connections.items()
        }
    
    def get_connection_count(self) -> int:
        """获取连接数量"""
        return len(self._connections)


class DefaultExchangePool:
    """默认交易所连接池
    
    使用配置文件中的默认API密钥
    """
    
    def __init__(self):
        self.pool = ExchangePool()
        self._default_configs = {
            "gateio": {
                "api_key": settings.GATEIO_API_KEY,
                "api_secret": settings.GATEIO_API_SECRET,
                "testnet": settings.GATEIO_TESTNET
            }
        }
    
    async def get_default_exchange(self, exchange_name: str) -> Optional[BaseExchange]:
        """获取默认配置的交易所实例
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            交易所实例，如果配置不存在返回None
        """
        if exchange_name not in self._default_configs:
            return None
        
        config = self._default_configs[exchange_name]
        
        if not config["api_key"] or not config["api_secret"]:
            logger.warning(f"交易所 {exchange_name} 的API密钥未配置")
            return None
        
        return await self.pool.get_exchange(
            exchange_name,
            config["api_key"],
            config["api_secret"],
            config["testnet"]
        )
    
    @asynccontextmanager
    async def get_default_exchange_context(self, exchange_name: str):
        """获取默认交易所上下文管理器"""
        exchange = await self.get_default_exchange(exchange_name)
        if not exchange:
            raise ValueError(f"无法获取交易所 {exchange_name} 的默认配置")
        
        try:
            yield exchange
        except Exception as e:
            logger.error(f"默认交易所操作异常: {e}")
            raise
    
    async def close_all(self):
        """关闭所有连接"""
        await self.pool.close_all()


# 全局交易所连接池实例
exchange_pool = DefaultExchangePool()