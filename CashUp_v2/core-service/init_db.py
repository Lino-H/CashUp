#!/usr/bin/env python3
"""
数据库初始化脚本
创建表结构和默认管理员用户
"""

import asyncio
import sys
import os
from passlib.context import CryptContext

# 添加项目路径
sys.path.append('/app')

from database.connection import get_database, Base
from models.models import User, UserRole, UserStatus
from sqlalchemy.ext.asyncio import AsyncSession

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def init_database():
    """初始化数据库"""
    print("开始初始化数据库...")
    
    try:
        # 创建数据库连接
        db = get_database()
        await db.connect()
        print("✅ 数据库表创建成功")
        
        # 创建默认管理员用户
        async with db.session() as session:
            # 检查是否已存在管理员用户
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.username == "admin")
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                # 创建管理员用户
                admin_user = User(
                    username="admin",
                    email="admin@cashup.com",
                    password_hash=pwd_context.hash("admin123"),
                    full_name="系统管理员",
                    role=UserRole.ADMIN,
                    status=UserStatus.ACTIVE,
                    is_verified=True
                )
                
                session.add(admin_user)
                await session.commit()
                print("✅ 默认管理员用户创建成功")
                print("   用户名: admin")
                print("   密码: admin123")
            else:
                print("✅ 管理员用户已存在")
        
        print("🎉 数据库初始化完成")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database())