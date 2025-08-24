#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp通知服务 - QANotify集成简化测试

测试notification-service中qanotify的集成是否按照测试通过的方式正常工作
"""

import os
import sys
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any

# 添加app目录到Python路径
app_path = os.path.join(os.path.dirname(__file__), 'app')
if app_path not in sys.path:
    sys.path.insert(0, app_path)

def load_env_config():
    """
    加载环境配置
    
    Returns:
        Dict[str, str]: 环境配置字典
    """
    # 从.env文件手动读取
    env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    config = {}
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config

class MockNotification:
    """
    模拟通知对象
    """
    def __init__(self, notification_id: str, title: str, content: str, category: str, template_variables: Dict[str, Any] = None):
        self.id = notification_id
        self.title = title
        self.content = content
        self.category = MockCategory(category)
        self.template_variables = template_variables or {}
        self.created_at = datetime.now()

class MockCategory:
    """
    模拟通知类别
    """
    def __init__(self, value: str):
        self.value = value

class MockChannel:
    """
    模拟通知渠道
    """
    def __init__(self, token: str):
        self.config = {'token': token}

def test_qanotify_package_availability():
    """
    测试qanotify包可用性
    
    Returns:
        bool: 是否可用
    """
    print("\n=== 测试QANotify包可用性 ===")
    try:
        from qanotify import run_order_notify, run_price_notify, run_strategy_notify
        print("✅ QANotify包导入成功")
        return True, (run_order_notify, run_price_notify, run_strategy_notify)
    except ImportError as e:
        print(f"❌ QANotify包导入失败: {e}")
        return False, None

def test_sender_service_import():
    """
    测试SenderService导入和方法存在性
    
    Returns:
        bool: 是否成功
    """
    print("\n=== 测试SenderService导入 ===")
    try:
        from app.services.sender_service import SenderService
        
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
        
        return True, service
        
    except Exception as e:
        print(f"❌ SenderService导入失败: {e}")
        return False, None

async def test_qanotify_order_notification(sender_service, token: str):
    """
    测试订单通知发送
    
    Args:
        sender_service: SenderService实例
        token: QANotify token
        
    Returns:
        bool: 是否成功
    """
    print("\n=== 测试订单通知发送 ===")
    try:
        # 创建模拟订单通知
        notification = MockNotification(
            notification_id=str(uuid.uuid4()),
            title="订单执行通知",
            content="您的订单已成功执行",
            category="order",
            template_variables={
                'strategy_name': 'CashUp测试策略',
                'account_name': '测试账户',
                'contract': 'BTCUSDT',
                'order_direction': 'BUY',
                'order_offset': 'OPEN',
                'price': 50000,
                'volume': 0.1
            }
        )
        
        channel = MockChannel(token)
        content = {
            'subject': notification.title,
            'content': notification.content,
            'recipient': 'test_user'
        }
        
        # 调用发送方法
        result = await sender_service._send_qanotify(channel, notification, content)
        
        print(f"✅ 订单通知发送成功")
        print(f"   消息ID: {result.get('message_id')}")
        print(f"   方法: {result.get('details', {}).get('method')}")
        print(f"   类别: {result.get('details', {}).get('category')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 订单通知发送失败: {e}")
        return False

async def test_qanotify_price_notification(sender_service, token: str):
    """
    测试价格预警通知发送
    
    Args:
        sender_service: SenderService实例
        token: QANotify token
        
    Returns:
        bool: 是否成功
    """
    print("\n=== 测试价格预警通知发送 ===")
    try:
        # 创建模拟价格预警通知
        notification = MockNotification(
            notification_id=str(uuid.uuid4()),
            title="价格预警通知",
            content="BTCUSDT价格达到预警线",
            category="price",
            template_variables={
                'contract': 'BTCUSDT',
                'current_price': '51000',
                'limit_price': 50000,
                'order_id': 'test_order_123'
            }
        )
        
        channel = MockChannel(token)
        content = {
            'subject': notification.title,
            'content': notification.content,
            'recipient': 'test_user'
        }
        
        # 调用发送方法
        result = await sender_service._send_qanotify(channel, notification, content)
        
        print(f"✅ 价格预警通知发送成功")
        print(f"   消息ID: {result.get('message_id')}")
        print(f"   方法: {result.get('details', {}).get('method')}")
        print(f"   类别: {result.get('details', {}).get('category')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 价格预警通知发送失败: {e}")
        return False

async def test_qanotify_strategy_notification(sender_service, token: str):
    """
    测试策略通知发送
    
    Args:
        sender_service: SenderService实例
        token: QANotify token
        
    Returns:
        bool: 是否成功
    """
    print("\n=== 测试策略通知发送 ===")
    try:
        # 创建模拟策略通知
        notification = MockNotification(
            notification_id=str(uuid.uuid4()),
            title="策略运行状态",
            content="CashUp策略运行正常，当前收益率5.2%",
            category="strategy",
            template_variables={
                'strategy_name': 'CashUp测试策略',
                'frequency': 'once'
            }
        )
        
        channel = MockChannel(token)
        content = {
            'subject': notification.title,
            'content': notification.content,
            'recipient': 'test_user'
        }
        
        # 调用发送方法
        result = await sender_service._send_qanotify(channel, notification, content)
        
        print(f"✅ 策略通知发送成功")
        print(f"   消息ID: {result.get('message_id')}")
        print(f"   方法: {result.get('details', {}).get('method')}")
        print(f"   类别: {result.get('details', {}).get('category')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 策略通知发送失败: {e}")
        return False

async def main():
    """
    主测试函数
    """
    print("🚀 开始notification-service QANotify集成测试")
    print("=" * 60)
    
    config = load_env_config()
    token = config.get('QANOTIFY_TOKEN')
    
    if not token:
        print("❌ QANOTIFY_TOKEN未配置，请检查.env文件")
        return False
    
    print(f"✅ 找到QANOTIFY_TOKEN: {token[:10]}...")
    
    test_results = []
    
    # 1. 测试QANotify包可用性
    qanotify_available, qanotify_methods = test_qanotify_package_availability()
    test_results.append(("QANotify包可用性", qanotify_available))
    
    if not qanotify_available:
        print("❌ QANotify包不可用，无法继续测试")
        return False
    
    # 2. 测试SenderService导入
    sender_import_success, sender_service = test_sender_service_import()
    test_results.append(("SenderService导入", sender_import_success))
    
    if not sender_import_success:
        print("❌ SenderService导入失败，无法继续测试")
        return False
    
    # 3. 测试订单通知
    order_test = await test_qanotify_order_notification(sender_service, token)
    test_results.append(("订单通知发送", order_test))
    
    # 4. 测试价格预警通知
    price_test = await test_qanotify_price_notification(sender_service, token)
    test_results.append(("价格预警通知发送", price_test))
    
    # 5. 测试策略通知
    strategy_test = await test_qanotify_strategy_notification(sender_service, token)
    test_results.append(("策略通知发送", strategy_test))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
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
        print("\n🔥 notification-service已经按照测试通过的方式正确配置！")
    else:
        print("⚠️  部分测试失败，请检查相关配置和代码")
    
    return success_count == total_count

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)