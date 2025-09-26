#!/usr/bin/env python3
"""
简单登录测试 - 绕过所有复杂性
"""

import asyncio
import sys
sys.path.append('/app')

from database.connection import get_database
from services.auth import AuthService
from database.redis import get_redis

async def simple_login_test():
    """简单登录测试"""
    try:
        print("开始简单登录测试...")
        
        # 获取数据库和Redis连接
        db = get_database()
        redis_client = await get_redis()
        
        # 测试用户认证
        async with db.session() as session:
            auth_service = AuthService(session, redis_client)
            
            # 直接测试认证
            user = await auth_service.authenticate_user("admin", "admin123")
            
            if user:
                print(f"✅ 登录成功!")
                print(f"   用户ID: {user.id}")
                print(f"   用户名: {user.username}")
                print(f"   邮箱: {user.email}")
                print(f"   角色: {user.role}")
                
                # 创建会话
                session_id = await auth_service.create_session(user.id)
                print(f"   会话ID: {session_id}")
                
                return {
                    "success": True,
                    "user_id": user.id,
                    "username": user.username,
                    "session_id": session_id
                }
            else:
                print("❌ 登录失败: 用户名或密码错误")
                return {"success": False, "error": "用户名或密码错误"}
                
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(simple_login_test())
    print(f"测试结果: {result}")