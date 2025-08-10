#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - Gate.io 交易所接口共享库

提供统一的 Gate.io API 客户端实现，供各微服务使用
"""

from .gateio_client import GateIOClient, GateIORestClient, GateIOWebSocketClient

__all__ = [
    "GateIOClient",
    "GateIORestClient", 
    "GateIOWebSocketClient"
]