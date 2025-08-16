#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v1版本初始化文件
"""

from fastapi import APIRouter

from .strategies import router as strategies_router
from .backtests import router as backtests_router
from .risk import router as risk_router

# 创建v1版本的主路由
api_v1_router = APIRouter(prefix="/v1")

# 注册子路由
api_v1_router.include_router(strategies_router)
api_v1_router.include_router(backtests_router)
api_v1_router.include_router(risk_router)

__all__ = ["api_v1_router"]