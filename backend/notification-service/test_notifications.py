#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知服务测试脚本
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


class NotificationTester:
    """通知服务测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_email_notification(self, recipient: str = "371886367@qq.com") -> Dict[str, Any]:
        """测试邮件通知"""
        payload = {
            "title": "CashUp邮件测试",
            "content": "这是一条来自CashUp量化交易系统的测试邮件。",
            "category": "test",
            "priority": "normal",
            "channels": ["email"],
            "recipients": {
                "email": [recipient]
            },
            "template_variables": {
                "user_name": "测试用户",
                "system_name": "CashUp"
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/notifications",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                print(f"邮件通知测试结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
        except Exception as e:
            print(f"邮件通知测试失败: {str(e)}")
            return {"error": str(e)}
    
    async def test_wxpusher_notification(self, uid: str = "UID_IEJEQcqISvVDlgVaIee3B8S5hTeY") -> Dict[str, Any]:
        """测试WxPusher通知"""
        payload = {
            "title": "CashUp微信推送测试",
            "content": "这是一条来自CashUp量化交易系统的测试微信推送。",
            "category": "test",
            "priority": "normal",
            "channels": ["wxpusher"],
            "recipients": {
                "wxpusher": [uid]
            },
            "template_variables": {
                "user_name": "测试用户",
                "system_name": "CashUp"
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/notifications",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                print(f"WxPusher通知测试结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
        except Exception as e:
            print(f"WxPusher通知测试失败: {str(e)}")
            return {"error": str(e)}
    
    async def test_pushplus_notification(self, token: str = "60ad54690c904ed3b35a06640e1af904") -> Dict[str, Any]:
        """测试PushPlus通知"""
        payload = {
            "title": "CashUp PushPlus测试",
            "content": "这是一条来自CashUp量化交易系统的测试PushPlus推送。",
            "category": "test",
            "priority": "normal",
            "channels": ["pushplus"],
            "recipients": {
                "pushplus": [token]
            },
            "template_variables": {
                "user_name": "测试用户",
                "system_name": "CashUp"
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/notifications",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                print(f"PushPlus通知测试结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
        except Exception as e:
            print(f"PushPlus通知测试失败: {str(e)}")
            return {"error": str(e)}
    
    async def check_service_health(self) -> Dict[str, Any]:
        """检查服务健康状态"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                result = await response.json()
                print(f"服务健康状态: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
        except Exception as e:
            print(f"健康检查失败: {str(e)}")
            return {"error": str(e)}


async def main():
    """主函数"""
    print("🚀 开始测试CashUp通知服务...")
    
    async with NotificationTester() as tester:
        # 检查服务健康状态
        print("\n1. 检查服务健康状态")
        await tester.check_service_health()
        
        # 测试邮件通知
        print("\n2. 测试邮件通知")
        await tester.test_email_notification()
        
        # 测试WxPusher通知
        print("\n3. 测试WxPusher通知")
        await tester.test_wxpusher_notification()
        
        # 测试PushPlus通知
        print("\n4. 测试PushPlus通知")
        await tester.test_pushplus_notification()
    
    print("\n✅ 通知服务测试完成！")


if __name__ == "__main__":
    asyncio.run(main())