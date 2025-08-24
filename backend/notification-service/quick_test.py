#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速通知服务测试脚本
"""

import requests
import json
from typing import Dict, Any


def test_notification_channels():
    """测试所有通知渠道"""
    base_url = "http://localhost:8010"
    
    # 测试数据
    test_cases = [
        {
            "name": "邮件通知",
            "payload": {
                "title": "CashUp邮件测试",
                "content": "这是一条来自CashUp量化交易系统的测试邮件。",
                "category": "test",
                "priority": "normal",
                "channels": ["email"],
                "recipients": {
                    "email": ["371886367@qq.com"]
                }
            }
        },
        {
            "name": "WxPusher通知",
            "payload": {
                "title": "CashUp微信推送测试",
                "content": "这是一条来自CashUp量化交易系统的测试微信推送。",
                "category": "test",
                "priority": "normal",
                "channels": ["wxpusher"],
                "recipients": {
                    "wxpusher": ["UID_IEJEQcqISvVDlgVaIee3B8S5hTeY"]
                }
            }
        },
        {
            "name": "PushPlus通知",
            "payload": {
                "title": "CashUp PushPlus测试",
                "content": "这是一条来自CashUp量化交易系统的测试PushPlus推送。",
                "category": "test",
                "priority": "normal",
                "channels": ["pushplus"],
                "recipients": {
                    "pushplus": ["60ad54690c904ed3b35a06640e1af904"]
                }
            }
        },
        {
            "name": "QANotify通知",
            "payload": {
                "title": "CashUp QANotify测试",
                "content": "这是一条来自CashUp量化交易系统的测试QANotify推送。",
                "category": "test",
                "priority": "normal",
                "channels": ["qanotify"],
                "recipients": {
                    "qanotify": ["test_user"]
                }
            }
        }
    ]
    
    print("🚀 开始测试CashUp通知服务...")
    
    # 检查服务健康状态
    print("\n1. 检查服务健康状态")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 通知服务运行正常")
        else:
            print(f"❌ 服务健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到通知服务: {str(e)}")
        return
    
    # 测试各个通知渠道
    for i, test_case in enumerate(test_cases, 2):
        print(f"\n{i}. 测试{test_case['name']}")
        try:
            response = requests.post(
                f"{base_url}/api/v1/notifications",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ {test_case['name']}测试成功")
                print(f"   通知ID: {result.get('id', 'N/A')}")
                print(f"   状态: {result.get('status', 'N/A')}")
            else:
                print(f"❌ {test_case['name']}测试失败: HTTP {response.status_code}")
                print(f"   错误信息: {response.text}")
                
        except Exception as e:
            print(f"❌ {test_case['name']}测试异常: {str(e)}")
    
    print("\n✅ 通知服务测试完成！")


if __name__ == "__main__":
    test_notification_channels()