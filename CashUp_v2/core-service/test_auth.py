#!/usr/bin/env python3
"""
测试认证功能
"""

import asyncio
import sys
import traceback

async def test_auth():
    try:
        print("开始测试认证功能...")
        
        # 测试导入
        from schemas.auth import LoginRequest
        print("✅ LoginRequest导入成功")
        
        from services.auth import AuthService
        print("✅ AuthService导入成功")
        
        from database.connection import get_database
        print("✅ get_database导入成功")
        
        from database.redis import get_redis
        print("✅ get_redis导入成功")
        
        # 测试数据库连接
        db = get_database()
        print("✅ 数据库实例创建成功")
        
        # 测试Redis连接
        redis_client = await get_redis()
        print("✅ Redis连接成功")
        
        # 测试用户查询
        async with db.session() as session:
            auth_service = AuthService(session, redis_client)
            user = await auth_service.get_user_by_username("admin")
            if user:
                print(f"✅ 找到用户: {user.username}")
                print(f"   用户ID: {user.id}")
                print(f"   邮箱: {user.email}")
                print(f"   角色: {user.role}")
            else:
                print("❌ 未找到admin用户")
        
        print("🎉 认证功能测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth())