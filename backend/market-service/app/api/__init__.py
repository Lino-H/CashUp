#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 市场数据服务API模块

统一管理所有API路由
"""

from .market_data import router as market_data_router
from .indicators import router as indicators_router

__all__ = [
    "market_data_router",
    "indicators_router"
]