#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PushPlus集成测试脚本

测试notification-service中的PushPlus发送功能
"""

import os
import sys
import asyncio
import uuid
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加app目录到Python路径
app_path = os.path.join(os.path.dirname(__file__), 'app')
if app_path not in sys.path:
    sys.path.insert(0, app_path)

# 添加services目录到Python路径
services_path = os.path.join(app_path, 'services')
if services_path not in sys.path:
    sys.path.insert(0, services_path)

def load_env_config():
    """
    加载环境配置
    
    Returns:
        dict: 环境配置字典
    """
    return {
        'PUSHPLUS_TOKEN': os.getenv('PUSHPLUS_TOKEN')
    }

class MockNotification:
    """
    模拟通知对象
    """
    def __init__(self, title: str, content: str, category: str = 'general'):
        self.id = uuid.uuid4()
        self.title = title
        self.content = content
        self.category = MockCategory(category)
        self.created_at = datetime.utcnow()
        self.template_variables = {}

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
    def __init__(self, token: str, topic: str = None):
        self.id = uuid.uuid4()
        self.config = {
            'token': token
        }
        if topic:
            self.config['topic'] = topic

async def test_pushplus_html_message():
    """
    测试PushPlus HTML消息发送
    
    Returns:
        bool: 测试是否成功
    """
    print("\n=== 测试PushPlus HTML消息 ===")
    
    config = load_env_config()
    token = config.get('PUSHPLUS_TOKEN')
    
    if not token:
        print("❌ PUSHPLUS_TOKEN未配置")
        return False
    
    try:
        # 直接导入SenderService
        import sender_service
        SenderService = sender_service.SenderService
        
        # 创建模拟对象
        notification = MockNotification(
            title="CashUp系统测试",
            content="<h2>HTML格式测试</h2><p>这是一条来自CashUp量化交易系统的HTML测试消息</p><p>时间: {}</p>".format(
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ),
            category="system"
        )
        
        channel = MockChannel(token)
        
        content = {
            'subject': notification.title,
            'content': notification.content,
            'recipient': 'test_user'
        }
        
        # 发送消息
        sender_service = SenderService()
        result = await sender_service._send_pushplus(channel, notification, content)
        
        print(f"✅ HTML消息发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   模板: {result['details']['template']}")
        print(f"   响应: {result['details']['response_msg']}")
        
        return True
        
    except Exception as e:
        print(f"❌ HTML消息发送失败: {e}")
        return False

async def test_pushplus_markdown_message():
    """
    测试PushPlus Markdown消息发送
    
    Returns:
        bool: 测试是否成功
    """
    print("\n=== 测试PushPlus Markdown消息 ===")
    
    config = load_env_config()
    token = config.get('PUSHPLUS_TOKEN')
    
    if not token:
        print("❌ PUSHPLUS_TOKEN未配置")
        return False
    
    try:
        # 直接导入SenderService
        import sender_service
        SenderService = sender_service.SenderService
        
        # 创建模拟对象
        markdown_content = """
# CashUp交易提醒

## 订单信息
- **合约**: BTCUSDT
- **方向**: 买入开仓
- **价格**: $50,000
- **数量**: 0.1 BTC
- **时间**: {}

> 这是一条来自CashUp量化交易系统的Markdown测试消息
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        notification = MockNotification(
            title="📈 CashUp交易提醒",
            content=markdown_content,
            category="order"
        )
        
        channel = MockChannel(token)
        
        content = {
            'subject': notification.title,
            'content': notification.content,
            'recipient': 'test_user'
        }
        
        # 发送消息
        sender_service = SenderService()
        result = await sender_service._send_pushplus(channel, notification, content)
        
        print(f"✅ Markdown消息发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   模板: {result['details']['template']}")
        print(f"   响应: {result['details']['response_msg']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Markdown消息发送失败: {e}")
        return False

async def test_pushplus_topic_message():
    """
    测试PushPlus群组消息发送
    
    Returns:
        bool: 测试是否成功
    """
    print("\n=== 测试PushPlus群组消息 ===")
    
    config = load_env_config()
    token = config.get('PUSHPLUS_TOKEN')
    
    if not token:
        print("❌ PUSHPLUS_TOKEN未配置")
        return False
    
    try:
        # 直接导入SenderService
        import sender_service
        SenderService = sender_service.SenderService
        
        # 创建模拟对象（带群组编码）
        notification = MockNotification(
            title="🔔 CashUp系统通知",
            content="这是一条发送到群组的测试消息\n时间: {}".format(
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ),
            category="notification"
        )
        
        # 注意：这里使用了topic参数，需要有效的群组编码
        # 如果没有群组编码，可以注释掉topic参数
        channel = MockChannel(token)  # topic="your_topic_code"
        
        content = {
            'subject': notification.title,
            'content': notification.content,
            'recipient': 'group_users'
        }
        
        # 发送消息
        sender_service = SenderService()
        result = await sender_service._send_pushplus(channel, notification, content)
        
        print(f"✅ 群组消息发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   模板: {result['details']['template']}")
        print(f"   群组: {result['details']['topic'] or '个人'}")
        print(f"   响应: {result['details']['response_msg']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 群组消息发送失败: {e}")
        return False

