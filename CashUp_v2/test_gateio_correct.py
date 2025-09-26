#!/usr/bin/env python3
"""
测试Gate.io API连接（使用正确的端点）
"""

import asyncio
import aiohttp
import sys
import os

# 添加项目路径
sys.path.append('/Users/domi/Documents/code/Github/CashUp/CashUp_v2/trading-engine')

async def test_gateio_correct():
    """测试Gate.io API连接"""
    print("开始测试Gate.io API连接...")

    # 测试配置
    config = {
        'name': 'GateIO',
        'type': 'gateio',
        'api_key': os.getenv('GATE_IO_API_KEY', ''),
        'api_secret': os.getenv('GATE_IO_SECRET_KEY', ''),
        'sandbox': False  # 使用生产环境
    }

    try:
        from exchanges.gateio import GateIOExchange

        # 创建交易所客户端
        exchange = GateIOExchange(config)
        async with exchange:
            print("✅ 创建Gate.io客户端成功")

            # 测试1：获取服务器时间
            print("测试1: 获取服务器时间...")
            server_time = await exchange.get_server_time()
            print(f"✅ 服务器时间: {server_time}")

            # 测试2：获取ETH/USDT行情
            print("测试2: 获取ETH/USDT行情...")
            ticker = await exchange.get_ticker("ETH/USDT")
            print(f"✅ ETH/USDT行情: last={ticker.last_price}, bid={ticker.bid_price}, ask={ticker.ask_price}")

            # 测试3：获取订单簿
            print("测试3: 获取ETH/USDT订单簿...")
            order_book = await exchange.get_order_book("ETH/USDT", limit=10)
            print(f"✅ 订单簿: bids={len(order_book.get('bids', []))}, asks={len(order_book.get('asks', []))}")

            # 测试4：获取K线数据
            print("测试4: 获取ETH/USDT K线数据...")
            klines = await exchange.get_klines("ETH/USDT", "1h", limit=10)
            print(f"✅ K线数据: 获取到{len(klines)}条K线")
            if klines:
                latest_kline = klines[-1]
                print(f"最新K线: {latest_kline.open_time} - {latest_kline.close_time}, O={latest_kline.open_price}, H={latest_kline.high_price}, L={latest_kline.low_price}, C={latest_kline.close_price}")

            # 测试5：获取交易对信息
            print("测试5: 获取交易对信息...")
            symbols = await exchange.get_symbols()
            print(f"✅ 交易对信息: 共{len(symbols)}个交易对")

            print("🎉 Gate.io API连接测试全部通过！")
            return True

    except Exception as e:
        print(f"❌ Gate.io API连接测试失败: {e}")
        return False

async def test_with_direct_requests():
    """使用直接HTTP请求测试Gate.io API"""
    print("\n开始直接HTTP请求测试Gate.io API...")

    base_url = "https://api.gateio.ws"

    try:
        async with aiohttp.ClientSession() as session:
            # 测试服务器时间
            print("测试1: 获取服务器时间...")
            async with session.get(f"{base_url}/api/v4/spot/time") as response:
                if response.status == 200:
                    data = await response.json()
                    server_time = data['server_time']
                    print(f"✅ 服务器时间: {server_time}")
                else:
                    print(f"❌ 服务器时间请求失败: {response.status}")
                    return False

            # 测试行情数据
            print("测试2: 获取ETH/USDT行情...")
            async with session.get(f"{base_url}/api/v4/spot/tickers?currency_pair=ETH_USDT") as response:
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
            async with session.get(f"{base_url}/api/v4/spot/order_book?currency_pair=ETH_USDT&limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 订单簿: bids={len(data.get('bids', []))}, asks={len(data.get('asks', []))}")
                else:
                    print(f"❌ 订单簿请求失败: {response.status}")
                    return False

            print("🎉 直接HTTP请求测试Gate.io API全部通过！")
            return True

    except Exception as e:
        print(f"❌ 直接HTTP请求测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("开始Gate.io API连接测试...")

    # 测试1：使用封装的类
    class_success = await test_gateio_correct()

    # 测试2：使用直接HTTP请求
    direct_success = await test_with_direct_requests()

    # 总结
    print("\n" + "="*50)
    print("Gate.io API连接测试结果汇总")
    print("="*50)

    class_status = "✅ 通过" if class_success else "❌ 失败"
    direct_status = "✅ 通过" if direct_success else "❌ 失败"

    print(f"封装类测试: {class_status}")
    print(f"直接请求测试: {direct_status}")

    success_count = sum([class_success, direct_success])
    total_count = 2

    print(f"\n总结: {success_count}/{total_count} 个测试通过")

    if success_count == total_count:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))