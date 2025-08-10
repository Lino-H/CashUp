#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alembic环境配置文件

用于数据库迁移的环境设置
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入应用模块
from app.core.config import get_settings
from app.core.database import Base
from app.models import *  # 导入所有模型

# Alembic配置对象
config = context.config

# 设置日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 获取应用设置
settings = get_settings()

# 设置数据库URL
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.get_database_url())

# 目标元数据
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    在'离线'模式下运行迁移
    
    这将配置上下文，只使用URL而不是Engine，
    尽管这里也需要一个Engine，但我们不创建连接；
    我们只是将URL传递给context.configure()。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    执行迁移
    
    Args:
        connection: 数据库连接
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        # 自定义比较函数
        compare_server_default=True,
        # 渲染项目配置
        render_as_batch=True
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    在'在线'模式下运行异步迁移
    
    在这种情况下，我们需要创建一个Engine并将连接与上下文关联。
    """
    # 获取配置
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.get_database_url()
    
    # 创建异步引擎
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    在'在线'模式下运行迁移
    """
    asyncio.run(run_async_migrations())


# 根据上下文决定运行模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()