#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - API模块

提供REST API接口
"""

from .v1.router import api_router

__all__ = [
    "api_router"
]