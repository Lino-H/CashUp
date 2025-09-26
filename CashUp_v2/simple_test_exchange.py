#!/usr/bin/env python3
"""
简化版交易所接口连接测试 - 只测试公开API
"""

import asyncio
import logging
import sys
from datetime import datetime

# 添加项目路径到系统路径
sys.path.append('/Users/domi/Documents/code/Github/CashUp/CashUp_v2')
sys.path.append('/Users/domi/Documents/code/Github/CashUp/CashUp_v2/trading-engine')

async def test_gateio_public_api():
    """测试Gate.io公开API"""
    print("开始测试Gate.io公开API...")

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            # 测试服务器时间
            print("测试1: 获取服务器时间...")
            async with session.get('https://api.gateio.ws/api/v4/time') as response:
                if response.status == 200:
                    data = await response.json()
                    server_time = datetime.fromtimestamp(data['server_time'])
                    print(f"✅ 服务器时间: {server_time}")
                else:
                    print(f"❌ 服务器时间请求失败: {response.status}")
                    return False

            # 测试行情数据
            print("测试2: 获取ETH/USDT行情...")
            async with session.get('https://api.gateio.ws/api/v4/spot/tickers?currency_pair=ETH_USDT') as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        ticker = data[0]
                        print(f"✅ ETH/USDT行情: last={ticker['last']}, bid={ticker['highest_bid']}, ask={ticker['lowest_ask']}")
                    else:
                        print("❌ 无法获取行情数据")
                        return False
                else:
                    print(f"❌ 行情数据请求失败: {response.status}")
                    return False

            # 测试订单簿
            print("测试3: 获取ETH/USDT订单簿...")
            async with session.get('https://api.gateio.ws/api/v4/spot/order_book?currency_pair=ETH_USDT&limit=5') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 订单簿: bids={len(data.get('bids', []))}, asks={len(data.get('asks', []))}")
                else:
                    print(f"❌ 订单簿请求失败: {response.status}")
                    return False

            # 测试K线数据
            print("测试4: 获取ETH/USDT K线数据...")
            async with session.get('https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair=ETH_USDT&interval=1h&limit=5') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ K线数据: 获取到{len(data)}条K线")
                    if data and len(data) > 0:
                        latest_kline = data[-1]
                        print(f"最新K线: O={latest_kline[1]}, H={latest_kline[2]}, L={latest_kline[3]}, C={latest_kline[4]}")
                else:
                    print(f"❌ K线数据请求失败: {response.status}")
                    return False

            # 测试交易对信息
            print("测试5: 获取交易对信息...")
            async with session.get('https://api.gateio.ws/api/v4/spot/currency_pairs') as response:
                if response.status == 200:
                    data = await response.json()
                    tradable_pairs = [item for item in data if item['trade_status'] == 'tradable']
                    print(f"✅ 交易对信息: 共{len(tradable_pairs)}个可交易对")
                else:
                    print(f"❌ 交易对信息请求失败: {response.status}")
                    return False

            print("🎉 Gate.io公开API测试全部通过！")
            return True

    except Exception as e:
        print(f"❌ Gate.io公开API测试失败: {e}")
        return False

async def test_binance_public_api():
    """测试Binance公开API"""
    print("\n开始测试Binance公开API...")

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            # 测试服务器时间
            print("测试1: 获取服务器时间...")
            async with session.get('https://api.binance.com/api/v3/time') as response:
                if response.status == 200:
                    data = await response.json()
                    server_time = datetime.fromtimestamp(data['serverTime'] / 1000)
                    print(f"✅ 服务器时间: {server_time}")
                else:
                    print(f"❌ 服务器时间请求失败: {response.status}")
                    return False

            # 测试行情数据
            print("测试2: 获取BTC/USDT行情...")
            async with session.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ BTC/USDT行情: last={data['lastPrice']}, bid={data['bidPrice']}, ask={data['askPrice']}")
                else:
                    print(f"❌ 行情数据请求失败: {response.status}")
                    return False

            # 测试订单簿
            print("测试3: 获取BTC/USDT订单簿...")
            async with session.get('https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 订单簿: bids={len(data.get('bids', []))}, asks={len(data.get('asks', []))}")
                else:
                    print(f"❌ 订单簿请求失败: {response.status}")
                    return False

            # 测试K线数据
            print("测试4: 获取BTC/USDT K线数据...")
            async with session.get('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=5') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ K线数据: 获取到{len(data)}条K线")
                    if data and len(data) > 0:
                        latest_kline = data[-1]
                        print(f"最新K线: O={latest_kline[1]}, H={latest_kline[2]}, L={latest_kline[3]}, C={latest_kline[4]}")
                else:
                    print(f"❌ K线数据请求失败: {response.status}")
                    return False

            # 测试交易对信息
            print("测试5: 获取交易对信息...")
            async with session.get('https://api.binance.com/api/v3/exchangeInfo') as response:
                if response.status == 200:
                    data = await response.json()
                    trading_pairs = [item for item in data['symbols'] if item['status'] == 'TRADING']
                    print(f"✅ 交易对信息: 共{len(trading_pairs)}个可交易对")
                else:
                    print(f"❌ 交易对信息请求失败: {response.status}")
                    return False

            print("🎉 Binance公开API测试全部通过！")
            return True

    except Exception as e:
        print(f"❌ Binance公开API测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("开始交易所公开API连接测试...")

    # 测试Gate.io
    gateio_success = await test_gateio_public_api()

    # 测试Binance
    binance_success = await test_binance_public_api()

    # 总结
    print("\n" + "="*50)
    print("交易所公开API连接测试结果汇总")
    print("="*50)

    gateio_status = "✅ 通过" if gateio_success else "❌ 失败"
    binance_status = "✅ 通过" if binance_success else "❌ 失败"

    print(f"Gate.io: {gateio_status}")
    print(f"Binance: {binance_status}")

    success_count = sum([gateio_success, binance_success])
    total_count = 2

    print(f"\n总结: {success_count}/{total_count} 个交易所公开API测试通过")

    if success_count == total_count:
        print("🎉 所有交易所公开API连接正常！")
        return 0
    else:
        print("⚠️  部分交易所公开API连接有问题，请检查网络")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))