#!/usr/bin/env python3
"""
交易所接口连接测试脚本
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

# 添加项目路径到系统路径
sys.path.append('/Users/domi/Documents/code/Github/CashUp/CashUp_v2')
sys.path.append('/Users/domi/Documents/code/Github/CashUp/CashUp_v2/trading-engine')

from exchanges.gateio import GateIOExchange
from exchanges.binance import BinanceExchange

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_gateio_connection() -> Dict[str, Any]:
    """测试Gate.io连接"""
    logger.info("开始测试Gate.io连接...")

    # 测试配置（使用生产环境）
    config = {
        'name': 'GateIO',
        'type': 'gateio',
        'api_key': os.getenv('GATE_IO_API_KEY', ''),
        'api_secret': os.getenv('GATE_IO_SECRET_KEY', ''),
        'sandbox': False  # 使用生产环境
    }

    try:
        # 创建Gate.io客户端
        exchange = GateIOExchange(config)
        async with exchange:
            # 测试1：获取服务器时间
            logger.info("测试1: 获取服务器时间...")
            server_time = await exchange.get_server_time()
            logger.info(f"✅ 服务器时间: {server_time}")

            # 测试2：获取ETH/USDT行情
            logger.info("测试2: 获取ETH/USDT行情...")
            ticker = await exchange.get_ticker("ETH/USDT")
            logger.info(f"✅ ETH/USDT行情: last={ticker.last_price}, bid={ticker.bid_price}, ask={ticker.ask_price}")

            # 测试3：获取订单簿
            logger.info("测试3: 获取ETH/USDT订单簿...")
            order_book = await exchange.get_order_book("ETH/USDT", limit=10)
            logger.info(f"✅ 订单簿: bids={len(order_book.get('bids', []))}, asks={len(order_book.get('asks', []))}")

            # 测试4：获取K线数据
            logger.info("测试4: 获取ETH/USDT K线数据...")
            klines = await exchange.get_klines("ETH/USDT", "1h", limit=10)
            logger.info(f"✅ K线数据: 获取到{len(klines)}条K线")
            if klines:
                latest_kline = klines[-1]
                logger.info(f"最新K线: {latest_kline.open_time} - {latest_kline.close_time}, O={latest_kline.open_price}, H={latest_kline.high_price}, L={latest_kline.low_price}, C={latest_kline.close_price}")

            # 测试5：获取交易对信息
            logger.info("测试5: 获取交易对信息...")
            symbols = await exchange.get_symbols()
            logger.info(f"✅ 交易对信息: 共{len(symbols)}个交易对")

            return {
                'exchange': 'GateIO',
                'status': 'success',
                'tests': [
                    {'name': '服务器时间', 'status': 'success', 'data': server_time.isoformat()},
                    {'name': '行情数据', 'status': 'success', 'data': f'last_price={ticker.last_price}'},
                    {'name': '订单簿', 'status': 'success', 'data': f'bids={len(order_book.get("bids", []))}'},
                    {'name': 'K线数据', 'status': 'success', 'data': f'{len(klines)}条K线'},
                    {'name': '交易对信息', 'status': 'success', 'data': f'{len(symbols)}个交易对'}
                ]
            }

    except Exception as e:
        logger.error(f"❌ Gate.io连接测试失败: {e}")
        return {
            'exchange': 'GateIO',
            'status': 'error',
            'error': str(e),
            'tests': []
        }

async def test_binance_connection() -> Dict[str, Any]:
    """测试Binance连接"""
    logger.info("开始测试Binance连接...")

    # 测试配置（使用生产环境）
    config = {
        'name': 'Binance',
        'type': 'binance',
        'api_key': os.getenv('BINANCE_API_KEY', ''),
        'api_secret': os.getenv('BINANCE_SECRET_KEY', ''),
        'sandbox': False  # 使用生产环境
    }

    try:
        # 创建Binance客户端
        exchange = BinanceExchange(config)
        async with exchange:
            # 测试1：获取服务器时间
            logger.info("测试1: 获取服务器时间...")
            server_time = await exchange.get_server_time()
            logger.info(f"✅ 服务器时间: {server_time}")

            # 测试2：获取BTC/USDT行情
            logger.info("测试2: 获取BTC/USDT行情...")
            ticker = await exchange.get_ticker("BTC/USDT")
            logger.info(f"✅ BTC/USDT行情: last={ticker.last_price}, bid={ticker.bid_price}, ask={ticker.ask_price}")

            # 测试3：获取订单簿
            logger.info("测试3: 获取BTC/USDT订单簿...")
            order_book = await exchange.get_order_book("BTC/USDT", limit=10)
            logger.info(f"✅ 订单簿: bids={len(order_book.get('bids', []))}, asks={len(order_book.get('asks', []))}")

            # 测试4：获取K线数据
            logger.info("测试4: 获取BTC/USDT K线数据...")
            klines = await exchange.get_klines("BTC/USDT", "1h", limit=10)
            logger.info(f"✅ K线数据: 获取到{len(klines)}条K线")
            if klines:
                latest_kline = klines[-1]
                logger.info(f"最新K线: {latest_kline.open_time} - {latest_kline.close_time}, O={latest_kline.open_price}, H={latest_kline.high_price}, L={latest_kline.low_price}, C={latest_kline.close_price}")

            # 测试5：获取交易对信息
            logger.info("测试5: 获取交易对信息...")
            symbols = await exchange.get_symbols()
            logger.info(f"✅ 交易对信息: 共{len(symbols)}个交易对")

            return {
                'exchange': 'Binance',
                'status': 'success',
                'tests': [
                    {'name': '服务器时间', 'status': 'success', 'data': server_time.isoformat()},
                    {'name': '行情数据', 'status': 'success', 'data': f'last_price={ticker.last_price}'},
                    {'name': '订单簿', 'status': 'success', 'data': f'bids={len(order_book.get("bids", []))}'},
                    {'name': 'K线数据', 'status': 'success', 'data': f'{len(klines)}条K线'},
                    {'name': '交易对信息', 'status': 'success', 'data': f'{len(symbols)}个交易对'}
                ]
            }

    except Exception as e:
        logger.error(f"❌ Binance连接测试失败: {e}")
        return {
            'exchange': 'Binance',
            'status': 'error',
            'error': str(e),
            'tests': []
        }

async def main():
    """主函数"""
    logger.info("开始交易所接口连接测试...")

    # 测试Gate.io
    gateio_result = await test_gateio_connection()

    # 测试Binance
    binance_result = await test_binance_connection()

    # 打印结果汇总
    print("\n" + "="*50)
    print("交易所接口连接测试结果汇总")
    print("="*50)

    for result in [gateio_result, binance_result]:
        exchange_name = result['exchange']
        status = result['status']
        emoji = "✅" if status == 'success' else "❌"

        print(f"\n{emoji} {exchange_name}: {status}")
        if status == 'error':
            print(f"   错误: {result['error']}")
        else:
            print("   测试项目:")
            for test in result['tests']:
                test_emoji = "✅" if test['status'] == 'success' else "❌"
                print(f"     {test_emoji} {test['name']}: {test['data']}")

    # 总结
    success_count = sum(1 for r in [gateio_result, binance_result] if r['status'] == 'success')
    total_count = len([gateio_result, binance_result])

    print(f"\n总结: {success_count}/{total_count} 个交易所连接测试通过")

    if success_count == total_count:
        print("🎉 所有交易所接口连接正常！")
        return 0
    else:
        print("⚠️  部分交易所接口连接有问题，请检查配置和网络")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))