#!/usr/bin/env python3
"""
直接测试交易所API端点
"""

import aiohttp
import asyncio

async def test_gateio_endpoints():
    """测试Gate.io API端点"""
    print("测试Gate.io API端点...")

    base_url = "https://api.gateio.ws"

    # 尝试不同的时间端点
    endpoints = [
        "/api/v4/time",
        "/api/v4/spot/time",
        "/api/v4/futures/time"
    ]

    for endpoint in endpoints:
        try:
            print(f"测试端点: {endpoint}")
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url + endpoint) as response:
                    print(f"  状态码: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"  响应: {data}")
                    elif response.status == 404:
                        content = await response.text()
                        print(f"  404内容: {content[:100]}...")
        except Exception as e:
            print(f"  错误: {e}")

async def test_binance_endpoints():
    """测试Binance API端点"""
    print("\n测试Binance API端点...")

    base_url = "https://api.binance.com"

    # 尝试不同的时间端点
    endpoints = [
        "/api/v3/time",
        "/api/v3/ping",
        "/api/v3/ticker/price"
    ]

    for endpoint in endpoints:
        try:
            print(f"测试端点: {endpoint}")
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url + endpoint) as response:
                    print(f"  状态码: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"  响应: {data}")
                    elif response.status == 404:
                        content = await response.text()
                        print(f"  404内容: {content[:100]}...")
        except Exception as e:
            print(f"  错误: {e}")

async def test_alternative_endpoints():
    """测试备用API端点"""
    print("\n测试备用API端点...")

    # 测试其他可能的端点
    test_cases = [
        ("https://www.gate.io/api/v4/time", "Gate.io主站"),
        ("https://api.gate.io/api/v4/time", "Gate.io备用"),
        ("https://api.binance.com/api/v3/ping", "Binance Ping"),
        ("https://binance.com/api/v3/ping", "Binance主站"),
    ]

    for url, name in test_cases:
        try:
            print(f"测试 {name}: {url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    print(f"  状态码: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"  响应: {data}")
        except Exception as e:
            print(f"  错误: {e}")

async def main():
    await test_gateio_endpoints()
    await test_binance_endpoints()
    await test_alternative_endpoints()

if __name__ == "__main__":
    asyncio.run(main())