"""
配置管理服务 - 简化版本，避免aioredis依赖
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigService:
    """配置管理服务"""

    def __init__(self):
        self.config_cache: Dict[str, Dict[str, Any]] = {}
        self.exchange_configs: Dict[str, Dict[str, Any]] = {
            'gateio': {
                'name': 'Gate.io',
                'api_key': '',
                'api_secret': '',
                'sandbox': True,
                'base_url': 'https://fx-api-testnet.gateio.ws',
                'ws_url': 'wss://fx-ws-testnet.gateio.ws'
            },
            'binance': {
                'name': 'Binance',
                'api_key': '',
                'api_secret': '',
                'sandbox': True,
                'base_url': 'https://testnet.binance.vision',
                'ws_url': 'wss://testnet.binance.vision'
            }
        }
        self.trading_config = {
            'default_leverage': 3,
            'max_position_size': 100.0,
            'risk_limits': {
                'max_daily_loss': 10.0,  # 10% of account
                'max_position_ratio': 0.3,  # 30% of account
                'stop_loss_ratio': 0.02,  # 2% stop loss
                'take_profit_ratio': 0.05  # 5% take profit
            },
            'simulation_mode': True,
            'simulation_balance': 10000.0
        }
        self.cache_ttl = 300  # 5分钟缓存

    def initialize(self):
        """初始化配置服务"""
        # 初始化默认配置到缓存
        for exchange_name, config in self.exchange_configs.items():
            self.config_cache[f"exchange_config:{exchange_name}"] = config

        self.config_cache["trading_config"] = self.trading_config

        # 从环境变量加载API密钥
        import os
        gateio_config = self.exchange_configs.get('gateio', {})
        gateio_config['api_key'] = os.getenv('GATE_IO_API_KEY', '')
        gateio_config['api_secret'] = os.getenv('GATE_IO_SECRET_KEY', '')

        binance_config = self.exchange_configs.get('binance', {})
        binance_config['api_key'] = os.getenv('BINANCE_API_KEY', '')
        binance_config['api_secret'] = os.getenv('BINANCE_SECRET_KEY', '')

        logger.info("配置服务初始化完成")

    def get_exchange_config(self, exchange_name: str) -> Optional[Dict[str, Any]]:
        """获取交易所配置"""
        cache_key = f"exchange_config:{exchange_name}"

        # 从缓存获取
        if cache_key in self.config_cache:
            return self.config_cache[cache_key]

        # 从主配置获取
        if exchange_name in self.exchange_configs:
            return self.exchange_configs[exchange_name]

        return None

    def get_api_credentials(self, exchange_name: str) -> Dict[str, str]:
        """获取API凭证"""
        config = self.get_exchange_config(exchange_name)
        if config:
            return {
                'api_key': config.get('api_key', ''),
                'api_secret': config.get('api_secret', ''),
                'passphrase': config.get('passphrase', '')
            }
        return {}

    def get_trading_config(self) -> Dict[str, Any]:
        """获取交易配置"""
        return self.trading_config

    def get_simulation_config(self) -> Dict[str, Any]:
        """获取模拟交易配置"""
        return self.trading_config.get('simulation_mode', {})

    def update_exchange_config(self, exchange_name: str, config: Dict[str, Any]) -> bool:
        """更新交易所配置"""
        try:
            # 更新主配置
            if exchange_name in self.exchange_configs:
                self.exchange_configs[exchange_name].update(config)
            else:
                self.exchange_configs[exchange_name] = config

            # 更新缓存
            cache_key = f"exchange_config:{exchange_name}"
            self.config_cache[cache_key] = config

            logger.info(f"更新交易所配置成功: {exchange_name}")
            return True
        except Exception as e:
            logger.error(f"更新交易所配置失败: {e}")
            return False

    def set_api_credentials(self, exchange_name: str, credentials: Dict[str, str]) -> bool:
        """设置API凭证"""
        try:
            config = self.get_exchange_config(exchange_name)
            if config:
                config.update(credentials)
                self.update_exchange_config(exchange_name, config)
                logger.info(f"设置API凭证成功: {exchange_name}")
                return True
        except Exception as e:
            logger.error(f"设置API凭证失败: {e}")
            return False

    def get_all_exchange_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有交易所配置"""
        return self.exchange_configs

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取配置"""
        return self.config_cache.get(key)

    def _set_cache(self, key: str, value: Dict[str, Any]):
        """设置缓存"""
        self.config_cache[key] = value