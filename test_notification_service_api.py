#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp通知服务API测试脚本
通过notification服务的API接口测试三个渠道（wxpusher、pushplus、qanotify）
"""

import os
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple

# 通知服务的基础URL
BASE_URL = "http://localhost:8010"

def load_env_config():
    """
    加载环境变量配置
    """
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def check_service_health() -> bool:
    """
    检查通知服务是否正常运行
    
    Returns:
        bool: 服务是否正常
    """
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 服务健康检查失败: {e}")
        return False

def get_channels() -> List[Dict[str, Any]]:
    """
    获取已配置的通知渠道
    
    Returns:
        List[Dict]: 渠道列表
    """
    try:
        response = requests.get(f"{BASE_URL}/api/v1/channels", timeout=10)
        if response.status_code == 200:
            return response.json().get('channels', [])
        else:
            print(f"❌ 获取渠道失败: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ 获取渠道异常: {e}")
        return []

def send_test_notification(channel_name: str, test_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    发送测试通知
    
    Args:
        channel_name: 渠道名称
        test_data: 测试数据
        
    Returns:
        Tuple[bool, Dict]: (是否成功, 响应数据)
    """
    try:
        print(f"\n📤 发送 {channel_name} 测试通知...")
        print(f"请求数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/notifications",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"响应状态: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ {channel_name} 通知发送成功!")
            return True, result
        else:
            print(f"❌ {channel_name} 通知发送失败: {response.status_code}")
            return False, {"error": response.text, "status_code": response.status_code}
            
    except Exception as e:
        print(f"❌ {channel_name} 发送异常: {e}")
        return False, {"error": str(e)}

def test_wxpusher() -> Tuple[str, bool, Dict[str, Any]]:
    """
    测试WxPusher渠道
    
    Returns:
        Tuple[str, bool, Dict]: (渠道名, 是否成功, 结果数据)
    """
    test_data = {
        "title": "CashUp WxPusher测试通知",
        "content": f"这是一条来自CashUp系统的WxPusher测试通知\n\n发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n渠道: WxPusher\n状态: 测试中",
        "category": "system",
        "priority": "normal",
        "channels": ["wxpusher"],
        "recipients": {},  # 空recipients，测试默认配置
        "metadata": {
            "test_mode": True,
            "test_timestamp": datetime.now().isoformat()
        }
    }
    
    success, result = send_test_notification("WxPusher", test_data)
    return "WxPusher", success, result

def test_pushplus() -> Tuple[str, bool, Dict[str, Any]]:
    """
    测试PushPlus渠道
    
    Returns:
        Tuple[str, bool, Dict]: (渠道名, 是否成功, 结果数据)
    """
    test_data = {
        "title": "CashUp PushPlus测试通知",
        "content": f"这是一条来自CashUp系统的PushPlus测试通知<br><br>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>渠道: PushPlus<br>状态: 测试中",
        "category": "system",
        "priority": "normal",
        "channels": ["pushplus"],
        "recipients": {},  # 空recipients，测试默认配置
        "metadata": {
            "test_mode": True,
            "test_timestamp": datetime.now().isoformat()
        }
    }
    
    success, result = send_test_notification("PushPlus", test_data)
    return "PushPlus", success, result

def test_qanotify() -> Tuple[str, bool, Dict[str, Any]]:
    """
    测试QANotify渠道
    
    Returns:
        Tuple[str, bool, Dict]: (渠道名, 是否成功, 结果数据)
    """
    test_data = {
        "title": "CashUp QANotify测试通知",
        "content": f"这是一条来自CashUp系统的QANotify测试通知\n\n发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n渠道: QANotify\n状态: 测试中",
        "category": "system",
        "priority": "normal",
        "channels": ["qanotify"],
        "recipients": {},  # 空recipients，测试默认配置
        "metadata": {
            "test_mode": True,
            "test_timestamp": datetime.now().isoformat()
        }
    }
    
    success, result = send_test_notification("QANotify", test_data)
    return "QANotify", success, result

