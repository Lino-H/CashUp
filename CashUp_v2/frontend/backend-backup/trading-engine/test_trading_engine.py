"""
交易引擎测试脚本
用于验证交易引擎的基本功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

async def test_strategy_manager():
    """测试策略管理器"""
    print("🧪 测试策略管理器...")

    try:
        from strategies.strategy_manager import get_strategy_manager
        from exchanges.base import ExchangeManager

        # 创建交易所管理器（模拟）
        exchange_manager = ExchangeManager()
        await exchange_manager.initialize()

        # 创建策略管理器
        strategy_manager = await get_strategy_manager()

        # 测试获取策略状态
        status = await strategy_manager.get_strategy_status()
        print(f"✅ 策略状态: {status}")

        # 测试启动单个策略
        success = await strategy_manager.start_strategy('grid')
        print(f"✅ 启动网格策略: {success}")

        # 等待策略运行
        await asyncio.sleep(2)

        # 测试获取策略信号
        signals = await strategy_manager.get_strategy_signals('grid', 5)
        print(f"✅ 网格策略信号: {len(signals)} 个")

        # 测试获取策略持仓
        positions = await strategy_manager.get_strategy_positions('grid')
        print(f"✅ 网格策略持仓: {len(positions)} 个")

        # 测试停止策略
        success = await strategy_manager.stop_strategy('grid')
        print(f"✅ 停止网格策略: {success}")

        await exchange_manager.close()
        return True

    except Exception as e:
        print(f"❌ 策略管理器测试失败: {e}")
        return False

async def test_base_strategies():
    """测试基础策略"""
    print("\n🧪 测试基础策略...")

    try:
        from strategies.base_strategy import GridStrategy, TrendFollowingStrategy, ArbitrageStrategy

        # 测试网格策略
        grid_config = {
            'grid_levels': 3,
            'grid_spacing': 0.01,
            'base_price': 3000.0,
            'grid_size': 0.1,
            'max_position_size': 10.0
        }

        grid_strategy = GridStrategy(grid_config)
        await grid_strategy.initialize()
        print(f"✅ 网格策略初始化成功: {grid_strategy.name}")

        # 测试趋势跟踪策略
        trend_config = {
            'ma_short': 5,
            'ma_long': 10,
            'rsi_period': 9,
            'position_size': 1.0
        }

        trend_strategy = TrendFollowingStrategy(trend_config)
        await trend_strategy.initialize()
        print(f"✅ 趋势跟踪策略初始化成功: {trend_strategy.name}")

        # 测试套利策略
        arbitrage_config = {
            'min_profit_rate': 0.001,
            'price_tolerance': 0.005
        }

        arbitrage_strategy = ArbitrageStrategy(arbitrage_config)
        await arbitrage_strategy.initialize()
        print(f"✅ 套利策略初始化成功: {arbitrage_strategy.name}")

        # 测试市场分析（模拟数据）
        market_data = {
            'BTC/USDT': {
                'last_price': 30000.0,
                'bid_price': 29950.0,
                'ask_price': 30050.0,
                'volume_24h': 50000000.0,
                'price_change_24h': 2.5
            },
            'ETH/USDT': {
                'last_price': 2000.0,
                'bid_price': 1990.0,
                'ask_price': 2010.0,
                'volume_24h': 30000000.0,
                'price_change_24h': -1.2
            }
        }

        # 测试网格策略分析
        grid_signals = await grid_strategy.analyze_market(market_data)
        print(f"✅ 网格策略生成信号: {len(grid_signals)} 个")

        # 测试趋势跟踪策略分析
        trend_signals = await trend_strategy.analyze_market(market_data)
        print(f"✅ 趋势跟踪策略生成信号: {len(trend_signals)} 个")

        # 测试套利策略分析
        arbitrage_signals = await arbitrage_strategy.analyze_market(market_data)
        print(f"✅ 套利策略生成信号: {len(arbitrage_signals)} 个")

        return True

    except Exception as e:
        print(f"❌ 基础策略测试失败: {e}")
        return False

async def test_exchange_manager():
    """测试交易所管理器"""
    print("\n🧪 测试交易所管理器...")

    try:
        from exchanges.base import ExchangeManager

        exchange_manager = ExchangeManager()
        await exchange_manager.initialize()
        print(f"✅ 交易所管理器初始化成功")

        # 测试获取订单状态映射
        status_mapping = exchange_manager._map_order_status('open')
        print(f"✅ 订单状态映射: {status_mapping}")

        # 测试获取订单类型映射
        type_mapping = exchange_manager._map_order_type('limit')
        print(f"✅ 订单类型映射: {type_mapping}")

        # 测试创建订单请求
        from exchanges.base import OrderRequest, OrderSide, OrderType

        order_request = OrderRequest(
            symbol='BTC/USDT',
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=0.1,
            price=30000.0
        )

        print(f"✅ 订单请求创建成功: {order_request}")

        await exchange_manager.close()
        return True

    except Exception as e:
        print(f"❌ 交易所管理器测试失败: {e}")
        return False

async def test_config_service():
    """测试配置服务"""
    print("\n🧪 测试配置服务...")

    try:
        from services.config_service import ConfigService

        config_service = ConfigService()
        await config_service.initialize()
        print(f"✅ 配置服务初始化成功")

        # 测试获取默认交易所配置
        gateio_config = await config_service.get_exchange_config('gateio')
        print(f"✅ Gate.io配置: {gateio_config['name']}")

        # 测试获取交易配置
        trading_config = await config_service.get_trading_config()
        print(f"✅ 交易配置: {trading_config['default_leverage']}x 杠杆")

        # 测试获取模拟配置
        simulation_config = await config_service.get_simulation_config()
        print(f"✅ 模拟配置: {simulation_config['simulation_mode']}")

        return True

    except Exception as e:
        print(f"❌ 配置服务测试失败: {e}")
        return False

async def test_main_app():
    """测试主应用"""
    print("\n🧪 测试主应用...")

    try:
        from main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # 测试根路径
        response = client.get("/")
        print(f"✅ 根路径: {response.status_code}")

        # 测试健康检查
        response = client.get("/health")
        print(f"✅ 健康检查: {response.status_code}")

        # 测试策略状态
        response = client.get("/api/v1/strategies/status")
        print(f"✅ 策略状态: {response.status_code}")

        # 测试交易接口
        response = client.get("/api/v1/balances")
        print(f"✅ 余额查询: {response.status_code}")

        # 测试账户信息
        response = client.get("/api/v1/account/info")
        print(f"✅ 账户信息: {response.status_code}")

        return True

    except Exception as e:
        print(f"❌ 主应用测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始交易引擎测试...")
    print("=" * 50)

    results = []

    # 运行各个测试
    tests = [
        test_config_service,
        test_exchange_manager,
        test_base_strategies,
        test_strategy_manager,
        test_main_app
    ]

    for test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
            results.append(False)

    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")

    passed = sum(results)
    total = len(results)

    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")

    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print(f"⚠️ 有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    asyncio.run(run_all_tests())