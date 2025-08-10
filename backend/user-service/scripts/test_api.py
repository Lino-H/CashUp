#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - API测试脚本

测试用户服务的主要API功能
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logging import setup_logging, get_logger

# 设置日志
setup_logging()
logger = get_logger("test_api")


class APITester:
    """
    API测试器
    """
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or f"http://{settings.HOST}:{settings.PORT}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.test_results = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """
        获取请求头
        
        Args:
            include_auth: 是否包含认证头
        
        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if include_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        return headers
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        include_auth: bool = True,
        expected_status: int = 200
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            include_auth: 是否包含认证头
            expected_status: 期望的状态码
        
        Returns:
            Dict[str, Any]: 响应数据
        """
        url = f"{self.base_url}{endpoint}"
        headers = self.get_headers(include_auth)
        
        logger.info(f"📤 {method} {endpoint}")
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data
            ) as response:
                response_data = await response.json()
                
                # 记录测试结果
                test_result = {
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": response.status,
                    "expected_status": expected_status,
                    "success": response.status == expected_status,
                    "response": response_data
                }
                self.test_results.append(test_result)
                
                if response.status == expected_status:
                    logger.info(f"✅ {method} {endpoint} - {response.status}")
                else:
                    logger.error(f"❌ {method} {endpoint} - {response.status} (期望: {expected_status})")
                    logger.error(f"   响应: {response_data}")
                
                return response_data
                
        except Exception as e:
            logger.error(f"❌ 请求失败: {method} {endpoint} - {str(e)}")
            self.test_results.append({
                "method": method,
                "endpoint": endpoint,
                "status_code": 0,
                "expected_status": expected_status,
                "success": False,
                "error": str(e)
            })
            raise
    
    async def test_health_check(self):
        """
        测试健康检查
        """
        logger.info("🔍 测试健康检查...")
        await self.make_request("GET", "/health", include_auth=False)
    
    async def test_api_root(self):
        """
        测试API根路径
        """
        logger.info("🔍 测试API根路径...")
        await self.make_request("GET", "/api/v1/", include_auth=False)
    
    async def test_user_registration(self):
        """
        测试用户注册
        """
        logger.info("🔍 测试用户注册...")
        
        # 测试正常注册
        user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "full_name": "测试用户"
        }
        
        response = await self.make_request(
            "POST",
            "/api/v1/users/register",
            data=user_data,
            include_auth=False,
            expected_status=201
        )
        
        return response
    
    async def test_user_login(self, username: str = "admin", password: str = "admin123456"):
        """
        测试用户登录
        
        Args:
            username: 用户名
            password: 密码
        """
        logger.info(f"🔍 测试用户登录 ({username})...")
        
        login_data = {
            "username": username,
            "password": password
        }
        
        response = await self.make_request(
            "POST",
            "/api/v1/users/login",
            data=login_data,
            include_auth=False
        )
        
        # 保存访问令牌
        if "access_token" in response:
            self.access_token = response["access_token"]
            logger.info("✅ 获取访问令牌成功")
        
        return response
    
    async def test_get_current_user(self):
        """
        测试获取当前用户信息
        """
        logger.info("🔍 测试获取当前用户信息...")
        
        response = await self.make_request(
            "GET",
            "/api/v1/users/me"
        )
        
        return response
    
    async def test_update_current_user(self):
        """
        测试更新当前用户信息
        """
        logger.info("🔍 测试更新当前用户信息...")
        
        update_data = {
            "full_name": "更新后的用户名",
            "bio": "这是一个测试用户的简介"
        }
        
        response = await self.make_request(
            "PUT",
            "/api/v1/users/me",
            data=update_data
        )
        
        return response
    
    async def test_password_strength(self):
        """
        测试密码强度检查
        """
        logger.info("🔍 测试密码强度检查...")
        
        # 测试弱密码
        weak_password_data = {"password": "123"}
        await self.make_request(
            "POST",
            "/api/v1/users/check-password-strength",
            data=weak_password_data,
            include_auth=False
        )
        
        # 测试强密码
        strong_password_data = {"password": "StrongPassword123!"}
        await self.make_request(
            "POST",
            "/api/v1/users/check-password-strength",
            data=strong_password_data,
            include_auth=False
        )
    
    async def test_username_availability(self):
        """
        测试用户名可用性检查
        """
        logger.info("🔍 测试用户名可用性检查...")
        
        # 测试已存在的用户名
        await self.make_request(
            "GET",
            "/api/v1/users/check-username/admin",
            include_auth=False
        )
        
        # 测试不存在的用户名
        await self.make_request(
            "GET",
            "/api/v1/users/check-username/nonexistentuser",
            include_auth=False
        )
    
    async def test_email_availability(self):
        """
        测试邮箱可用性检查
        """
        logger.info("🔍 测试邮箱可用性检查...")
        
        # 测试已存在的邮箱
        await self.make_request(
            "GET",
            "/api/v1/users/check-email/admin@cashup.com",
            include_auth=False
        )
        
        # 测试不存在的邮箱
        await self.make_request(
            "GET",
            "/api/v1/users/check-email/nonexistent@example.com",
            include_auth=False
        )
    
    async def test_token_refresh(self):
        """
        测试令牌刷新
        """
        logger.info("🔍 测试令牌刷新...")
        
        # 首先需要登录获取刷新令牌
        login_response = await self.test_user_login()
        
        if "refresh_token" in login_response:
            refresh_data = {
                "refresh_token": login_response["refresh_token"]
            }
            
            response = await self.make_request(
                "POST",
                "/api/v1/users/refresh-token",
                data=refresh_data,
                include_auth=False
            )
            
            # 更新访问令牌
            if "access_token" in response:
                self.access_token = response["access_token"]
            
            return response
    
    async def test_logout(self):
        """
        测试用户登出
        """
        logger.info("🔍 测试用户登出...")
        
        response = await self.make_request(
            "POST",
            "/api/v1/users/logout"
        )
        
        # 清除访问令牌
        self.access_token = None
        
        return response
    
    async def test_unauthorized_access(self):
        """
        测试未授权访问
        """
        logger.info("🔍 测试未授权访问...")
        
        # 清除令牌
        old_token = self.access_token
        self.access_token = None
        
        try:
            await self.make_request(
                "GET",
                "/api/v1/users/me",
                expected_status=401
            )
        finally:
            # 恢复令牌
            self.access_token = old_token
    
    def print_test_summary(self):
        """
        打印测试摘要
        """
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info("")
        logger.info("📊 测试摘要:")
        logger.info(f"   总测试数: {total_tests}")
        logger.info(f"   通过: {passed_tests}")
        logger.info(f"   失败: {failed_tests}")
        logger.info(f"   成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            logger.info("")
            logger.info("❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"   {result['method']} {result['endpoint']} - {result.get('status_code', 'ERROR')}")
        
        logger.info("")


async def check_service_availability(base_url: str) -> bool:
    """
    检查服务是否可用
    
    Args:
        base_url: 服务基础URL
    
    Returns:
        bool: 服务是否可用
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/health", timeout=5) as response:
                return response.status == 200
    except Exception:
        return False


