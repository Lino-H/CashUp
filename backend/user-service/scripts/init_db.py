#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 数据库初始化脚本

初始化数据库表结构和基础数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_db, get_db
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.models.user import User, Role, Permission, UserRole, UserStatus
from app.core.security import hash_password
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 设置日志
setup_logging()
logger = get_logger("init_db")


async def create_default_roles_and_permissions():
    """
    创建默认角色和权限
    """
    logger.info("开始创建默认角色和权限...")
    
    async for db in get_db():
        try:
            # 检查是否已存在角色
            result = await db.execute(select(Role))
            existing_roles = result.scalars().all()
            
            if existing_roles:
                logger.info("角色已存在，跳过创建")
                return
            
            # 创建权限
            permissions_data = [
                {"name": "user:read", "display_name": "查看用户", "description": "查看用户信息", "resource": "user", "action": "read"},
                {"name": "user:write", "display_name": "修改用户", "description": "修改用户信息", "resource": "user", "action": "write"},
                {"name": "user:delete", "display_name": "删除用户", "description": "删除用户", "resource": "user", "action": "delete"},
                {"name": "user:admin", "display_name": "用户管理", "description": "用户管理", "resource": "user", "action": "admin"},
                {"name": "trading:read", "display_name": "查看交易", "description": "查看交易信息", "resource": "trading", "action": "read"},
                {"name": "trading:write", "display_name": "执行交易", "description": "执行交易操作", "resource": "trading", "action": "write"},
                {"name": "trading:admin", "display_name": "交易管理", "description": "交易管理", "resource": "trading", "action": "admin"},
                {"name": "strategy:read", "display_name": "查看策略", "description": "查看策略信息", "resource": "strategy", "action": "read"},
                {"name": "strategy:write", "display_name": "修改策略", "description": "创建和修改策略", "resource": "strategy", "action": "write"},
                {"name": "strategy:admin", "display_name": "策略管理", "description": "策略管理", "resource": "strategy", "action": "admin"},
                {"name": "portfolio:read", "display_name": "查看组合", "description": "查看投资组合", "resource": "portfolio", "action": "read"},
                {"name": "portfolio:write", "display_name": "修改组合", "description": "修改投资组合", "resource": "portfolio", "action": "write"},
                {"name": "portfolio:admin", "display_name": "组合管理", "description": "投资组合管理", "resource": "portfolio", "action": "admin"},
                {"name": "risk:read", "display_name": "查看风险", "description": "查看风险信息", "resource": "risk", "action": "read"},
                {"name": "risk:write", "display_name": "修改风险", "description": "修改风险设置", "resource": "risk", "action": "write"},
                {"name": "risk:admin", "display_name": "风险管理", "description": "风险管理", "resource": "risk", "action": "admin"},
                {"name": "market:read", "display_name": "查看市场", "description": "查看市场数据", "resource": "market", "action": "read"},
                {"name": "market:admin", "display_name": "市场管理", "description": "市场数据管理", "resource": "market", "action": "admin"},
                {"name": "notification:read", "display_name": "查看通知", "description": "查看通知", "resource": "notification", "action": "read"},
                {"name": "notification:write", "display_name": "发送通知", "description": "发送通知", "resource": "notification", "action": "write"},
                {"name": "notification:admin", "display_name": "通知管理", "description": "通知管理", "resource": "notification", "action": "admin"},
                {"name": "system:admin", "display_name": "系统管理", "description": "系统管理", "resource": "system", "action": "admin"}
            ]
            
            permissions = []
            for perm_data in permissions_data:
                permission = Permission(**perm_data)
                db.add(permission)
                permissions.append(permission)
            
            await db.flush()  # 获取权限ID
            
            # 创建角色
            roles_data = [
                {
                    "name": UserRole.ADMIN.value,
                    "display_name": "系统管理员",
                    "description": "系统管理员，拥有所有权限",
                    "permissions": permissions  # 管理员拥有所有权限
                },
                {
                    "name": UserRole.TRADER.value,
                    "display_name": "交易员",
                    "description": "交易员，可以执行交易操作",
                    "permissions": [
                        p for p in permissions 
                        if any(prefix in p.name for prefix in [
                            "user:read", "trading:", "strategy:", "portfolio:", 
                            "risk:read", "market:read", "notification:read"
                        ])
                    ]
                },
                {
                    "name": UserRole.DEVELOPER.value,
                    "display_name": "策略开发者",
                    "description": "策略开发者，可以开发和测试策略",
                    "permissions": [
                        p for p in permissions 
                        if any(prefix in p.name for prefix in [
                            "user:read", "strategy:", "portfolio:read", 
                            "risk:read", "market:read", "notification:read"
                        ])
                    ]
                }
            ]
            
            for role_data in roles_data:
                role = Role(
                    name=role_data["name"],
                    display_name=role_data["display_name"],
                    description=role_data["description"]
                )
                role.permissions = role_data["permissions"]
                db.add(role)
            
            await db.commit()
            logger.info(f"✅ 成功创建 {len(permissions_data)} 个权限和 {len(roles_data)} 个角色")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 创建角色和权限失败: {str(e)}")
            raise
        finally:
            break


