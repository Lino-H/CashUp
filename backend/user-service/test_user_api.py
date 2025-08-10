#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp用户服务API测试脚本

测试用户认证系统的核心功能：
- 用户注册
- 用户登录
- 获取用户信息
- 更新用户信息
- JWT令牌验证
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from datetime import datetime


class UserAPITester:
    """
    用户API测试类
    
    提供完整的用户认证系统测试功能
    """
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        初始化测试器
        
        Args:
            base_url: API服务基础URL
        """
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.test_user_data = {
            "username": f"testuser_{int(datetime.now().timestamp())}",
            "email": f"test_{int(datetime.now().timestamp())}@example.com",
            "password": "TestPassword123",
            "full_name": "测试用户",
            "bio": "这是一个测试用户账户",
            "timezone": "Asia/Shanghai",
            "language": "zh-CN"
        }
    
    async def __aenter__(self):
        """
        异步上下文管理器入口
        """
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器出口
        """
        if self.session:
            await self.session.close()
    
    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_auth: bool = False
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            headers: 请求头
            use_auth: 是否使用认证令牌
            
        Returns:
            Dict: 响应数据
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = headers or {}
        
        if use_auth and self.access_token:
            request_headers["Authorization"] = f"Bearer {self.access_token}"
        
        if data:
            request_headers["Content-Type"] = "application/json"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                headers=request_headers
            ) as response:
                response_data = await response.json()
                return {
                    "status_code": response.status,
                    "data": response_data,
                    "success": 200 <= response.status < 300
                }
        except Exception as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False
            }
    
    async def test_health_check(self) -> bool:
        """
        测试健康检查接口
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试健康检查接口 ===")
        
        response = await self.make_request("GET", "/")
        
        if response["success"]:
            print("✅ 健康检查通过")
            print(f"响应: {response['data']}")
            return True
        else:
            print("❌ 健康检查失败")
            print(f"错误: {response['data']}")
            return False
    
    async def test_user_registration(self) -> bool:
        """
        测试用户注册功能
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试用户注册功能 ===")
        
        response = await self.make_request(
            "POST", 
            "/api/v1/users/register", 
            data=self.test_user_data
        )
        
        if response["success"]:
            print("✅ 用户注册成功")
            user_data = response["data"]
            print(f"用户ID: {user_data.get('id')}")
            print(f"用户名: {user_data.get('username')}")
            print(f"邮箱: {user_data.get('email')}")
            print(f"状态: {user_data.get('status')}")
            return True
        else:
            print("❌ 用户注册失败")
            print(f"错误: {response['data']}")
            return False
    
    async def test_user_login(self) -> bool:
        """
        测试用户登录功能
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试用户登录功能 ===")
        
        login_data = {
            "username": self.test_user_data["username"],
            "password": self.test_user_data["password"]
        }
        
        response = await self.make_request(
            "POST", 
            "/api/v1/users/login", 
            data=login_data
        )
        
        if response["success"]:
            print("✅ 用户登录成功")
            login_response = response["data"]
            
            # 保存令牌
            token_data = login_response.get("token", {})
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            
            print(f"访问令牌: {self.access_token[:50]}...")
            print(f"刷新令牌: {self.refresh_token[:50]}...")
            print(f"令牌类型: {token_data.get('token_type')}")
            print(f"过期时间: {token_data.get('expires_in')}秒")
            
            # 用户信息
            user_info = login_response.get("user", {})
            print(f"登录用户: {user_info.get('username')}")
            print(f"用户角色: {user_info.get('roles')}")
            
            return True
        else:
            print("❌ 用户登录失败")
            print(f"错误: {response['data']}")
            return False
    
    async def test_get_current_user(self) -> bool:
        """
        测试获取当前用户信息
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试获取当前用户信息 ===")
        
        if not self.access_token:
            print("❌ 缺少访问令牌，请先登录")
            return False
        
        response = await self.make_request(
            "GET", 
            "/api/v1/users/me", 
            use_auth=True
        )
        
        if response["success"]:
            print("✅ 获取用户信息成功")
            user_data = response["data"]
            print(f"用户ID: {user_data.get('id')}")
            print(f"用户名: {user_data.get('username')}")
            print(f"邮箱: {user_data.get('email')}")
            print(f"真实姓名: {user_data.get('full_name')}")
            print(f"邮箱验证: {user_data.get('is_email_verified')}")
            print(f"用户角色: {user_data.get('roles')}")
            print(f"创建时间: {user_data.get('created_at')}")
            return True
        else:
            print("❌ 获取用户信息失败")
            print(f"错误: {response['data']}")
            return False
    
    async def test_update_user_profile(self) -> bool:
        """
        测试更新用户资料
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试更新用户资料 ===")
        
        if not self.access_token:
            print("❌ 缺少访问令牌，请先登录")
            return False
        
        update_data = {
            "full_name": "更新后的测试用户",
            "bio": "这是更新后的用户简介",
            "timezone": "Asia/Shanghai"
        }
        
        response = await self.make_request(
            "PUT", 
            "/api/v1/users/me", 
            data=update_data,
            use_auth=True
        )
        
        if response["success"]:
            print("✅ 用户资料更新成功")
            user_data = response["data"]
            print(f"更新后姓名: {user_data.get('full_name')}")
            print(f"更新后简介: {user_data.get('bio')}")
            print(f"更新时间: {user_data.get('updated_at')}")
            return True
        else:
            print("❌ 用户资料更新失败")
            print(f"错误: {response['data']}")
            return False
    
    async def test_token_refresh(self) -> bool:
        """
        测试令牌刷新功能
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试令牌刷新功能 ===")
        
        if not self.refresh_token:
            print("❌ 缺少刷新令牌，请先登录")
            return False
        
        refresh_data = {
            "refresh_token": self.refresh_token
        }
        
        response = await self.make_request(
            "POST", 
            "/api/v1/users/refresh", 
            data=refresh_data
        )
        
        if response["success"]:
            print("✅ 令牌刷新成功")
            token_data = response["data"]
            
            # 更新令牌
            old_access_token = self.access_token
            self.access_token = token_data.get("access_token")
            
            print(f"新访问令牌: {self.access_token[:50]}...")
            print(f"令牌已更新: {old_access_token != self.access_token}")
            return True
        else:
            print("❌ 令牌刷新失败")
            print(f"错误: {response['data']}")
            return False
    
    async def test_unauthorized_access(self) -> bool:
        """
        测试未授权访问
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试未授权访问 ===")
        
        # 不使用任何认证令牌发送请求
        response = await self.make_request(
            "GET", 
            "/api/v1/users/me", 
            use_auth=False
        )
        
        # 检查是否返回401或403状态码
        if not response["success"] and response["status_code"] in [401, 403]:
            print("✅ 未授权访问被正确拒绝")
            print(f"状态码: {response['status_code']}")
            print(f"错误信息: {response['data'].get('message', 'N/A')}")
            return True
        else:
            print("❌ 未授权访问测试失败")
            print(f"状态码: {response['status_code']}")
            print(f"响应: {response['data']}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """
        运行所有测试
        
        Returns:
            Dict[str, bool]: 测试结果
        """
        print("🚀 开始用户服务API测试")
        print(f"测试目标: {self.base_url}")
        print(f"测试用户: {self.test_user_data['username']}")
        
        test_results = {}
        
        # 按顺序执行测试
        test_results["health_check"] = await self.test_health_check()
        test_results["user_registration"] = await self.test_user_registration()
        test_results["user_login"] = await self.test_user_login()
        test_results["get_current_user"] = await self.test_get_current_user()
        test_results["update_user_profile"] = await self.test_update_user_profile()
        test_results["token_refresh"] = await self.test_token_refresh()
        test_results["unauthorized_access"] = await self.test_unauthorized_access()
        
        # 输出测试总结
        print("\n" + "="*50)
        print("📊 测试结果总结")
        print("="*50)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed_tests += 1
        
        print(f"\n总计: {passed_tests}/{total_tests} 测试通过")
        success_rate = (passed_tests / total_tests) * 100
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 所有测试通过！用户认证系统运行正常。")
        elif success_rate >= 80:
            print("\n⚠️  大部分测试通过，但有少数问题需要关注。")
        else:
            print("\n🚨 多个测试失败，需要检查系统配置和实现。")
        
        return test_results


async def main():
    """
    主函数 - 运行用户API测试
    """
    async with UserAPITester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())