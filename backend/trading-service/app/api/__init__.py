#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - API路由模块

统一管理所有API路由
"""

from .orders import router as orders_router
from .trades import router as trades_router
from .positions import router as positions_router
from .balances import router as balances_router

__all__ = [
    "orders_router",
    "trades_router",
    "positions_router",
    "balances_router"
]