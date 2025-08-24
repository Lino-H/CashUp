#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的PushPlus测试脚本

直接测试PushPlus发送功能，不依赖复杂的导入
"""

import os
import asyncio
import aiohttp
import json
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_pushplus_send(token: str, title: str, content: str, template: str = "html", topic: str = None):
    """
    测试PushPlus发送功能
    
    Args:
        token: PushPlus token
        title: 消息标题
        content: 消息内容
        template: 消息模板 (html, markdown, json)
        topic: 群组编码（可选）
    
    Returns:
        dict: 发送结果
    """
    url = "http://www.pushplus.plus/send"
    
    # 构建请求数据
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": template
    }
    
    if topic:
        data["topic"] = topic
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = await response.json()
                
                return {
                    "success": response.status == 200 and result.get("code") == 200,
                    "status_code": response.status,
                    "response": result,
                    "message_id": result.get("data") if result.get("code") == 200 else None,
                    "error": result.get("msg") if result.get("code") != 200 else None
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": None,
            "response": None,
            "message_id": None
        }

async def test_pushplus_html():
    """
    测试HTML格式消息
    """
    print("\n=== 测试PushPlus HTML消息 ===")
    
    token = os.getenv('PUSHPLUS_TOKEN')
    if not token:
        print("❌ PUSHPLUS_TOKEN未配置")
        return False
    
    title = "🧪 CashUp系统测试 - HTML"
    content = """
<h2>🚀 CashUp量化交易系统</h2>
<p><strong>测试类型:</strong> HTML格式消息</p>
<p><strong>测试时间:</strong> {}</p>
<div style="background-color: #f0f8ff; padding: 10px; border-left: 4px solid #007acc;">
    <p>✅ 这是一条HTML格式的测试消息</p>
    <p>📊 系统运行正常</p>
</div>
<hr>
<p><em>来自 notification-service 的自动化测试</em></p>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    result = await test_pushplus_send(token, title, content, "html")
    
    if result["success"]:
        print(f"✅ HTML消息发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   响应: {result['response']['msg']}")
        return True
    else:
        print(f"❌ HTML消息发送失败: {result['error']}")
        return False

async def test_pushplus_markdown():
    """
    测试Markdown格式消息
    """
    print("\n=== 测试PushPlus Markdown消息 ===")
    
    token = os.getenv('PUSHPLUS_TOKEN')
    if not token:
        print("❌ PUSHPLUS_TOKEN未配置")
        return False
    
    title = "📈 CashUp交易提醒 - Markdown"
    content = """
# 🚀 CashUp量化交易系统

## 📊 交易信息
- **合约**: BTCUSDT
- **方向**: 买入开仓
- **价格**: $50,000
- **数量**: 0.1 BTC
- **时间**: {}

## 📈 市场分析
> 当前市场趋势良好，建议持续关注

### ✅ 系统状态
- [x] 策略运行正常
- [x] 风控系统正常
- [x] 通知系统正常

---
*来自 notification-service 的自动化测试*
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    result = await test_pushplus_send(token, title, content, "markdown")
    
    if result["success"]:
        print(f"✅ Markdown消息发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   响应: {result['response']['msg']}")
        return True
    else:
        print(f"❌ Markdown消息发送失败: {result['error']}")
        return False

async def test_pushplus_json():
    """
    测试JSON格式消息
    """
    print("\n=== 测试PushPlus JSON消息 ===")
    
    token = os.getenv('PUSHPLUS_TOKEN')
    if not token:
        print("❌ PUSHPLUS_TOKEN未配置")
        return False
    
    title = "🔔 CashUp系统通知 - JSON"
    
    # JSON格式的内容
    json_content = {
        "system": "CashUp量化交易系统",
        "type": "系统通知",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data": {
            "status": "正常",
            "message": "这是一条JSON格式的测试消息",
            "details": {
                "service": "notification-service",
                "test_type": "JSON格式测试",
                "success": True
            }
        }
    }
    
    content = json.dumps(json_content, ensure_ascii=False, indent=2)
    
    result = await test_pushplus_send(token, title, content, "json")
    
    if result["success"]:
        print(f"✅ JSON消息发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   响应: {result['response']['msg']}")
        return True
    else:
        print(f"❌ JSON消息发送失败: {result['error']}")
        return False

def show_pushplus_api_guide():
    """
    显示PushPlus API使用指南
    """
    print("\n" + "=" * 60)
    print("📚 PushPlus API 使用指南")
    print("=" * 60)
    
    print("\n🔗 **API接口:**")
    print("   POST http://www.pushplus.plus/send")
    
    print("\n📝 **请求参数:**")
    print("   - token: 用户令牌（必填）")
    print("   - title: 消息标题（必填）")
    print("   - content: 消息内容（必填）")
    print("   - template: 消息模板（可选，默认html）")
    print("   - topic: 群组编码（可选）")
    
    print("\n🎨 **支持的模板:**")
    print("   - html: HTML格式")
    print("   - markdown: Markdown格式")
    print("   - json: JSON格式")
    print("   - cloudMonitor: 云监控格式")
    
    print("\n📱 **在notification-service中调用:**")
    print("```python")
    print("# 配置渠道")
    print("channel_config = {")
    print('    "token": "your_pushplus_token",')
    print('    "topic": "your_topic_code"  # 可选')
    print("}")
    print("")
    print("# 发送消息")
    print("result = await sender_service._send_pushplus(channel, notification, content)")
    print("```")
    
    print("\n🔧 **环境配置:**")
    print("   在.env文件中设置: PUSHPLUS_TOKEN=你的token")

async def main():
    """
    主测试函数
    """
    print("🚀 开始PushPlus API测试")
    print("=" * 60)
    
    # 显示使用指南
    show_pushplus_api_guide()
    
    # 检查token配置
    token = os.getenv('PUSHPLUS_TOKEN')
    if not token:
        print("\n❌ 错误: PUSHPLUS_TOKEN未配置")
        print("请在.env文件中设置 PUSHPLUS_TOKEN=你的token")
        return False
    
    print(f"\n✅ PUSHPLUS_TOKEN已配置: {token[:10]}...")
    
    # 运行测试
    test_results = []
    
    # 测试HTML消息
    result1 = await test_pushplus_html()
    test_results.append(("HTML消息测试", result1))
    
    # 等待1秒避免频率限制
    await asyncio.sleep(1)
    
    # 测试Markdown消息
    result2 = await test_pushplus_markdown()
    test_results.append(("Markdown消息测试", result2))
    
    # 等待1秒避免频率限制
    await asyncio.sleep(1)
    
    # 测试JSON消息
    result3 = await test_pushplus_json()
    test_results.append(("JSON消息测试", result3))
    
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
        print("🎉 所有PushPlus API测试通过！")
        print("\n✅ 确认事项:")
        print("   - PushPlus API调用正常")
        print("   - 支持HTML、Markdown、JSON格式")
        print("   - 消息发送成功")
        print("   - notification-service可以使用相同的逻辑")
    else:
        print("⚠️  部分测试失败，请检查token配置和网络连接")
    
    return success_count == total_count

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        exit(1)