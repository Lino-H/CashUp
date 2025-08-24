#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - QANotify集成测试

测试notification-service中QANotify的集成是否正常工作
"""

import os
import sys
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.notification import Notification, NotificationCategory, NotificationPriority
from app.models.channel import NotificationChannel, ChannelType
from app.services.sender_service import SenderService


class MockAsyncSession:
    """模拟数据库会话"""
    async def execute(self, *args, **kwargs):
        pass
    
    async def commit(self):
        pass


def load_env_config() -> Dict[str, str]:
    """
    加载环境配置
    
    Returns:
        Dict[str, str]: 配置字典
    """
    config = {}
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config


def create_test_notification(category: str, template_vars: Dict[str, Any] = None) -> Notification:
    """
    创建测试通知对象
    
    Args:
        category: 通知类别
        template_vars: 模板变量
        
    Returns:
        Notification: 通知对象
    """
    notification = Notification(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title=f"测试{category}通知",
        content=f"这是一个{category}测试消息",
        category=NotificationCategory(category) if category in ['order', 'price', 'strategy'] else NotificationCategory.GENERAL,
        priority=NotificationPriority.NORMAL,
        channels=['qanotify'],
        recipients=['test'],
        template_variables=template_vars or {},
        created_at=datetime.utcnow()
    )
    return notification


def create_test_channel(token: str) -> NotificationChannel:
    """
    创建测试QANotify渠道
    
    Args:
        token: QANotify token
        
    Returns:
        NotificationChannel: 渠道对象
    """
    channel = NotificationChannel(
        id=uuid.uuid4(),
        name="测试QANotify渠道",
        type=ChannelType.QANOTIFY,
        config={'token': token},
        is_active=True
    )
    return channel


async def test_qanotify_order_notification():
    """
    测试订单通知
    """
    print("\n=== 测试订单通知 ===")
    
    config = load_env_config()
    token = config.get('QANOTIFY_TOKEN')
    
    if not token:
        print("❌ 未找到QANOTIFY_TOKEN配置")
        return False
    
    # 创建测试数据
    template_vars = {
        'strategy_name': 'CashUp测试策略',
        'account_name': '测试账户',
        'contract': 'BTC/USDT',
        'order_direction': 'BUY',
        'order_offset': 'OPEN',
        'price': 50000,
        'volume': 0.1
    }
    
    notification = create_test_notification('order', template_vars)
    channel = create_test_channel(token)
    
    # 准备发送内容
    content = {
        'subject': notification.title,
        'content': notification.content,
        'recipient': 'test'
    }
    
    try:
        sender_service = SenderService()
        result = await sender_service._send_qanotify(channel, notification, content)
        
        print(f"✅ 订单通知发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   方法: {result['details']['method']}")
        print(f"   类别: {result['details']['category']}")
        return True
        
    except Exception as e:
        print(f"❌ 订单通知发送失败: {str(e)}")
        return False


async def test_qanotify_price_notification():
    """
    测试价格预警通知
    """
    print("\n=== 测试价格预警通知 ===")
    
    config = load_env_config()
    token = config.get('QANOTIFY_TOKEN')
    
    if not token:
        print("❌ 未找到QANOTIFY_TOKEN配置")
        return False
    
    # 创建测试数据
    template_vars = {
        'contract': 'ETH/USDT',
        'current_price': '3000.50',
        'limit_price': 3100,
        'order_id': 'test_order_123'
    }
    
    notification = create_test_notification('price', template_vars)
    notification.title = "ETH价格预警"
    channel = create_test_channel(token)
    
    # 准备发送内容
    content = {
        'subject': notification.title,
        'content': notification.content,
        'recipient': 'test'
    }
    
    try:
        sender_service = SenderService()
        result = await sender_service._send_qanotify(channel, notification, content)
        
        print(f"✅ 价格预警通知发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   方法: {result['details']['method']}")
        print(f"   类别: {result['details']['category']}")
        return True
        
    except Exception as e:
        print(f"❌ 价格预警通知发送失败: {str(e)}")
        return False


async def test_qanotify_strategy_notification():
    """
    测试策略通知
    """
    print("\n=== 测试策略通知 ===")
    
    config = load_env_config()
    token = config.get('QANOTIFY_TOKEN')
    
    if not token:
        print("❌ 未找到QANOTIFY_TOKEN配置")
        return False
    
    # 创建测试数据
    template_vars = {
        'strategy_name': 'CashUp量化策略',
        'frequency': 'daily'
    }
    
    notification = create_test_notification('strategy', template_vars)
    notification.title = "策略执行报告"
    notification.content = "今日策略执行完成，收益率+2.5%"
    channel = create_test_channel(token)
    
    # 准备发送内容
    content = {
        'subject': notification.title,
        'content': notification.content,
        'recipient': 'test'
    }
    
    try:
        sender_service = SenderService()
        result = await sender_service._send_qanotify(channel, notification, content)
        
        print(f"✅ 策略通知发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   方法: {result['details']['method']}")
        print(f"   类别: {result['details']['category']}")
        return True
        
    except Exception as e:
        print(f"❌ 策略通知发送失败: {str(e)}")
        return False


async def main():
    """
    主测试函数
    """
    print("🚀 开始QANotify集成测试")
    print("=" * 50)
    
    # 执行测试
    results = []
    results.append(await test_qanotify_order_notification())
    results.append(await test_qanotify_price_notification())
    results.append(await test_qanotify_strategy_notification())
    
    # 统计结果
    success_count = sum(results)
    total_count = len(results)
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果汇总: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        print("🎉 所有QANotify集成测试通过！")
    else:
        print(f"⚠️  有 {total_count - success_count} 个测试失败")
    
    return success_count == total_count


if __name__ == "__main__":
    asyncio.run(main())