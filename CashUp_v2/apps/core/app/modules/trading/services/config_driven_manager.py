"""
配置驱动的交易所接入模块
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from pathlib import Path

from trading_engine.config.exchange_config import ExchangeConfigManager, ExchangeConfig
from trading_engine.exchanges.base import ExchangeBase, ExchangeAdapter, ExchangeManager
from trading_engine.exchanges.binance import BinanceExchange
from trading_engine.exchanges.gateio import GateIOExchange

logger = logging.getLogger(__name__)

class ExchangeFactory:
    """交易所工厂类"""
    
    # 交易所类型映射
    _exchange_classes: Dict[str, Type[ExchangeBase]] = {
        'binance': BinanceExchange,
        'gateio': GateIOExchange,
        # 可以继续添加其他交易所
        # 'okx': OKXExchange,
        # 'huobi': HuobiExchange,
        # 'bybit': BybitExchange,
    }
    
    @classmethod
    def register_exchange(cls, exchange_type: str, exchange_class: Type[ExchangeBase]):
        """注册新的交易所类型"""
        cls._exchange_classes[exchange_type] = exchange_class
        logger.info(f"已注册交易所类型: {exchange_type}")
    
    @classmethod
    def create_exchange(cls, config: ExchangeConfig) -> Optional[ExchangeBase]:
        """根据配置创建交易所实例"""
        exchange_class = cls._exchange_classes.get(config.type)
        
        if not exchange_class:
            logger.error(f"不支持的交易所类型: {config.type}")
            return None
        
        try:
            # 转换配置为字典格式
            config_dict = {
                'name': config.name,
                'api_key': config.api_key,
                'api_secret': config.api_secret,
                'sandbox': config.sandbox,
                'rate_limit': config.rate_limit,
            }
            
            # 添加交易所特定的配置
            if config.passphrase:
                config_dict['passphrase'] = config.passphrase
            
            # 创建交易所实例
            exchange = exchange_class(config_dict)
            logger.info(f"成功创建交易所实例: {config.name} ({config.type})")
            
            return exchange
            
        except Exception as e:
            logger.error(f"创建交易所实例失败 {config.name}: {e}")
            return None
    
    @classmethod
    def get_supported_exchanges(cls) -> List[str]:
        """获取支持的交易所类型列表"""
        return list(cls._exchange_classes.keys())
    
    @classmethod
    def is_exchange_supported(cls, exchange_type: str) -> bool:
        """检查是否支持指定的交易所类型"""
        return exchange_type in cls._exchange_classes

class ConfigDrivenExchangeManager:
    """配置驱动的交易所管理器"""
    
    def __init__(self, config_path: str = "configs/exchanges.yaml"):
        self.config_manager = ExchangeConfigManager(config_path)
        self.exchange_manager = ExchangeManager()
        self.exchange_adapters: Dict[str, ExchangeAdapter] = {}
        self.health_status: Dict[str, Dict[str, Any]] = {}
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """初始化交易所管理器"""
        try:
            logger.info("正在初始化配置驱动的交易所管理器...")
            
            # 加载配置
            config = self.config_manager.load_config()
            
            # 验证配置
            errors = self.config_manager.validate_config()
            if errors:
                logger.error(f"配置验证失败: {errors}")
                return False
            
            # 初始化启用的交易所
            enabled_exchanges = self.config_manager.get_enabled_exchanges()
            
            for name, exchange_config in enabled_exchanges.items():
                success = await self._initialize_exchange(name, exchange_config)
                if not success:
                    logger.warning(f"初始化交易所失败: {name}")
            
            self.is_initialized = True
            logger.info(f"交易所管理器初始化完成，成功启用 {len(self.exchange_adapters)} 个交易所")
            
            return True
            
        except Exception as e:
            logger.error(f"初始化交易所管理器失败: {e}")
            return False
    
    async def _initialize_exchange(self, name: str, config: ExchangeConfig) -> bool:
        """初始化单个交易所"""
        try:
            # 创建交易所实例
            exchange = ExchangeFactory.create_exchange(config)
            if not exchange:
                return False
            
            # 创建适配器
            adapter = ExchangeAdapter(config.__dict__)
            
            # 测试连接
            if not await adapter.test_connection():
                logger.warning(f"交易所连接测试失败: {name}")
                return False
            
            # 添加到管理器
            self.exchange_manager.add_exchange(name, config.__dict__)
            self.exchange_adapters[name] = adapter
            
            # 初始化健康状态
            self.health_status[name] = {
                'status': 'healthy',
                'last_check': None,
                'error_count': 0,
                'response_time': 0,
                'enabled': True
            }
            
            logger.info(f"成功初始化交易所: {name}")
            return True
            
        except Exception as e:
            logger.error(f"初始化交易所失败 {name}: {e}")
            return False
    
    async def reload_config(self) -> bool:
        """重新加载配置"""
        try:
            logger.info("正在重新加载交易所配置...")
            
            # 保存当前配置
            old_enabled = set(self.config_manager.get_enabled_exchange_names())
            
            # 重新加载配置
            config = self.config_manager.load_config()
            
            # 获取新的启用列表
            new_enabled = set(self.config_manager.get_enabled_exchange_names())
            
            # 计算变更
            to_remove = old_enabled - new_enabled
            to_add = new_enabled - old_enabled
            to_reload = new_enabled & old_enabled
            
            # 移除不再启用的交易所
            for name in to_remove:
                await self._disable_exchange(name)
            
            # 重新加载配置变更的交易所
            for name in to_reload:
                await self._reload_exchange(name)
            
            # 添加新启用的交易所
            for name in to_add:
                exchange_config = self.config_manager.get_exchange_config(name)
                if exchange_config:
                    await self._initialize_exchange(name, exchange_config)
            
            logger.info(f"配置重新加载完成: 移除 {len(to_remove)} 个，添加 {len(to_add)} 个，重载 {len(to_reload)} 个")
            return True
            
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            return False
    
    async def _disable_exchange(self, name: str):
        """禁用交易所"""
        try:
            if name in self.exchange_adapters:
                # 清理资源
                adapter = self.exchange_adapters[name]
                # TODO: 关闭WebSocket连接等清理工作
                
                # 从管理器中移除
                self.exchange_manager.remove_exchange(name)
                del self.exchange_adapters[name]
                
                if name in self.health_status:
                    self.health_status[name]['enabled'] = False
                    self.health_status[name]['status'] = 'disabled'
                
                logger.info(f"已禁用交易所: {name}")
                
        except Exception as e:
            logger.error(f"禁用交易所失败 {name}: {e}")
    
    async def _reload_exchange(self, name: str):
        """重新加载交易所配置"""
        try:
            # 先禁用
            await self._disable_exchange(name)
            
            # 获取新配置
            exchange_config = self.config_manager.get_exchange_config(name)
            if exchange_config:
                # 重新初始化
                await self._initialize_exchange(name, exchange_config)
            
        except Exception as e:
            logger.error(f"重新加载交易所失败 {name}: {e}")
    
    def get_exchange_adapter(self, name: str) -> Optional[ExchangeAdapter]:
        """获取交易所适配器"""
        return self.exchange_adapters.get(name)
    
    def get_exchange_adapters(self) -> Dict[str, ExchangeAdapter]:
        """获取所有交易所适配器"""
        return self.exchange_adapters.copy()
    
    def get_enabled_exchanges(self) -> List[str]:
        """获取所有启用的交易所名称"""
        return list(self.exchange_adapters.keys())
    
    def is_exchange_enabled(self, name: str) -> bool:
        """检查交易所是否启用"""
        return name in self.exchange_adapters
    
    async def test_exchange_connection(self, name: str) -> bool:
        """测试交易所连接"""
        adapter = self.get_exchange_adapter(name)
        if not adapter:
            return False
        
        try:
            start_time = asyncio.get_event_loop().time()
            result = await adapter.test_connection()
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # 更新健康状态
            if name in self.health_status:
                status = self.health_status[name]
                status['last_check'] = asyncio.get_event_loop().time()
                status['response_time'] = response_time
                
                if result:
                    status['status'] = 'healthy'
                    status['error_count'] = 0
                else:
                    status['status'] = 'unhealthy'
                    status['error_count'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"测试交易所连接失败 {name}: {e}")
            return False
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """测试所有交易所连接"""
        results = {}
        
        for name in self.get_enabled_exchanges():
            results[name] = await self.test_exchange_connection(name)
        
        return results
    
    def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有交易所的健康状态"""
        return self.health_status.copy()
    
    def get_exchange_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取交易所信息"""
        adapter = self.get_exchange_adapter(name)
        if not adapter:
            return None
        
        info = adapter.get_info()
        info['health_status'] = self.health_status.get(name, {})
        
        return info
    
    def get_all_exchanges_info(self) -> List[Dict[str, Any]]:
        """获取所有交易所信息"""
        info_list = []
        
        for name, adapter in self.exchange_adapters.items():
            info = adapter.get_info()
            info['health_status'] = self.health_status.get(name, {})
            info_list.append(info)
        
        return info_list
    
    async def enable_exchange(self, name: str) -> bool:
        """启用交易所"""
        if name in self.exchange_adapters:
            logger.warning(f"交易所已启用: {name}")
            return True
        
        # 更新配置
        if not self.config_manager.enable_exchange(name):
            return False
        
        # 获取配置并初始化
        exchange_config = self.config_manager.get_exchange_config(name)
        if exchange_config:
            return await self._initialize_exchange(name, exchange_config)
        
        return False
    
    async def disable_exchange(self, name: str) -> bool:
        """禁用交易所"""
        if name not in self.exchange_adapters:
            logger.warning(f"交易所未启用: {name}")
            return True
        
        # 更新配置
        if not self.config_manager.disable_exchange(name):
            return False
        
        # 禁用交易所
        await self._disable_exchange(name)
        return True
    
    async def update_exchange_config(self, name: str, updates: Dict[str, Any]) -> bool:
        """更新交易所配置"""
        # 更新配置文件
        if not self.config_manager.update_exchange_config(name, updates):
            return False
        
        # 如果交易所已启用，重新加载
        if name in self.exchange_adapters:
            await self._reload_exchange(name)
        
        return True
    
    async def save_config(self) -> bool:
        """保存配置"""
        return self.config_manager.save_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        summary = self.config_manager.get_config_summary()
        summary['active_exchanges'] = len(self.exchange_adapters)
        summary['exchange_status'] = {
            name: status.get('status', 'unknown') 
            for name, status in self.health_status.items()
        }
        
        return summary
    
    async def health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        results = {
            'timestamp': asyncio.get_event_loop().time(),
            'total_exchanges': len(self.exchange_adapters),
            'healthy_exchanges': 0,
            'unhealthy_exchanges': 0,
            'details': {}
        }
        
        for name in self.get_enabled_exchanges():
            is_healthy = await self.test_exchange_connection(name)
            
            if is_healthy:
                results['healthy_exchanges'] += 1
            else:
                results['unhealthy_exchanges'] += 1
            
            results['details'][name] = {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'response_time': self.health_status[name].get('response_time', 0),
                'error_count': self.health_status[name].get('error_count', 0),
                'last_check': self.health_status[name].get('last_check')
            }
        
        return results
    
    async def close(self):
        """关闭管理器，清理资源"""
        try:
            logger.info("正在关闭交易所管理器...")
            
            # 关闭所有交易所连接
            for name, adapter in self.exchange_adapters.items():
                try:
                    # TODO: 实现具体的关闭逻辑
                    # await adapter.close()
                    logger.info(f"已关闭交易所连接: {name}")
                except Exception as e:
                    logger.error(f"关闭交易所连接失败 {name}: {e}")
            
            self.exchange_adapters.clear()
            self.health_status.clear()
            
            logger.info("交易所管理器已关闭")
            
        except Exception as e:
            logger.error(f"关闭交易所管理器失败: {e}")

# 全局实例
_exchange_manager: Optional[ConfigDrivenExchangeManager] = None

def get_exchange_manager() -> ConfigDrivenExchangeManager:
    """获取全局交易所管理器实例"""
    global _exchange_manager
    if _exchange_manager is None:
        _exchange_manager = ConfigDrivenExchangeManager()
    return _exchange_manager

async def initialize_exchange_manager(config_path: str = "configs/exchanges.yaml") -> ConfigDrivenExchangeManager:
    """初始化全局交易所管理器"""
    global _exchange_manager
    _exchange_manager = ConfigDrivenExchangeManager(config_path)
    await _exchange_manager.initialize()
    return _exchange_manager