def test_order_notification() -> Tuple[str, bool, Dict[str, Any]]:
    """
    测试订单通知（QANotify特定类型）
    
    Returns:
        Tuple[str, bool, Dict]: (渠道名, 是否成功, 结果数据)
    """
    test_data = {
        "title": "CashUp订单通知测试",
        "content": "订单执行通知",
        "category": "trading",
        "priority": "high",
        "channels": ["qanotify"],
        "recipients": {},
        "template_variables": {
            "strategy_name": "TestStrategy",
            "account_name": "TestAccount",
            "contract": "BTCUSDT",
            "order_direction": "BUY",
            "order_offset": "OPEN",
            "price": 50000.0,
            "volume": 0.1
        },
        "metadata": {
            "test_mode": True,
            "test_timestamp": datetime.now().isoformat()
        }
    }
    
    success, result = send_test_notification("QANotify-Order", test_data)
    return "QANotify-Order", success, result

def test_price_notification() -> Tuple[str, bool, Dict[str, Any]]:
    """
    测试价格预警通知（QANotify特定类型）
    
    Returns:
        Tuple[str, bool, Dict]: (渠道名, 是否成功, 结果数据)
    """
    test_data = {
        "title": "CashUp价格预警测试",
        "content": "价格预警通知",
        "category": "alert",
        "priority": "high",
        "channels": ["qanotify"],
        "recipients": {},
        "template_variables": {
            "contract": "BTCUSDT",
            "current_price": "51000.0",
            "limit_price": 50000.0,
            "order_id": "test_order_123"
        },
        "metadata": {
            "test_mode": True,
            "test_timestamp": datetime.now().isoformat()
        }
    }
    
    success, result = send_test_notification("QANotify-Price", test_data)
    return "QANotify-Price", success, result

def main():
    """
    主函数
    """
    print("\n" + "="*80)
    print("CashUp 通知服务API测试")
    print("="*80)
    
    # 加载环境变量
    load_env_config()
    
    # 检查服务状态
    print("\n=== 服务状态检查 ===")
    if not check_service_health():
        print("❌ 通知服务未运行或不可访问")
        print("请确保notification服务正在运行在 http://localhost:8010")
        return
    
    print("✅ 通知服务运行正常")
    
    # 获取渠道信息
    print("\n=== 渠道配置检查 ===")
    channels = get_channels()
    if channels:
        print(f"✅ 找到 {len(channels)} 个已配置的渠道:")
        for channel in channels:
            print(f"  - {channel.get('name', 'Unknown')}: {channel.get('type', 'Unknown')}")
    else:
        print("⚠️ 未找到已配置的渠道")
    
    # 执行测试
    print("\n=== 开始通知测试 ===")
    test_results = []
    
    # 测试基本通知
    test_results.append(test_wxpusher())
    time.sleep(2)  # 避免请求过快
    
    test_results.append(test_pushplus())
    time.sleep(2)
    
    test_results.append(test_qanotify())
    time.sleep(2)
    
    # 测试QANotify特定类型
    test_results.append(test_order_notification())
    time.sleep(2)
    
    test_results.append(test_price_notification())
    
    # 生成测试报告
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)
    
    success_count = sum(1 for _, success, _ in test_results if success)
    total_count = len(test_results)
    
    for channel, success, result in test_results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{channel:20}: {status}")
        if not success and 'error' in result:
            print(f"{'':22}错误: {result['error'][:100]}...")
    
    print(f"\n总计: {success_count}/{total_count} 个测试通过")
    print(f"成功率: {(success_count/total_count*100):.1f}%")
    
    # 保存详细报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"notification_service_test_report_{timestamp}.json"
    
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "service_url": BASE_URL,
        "summary": {
            "total": total_count,
            "success": success_count,
            "failed": total_count - success_count,
            "success_rate": f"{(success_count/total_count*100):.1f}%"
        },
        "channels": [{
            "name": channel.get('name'),
            "type": channel.get('type'),
            "status": channel.get('status')
        } for channel in channels],
        "test_results": [{
            "channel": channel,
            "success": success,
            "result": result
        } for channel, success, result in test_results]
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 详细报告已保存到: {report_file}")
    
    if success_count == total_count:
        print("\n🎉 所有通知测试通过！")
    elif success_count > 0:
        print("\n⚠️ 部分通知测试通过，请检查失败的渠道配置")
    else:
        print("\n💥 所有通知测试失败！请检查服务配置和渠道设置")

if __name__ == "__main__":
    main()