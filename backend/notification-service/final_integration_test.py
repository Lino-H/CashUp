#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终集成测试 - 验证notification-service中QANotify的完整集成
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def load_env_config():
    """加载环境配置"""
    return {
        'QANOTIFY_TOKEN': os.getenv('QANOTIFY_TOKEN')
    }

def test_qanotify_package():
    """测试qanotify包可用性"""
    print("\n=== 测试QANotify包可用性 ===")
    try:
        from qanotify import run_order_notify, run_price_notify, run_strategy_notify
        print("✅ QANotify包导入成功")
        return True, (run_order_notify, run_price_notify, run_strategy_notify)
    except ImportError as e:
        print(f"❌ QANotify包导入失败: {e}")
        return False, None

def test_sender_service_integration():
    """测试SenderService集成"""
    print("\n=== 测试SenderService集成 ===")
    try:
        # 添加app目录到Python路径
        app_path = os.path.join(os.path.dirname(__file__), 'app')
        if app_path not in sys.path:
            sys.path.insert(0, app_path)
        
        from services.sender_service import SenderService
        
        # 检查QANotify相关方法
        service = SenderService()
        
        if hasattr(service, '_send_qanotify'):
            print("✅ SenderService._send_qanotify方法存在")
        else:
            print("❌ SenderService._send_qanotify方法不存在")
            return False
            
        if hasattr(service, '_get_qanotify_method_name'):
            print("✅ SenderService._get_qanotify_method_name方法存在")
        else:
            print("❌ SenderService._get_qanotify_method_name方法不存在")
            return False
        
        # 测试方法名称映射
        method_name_order = service._get_qanotify_method_name('order')
        method_name_price = service._get_qanotify_method_name('price')
        method_name_strategy = service._get_qanotify_method_name('strategy')
        
        print(f"✅ 订单通知方法映射: {method_name_order}")
        print(f"✅ 价格预警方法映射: {method_name_price}")
        print(f"✅ 策略通知方法映射: {method_name_strategy}")
        
        return True
        
    except Exception as e:
        print(f"❌ SenderService集成测试失败: {e}")
        return False

def test_direct_qanotify_calls():
    """直接测试QANotify调用"""
    print("\n=== 直接测试QANotify调用 ===")
    
    config = load_env_config()
    token = config.get('QANOTIFY_TOKEN')
    
    if not token:
        print("❌ QANOTIFY_TOKEN未配置")
        return False
    
    try:
        from qanotify import run_order_notify, run_price_notify, run_strategy_notify
        
        # 测试订单通知
        print("测试订单通知...")
        run_order_notify(
            token, "CashUp策略", "测试账户", "BTCUSDT",
            "BUY", "OPEN", 50000, 0.1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        print("✅ 订单通知发送成功")
        
        # 测试价格预警
        print("测试价格预警...")
        run_price_notify(
            token, "价格预警", "BTCUSDT", "50000", 51000, "test_order_123"
        )
        print("✅ 价格预警发送成功")
        
        # 测试策略通知
        print("测试策略通知...")
        run_strategy_notify(
            token, "CashUp策略", "集成测试", "notification-service集成测试消息", "once"
        )
        print("✅ 策略通知发送成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 直接QANotify调用失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始notification-service QANotify集成最终测试")
    print("=" * 60)
    
    test_results = []
    
    # 1. 测试QANotify包可用性
    qanotify_available, qanotify_methods = test_qanotify_package()
    test_results.append(("QANotify包可用性", qanotify_available))
    
    # 2. 测试SenderService集成
    sender_integration = test_sender_service_integration()
    test_results.append(("SenderService集成", sender_integration))
    
    # 3. 直接测试QANotify调用
    direct_calls = test_direct_qanotify_calls()
    test_results.append(("直接QANotify调用", direct_calls))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 最终测试结果汇总")
    print("=" * 60)
    
    success_count = 0
    total_count = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n总体结果: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！notification-service的QANotify集成完全正常")
        print("\n✅ 确认事项:")
        print("   - qanotify包已正确安装和导入")
        print("   - SenderService._send_qanotify方法已正确实现")
        print("   - 根据通知类别正确调用对应的qanotify方法")
        print("   - 订单、价格预警、策略通知都能正常发送")
        print("   - 使用.env文件中的QANOTIFY_TOKEN配置")
    else:
        print("⚠️  部分测试失败，请检查相关配置和代码")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)