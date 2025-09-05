"""
数据库初始化脚本
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from ..config.settings import settings
from ..models.models import Base
from ..utils.logger import get_logger

logger = get_logger(__name__)

async def create_tables():
    """创建数据库表"""
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    logger.info("✅ 数据库表创建成功")

async def init_database():
    """初始化数据库"""
    logger.info("🚀 开始初始化数据库...")
    
    try:
        # 创建表
        await create_tables()
        
        # 创建默认数据
        await create_default_data()
        
        logger.info("✅ 数据库初始化完成")
    
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise

async def create_default_data():
    """创建默认数据"""
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # 创建默认管理员用户
            from .services.auth import AuthService
            auth_service = AuthService(session)
            
            # 检查是否已存在管理员用户
            admin_user = await auth_service.get_user_by_username("admin")
            if not admin_user:
                await auth_service.create_user(
                    username="admin",
                    email="admin@cashup.com",
                    password="admin123",
                    full_name="系统管理员"
                )
                
                # 更新用户为管理员角色
                from sqlalchemy import update
                from ..models.models import User
                await session.execute(
                    update(User)
                    .where(User.username == "admin")
                    .values(role="admin", is_verified=True)
                )
                await session.commit()
                logger.info("✅ 创建默认管理员用户: admin / admin123")
            
            # 创建默认系统配置
            from .services.config import ConfigService
            config_service = ConfigService(session)
            
            default_configs = [
                {
                    "key": "system_name",
                    "value": "CashUp量化交易系统",
                    "description": "系统名称",
                    "category": "system",
                    "is_system": True
                },
                {
                    "key": "system_version",
                    "value": "2.0.0",
                    "description": "系统版本",
                    "category": "system",
                    "is_system": True
                },
                {
                    "key": "max_strategies",
                    "value": 10,
                    "description": "最大策略数量",
                    "category": "trading",
                    "is_system": True
                },
                {
                    "key": "default_timeframe",
                    "value": "1h",
                    "description": "默认时间周期",
                    "category": "trading",
                    "is_system": True
                },
                {
                    "key": "risk_percent",
                    "value": 2.0,
                    "description": "默认风险百分比",
                    "category": "risk",
                    "is_system": True
                }
            ]
            
            for config_data in default_configs:
                existing_config = await config_service.get_config_by_key(config_data["key"])
                if not existing_config:
                    from .schemas.config import ConfigCreate
                    config_create = ConfigCreate(**config_data)
                    await config_service.create_config(config_create)
            
            logger.info("✅ 创建默认系统配置")
        
        except Exception as e:
            logger.error(f"❌ 创建默认数据失败: {e}")
            raise
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_database())