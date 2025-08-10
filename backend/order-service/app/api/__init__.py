#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务API包

导出API路由
"""

from .v1.router import api_router

__all__ = ["api_router"]