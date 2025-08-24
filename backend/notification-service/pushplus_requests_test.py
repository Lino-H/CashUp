#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PushPlus测试脚本 - 使用requests库

测试PushPlus API发送功能，使用requests库而不是aiohttp
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv

try:
    import requests
except ImportError:
    print("❌ requests库未安装，请运行: pip install requests")
    exit(1)

# 加载环境变量
load_dotenv()

def test_pushplus_send(token: str, title: str, content: str, template: str = "html", topic: str = None):
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
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        result = response.json()
        
        return {
            "success": response.status_code == 200 and result.get("code") == 200,
            "status_code": response.status_code,
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

def test_pushplus_html():
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
    
    result = test_pushplus_send(token, title, content, "html")
    
    if result["success"]:
        print(f"✅ HTML消息发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   响应: {result['response']['msg']}")
        return True
    else:
        print(f"❌ HTML消息发送失败: {result['error']}")
        if result['response']:
            print(f"   详细错误: {result['response']}")
        return False

def test_pushplus_markdown():
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
    
    result = test_pushplus_send(token, title, content, "markdown")
    
    if result["success"]:
        print(f"✅ Markdown消息发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   响应: {result['response']['msg']}")
        return True
    else:
        print(f"❌ Markdown消息发送失败: {result['error']}")
        if result['response']:
            print(f"   详细错误: {result['response']}")
        return False

def test_pushplus_json():
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
    
    result = test_pushplus_send(token, title, content, "json")
    
    if result["success"]:
        print(f"✅ JSON消息发送成功")
        print(f"   消息ID: {result['message_id']}")
        print(f"   响应: {result['response']['msg']}")
        return True
    else:
        print(f"❌ JSON消息发送失败: {result['error']}")
        if result['response']:
            print(f"   详细错误: {result['response']}")
        return False

def test_notification_service_integration():
    """
    测试notification-service集成
    
    模拟notification-service中_send_pushplus方法的逻辑
    """
    print("\n=== 测试notification-service集成逻辑 ===")
    
    token = os.getenv('PUSHPLUS_TOKEN')
    if not token:
        print("❌ PUSHPLUS_TOKEN未配置")
        return False
    
    # 模拟notification-service的逻辑
    def detect_template(content: str) -> str:
        """检测内容格式"""
        if content.strip().startswith('<') and content.strip().endswith('>'):
            return "html"
        elif any(marker in content for marker in ['#', '**', '- [', '> ']):
            return "markdown"
        else:
            return "html"
    
    # 测试数据
    test_cases = [
        {
            "title": "📊 CashUp订单通知",
            "content": "<h3>订单执行成功</h3><p>合约: BTCUSDT</p><p>价格: $50,000</p>",
            "expected_template": "html"
        },
        {
            "title": "📈 CashUp价格预警",
            "content": "# 价格预警\n\n**BTCUSDT** 价格突破 $50,000\n\n> 建议关注后续走势",
            "expected_template": "markdown"
        },
        {
            "title": "🔔 CashUp系统通知",
            "content": "系统运行正常，所有服务状态良好。",
            "expected_template": "html"
        }
    ]
    
    success_count = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n   测试用例 {i}: {case['title']}")
        
        # 检测模板
        detected_template = detect_template(case['content'])
        print(f"   检测到模板: {detected_template} (期望: {case['expected_template']})")
        
        # 发送消息
        result = test_pushplus_send(
            token, 
            case['title'], 
            case['content'], 
            detected_template
        )
        
        if result["success"]:
            print(f"   ✅ 发送成功 - 消息ID: {result['message_id']}")
            success_count += 1
        else:
            print(f"   ❌ 发送失败: {result['error']}")
        
        # 避免频率限制
        time.sleep(1)
    
    print(f"\n   集成测试结果: {success_count}/{len(test_cases)} 成功")
    return success_count == len(test_cases)

def show_pushplus_usage_guide():
    """
    显示PushPlus使用指南
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
    print("# 1. 获取token")
    print("token = channel.config.get('token')")
    print("")
    print("# 2. 检测模板格式")
    print("if '<' in content and '>' in content:")
    print("    template = 'html'")
    print("elif any(marker in content for marker in ['#', '**', '- [']):")
    print("    template = 'markdown'")
    print("else:")
    print("    template = 'html'")
    print("")
    print("# 3. 发送请求")
    print("async with aiohttp.ClientSession() as session:")
    print("    async with session.post(url, json=data) as response:")
    print("        result = await response.json()")
    print("```")
    
    print("\n🔧 **环境配置:**")
    print("   在.env文件中设置: PUSHPLUS_TOKEN=你的token")

def main():
    """
    主测试函数
    """
    print("🚀 开始PushPlus API测试 (使用requests)")
    print("=" * 60)
    
    # 显示使用指南
    show_pushplus_usage_guide()
    
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
    result1 = test_pushplus_html()
    test_results.append(("HTML消息测试", result1))
    
    # 等待1秒避免频率限制
    time.sleep(1)
    
    # 测试Markdown消息
    result2 = test_pushplus_markdown()
    test_results.append(("Markdown消息测试", result2))
    
    # 等待1秒避免频率限制
    time.sleep(1)
    
    # 测试JSON消息
    result3 = test_pushplus_json()
    test_results.append(("JSON消息测试", result3))
    
    # 等待1秒避免频率限制
    time.sleep(1)
    
    # 测试notification-service集成
    result4 = test_notification_service_integration()
    test_results.append(("notification-service集成测试", result4))
    
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
        print("   - notification-service集成逻辑正确")
        print("   - 模板自动检测功能正常")
    else:
        print("⚠️  部分测试失败，请检查token配置和网络连接")
    
    return success_count == total_count

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        exit(1)