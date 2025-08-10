from typing import Dict, List, Type, Optional, Any
from .base import BaseExchange, ExchangeInfo, ExchangeType
import logging

logger = logging.getLogger(__name__)


class ExchangeManager:
    """交易所管理器
    
    负责注册、管理和创建交易所实例
    """
    
    def __init__(self):
        self._exchanges: Dict[str, Type[BaseExchange]] = {}
        self._exchange_infos: Dict[str, ExchangeInfo] = {}
    
    def register_exchange(self, exchange_class: Type[BaseExchange]) -> None:
        """注册交易所
        
        Args:
            exchange_class: 交易所类
        """
        # 创建临时实例获取交易所信息
        temp_instance = exchange_class("", "", testnet=True)
        exchange_info = temp_instance.get_exchange_info()
        
        self._exchanges[exchange_info.name] = exchange_class
        self._exchange_infos[exchange_info.name] = exchange_info
        
        logger.info(f"已注册交易所: {exchange_info.display_name} ({exchange_info.name})")
    
    def get_available_exchanges(self) -> List[ExchangeInfo]:
        """获取所有可用的交易所列表
        
        Returns:
            交易所信息列表
        """
        return list(self._exchange_infos.values())
    
    def get_exchange_info(self, exchange_name: str) -> Optional[ExchangeInfo]:
        """获取指定交易所信息
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            交易所信息，如果不存在返回None
        """
        return self._exchange_infos.get(exchange_name)
    
    def is_exchange_available(self, exchange_name: str) -> bool:
        """检查交易所是否可用
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            是否可用
        """
        return exchange_name in self._exchanges
    
    def get_exchanges_by_type(self, exchange_type: ExchangeType) -> List[ExchangeInfo]:
        """根据交易类型获取支持的交易所
        
        Args:
            exchange_type: 交易类型
            
        Returns:
            支持该交易类型的交易所列表
        """
        return [
            info for info in self._exchange_infos.values()
            if exchange_type in info.supported_types
        ]
    
    def create_exchange(self, exchange_name: str, api_key: str, api_secret: str,
                       testnet: bool = False, **kwargs) -> BaseExchange:
        """创建交易所实例
        
        Args:
            exchange_name: 交易所名称
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网
            **kwargs: 其他参数
            
        Returns:
            交易所实例
            
        Raises:
            ValueError: 交易所不存在
        """
        if exchange_name not in self._exchanges:
            available = list(self._exchanges.keys())
            raise ValueError(f"交易所 '{exchange_name}' 不存在。可用交易所: {available}")
        
        exchange_class = self._exchanges[exchange_name]
        return exchange_class(api_key, api_secret, testnet, **kwargs)
    
    def get_exchange_names(self) -> List[str]:
        """获取所有交易所名称
        
        Returns:
            交易所名称列表
        """
        return list(self._exchanges.keys())
    
    def unregister_exchange(self, exchange_name: str) -> bool:
        """注销交易所
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            是否成功注销
        """
        if exchange_name in self._exchanges:
            del self._exchanges[exchange_name]
            del self._exchange_infos[exchange_name]
            logger.info(f"已注销交易所: {exchange_name}")
            return True
        return False
    
    def clear_all(self) -> None:
        """清空所有注册的交易所"""
        self._exchanges.clear()
        self._exchange_infos.clear()
        logger.info("已清空所有注册的交易所")


# 全局交易所管理器实例
exchange_manager = ExchangeManager()


def register_exchange(exchange_class: Type[BaseExchange]) -> None:
    """注册交易所的便捷函数
    
    Args:
        exchange_class: 交易所类
    """
    exchange_manager.register_exchange(exchange_class)


def get_exchange_manager() -> ExchangeManager:
    """获取全局交易所管理器
    
    Returns:
        交易所管理器实例
    """
    return exchange_manager