async def main():
    """
    主函数
    """
    logger.info("🚀 开始API测试...")
    
    base_url = f"http://{settings.HOST}:{settings.PORT}"
    logger.info(f"🔗 测试目标: {base_url}")
    
    # 检查服务是否可用
    logger.info("🔍 检查服务可用性...")
    if not await check_service_availability(base_url):
        logger.error("❌ 服务不可用，请确保用户服务正在运行")
        logger.error(f"   启动命令: python scripts/start.py --dev")
        sys.exit(1)
    
    logger.info("✅ 服务可用，开始测试")
    logger.info("")
    
    async with APITester(base_url) as tester:
        try:
            # 基础功能测试
            await tester.test_health_check()
            await tester.test_api_root()
            
            # 用户认证测试
            await tester.test_user_login()
            await tester.test_get_current_user()
            await tester.test_update_current_user()
            
            # 密码和验证测试
            await tester.test_password_strength()
            await tester.test_username_availability()
            await tester.test_email_availability()
            
            # 令牌管理测试
            await tester.test_token_refresh()
            
            # 安全测试
            await tester.test_unauthorized_access()
            
            # 登出测试
            await tester.test_logout()
            
            # 用户注册测试（放在最后，避免影响其他测试）
            try:
                await tester.test_user_registration()
            except Exception as e:
                logger.warning(f"⚠️  用户注册测试失败（可能用户已存在）: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ 测试过程中发生错误: {str(e)}")
        
        # 打印测试摘要
        tester.print_test_summary()
    
    logger.info("🎉 API测试完成！")


if __name__ == "__main__":
    asyncio.run(main())