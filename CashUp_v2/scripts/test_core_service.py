"""
核心服务测试脚本
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

async def test_health_check():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"健康检查状态: {response.status_code}")
        if response.status_code == 200:
            print(f"响应数据: {response.json()}")
        print()

async def test_root():
    """测试根路径"""
    print("🔍 测试根路径...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        print(f"根路径状态: {response.status_code}")
        if response.status_code == 200:
            print(f"响应数据: {response.json()}")
        print()

async def test_user_registration():
    """测试用户注册"""
    print("🔍 测试用户注册...")
    
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123",
        "full_name": "测试用户"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/auth/register", json=user_data)
        print(f"用户注册状态: {response.status_code}")
        if response.status_code == 200:
            print(f"用户注册成功: {response.json()}")
        else:
            print(f"用户注册失败: {response.text}")
        print()

async def test_user_login():
    """测试用户登录"""
    print("🔍 测试用户登录...")
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"用户登录状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"登录成功: {data}")
            return data.get("access_token")
        else:
            print(f"登录失败: {response.text}")
        print()
    
    return None

async def test_get_current_user(token):
    """测试获取当前用户"""
    print("🔍 测试获取当前用户...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/users/me", headers=headers)
        print(f"获取用户状态: {response.status_code}")
        if response.status_code == 200:
            print(f"用户信息: {response.json()}")
        else:
            print(f"获取用户失败: {response.text}")
        print()

async def test_config_management(token):
    """测试配置管理"""
    print("🔍 测试配置管理...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 创建配置
    config_data = {
        "key": "test_config",
        "value": "test_value",
        "description": "测试配置",
        "category": "test"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/config/", json=config_data, headers=headers)
        print(f"创建配置状态: {response.status_code}")
        if response.status_code == 200:
            print(f"配置创建成功: {response.json()}")
        else:
            print(f"配置创建失败: {response.text}")
        print()

async def main():
    """主测试函数"""
    print("🚀 开始测试核心服务...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试地址: {BASE_URL}")
    print("-" * 50)
    
    # 基础测试
    await test_health_check()
    await test_root()
    
    # 用户管理测试
    await test_user_registration()
    
    # 登录和授权测试
    token = await test_user_login()
    
    if token:
        # 需要认证的测试
        await test_get_current_user(token)
        await test_config_management(token)
    
    print("-" * 50)
    print("✅ 核心服务测试完成")

if __name__ == "__main__":
    asyncio.run(main())