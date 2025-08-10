#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知服务应用程序包

通知服务的主要应用程序包，提供通知发送、模板管理、渠道管理等功能
"""

__version__ = "1.0.0"
__author__ = "CashUp Team"
__description__ = "CashUp量化交易系统通知服务"

# 导出主要组件
from .main import app

__all__ = ["app"]