#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp系统测试脚本
"""

import requests
import json
from typing import Dict, Any, Optional


class CashUpTester:
    """CashUp系统测试类"""
    
    def __init__(self):
        self.user_service_url = "http://localhost:8001"
        self.notification_service_url = "http://localhost:8010"
        self.access_token = None
    
    def test_admin_login(self, username: str = "admin", password: str = "admin123456") -> Dict[str, Any]:
        """测试管理员登录"""
        print(f"\n🔐 测试管理员登录: {username}")
        
        try:
            response = requests.post(
                f"{self.user_service_url}/auth/login",
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                print(f"✅ 登录成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
            else:
                print(f"❌ 登录失败: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
                
        except Exception as e:
            print(f"❌ 登录异常: {str(e)}")
            return {"error": str(e)}
    
    def test_user_info(self) -> Dict[str, Any]:
        """测试获取用户信息"""
        print("\n👤 测试获取用户信息")
        
        if not self.access_token:
            print("❌ 未登录，无法获取用户信息")
            return {"error": "Not authenticated"}
        
        try:
            response = requests.get(
                f"{self.user_service_url}/users/me",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 用户信息获取成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
            else:
                print(f"❌ 用户信息获取失败: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
                
        except Exception as e:
            print(f"❌ 用户信息获取异常: {str(e)}")
            return {"error": str(e)}
    
    def test_email_notification(self, recipient: str = "371886367@qq.com") -> Dict[str, Any]:
        """测试邮件通知"""
        print(f"\n📧 测试邮件通知: {recipient}")
        
        if not self.access_token:
            print("❌ 未登录，无法发送通知")
            return {"error": "Not authenticated"}
        
        payload = {
            "title": "CashUp邮件测试",
            "content": "这是一条来自CashUp量化交易系统的测试邮件。\n\n系统时间: 2025-08-23\n测试用户: admin",
            "category": "test",
            "priority": "normal",
            "channels": ["email"],
            "recipients": {
                "email": [recipient]
            }
        }
        
        try:
            response = requests.post(
                f"{self.notification_service_url}/api/v1/notifications",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.access_token}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 邮件通知发送成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
            else:
                print(f"❌ 邮件通知发送失败: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
                
        except Exception as e:
            print(f"❌ 邮件通知发送异常: {str(e)}")
            return {"error": str(e)}
    
    def test_wxpusher_notification(self, uid: str = "UID_IEJEQcqISvVDlgVaIee3B8S5hTeY") -> Dict[str, Any]:
        """测试WxPusher通知"""
        print(f"\n📱 测试WxPusher通知: {uid}")
        
        if not self.access_token:
            print("❌ 未登录，无法发送通知")
            return {"error": "Not authenticated"}
        
        payload = {
            "title": "CashUp微信推送测试",
            "content": "这是一条来自CashUp量化交易系统的测试微信推送。\n\n系统时间: 2025-08-23\n测试用户: admin",
            "category": "test",
            "priority": "normal",
            "channels": ["wxpusher"],
            "recipients": {
                "wxpusher": [uid]
            }
        }
        
        try:
            response = requests.post(
                f"{self.notification_service_url}/api/v1/notifications",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.access_token}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ WxPusher通知发送成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
            else:
                print(f"❌ WxPusher通知发送失败: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
                
        except Exception as e:
            print(f"❌ WxPusher通知发送异常: {str(e)}")
            return {"error": str(e)}
    
    def test_pushplus_notification(self) -> Dict[str, Any]:
        """测试PushPlus通知"""
        print("\n📲 测试PushPlus通知")
        
        if not self.access_token:
            print("❌ 未登录，无法发送通知")
            return {"error": "Not authenticated"}
        
        payload = {
            "title": "CashUp PushPlus测试",
            "content": "这是一条来自CashUp量化交易系统的测试PushPlus推送。\n\n系统时间: 2025-08-23\n测试用户: admin",
            "category": "test",
            "priority": "normal",
            "channels": ["pushplus"],
            "recipients": {
                "pushplus": ["default"]
            }
        }
        
        try:
            response = requests.post(
                f"{self.notification_service_url}/api/v1/notifications",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.access_token}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ PushPlus通知发送成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
            else:
                print(f"❌ PushPlus通知发送失败: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
                
        except Exception as e:
            print(f"❌ PushPlus通知发送异常: {str(e)}")
            return {"error": str(e)}


def main():
    """主函数"""
    print("🚀 开始测试CashUp系统...")
    
    tester = CashUpTester()
    
    # 1. 测试管理员登录
    login_result = tester.test_admin_login()
    if "error" in login_result:
        print("\n❌ 登录失败，无法继续测试")
        return
    
    # 2. 测试获取用户信息
    tester.test_user_info()
    
    # 3. 测试邮件通知
    tester.test_email_notification()
    
    # 4. 测试WxPusher通知
    tester.test_wxpusher_notification()
    
    # 5. 测试PushPlus通知
    tester.test_pushplus_notification()
    
    print("\n✅ CashUp系统测试完成！")


if __name__ == "__main__":
    main()