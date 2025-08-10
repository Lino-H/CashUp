#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - API路由主文件

配置服务的API路由汇总
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_database_session, check_database_health
from ...core.cache import check_redis_health
from .configs import router as configs_router
from .templates import router as templates_router

# 创建API路由器
api_router = APIRouter(prefix="/api/v1")

# 包含子路由
api_router.include_router(configs_router)
api_router.include_router(templates_router)


@api_router.get("/")
async def root():
    """
    API根路径
    """
    return {
        "service": "CashUp Config Service",
        "version": "1.0.0",
        "description": "CashUp量化交易系统配置管理服务",
        "endpoints": {
            "configs": "/api/v1/configs",
            "templates": "/api/v1/templates",
            "health": "/api/v1/health"
        }
    }


@api_router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_database_session)
):
    """
    健康检查接口
    """
    health_status = {
        "status": "healthy",
        "timestamp": None,
        "services": {
            "database": "unknown",
            "redis": "unknown"
        }
    }
    
    try:
        from datetime import datetime
        health_status["timestamp"] = datetime.utcnow().isoformat()
        
        # 检查数据库连接
        try:
            db_health = await check_database_health(db)
            health_status["services"]["database"] = "healthy" if db_health else "unhealthy"
        except Exception as e:
            health_status["services"]["database"] = f"error: {str(e)}"
        
        # 检查Redis连接
        try:
            redis_health = await check_redis_health()
            health_status["services"]["redis"] = "healthy" if redis_health else "unhealthy"
        except Exception as e:
            health_status["services"]["redis"] = f"error: {str(e)}"
        
        # 判断整体状态
        if any(status != "healthy" for status in health_status["services"].values()):
            health_status["status"] = "degraded"
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
    
    return health_status


@api_router.get("/info")
async def service_info():
    """
    服务信息接口
    """
    return {
        "service_name": "config-service",
        "version": "1.0.0",
        "description": "CashUp量化交易系统配置管理服务",
        "features": [
            "配置CRUD操作",
            "配置版本管理",
            "配置模板管理",
            "配置验证",
            "配置缓存",
            "配置同步",
            "配置审计",
            "批量操作",
            "权限控制",
            "热更新"
        ],
        "supported_config_types": [
            "SYSTEM",
            "USER",
            "TRADING",
            "STRATEGY",
            "NOTIFICATION",
            "MONITORING"
        ],
        "supported_config_scopes": [
            "GLOBAL",
            "USER",
            "STRATEGY"
        ],
        "supported_config_formats": [
            "JSON",
            "YAML",
            "TOML",
            "INI",
            "ENV"
        ]
    }