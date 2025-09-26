#!/usr/bin/env python3
"""
测试两个交易所的API连接
"""

import asyncio
import sys
from datetime import datetime

# 添加项目路径
sys.path.append('/Users/domi/Documents/code/Github/CashUp/CashUp_v2')
sys.path.append('/Users/domi/Documents/code/Github/CashUp/CashUp_v2/trading-engine')

async def test_gateio():
    """测试Gate.io API"""
    print("开始测试Gate.io API...")

    try:
        from exchanges.gateio import GateIOExchange

        config = {
            'name': 'GateIO',
            'type': 'gateio',
            'api_key': '',
            'api_secret': '',
            'sandbox': False
        }

        exchange = GateIOExchange(config)
        async with exchange:
            print("✅ 创建Gate.io客户端成功")

            # 测试服务器时间
            server_time = await exchange.get_server_time()
            print(f"✅ 服务器时间: {server_time}")

            # 测试行情数据
            ticker = await exchange.get_ticker("ETH/USDT")
            print(f"✅ ETH/USDT行情: last={ticker.last_price}, bid={ticker.bid_price}, ask={ticker.ask_price}")

            # 测试订单簿
            order_book = await exchange.get_order_book("ETH/USDT", limit=10)
            print(f"✅ 订单簿: bids={len(order_book.get('bids', []))}, asks={len(order_book.get('asks', []))}")

            # 测试K线数据
            klines = await exchange.get_klines("ETH/USDT", "1h", limit=10)
            print(f"✅ K线数据: 获取到{len(klines)}条K线")

            # 测试交易对信息
            symbols = await exchange.get_symbols()
            print(f"✅ 交易对信息: 共{len(symbols)}个交易对")

            print("🎉 Gate.io API连接测试全部通过！")
            return True

    except Exception as e:
        print(f"❌ Gate.io API连接测试失败: {e}")
        return False

async def test_binance():
    """测试Binance API"""
    print("\n开始测试Binance API...")

    try:
        from exchanges.binance import BinanceExchange

        config = {
            'name': 'Binance',
            'type': 'binance',
            'api_key': '',
            'api_secret': '',
            'sandbox': False
        }

        exchange = BinanceExchange(config)
        async with exchange:
            print("✅ 创建Binance客户端成功")

            # 测试服务器时间
            server_time = await exchange.get_server_time()
            print(f"✅ 服务器时间: {server_time}")

            # 测试行情数据
            ticker = await exchange.get_ticker("BTC/USDT")
            print(f"✅ BTC/USDT行情: last={ticker.last_price}, bid={ticker.bid_price}, ask={ticker.ask_price}")

            # 测试订单簿
            order_book = await exchange.get_order_book("BTC/USDT", limit=10)
            print(f"✅ 订单簿: bids={len(order_book.get('bids', []))}, asks={len(order_book.get('asks', []))}")

            # 测试K线数据
            klines = await exchange.get_klines("BTC/USDT", "1h", limit=10)
            print(f"✅ K线数据: 获取到{len(klines)}条K线")

            # 测试交易对信息
            symbols = await exchange.get_symbols()
            print(f"✅ 交易对信息: 共{len(symbols)}个交易对")

            print("🎉 Binance API连接测试全部通过！")
            return True

    except Exception as e:
        print(f"❌ Binance API连接测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("开始交易所API连接测试...")

    # 测试Gate.io
    gateio_success = await test_gateio()

    # 测试Binance
    binance_success = await test_binance()

    # 总结
    print("\n" + "="*50)
    print("交易所API连接测试结果汇总")
    print("="*50)

    gateio_status = "✅ 通过" if gateio_success else "❌ 失败"
    binance_status = "✅ 通过" if binance_success else "❌ 失败"

    print(f"Gate.io: {gateio_status}")
    print(f"Binance: {binance_status}")

    success_count = sum([gateio_success, binance_success])
    total_count = 2

    print(f"\n总结: {success_count}/{total_count} 个交易所API测试通过")

    if success_count == total_count:
        print("🎉 所有交易所API连接正常！")
        return 0
    else:
        print("⚠️  部分交易所API连接有问题，请检查网络")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))