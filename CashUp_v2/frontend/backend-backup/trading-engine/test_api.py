"""
交易引擎API测试脚本
用于验证所有API接口的功能
"""

import asyncio
import requests
import json
import time
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8002"

def test_api_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)

        if response.status_code == expected_status:
            print(f"✅ {endpoint}: {response.status_code}")
            return response.json()
        else:
            print(f"❌ {endpoint}: 期望 {expected_status}, 实际 {response.status_code}")
            print(f"   响应: {response.text[:200]}...")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint}: 连接失败 - {e}")
        return None

def test_health_checks():
    """测试健康检查接口"""
    print("\n🧪 测试健康检查接口...")

    # 测试根路径
    result = test_api_endpoint("/", method="GET")
    if result:
        print(f"   服务名称: {result.get('service')}")
        print(f"   版本: {result.get('version')}")

    # 测试健康检查
    result = test_api_endpoint("/health", method="GET")
    if result:
        print(f"   状态: {result.get('status')}")
        print(f"   时间戳: {result.get('timestamp')}")

def test_strategy_apis():
    """测试策略管理API"""
    print("\n🧪 测试策略管理接口...")

    # 测试获取策略状态
    result = test_api_endpoint("/api/v1/strategies/status", method="GET")
    if result:
        print(f"   策略总数: {result.get('total_strategies')}")
        strategies = result.get('strategies', {})
        for name, status in strategies.items():
            print(f"   {name}: 运行中={status.get('running')}, 信号数={status.get('signal_count')}")

    # 测试获取策略模板
    result = test_api_endpoint("/api/v1/strategies/templates", method="GET")
    if result:
        print(f"   模板数量: {result.get('total_templates')}")
        templates = result.get('templates', {})
        for name, template in templates.items():
            print(f"   {name}: {template.get('name')} (风险: {template.get('risk_level')})")

    # 测试启动策略（假设grid策略存在）
    result = test_api_endpoint("/api/v1/strategies/grid/start", method="POST")
    if result:
        print(f"   启动结果: {result.get('message')}")

    # 测试获取策略信号
    result = test_api_endpoint("/api/v1/strategies/grid/signals?limit=5", method="GET")
    if result:
        print(f"   信号数量: {result.get('count')}")
        signals = result.get('signals', [])
        for signal in signals[:2]:  # 显示前2个信号
            print(f"   信号: {signal.get('action')} {signal.get('symbol')} 强度={signal.get('strength')}")

    # 测试停止策略
    result = test_api_endpoint("/api/v1/strategies/grid/stop", method="POST")
    if result:
        print(f"   停止结果: {result.get('message')}")

def test_trading_apis():
    """测试交易管理API"""
    print("\n🧪 测试交易管理接口...")

    # 测试获取账户余额
    result = test_api_endpoint("/api/v1/balances", method="GET")
    if result:
        print(f"   余额数量: {len(result.get('balances', []))}")
        for balance in result.get('balances', []):
            print(f"   {balance.get('asset')}: {balance.get('total')} (可用: {balance.get('free')})")

    # 测试获取账户信息
    result = test_api_endpoint("/api/v1/account/info", method="GET")
    if result:
        print(f"   总余额: {result.get('total_balance')}")
        print(f"   可用余额: {result.get('available_balance')}")
        print(f"   杠杆: {result.get('leverage')}x")
        print(f"   交易状态: {result.get('trading_enabled')}")

    # 测试获取订单列表
    result = test_api_endpoint("/api/v1/orders", method="GET")
    if result:
        print(f"   订单数量: {result.get('total_orders')}")
        orders = result.get('orders', [])
        for order in orders[:2]:  # 显示前2个订单
            print(f"   订单 {order.get('id')}: {order.get('side')} {order.get('symbol')}")

    # 测试获取持仓列表
    result = test_api_endpoint("/api/v1/positions", method="GET")
    if result:
        print(f"   持仓数量: {result.get('total_positions')}")
        positions = result.get('positions', [])
        for position in positions[:2]:  # 显示前2个持仓
            print(f"   持仓 {position.get('symbol')}: {position.get('side')} {position.get('size')}")

    # 测试创建订单
    order_data = {
        "symbol": "BTC/USDT",
        "side": "buy",
        "type": "limit",
        "quantity": 0.01,
        "price": 30000.0
    }
    result = test_api_endpoint("/api/v1/orders", method="POST", data=order_data)
    if result:
        print(f"   订单ID: {result.get('order_id')}")
        print(f"   创建时间: {result.get('order', {}).get('created_at')}")

def test_trading_service_apis():
    """测试交易服务API"""
    print("\n🧪 测试交易服务接口...")

    # 测试获取交易历史
    result = test_api_endpoint("/trading/orders/history?limit=5", method="GET")
    if result:
        print(f"   历史订单数量: {result.get('pagination', {}).get('total')}")

    # 测试获取账户摘要
    result = test_api_endpoint("/trading/account/summary", method="GET")
    if result:
        print(f"   总余额: {result.get('data', {}).get('total_balance')}")
        print(f"   风险等级: {result.get('data', {}).get('risk_level')}")

    # 测试获取可用交易对
    result = test_api_endpoint("/trading/symbols", method="GET")
    if result:
        print(f"   交易对数量: {result.get('total_symbols')}")
        symbols = result.get('symbols', [])
        for symbol in symbols:
            print(f"   {symbol.get('symbol')}: ${symbol.get('last_price')} (24h变化: {symbol.get('price_change_24h')}%)")

    # 测试获取费率
    result = test_api_endpoint("/trading/fees", method="GET")
    if result:
        fees = result.get('data', {})
        print(f"   现货交易费率: {fees.get('spot_trading', {})}")
        print(f"   期货交易费率: {fees.get('futures_trading', {})}")

def test_web_interface():
    """测试Web界面"""
    print("\n🧪 测试Web界面...")

    # 测试Swagger UI
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Swagger UI 可访问")
        else:
            print("❌ Swagger UI 访问失败")
    except:
        print("❌ Swagger UI 连接失败")

    # 测试ReDoc UI
    try:
        response = requests.get(f"{BASE_URL}/redoc", timeout=5)
        if response.status_code == 200:
            print("✅ ReDoc UI 可访问")
        else:
            print("❌ ReDoc UI 访问失败")
    except:
        print("❌ ReDoc UI 连接失败")

def run_api_tests():
    """运行所有API测试"""
    print("🚀 开始交易引擎API测试...")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {BASE_URL}")
    print("=" * 50)

    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 交易引擎服务器未运行或响应异常")
            return False
    except:
        print("❌ 无法连接到交易引擎服务器，请确保服务器在 http://localhost:8002 运行")
        return False

    # 运行所有测试
    test_functions = [
        test_health_checks,
        test_strategy_apis,
        test_trading_apis,
        test_trading_service_apis,
        test_web_interface
    ]

    passed = 0
    total = len(test_functions)

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")

    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 API测试结果汇总:")
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")

    if passed == total:
        print("🎉 所有API测试通过！")
        return True
    else:
        print(f"⚠️ 有 {total - passed} 个API测试失败")
        return False

if __name__ == "__main__":
    success = run_api_tests()
    if not success:
        exit(1)