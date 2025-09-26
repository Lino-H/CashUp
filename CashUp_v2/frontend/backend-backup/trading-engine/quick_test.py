#!/usr/bin/env python3
"""
快速功能验证脚本
"""

import asyncio
import sys
import os

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """测试基本导入"""
    print("🔍 测试基本模块导入...")

    try:
        # 测试基础模块
        from exchanges.base import ExchangeManager, Order, OrderSide, OrderType
        print("✅ 基础交易所模块导入成功")

        from exchanges.gateio import GateIOExchange
        print("✅ Gate.io交易所模块导入成功")

        from strategies.base_strategy import GridStrategy, TrendFollowingStrategy, ArbitrageStrategy
        print("✅ 策略基础模块导入成功")

        from strategies.strategy_manager import StrategyManager
        print("✅ 策略管理器模块导入成功")

        from services.config_service import ConfigService
        print("✅ 配置服务模块导入成功")

        # 测试主应用
        from main import app
        print("✅ 主应用导入成功")

        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_strategies():
    """测试策略功能"""
    print("\n🔍 测试策略功能...")

    try:
        # 创建配置
        grid_config = {
            'grid_levels': 3,
            'grid_spacing': 0.01,
            'base_price': 3000.0,
            'grid_size': 0.1,
            'max_position_size': 10.0
        }

        # 创建网格策略
        from strategies.base_strategy import GridStrategy
        grid_strategy = GridStrategy(grid_config)
        grid_strategy.name = "网格策略"
        print(f"✅ {grid_strategy.name} 创建成功")

        # 创建趋势策略
        trend_config = {
            'ma_short': 5,
            'ma_long': 10,
            'rsi_period': 9,
            'position_size': 1.0
        }

        from strategies.base_strategy import TrendFollowingStrategy
        trend_strategy = TrendFollowingStrategy(trend_config)
        trend_strategy.name = "趋势跟踪策略"
        print(f"✅ {trend_strategy.name} 创建成功")

        return True
    except Exception as e:
        print(f"❌ 策略测试失败: {e}")
        return False

def test_config():
    """测试配置服务"""
    print("\n🔍 测试配置服务...")

    try:
        from services.config_service import ConfigService

        config_service = ConfigService()
        config_service.initialize()
        print("✅ 配置服务初始化成功")

        # 获取默认配置
        gateio_config = config_service.get_exchange_config('gateio')
        print(f"✅ Gate.io配置获取成功: {gateio_config['name']}")

        trading_config = config_service.get_trading_config()
        print(f"✅ 交易配置获取成功: {trading_config['default_leverage']}x 杠杆")

        return True
    except Exception as e:
        print(f"❌ 配置服务测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始CashUp交易引擎快速验证...")
    print("=" * 50)

    results = []

    # 运行测试
    tests = [
        test_imports,
        test_strategies,
        test_config
    ]

    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
            results.append(False)

    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 快速验证结果:")

    passed = sum(results)
    total = len(results)

    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")

    if passed == total:
        print("🎉 所有核心功能验证通过！")
        print("\n🚀 启动交易引擎命令:")
        print("  uvicorn main:app --reload --host 0.0.0.0 --port 8002")
        return True
    else:
        print(f"⚠️ 有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)