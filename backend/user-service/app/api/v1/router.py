#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - API路由主文件

整合所有API路由模块
"""

from fastapi import APIRouter

from .users import router as users_router


# 创建API路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(users_router)


# 根路径
@api_router.get("/")
async def api_root():
    """
    API根路径
    
    Returns:
        dict: API基本信息
    """
    return {
        "message": "CashUp User Service API",
        "version": "v1",
        "endpoints": {
            "users": "/users",
            "docs": "/docs",
            "health": "/health"
        }
    }


@api_router.get("/health")
async def health_check():
    """
    健康检查接口
    
    Returns:
        dict: 服务健康状态
    """
    return {
        "status": "healthy",
        "service": "user-service",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }