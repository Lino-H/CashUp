#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - API v1版本

提供配置管理和模板管理的REST API接口
"""

from .router import api_router
from .configs import router as configs_router
from .templates import router as templates_router

__all__ = [
    "api_router",
    "configs_router",
    "templates_router"
]