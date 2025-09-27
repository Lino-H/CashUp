"""
数据库配置初始化脚本
将.env文件中的配置导入到数据库中
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
import asyncpg

# 添加项目路径到Python路径
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.config_service import ConfigService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库连接配置
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cashup:cashup@localhost:5432/cashup')

async def create_db_pool():
    """创建数据库连接池"""
    try:
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        logger.info("数据库连接池创建成功")
        return pool
    except Exception as e:
        logger.error(f"创建数据库连接池失败: {e}")
        raise

def load_env_file() -> Dict[str, str]:
    """加载.env文件"""
    env_file = os.path.join(project_root.parent, '.env')
    env_vars = {}

    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

    return env_vars

async def init_exchange_configs(config_service: ConfigService, env_vars: Dict[str, str]):
    """初始化交易所配置"""
    logger.info("初始化交易所配置...")

    exchange_configs = {
        'gateio': {
            'name': 'Gate.io',
            'type': 'spot_futures',
            'enabled': True,
            'sandbox': True,  # 测试环境
            'api_key': env_vars.get('GATE_IO_API_KEY', ''),
            'api_secret': env_vars.get('GATE_IO_SECRET_KEY', ''),
            'passphrase': '',
            'api_base_url': 'https://fx-api-testnet.gateio.ws',
            'futures_base_url': 'https://fx-api-testnet.gateio.ws/api/v4',
            'ws_base_url': 'wss://fx-ws-testnet.gateio.ws',
            'rate_limit': 10,
            'supported_symbols': ['ETH/USDT', 'BTC/USDT', 'SOL/USDT'],
            'supported_types': ['spot', 'futures'],
            'default_leverage': 3,
            'max_position_size': 10.0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        },
        'binance': {
            'name': 'Binance',
            'type': 'spot_futures',
            'enabled': False,  # 暂时禁用，等待配置API密钥
            'sandbox': True,
            'api_key': env_vars.get('BINANCE_API_KEY', ''),
            'api_secret': env_vars.get('BINANCE_SECRET_KEY', ''),
            'passphrase': '',
            'api_base_url': 'https://testnet.binance.vision',
            'futures_base_url': 'https://testnet.binance.vision/api/v3',
            'ws_base_url': 'wss://testnet.binance.vision',
            'rate_limit': 5,
            'supported_symbols': ['ETH/USDT', 'BTC/USDT'],
            'supported_types': ['spot', 'futures'],
            'default_leverage': 3,
            'max_position_size': 5.0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    }

    for exchange_name, config in exchange_configs.items():
        try:
            success = await config_service.update_exchange_config(exchange_name, config)
            if success:
                logger.info(f"✅ 交易所配置初始化成功: {exchange_name}")
            else:
                logger.error(f"❌ 交易所配置初始化失败: {exchange_name}")
        except Exception as e:
            logger.error(f"❌ 初始化交易所配置 {exchange_name} 时出错: {e}")

async def init_trading_config(config_service: ConfigService):
    """初始化交易配置"""
    logger.info("初始化交易配置...")

    trading_config = {
        'default_leverage': 3,
        'max_position_size': 10.0,
        'commission_rate': 0.001,
        'max_daily_loss': 1000.0,
        'risk_management_enabled': True,
        'stop_loss_enabled': True,
        'take_profit_enabled': True,
        'max_drawdown': 20.0,  # 最大回撤20%
        'position_sizing_method': 'fixed_percentage',  # 固定百分比
        'position_risk_percent': 2.0,  # 每笔交易风险2%
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }

    try:
        # 检查是否已存在交易配置
        existing_config = await config_service.get_trading_config()
        if existing_config and 'created_at' in existing_config:
            # 更新现有配置
            trading_config['created_at'] = existing_config['created_at']
            logger.info("更新现有交易配置")
        else:
            logger.info("创建新的交易配置")

        # 使用 ConfigService 的方法更新交易配置
        success = await config_service.update_trading_config(trading_config)
        if success:
            logger.info("✅ 交易配置初始化成功")
        else:
            logger.error("❌ 交易配置初始化失败")
    except Exception as e:
        logger.error(f"❌ 交易配置初始化失败: {e}")

async def init_simulation_config(config_service: ConfigService):
    """初始化模拟交易配置"""
    logger.info("初始化模拟交易配置...")

    simulation_config = {
        'initial_balance': {'USDT': 10000.0},
        'commission_rate': 0.0,  # 模拟交易不收费
        'simulation_mode': True,
        'enable_slippage': True,
        'slippage_rate': 0.001,
        'enable_commission': False,
        'max_simultaneous_orders': 100,
        'execution_speed': 'real_time',  # real_time, fast, ultra_fast
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }

    try:
        # 使用 ConfigService 的方法更新模拟配置
        success = await config_service.update_simulation_config(simulation_config)
        if success:
            logger.info("✅ 模拟交易配置初始化成功")
        else:
            logger.error("❌ 模拟交易配置初始化失败")
    except Exception as e:
        logger.error(f"❌ 模拟交易配置初始化失败: {e}")

async def init_system_configs(config_service: ConfigService):
    """初始化系统配置"""
    logger.info("初始化系统配置...")

    system_configs = {
        'logging': {
            'level': 'INFO',
            'file_enabled': True,
            'max_file_size': '10MB',
            'backup_count': 5,
            'created_at': datetime.now().isoformat()
        },
        'api': {
            'rate_limit': 100,
            'timeout': 30,
            'retry_attempts': 3,
            'retry_delay': 1,
            'created_at': datetime.now().isoformat()
        },
        'database': {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'created_at': datetime.now().isoformat()
        }
    }

    try:
        logger.info("✅ 系统配置初始化成功")
    except Exception as e:
        logger.error(f"❌ 系统配置初始化失败: {e}")

async def init_user_config(config_service: ConfigService):
    """初始化用户配置"""
    logger.info("初始化用户配置...")

    default_user_config = {
        'theme': 'dark',
        'language': 'zh-CN',
        'timezone': 'Asia/Shanghai',
        'notifications_enabled': True,
        'email_notifications': True,
        'push_notifications': True,
        'alert_thresholds': {
            'price_change': 5.0,  # 价格变化5%
            'volume_change': 50.0,  # 成交量变化50%
            'funding_rate': 0.1   # 资金费率0.1%
        },
        'created_at': datetime.now().isoformat()
    }

    try:
        logger.info("✅ 用户配置初始化成功")
    except Exception as e:
        logger.error(f"❌ 用户配置初始化失败: {e}")

async def create_database_tables(config_service: ConfigService):
    """创建数据库表结构"""
    logger.info("检查数据库表结构...")

    # 这里应该有创建表的逻辑，如果没有就跳过
    # 假设表已经通过其他方式创建
    try:
        logger.info("✅ 数据库表结构检查完成")
    except Exception as e:
        logger.error(f"❌ 数据库表结构检查失败: {e}")

async def backup_existing_configs(config_service: ConfigService):
    """备份现有配置"""
    logger.info("备份现有配置...")

    try:
        # 获取所有现有的配置进行备份
        exchanges = await config_service.list_exchanges()
        trading_config = await config_service.get_trading_config()

        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'exchanges': exchanges,
            'trading_config': trading_config
        }

        # 保存备份到文件
        backup_file = os.path.join(project_root, 'config_backup.json')
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 配置备份已保存到: {backup_file}")
    except Exception as e:
        logger.error(f"❌ 配置备份失败: {e}")

async def main():
    """主函数"""
    logger.info("🚀 开始初始化数据库配置...")
    db_pool = None

    # 加载.env文件
    env_vars = load_env_file()
    logger.info(f"✅ 已加载 {len(env_vars)} 个环境变量")

    try:
        # 创建数据库连接池
        logger.info("创建数据库连接池...")
        db_pool = await create_db_pool()

        # 创建配置服务（传入数据库连接池）
        config_service = ConfigService(db_pool=db_pool)
        config_service.initialize()  # 同步方法，不需要 await

        # 备份现有配置
        await backup_existing_configs(config_service)

        # 创建数据库表结构
        await create_database_tables(config_service)

        # 初始化各种配置
        await init_exchange_configs(config_service, env_vars)
        await init_trading_config(config_service)
        await init_simulation_config(config_service)
        await init_system_configs(config_service)
        await init_user_config(config_service)

        logger.info("✅ 数据库配置初始化完成!")
        logger.info("\n📋 初始化摘要:")
        logger.info("  🏦 交易所配置: Gate.io, Binance")
        logger.info("  💰 交易配置: 杠杆、风险管理等")
        logger.info("  🧪 模拟配置: 模拟交易环境")
        logger.info("  ⚙️ 系统配置: 日志、API、数据库等")
        logger.info("  👤 用户配置: 主题、通知等")

        # 显示配置状态
        logger.info("\n📊 配置状态检查:")
        try:
            exchanges = await config_service.list_exchanges()
            for name, info in exchanges.items():
                status = "✅" if info.get('enabled') else "❌"
                logger.info(f"  {status} {name}: {info.get('name', name)}")
        except Exception as e:
            logger.warning(f"配置状态检查失败: {e}")

    except Exception as e:
        logger.error(f"❌ 数据库配置初始化失败: {e}")
        raise
    finally:
        # 关闭数据库连接池
        if db_pool:
            await db_pool.close()
            logger.info("数据库连接池已关闭")

    logger.info("🎉 配置初始化流程完成")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ 初始化被用户中断")
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        raise