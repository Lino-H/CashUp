#!/usr/bin/env python3
"""
调试Ticker数据结构
"""

import aiohttp
import asyncio

async def debug_ticker():
    """调试Ticker数据"""
    print("调试Gate.io Ticker数据结构...")

    url = "https://api.gateio.ws/api/v4/spot/tickers?currency_pair=ETH_USDT"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"完整响应: {data}")

                    if data and len(data) > 0:
                        item = data[0]
                        print(f"\n第一个Ticker数据:")
                        for key, value in item.items():
                            print(f"  {key}: {value}")

                        # 检查字段是否存在
                        required_fields = ['last', 'highest_bid', 'lowest_ask', 'base_volume', 'high_24h', 'low_24h']
                        print(f"\n字段检查:")
                        for field in required_fields:
                            exists = field in item
                            print(f"  {field}: {'✓' if exists else '✗'}")
                else:
                    print(f"请求失败: {response.status}")
                    content = await response.text()
                    print(f"响应内容: {content}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    asyncio.run(debug_ticker())