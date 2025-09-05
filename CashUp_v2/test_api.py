#!/usr/bin/env python3
"""
API功能测试脚本
"""

import asyncio
import aiohttp
import json
import os

BASE_URL = "http://localhost:8001"

async def test_health_check():
    """测试健康检查接口"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 健康检查通过: {data}")
                    return True
                else:
                    print(f"❌ 健康检查失败: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

async def test_root_endpoint():
    """测试根接口"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 根接口正常: {data['service']}")
                    return True
                else:
                    print(f"❌ 根接口失败: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ 根接口异常: {e}")
        return False

async def test_user_registration():
    """测试用户注册"""
    try:
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "test123",
            "full_name": "测试用户"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    print(f"✅ 用户注册成功: {data['username']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 用户注册失败: {response.status} - {error_text}")
                    return False
    except Exception as e:
        print(f"❌ 用户注册异常: {e}")
        return False

async def test_user_login():
    """测试用户登录"""
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 用户登录成功: {data['user']['username']}")
                    return data.get('session_id')
                else:
                    error_text = await response.text()
                    print(f"❌ 用户登录失败: {response.status} - {error_text}")
                    return None
    except Exception as e:
        print(f"❌ 用户登录异常: {e}")
        return None

async def test_protected_endpoint(session_id=None):
    """测试受保护的接口"""
    try:
        headers = {}
        if session_id:
            headers["Authorization"] = f"Bearer {session_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/api/auth/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 受保护接口访问成功: {data['username']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 受保护接口访问失败: {response.status} - {error_text}")
                    return False
    except Exception as e:
        print(f"❌ 受保护接口访问异常: {e}")
        return False

async def test_api_docs():
    """测试API文档"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/docs") as response:
                if response.status == 200:
                    print("✅ API文档可访问")
                    return True
                else:
                    print(f"❌ API文档访问失败: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ API文档访问异常: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 开始测试CashUp v2 API功能...\n")
    
    # 基础接口测试
    print("🔍 基础接口测试:")
    health_ok = await test_health_check()
    root_ok = await test_root_endpoint()
    docs_ok = await test_api_docs()
    
    # 认证功能测试
    print("\n🔐 认证功能测试:")
    session_id = await test_user_login()
    auth_ok = session_id is not None
    
    if session_id:
        protected_ok = await test_protected_endpoint(session_id)
    else:
        protected_ok = await test_protected_endpoint()
    
    # 用户注册测试
    print("\n👥 用户管理测试:")
    register_ok = await test_user_registration()
    
    # 总结
    print("\n📋 API测试结果:")
    print(f"健康检查: {'✅ 通过' if health_ok else '❌ 失败'}")
    print(f"根接口: {'✅ 通过' if root_ok else '❌ 失败'}")
    print(f"API文档: {'✅ 通过' if docs_ok else '❌ 失败'}")
    print(f"用户登录: {'✅ 通过' if auth_ok else '❌ 失败'}")
    print(f"受保护接口: {'✅ 通过' if protected_ok else '❌ 失败'}")
    print(f"用户注册: {'✅ 通过' if register_ok else '❌ 失败'}")
    
    passed_tests = sum([health_ok, root_ok, docs_ok, auth_ok, protected_ok, register_ok])
    total_tests = 6
    
    print(f"\n📊 测试通过率: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 所有API测试通过！")
    elif passed_tests >= total_tests * 0.8:
        print("\n✅ 大部分API测试通过，系统基本可用")
    else:
        print("\n⚠️  多个API测试失败，需要检查服务配置")

if __name__ == "__main__":
    asyncio.run(main())