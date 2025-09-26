"""
Gate.io WebSocket数据订阅测试脚本
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def data_callback(data: Dict[str, Any]):
    """数据处理回调函数"""
    try:
        print(f"[{datetime.now()}] 收到数据类型: {type(data)}")

        if hasattr(data, '__dict__'):
            # 如果是数据类对象
            if hasattr(data, 'symbol'):
                print(f"📊 行情数据 - {data.symbol}: 最新价={getattr(data, 'last_price', 'N/A')}")
            elif hasattr(data, 'interval'):
                print(f"📈 K线数据 - {data.symbol} {data.interval}: 开盘={getattr(data, 'open_price', 'N/A')}, 收盘={getattr(data, 'close_price', 'N/A')}")
            elif hasattr(data, 'asks'):
                print(f"📋 订单簿 - {len(data.asks)} 卖盘, {len(data.bids)} 买盘")
            elif hasattr(data, 'funding_rate'):
                print(f"💰 资金费率 - {data.symbol}: 费率={getattr(data, 'funding_rate', 'N/A')}%, 下次结算={getattr(data, 'next_funding_time', 'N/A')}")
            else:
                print(f"📦 其他数据: {type(data).__name__}")
        else:
            # 如果是字典
            symbol = data.get('symbol', '未知')
            if 'last_price' in data:
                print(f"📊 行情数据 - {symbol}: 最新价={data['last_price']}")
            elif 'open_price' in data:
                print(f"📈 K线数据 - {symbol}: {data.get('interval', 'N/A')}")
            elif 'funding_rate' in data:
                print(f"💰 资金费率 - {symbol}: 费率={data['funding_rate']}")
            else:
                print(f"📦 字典数据: {symbol} - {list(data.keys())}")

    except Exception as e:
        logger.error(f"数据处理失败: {e}")

async def test_gateio_websocket():
    """测试Gate.io WebSocket连接和数据订阅"""
    print("🚀 开始测试Gate.io WebSocket数据订阅...")

    try:
        # 导入Gate.io客户端
        from exchanges.gateio import GateIOExchange

        # 配置测试参数（从环境变量获取真实的API密钥）
        config = {
            'name': 'gateio_test',
            'api_key': os.getenv('GATE_IO_API_KEY', ''),  # 从环境变量获取
            'api_secret': os.getenv('GATE_IO_SECRET_KEY', ''),  # 从环境变量获取
            'sandbox': True  # 使用测试环境
        }

        # 创建交易所客户端
        async with GateIOExchange(config) as client:
            print("✅ 成功创建Gate.io客户端")

            # 测试订阅ETHUSDT永续合约数据
            print("📡 订阅ETHUSDT永续合约数据...")

            # 订阅多个数据类型
            await client.subscribe_eth_usdt_data(data_callback)

            print("🎯 数据订阅成功，等待数据推送...")
            print("💡 按Ctrl+C停止测试")

            # 运行30秒来测试数据接收
            try:
                await asyncio.sleep(30)
            except KeyboardInterrupt:
                print("\n🛑 用户中断测试")

            print("📊 测试完成")

    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        print("❌ 请确保trading-engine目录在Python路径中")

    except Exception as e:
        logger.error(f"WebSocket测试失败: {e}")
        print(f"❌ 测试失败: {e}")

async def test_individual_subscriptions():
    """测试单独的数据订阅"""
    print("\n🔧 测试单独的数据订阅...")

    try:
        from exchanges.gateio import GateIOExchange

        config = {
            'name': 'gateio_test',
            'api_key': os.getenv('GATE_IO_API_KEY', ''),
            'api_secret': os.getenv('GATE_IO_SECRET_KEY', ''),
            'sandbox': True
        }

        async with GateIOExchange(config) as client:

            # 分别测试不同数据类型
            print("📊 订阅行情数据...")
            await client.subscribe_ticker('ETH/USDT', data_callback)
            await asyncio.sleep(5)

            print("📈 订阅K线数据...")
            await client.subscribe_kline('ETH/USDT', '1m', data_callback)
            await asyncio.sleep(5)

            print("📋 订阅订单簿...")
            await client.subscribe_order_book('ETH/USDT', data_callback)
            await asyncio.sleep(5)

            print("💰 订阅资金费率...")
            await client.subscribe_funding_rate('ETH/USDT', data_callback)
            await asyncio.sleep(10)

    except Exception as e:
        logger.error(f"单独订阅测试失败: {e}")

async def main():
    """主函数"""
    print("🏁 Gate.io WebSocket测试开始")
    print("=" * 50)

    # 测试主要功能
    await test_gateio_websocket()

    # 测试单独订阅
    await test_individual_subscriptions()

    print("=" * 50)
    print("✅ 所有测试完成")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        print(f"❌ 运行失败: {e}")