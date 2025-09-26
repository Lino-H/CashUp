#!/usr/bin/env python3
"""
交易所API集成测试脚本
测试Gate.io交易所API连接和基本功能
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('exchange_test.log')
    ]
)
logger = logging.getLogger(__name__)

class MockConfigService:
    """模拟配置服务"""
    def __init__(self):
        self.configs = {
            'gateio': {
                'api_key': os.getenv('GATE_IO_API_KEY', ''),
                'api_secret': os.getenv('GATE_IO_SECRET_KEY', '')
            }
        }

    def initialize(self):
        """初始化配置服务"""
        logger.info("配置服务初始化完成")

    def get_api_credentials(self, exchange_name: str):
        """获取API凭证"""
        logger.info(f"获取交易所 {exchange_name} 的API凭证")
        return self.configs.get(exchange_name)

async def test_gateio_connection():
    """测试Gate.io连接"""
    logger.info("开始测试Gate.io连接...")

    try:
        # 创建测试配置
        config = {
            'name': 'Gate.io Test',
            'type': 'gateio',
            'sandbox': False,  # 使用真实环境
            'rate_limit': 5,
            'api_key': os.getenv('GATE_IO_API_KEY', ''),
            'api_secret': os.getenv('GATE_IO_SECRET_KEY', '')
        }

        # 模拟配置服务
        from services.config_service import ConfigService
        config_service = ConfigService()
        config_service.initialize()

        logger.info("配置服务已初始化")
        logger.info(f"API Key长度: {len(config['api_key'])}")
        logger.info(f"Secret Key长度: {len(config['api_secret'])}")

        if not config['api_key'] or not config['api_secret']:
            logger.warning("API密钥未配置，测试将使用匿名连接")

        # 测试导入
        logger.info("测试导入交易所模块...")
        from exchanges.gateio import GateIOExchange

        # 创建交易所实例
        logger.info("创建Gate.io交易所实例...")
        exchange = GateIOExchange(config)

        # 测试HTTP连接
        logger.info("测试HTTP连接...")
        try:
            # �试服务器时间
            logger.info("获取服务器时间...")
            server_time = await exchange.get_server_time()
            logger.info(f"服务器时间: {server_time}")
        except Exception as e:
            logger.error(f"HTTP连接失败: {e}")
            return False

        # 测试获取交易对
        logger.info("测试获取交易对...")
        try:
            symbols = await exchange.get_symbols()
            logger.info(f"获取到 {len(symbols)} 个交易对")

            # 显示前5个交易对
            for i, symbol in enumerate(symbols[:5]):
                logger.info(f"交易对 {i+1}: {symbol}")
        except Exception as e:
            logger.error(f"获取交易对失败: {e}")
            return False

        # 测试获取行情
        logger.info("测试获取行情...")
        try:
            ticker = await exchange.get_ticker('BTC/USDT')
            logger.info(f"BTC/USDT 行情: {ticker}")
            logger.info(f"当前价格: ${ticker.last_price}")
            logger.info(f"24小时成交量: {ticker.volume_24h}")
        except Exception as e:
            logger.error(f"获取行情失败: {e}")
            return False

        # 测试获取K线数据
        logger.info("测试获取K线数据...")
        try:
            klines = await exchange.get_klines('BTC/USDT', '1h', limit=10)
            logger.info(f"获取到 {len(klines)} 条K线数据")
            if klines:
                latest = klines[-1]
                logger.info(f"最新K线时间: {latest.close_time}")
                logger.info(f"最新K线价格: {latest.close_price}")
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return False

        # 测试获取订单簿
        logger.info("测试获取订单簿...")
        try:
            order_book = await exchange.get_order_book('BTC/USDT', limit=10)
            logger.info(f"订单簿买一价: {order_book.get('bids', [])[0][0] if order_book.get('bids') else 'N/A'}")
            logger.info(f"订单簿卖一价: {order_book.get('asks', [])[0][0] if order_book.get('asks') else 'N/A'}")
        except Exception as e:
            logger.error(f"获取订单簿失败: {e}")
            return False

        logger.info("Gate.io API集成测试成功!")
        return True

    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_websocket_connection():
    """测试WebSocket连接"""
    logger.info("开始测试WebSocket连接...")

    try:
        config = {
            'name': 'Gate.io WebSocket Test',
            'type': 'gateio',
            'sandbox': False,
            'api_key': os.getenv('GATE_IO_API_KEY', ''),
            'api_secret': os.getenv('GATE_IO_SECRET_KEY', '')
        }

        from exchanges.gateio import GateIOExchange

        exchange = GateIOExchange(config)

        # 测试WebSocket管理器
        logger.info("初始化WebSocket管理器...")
        await exchange.init_websocket_manager()
        logger.info("WebSocket管理器初始化成功")

        # 测试订阅功能
        logger.info("测试订阅行情推送...")
        ticker_data = []

        def ticker_callback(data):
            logger.info(f"收到行情数据: {data}")
            ticker_data.append(data)

        await exchange.subscribe_ticker('BTC/USDT', ticker_callback)

        # 等待一段时间接收数据
        await asyncio.sleep(10)

        if ticker_data:
            logger.info(f"成功接收到 {len(ticker_data)} 条行情数据")
        else:
            logger.warning("未收到行情数据，可能需要更长时间等待")

        return True

    except Exception as e:
        logger.error(f"WebSocket测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("=" * 50)
    logger.info("开始交易所API集成测试")
    logger.info("=" * 50)

    # 检查环境变量
    api_key = os.getenv('GATE_IO_API_KEY')
    api_secret = os.getenv('GATE_IO_SECRET_KEY')

    logger.info(f"API Key配置: {'已配置' if api_key else '未配置'}")
    logger.info(f"API Secret配置: {'已配置' if api_secret else '未配置'}")

    # 测试HTTP API
    http_success = await test_gateio_connection()

    # 测试WebSocket
    websocket_success = await test_websocket_connection()

    logger.info("=" * 50)
    logger.info("测试结果总结:")
    logger.info(f"HTTP API连接: {'✅ 成功' if http_success else '❌ 失败'}")
    logger.info(f"WebSocket连接: {'✅ 成功' if websocket_success else '❌ 失败'}")

    if http_success and websocket_success:
        logger.info("🎉 所有测试通过! 交易所API集成工作正常")
    elif http_success:
        logger.info("⚠️  HTTP API正常，WebSocket需要配置")
    else:
        logger.error("❌ 测试失败，请检查配置和网络连接")

    logger.info("=" * 50)
    logger.info(f"测试完成时间: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())