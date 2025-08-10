#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - API v1路由初始化

导入和导出v1版本的所有API路由
"""

from fastapi import APIRouter

from .notifications import router as notifications_router
from .templates import router as templates_router
from .channels import router as channels_router
from .websocket import router as websocket_router
from .health import router as health_router

# 创建v1 API路由器
api_router = APIRouter(prefix="/api/v1")

# 注册子路由
api_router.include_router(
    notifications_router,
    prefix="/notifications",
    tags=["notifications"]
)

api_router.include_router(
    templates_router,
    prefix="/templates",
    tags=["templates"]
)

api_router.include_router(
    channels_router,
    prefix="/channels",
    tags=["channels"]
)

api_router.include_router(
    websocket_router,
    prefix="/ws",
    tags=["websocket"]
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["health"]
)

__all__ = ["api_router"]