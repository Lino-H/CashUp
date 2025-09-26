"""
交易引擎启动测试脚本
用于验证交易引擎启动和基本功能
"""

import asyncio
import sys
import os
import uvicorn
from datetime import datetime

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

async def test_dependencies():
    """测试依赖项"""
    print("🔍 测试依赖项...")

    try:
        # 测试基础导入
        import logging
        print("✅ 日志模块导入成功")

        import asyncio
        print("✅ 异步IO模块导入成功")

        from datetime import datetime, timezone
        print("✅ 日期时间模块导入成功")

        from typing import Dict, List, Optional, Any
        print("✅ 类型提示模块导入成功")

        # 测试dataclasses
        from dataclasses import dataclass
        from dataclasses import asdict

        @dataclass
        class TestClass:
            value: str

        test_obj = TestClass("test")
        serialized = asdict(test_obj)
        print("✅ dataclasses模块导入成功")

        # 测试FastAPI
        from fastapi import FastAPI
        print("✅ FastAPI模块导入成功")

        # 测试aiohttp
        import aiohttp
        print("✅ aiohttp模块导入成功")

        # 测试aioredis
        import aioredis
        print("✅ aioredis模块导入成功")

        print("🎉 所有依赖项测试通过！")
        return True

    except Exception as e:
        print(f"❌ 依赖项测试失败: {e}")
        return False

async def test_project_imports():
    """测试项目模块导入"""
    print("\n🔍 测试项目模块导入...")

    try:
        # 测试交易所模块
        from exchanges.base import ExchangeManager, Order, OrderSide, OrderType
        print("✅ 交易所基础模块导入成功")

        from exchanges.gateio import GateIOExchange
        print("✅ Gate.io交易所模块导入成功")

        # 测试策略模块
        from strategies.base_strategy import BaseStrategy, Signal, Position
        print("✅ 策略基础模块导入成功")

        from strategies.strategy_manager import StrategyManager
        print("✅ 策略管理器模块导入成功")

        # 测试配置服务
        from services.config_service import ConfigService
        print("✅ 配置服务模块导入成功")

        # 测试API路由
        from api.routes.strategies import router as strategies_router
        print("✅ 策略路由模块导入成功")

        from api.routes.trading import router as trading_router
        print("✅ 交易路由模块导入成功")

        print("🎉 所有项目模块导入成功！")
        return True

    except Exception as e:
        print(f"❌ 项目模块导入失败: {e}")
        return False

async def test_main_app():
    """测试主应用"""
    print("\n🔍 测试主应用...")

    try:
        from main import app

        # 检查应用配置
        assert app.title == "CashUp 交易引擎"
        assert app.version == "2.0.0"
        print("✅ 主应用配置正确")

        # 检查路由
        routes = [route.path for route in app.routes]
        required_routes = [
            "/", "/health", "/docs", "/redoc",
            "/api/v1/strategies/status",
            "/api/v1/orders", "/api/v1/positions",
            "/api/v1/balances", "/api/v1/account/info"
        ]

        for route in required_routes:
            if route in routes:
                print(f"✅ 路由存在: {route}")
            else:
                print(f"⚠️ 路由缺失: {route}")

        # 检查CORS配置
        cors_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware.cls, 'allow_origins'):
                cors_middleware = middleware.cls
                break

        if cors_middleware:
            print("✅ CORS中间件配置正确")
        else:
            print("⚠️ CORS中间件配置缺失")

        print("🎉 主应用测试完成！")
        return True

    except Exception as e:
        print(f"❌ 主应用测试失败: {e}")
        return False

async def test_strategy_initialization():
    """测试策略初始化"""
    print("\n🔍 测试策略初始化...")

    try:
        from strategies.strategy_manager import get_strategy_manager

        # 获取策略管理器
        strategy_manager = await get_strategy_manager()
        print("✅ 策略管理器获取成功")

        # 检查策略数量
        strategies = strategy_manager.strategies
        print(f"✅ 已加载策略数量: {len(strategies)}")

        # 检查策略名称
        for name, strategy in strategies.items():
            print(f"✅ 策略 {name}: {strategy.name}")

        # 测试获取策略状态
        status = await strategy_manager.get_strategy_status()
        print(f"✅ 策略状态获取成功: {len(status)} 个策略")

        print("🎉 策略初始化测试完成！")
        return True

    except Exception as e:
        print(f"❌ 策略初始化测试失败: {e}")
        return False

async def quick_start_test():
    """快速启动测试"""
    print("🚀 开始快速启动测试...")
    print("=" * 50)

    results = []

    # 运行测试
    tests = [
        test_dependencies,
        test_project_imports,
        test_main_app,
        test_strategy_initialization
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
        print("🎉 所有测试通过！可以正常启动交易引擎")
        return True
    else:
        print(f"⚠️ 有 {total - passed} 个测试失败")
        return False

async def start_engine():
    """启动交易引擎"""
    print("\n🚀 启动交易引擎...")
    print("=" * 50)

    try:
        from main import app

        print("📡 启动服务器在 http://localhost:8002")
        print("📖 API文档: http://localhost:8002/docs")
        print("📊 ReDoc文档: http://localhost:8002/redoc")

        # 启动服务器
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8002,
            reload=False,
            log_level="info"
        )

        server = uvicorn.Server(config)
        await server.serve()

    except Exception as e:
        print(f"❌ 启动失败: {e}")

async def main():
    """主函数"""
    print("🏁 CashUp交易引擎启动测试")
    print("=" * 50)

    # 运行测试
    success = await quick_start_test()

    if success:
        print("\n" + "=" * 50)
        print("🚀 开始启动交易引擎...")
        await start_engine()
    else:
        print("\n❌ 测试未通过，请检查错误信息后重试")

if __name__ == "__main__":
    asyncio.run(main())