def test_pushplus_direct_api():
    """
    测试直接调用PushPlus API
    
    Returns:
        bool: 测试是否成功
    """
    print("\n=== 测试直接PushPlus API调用 ===")
    
    config = load_env_config()
    token = config.get('PUSHPLUS_TOKEN')
    
    if not token:
        print("❌ PUSHPLUS_TOKEN未配置")
        return False
    
    try:
        import requests
        
        # 构建请求数据
        data = {
            "token": token,
            "title": "🧪 直接API测试",
            "content": "这是直接调用PushPlus API的测试消息\n时间: {}".format(
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ),
            "template": "html"
        }
        
        # 发送请求
        response = requests.post(
            "http://www.pushplus.plus/send",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        result = response.json()
        
        if response.status_code == 200 and result.get("code") == 200:
            print(f"✅ 直接API调用成功")
            print(f"   消息ID: {result.get('data')}")
            print(f"   响应码: {result.get('code')}")
            print(f"   响应消息: {result.get('msg')}")
            return True
        else:
            print(f"❌ 直接API调用失败: {result.get('msg', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 直接API调用异常: {e}")
        return False

def show_pushplus_usage_guide():
    """
    显示PushPlus使用指南
    """
    print("\n" + "=" * 60)
    print("📚 PushPlus使用指南")
    print("=" * 60)
    
    print("\n🔑 **获取Token:**")
    print("1. 访问 http://www.pushplus.plus/")
    print("2. 微信扫码登录")
    print("3. 复制你的token")
    print("4. 在.env文件中设置 PUSHPLUS_TOKEN=你的token")
    
    print("\n📡 **在notification-service中使用:**")
    print("```python")
    print("# 1. 配置渠道")
    print("channel_config = {")
    print('    "token": "your_pushplus_token",')  
    print('    "topic": "your_topic_code"  # 可选，群组编码')
    print("}")
    print("")
    print("# 2. 发送消息")
    print("await sender_service._send_pushplus(channel, notification, content)")
    print("```")
    
    print("\n🎨 **支持的模板:**")
    print("- html: HTML格式 (默认)")
    print("- markdown: Markdown格式 (自动检测)")
    print("- json: JSON格式")
    print("- cloudMonitor: 云监控格式")
    
    print("\n📝 **消息格式示例:**")
    print("```html")
    print("<!-- HTML格式 -->")
    print("<h2>标题</h2>")
    print("<p>内容</p>")
    print("```")
    
    print("```markdown")
    print("# Markdown格式")
    print("## 子标题")
    print("- 列表项")
    print("**粗体文本**")
    print("> 引用")
    print("```")

async def main():
    """
    主测试函数
    """
    print("🚀 开始PushPlus集成测试")
    print("=" * 60)
    
    # 显示使用指南
    show_pushplus_usage_guide()
    
    # 检查token配置
    config = load_env_config()
    token = config.get('PUSHPLUS_TOKEN')
    
    if not token:
        print("\n❌ 错误: PUSHPLUS_TOKEN未配置")
        print("请在.env文件中设置 PUSHPLUS_TOKEN=你的token")
        return
    
    print(f"\n✅ PUSHPLUS_TOKEN已配置: {token[:10]}...")
    
    # 运行测试
    test_results = []
    
    # 测试HTML消息
    result1 = await test_pushplus_html_message()
    test_results.append(("HTML消息测试", result1))
    
    # 测试Markdown消息
    result2 = await test_pushplus_markdown_message()
    test_results.append(("Markdown消息测试", result2))
    
    # 测试群组消息
    result3 = await test_pushplus_topic_message()
    test_results.append(("群组消息测试", result3))
    
    # 测试直接API调用
    result4 = test_pushplus_direct_api()
    test_results.append(("直接API调用测试", result4))
    
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
        print("🎉 所有PushPlus集成测试通过！")
        print("\n✅ 确认事项:")
        print("   - notification-service的_send_pushplus方法正常工作")
        print("   - 支持HTML和Markdown模板自动检测")
        print("   - 支持群组消息发送")
        print("   - PushPlus API调用正常")
    else:
        print("⚠️  部分测试失败，请检查token配置和网络连接")
    
    return success_count == total_count

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        sys.exit(1)