#!/usr/bin/env python3
"""
简单的基础设施测试脚本
"""

import asyncio
import asyncpg
import redis.asyncio as redis
import os

async def test_database():
    """测试数据库连接"""
    try:
        db_url = os.getenv('DATABASE_URL', 'postgresql://cashup:cashup@localhost:5432/cashup')
        conn = await asyncpg.connect(db_url)
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
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()
        print("✅ Redis连接成功")
        return True
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False

async def test_docker_services():
    """测试Docker服务状态"""
    try:
        import subprocess
        result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("🐳 Docker容器状态:")
            print(result.stdout)
            return True
        else:
            print("❌ Docker命令执行失败")
            return False
    except Exception as e:
        print(f"❌ Docker检查失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 开始测试CashUp v2项目基础设施...\n")
    
    # 测试Docker服务
    print("🐳 检查Docker服务:")
    docker_ok = await test_docker_services()
    
    # 测试数据库
    print("\n📊 测试数据库连接:")
    db_ok = await test_database()
    
    # 测试Redis
    print("\n📡 测试Redis连接:")
    redis_ok = await test_redis()
    
    # 总结
    print("\n📋 测试结果:")
    print(f"Docker服务: {'✅ 运行中' if docker_ok else '❌ 异常'}")
    print(f"数据库连接: {'✅ 通过' if db_ok else '❌ 失败'}")
    print(f"Redis连接: {'✅ 通过' if redis_ok else '❌ 失败'}")
    
    if docker_ok and db_ok and redis_ok:
        print("\n🎉 基础设施测试全部通过！")
        print("🚀 系统已就绪，可以开始功能测试")
    else:
        print("\n⚠️  部分测试失败，请检查配置和服务状态")

if __name__ == "__main__":
    asyncio.run(main())