#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - API v1路由

API v1版本的路由定义
"""

from fastapi import APIRouter

from .metrics import router as metrics_router
from .alerts import router as alerts_router
from .health import router as health_router
from .dashboard import router as dashboard_router
from .system import router as system_router

# 创建API路由器
api_router = APIRouter(prefix="/api/v1")

# 注册子路由
api_router.include_router(
    metrics_router,
    prefix="/metrics",
    tags=["metrics"]
)

api_router.include_router(
    alerts_router,
    prefix="/alerts",
    tags=["alerts"]
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    dashboard_router,
    prefix="/dashboard",
    tags=["dashboard"]
)

api_router.include_router(
    system_router,
    prefix="/system",
    tags=["system"]
)

__all__ = ['api_router']