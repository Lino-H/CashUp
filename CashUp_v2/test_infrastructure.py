#!/usr/bin/env python3
"""
简单的测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 测试数据库连接
import asyncio
import asyncpg
from core_service.config.settings import settings

async def test_database():
    """测试数据库连接"""
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        result = await conn.fetchval("SELECT version()")
        await conn.close()
        print(f"✅ 数据库连接成功: {result[:50]}...")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

async def test_redis():
    """测试Redis连接"""
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        print("✅ Redis连接成功")
        return True
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 开始测试CashUp v2项目功能...\n")
    
    # 测试数据库
    print("📊 测试数据库连接:")
    db_ok = await test_database()
    
    # 测试Redis
    print("\n📡 测试Redis连接:")
    redis_ok = await test_redis()
    
    # 总结
    print("\n📋 测试结果:")
    print(f"数据库连接: {'✅ 通过' if db_ok else '❌ 失败'}")
    print(f"Redis连接: {'✅ 通过' if redis_ok else '❌ 失败'}")
    
    if db_ok and redis_ok:
        print("\n🎉 基础设施测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查配置")

if __name__ == "__main__":
    asyncio.run(main())