"""
配置管理服务 - 从数据库和缓存中获取配置信息
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigService:
    """配置管理服务"""

    def __init__(self, db_pool=None, redis_client=None):
        self.db_pool = db_pool
        self.redis_client = redis_client
        self.config_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 300  # 5分钟缓存

    def initialize(self):
        """初始化配置服务（同步版本）"""
        if self.redis_client:
            # 如果有Redis客户端，暂时跳过缓存加载
            pass

    async def get_exchange_config(self, exchange_name: str) -> Optional[Dict[str, Any]]:
        """获取交易所配置"""
        cache_key = f"exchange_config:{exchange_name}"

        # 先从缓存获取
        cached_config = await self._get_from_cache(cache_key)
        if cached_config:
            return cached_config

        # 从数据库获取
        config = await self._get_exchange_config_from_db(exchange_name)

        if config:
            # 存入缓存
            await self._set_cache(cache_key, config)

        return config

    async def get_api_credentials(self, exchange_name: str) -> Dict[str, str]:
        """获取API凭证"""
        config = await self.get_exchange_config(exchange_name)
        if config:
            # 注意：API密钥应该从加密的数据库字段中获取
            # 这里简化处理，实际应该从专门的密钥管理服务获取
            return {
                'api_key': config.get('api_key', ''),
                'api_secret': config.get('api_secret', ''),
                'passphrase': config.get('passphrase', '')
            }
        return {}

    async def update_exchange_config(self, exchange_name: str, config: Dict[str, Any]) -> bool:
        """更新交易所配置"""
        try:
            # 更新数据库
            success = await self._update_exchange_config_in_db(exchange_name, config)

            if success:
                # 更新缓存
                cache_key = f"exchange_config:{exchange_name}"
                await self._set_cache(cache_key, config)

            return success
        except Exception as e:
            logger.error(f"更新交易所配置失败: {e}")
            return False

    async def set_api_credentials(self, exchange_name: str, credentials: Dict[str, str]) -> bool:
        """设置API凭证（加密存储）"""
        try:
            # 注意：实际应该加密存储
            config = await self.get_exchange_config(exchange_name)
            if not config:
                config = {'name': exchange_name}

            config.update({
                'api_key': credentials.get('api_key'),
                'api_secret': credentials.get('api_secret'),
                'passphrase': credentials.get('passphrase'),
                'updated_at': datetime.now().isoformat()
            })

            return await self.update_exchange_config(exchange_name, config)
        except Exception as e:
            logger.error(f"设置API凭证失败: {e}")
            return False

    async def get_trading_config(self) -> Dict[str, Any]:
        """获取交易配置"""
        cache_key = "trading_config"

        cached_config = await self._get_from_cache(cache_key)
        if cached_config:
            return cached_config

        config = await self._get_trading_config_from_db()
        if config:
            await self._set_cache(cache_key, config)

        return config or {
            'default_leverage': 3,
            'max_position_size': 10.0,
            'commission_rate': 0.001,
            'max_daily_loss': 1000.0,
            'risk_management_enabled': True
        }

    async def get_simulation_config(self) -> Dict[str, Any]:
        """获取模拟交易配置"""
        cache_key = "simulation_config"

        cached_config = await self._get_from_cache(cache_key)
        if cached_config:
            return cached_config

        config = await self._get_simulation_config_from_db()
        if config:
            await self._set_cache(cache_key, config)

        return config or {
            'initial_balance': {'USDT': 10000.0},
            'commission_rate': 0.0,
            'simulation_mode': True,
            'enable_slippage': True,
            'slippage_rate': 0.001
        }

    async def list_exchanges(self) -> Dict[str, Any]:
        """列出所有交易所配置"""
        cache_key = "exchange_list"

        cached_list = await self._get_from_cache(cache_key)
        if cached_list:
            return cached_list

        exchanges = await self._list_exchanges_from_db()

        if exchanges:
            await self._set_cache(cache_key, exchanges)

        return exchanges or {
            'gateio': {'name': 'Gate.io', 'type': 'spot_futures', 'enabled': True},
            'binance': {'name': 'Binance', 'type': 'spot_futures', 'enabled': True},
            'okx': {'name': 'OKX', 'type': 'spot_futures', 'enabled': False}
        }

    # 私有方法
    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if not self.redis_client:
            return self.config_cache.get(key)

        try:
            cached = await self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis获取缓存失败: {e}")

        return None

    async def _set_cache(self, key: str, value: Any):
        """设置缓存"""
        if not self.redis_client:
            self.config_cache[key] = value
            return

        try:
            await self.redis_client.setex(
                key,
                self.cache_ttl,
                json.dumps(value, default=str)
            )
        except Exception as e:
            logger.warning(f"Redis设置缓存失败: {e}")
            self.config_cache[key] = value

    async def _load_config_to_cache(self):
        """加载所有配置到缓存"""
        if not self.redis_client:
            return

        try:
            # 预加载常用配置
            await self.get_exchange_config('gateio')
            await self.get_trading_config()
            await self.get_simulation_config()
            await self.list_exchanges()

            logger.info("配置已加载到缓存")
        except Exception as e:
            logger.warning(f"预加载配置失败: {e}")

    # 数据库操作（简化版，实际应该使用SQLAlchemy）
    async def _get_exchange_config_from_db(self, exchange_name: str) -> Optional[Dict[str, Any]]:
        """从数据库获取交易所配置"""
        if not self.db_pool:
            # 如果没有数据库，返回默认配置
            return self._get_default_exchange_config(exchange_name)

        try:
            async with self.db_pool.acquire() as conn:
                # 注意：这里应该使用正确的SQL查询
                # 以下是简化示例
                query = "SELECT config FROM exchange_configs WHERE name = $1"
                result = await conn.fetchrow(query, exchange_name)

                if result:
                    return json.loads(result['config'])
        except Exception as e:
            logger.error(f"从数据库获取交易所配置失败: {e}")

        return self._get_default_exchange_config(exchange_name)

    async def _update_exchange_config_in_db(self, exchange_name: str, config: Dict[str, Any]) -> bool:
        """更新数据库中的交易所配置"""
        if not self.db_pool:
            return False

        try:
            async with self.db_pool.acquire() as conn:
                # 注意：这里应该使用正确的SQL查询
                query = """
                INSERT INTO exchange_configs (name, config, updated_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (name) DO UPDATE SET
                config = $2, updated_at = $3
                """
                await conn.execute(
                    query,
                    exchange_name,
                    json.dumps(config),
                    datetime.now().isoformat()
                )
                return True
        except Exception as e:
            logger.error(f"更新数据库配置失败: {e}")
            return False

    async def _get_trading_config_from_db(self) -> Optional[Dict[str, Any]]:
        """从数据库获取交易配置"""
        if not self.db_pool:
            return None

        try:
            async with self.db_pool.acquire() as conn:
                query = "SELECT config FROM system_configs WHERE type = 'trading'"
                result = await conn.fetchrow(query)
                return json.loads(result['config']) if result else None
        except Exception as e:
            logger.error(f"从数据库获取交易配置失败: {e}")
            return None

    async def _get_simulation_config_from_db(self) -> Optional[Dict[str, Any]]:
        """从数据库获取模拟配置"""
        if not self.db_pool:
            return None

        try:
            async with self.db_pool.acquire() as conn:
                query = "SELECT config FROM system_configs WHERE type = 'simulation'"
                result = await conn.fetchrow(query)
                return json.loads(result['config']) if result else None
        except Exception as e:
            logger.error(f"从数据库获取模拟配置失败: {e}")
            return None

    async def _list_exchanges_from_db(self) -> Optional[Dict[str, Any]]:
        """从数据库获取交易所列表"""
        if not self.db_pool:
            return None

        try:
            async with self.db_pool.acquire() as conn:
                query = "SELECT name, config FROM exchange_configs WHERE enabled = true"
                results = await conn.fetch(query)

                exchanges = {}
                for row in results:
                    config = json.loads(row['config'])
                    exchanges[row['name']] = {
                        'name': config.get('name', row['name']),
                        'type': config.get('type', 'unknown'),
                        'enabled': config.get('enabled', True)
                    }
                return exchanges
        except Exception as e:
            logger.error(f"从数据库获取交易所列表失败: {e}")
            return None

    def _get_default_exchange_config(self, exchange_name: str) -> Dict[str, Any]:
        """获取默认交易所配置"""
        defaults = {
            'gateio': {
                'name': 'Gate.io',
                'type': 'spot_futures',
                'enabled': True,
                'sandbox': True,  # 默认使用测试环境
                'api_base_url': 'https://fx-api-testnet.gateio.ws',
                'ws_base_url': 'wss://fx-ws-testnet.gateio.ws',
                'rate_limit': 10,
                'supported_symbols': ['ETH/USDT', 'BTC/USDT'],
                'supported_types': ['spot', 'futures'],
                'default_leverage': 3,
                'max_position_size': 10.0
            },
            'binance': {
                'name': 'Binance',
                'type': 'spot_futures',
                'enabled': True,
                'sandbox': True,
                'api_base_url': 'https://testnet.binance.vision',
                'ws_base_url': 'wss://testnet.binance.vision',
                'rate_limit': 5,
                'supported_symbols': ['ETH/USDT', 'BTC/USDT'],
                'supported_types': ['spot', 'futures']
            }
        }

        return defaults.get(exchange_name, {
            'name': exchange_name,
            'type': 'unknown',
            'enabled': False
        })

# 全局配置服务实例
_config_service_instance = None

async def get_config_service() -> ConfigService:
    """获取配置服务实例"""
    global _config_service_instance

    if _config_service_instance is None:
        # 默认配置（实际应该从DI容器获取）
        _config_service_instance = ConfigService()
        await _config_service_instance.initialize()

    return _config_service_instance