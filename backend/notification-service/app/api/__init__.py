#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - API路由初始化

导入和导出所有API路由模块
"""

from .v1 import api_router

__all__ = ["api_router"]