async def create_admin_user():
    """
    创建默认管理员用户
    """
    logger.info("开始创建默认管理员用户...")
    
    async for db in get_db():
        try:
            # 检查是否已存在管理员用户
            result = await db.execute(
                select(User).where(User.username == "admin")
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                logger.info("管理员用户已存在，跳过创建")
                return
            
            # 获取管理员角色
            result = await db.execute(
                select(Role).where(Role.name == UserRole.ADMIN.value)
            )
            admin_role = result.scalar_one_or_none()
            
            if not admin_role:
                logger.error("未找到管理员角色，请先创建角色")
                return
            
            # 创建管理员用户
            admin_user = User(
                username="admin",
                email="admin@cashup.com",
                hashed_password=hash_password("admin123456"),
                full_name="系统管理员",
                status=UserStatus.ACTIVE,
                is_email_verified=True,
                is_superuser=True
            )
            admin_user.roles = [admin_role]
            
            db.add(admin_user)
            await db.commit()
            
            logger.info("✅ 成功创建默认管理员用户")
            logger.info("   用户名: admin")
            logger.info("   密码: admin123456")
            logger.info("   邮箱: admin@cashup.com")
            logger.warning("⚠️  请在生产环境中立即修改默认密码！")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 创建管理员用户失败: {str(e)}")
            raise
        finally:
            break


async def create_demo_users():
    """
    创建演示用户
    """
    if not settings.DEBUG:
        logger.info("生产环境，跳过创建演示用户")
        return
    
    logger.info("开始创建演示用户...")
    
    async for db in get_db():
        try:
            # 获取角色
            result = await db.execute(select(Role))
            roles = {role.name: role for role in result.scalars().all()}
            
            demo_users = [
                {
                    "username": "trader1",
                    "email": "trader1@cashup.com",
                    "password": "trader123456",
                    "full_name": "交易员一号",
                    "role": UserRole.TRADER,
                    "role_obj": roles.get(UserRole.TRADER.value)
                },
                {
                    "username": "developer1",
                    "email": "developer1@cashup.com",
                    "password": "developer123456",
                    "full_name": "策略开发者一号",
                    "role": UserRole.DEVELOPER,
                    "role_obj": roles.get(UserRole.DEVELOPER.value)
                }
            ]
            
            created_count = 0
            for user_data in demo_users:
                # 检查用户是否已存在
                result = await db.execute(
                    select(User).where(User.username == user_data["username"])
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    continue
                
                # 创建用户
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=hash_password(user_data["password"]),
                    full_name=user_data["full_name"],
                    status=UserStatus.ACTIVE,
                    is_email_verified=True
                )
                
                if user_data["role_obj"]:
                    user.roles = [user_data["role_obj"]]
                
                db.add(user)
                created_count += 1
            
            if created_count > 0:
                await db.commit()
                logger.info(f"✅ 成功创建 {created_count} 个演示用户")
            else:
                logger.info("演示用户已存在，跳过创建")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 创建演示用户失败: {str(e)}")
            raise
        finally:
            break


async def main():
    """
    主函数
    """
    logger.info("🚀 开始初始化CashUp用户服务数据库...")
    logger.info(f"📊 调试模式: {settings.DEBUG}")
    logger.info(f"🔗 数据库: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'SQLite'}")
    
    try:
        # 初始化数据库
        await init_db()
        logger.info("✅ 数据库表结构初始化完成")
        
        # 创建角色和权限
        await create_default_roles_and_permissions()
        
        # 创建管理员用户
        await create_admin_user()
        
        # 创建演示用户（非生产环境）
        await create_demo_users()
        
        logger.info("🎉 数据库初始化完成！")
        logger.info("")
        logger.info("默认登录信息:")
        logger.info("  管理员 - 用户名: admin, 密码: admin123456")
        if settings.DEBUG:
            logger.info("  交易员 - 用户名: trader1, 密码: trader123456")
            logger.info("  策略开发者 - 用户名: developer1, 密码: developer123456")
        logger.info("")
        logger.warning("⚠️  请在生产环境中立即修改默认密码！")
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())