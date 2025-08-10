#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 模式模块

导入所有Pydantic模式
"""

# Order schemas
from app.schemas.order import (
    OrderBase,
    OrderCreate,
    OrderUpdate,
    OrderCancel,
    OrderResponse,
    OrderListResponse,
    OrderSummary,
    OrderFilter,
    BatchOrderCreate,
    BatchOrderResponse,
)

# Trade schemas
from app.schemas.trade import (
    TradeBase,
    TradeCreate,
    TradeResponse,
    TradeListResponse,
    TradeSummary,
    TradeFilter,
    TradeStatistics,
    DailyTradeReport,
)

# Position schemas
from app.schemas.position import (
    PositionBase,
    PositionCreate,
    PositionUpdate,
    PositionResponse,
    PositionListResponse,
    PositionSummary,
    PositionFilter,
    PositionRisk,
    PositionStatistics,
    PositionCloseRequest,
    PositionCloseResponse,
)

# Balance schemas
from app.schemas.balance import (
    BalanceBase,
    BalanceCreate,
    BalanceUpdate,
    BalanceResponse,
    BalanceListResponse,
    BalanceSummary,
    BalanceFilter,
    BalanceOperation,
    BalanceOperationResponse,
    BalanceTransfer,
    BalanceTransferResponse,
    BalanceHistory,
    BalanceStatistics,
)

# User schemas
from app.schemas.user import (
    UserResponse,
    UserProfile,
)

__all__ = [
    # Order schemas
    "OrderBase",
    "OrderCreate",
    "OrderUpdate",
    "OrderCancel",
    "OrderResponse",
    "OrderListResponse",
    "OrderSummary",
    "OrderFilter",
    "BatchOrderCreate",
    "BatchOrderResponse",
    
    # Trade schemas
    "TradeBase",
    "TradeCreate",
    "TradeResponse",
    "TradeListResponse",
    "TradeSummary",
    "TradeFilter",
    "TradeStatistics",
    "DailyTradeReport",
    
    # Position schemas
    "PositionBase",
    "PositionCreate",
    "PositionUpdate",
    "PositionResponse",
    "PositionListResponse",
    "PositionSummary",
    "PositionFilter",
    "PositionRisk",
    "PositionStatistics",
    "PositionCloseRequest",
    "PositionCloseResponse",
    
    # Balance schemas
    "BalanceBase",
    "BalanceCreate",
    "BalanceUpdate",
    "BalanceResponse",
    "BalanceListResponse",
    "BalanceSummary",
    "BalanceFilter",
    "BalanceOperation",
    "BalanceOperationResponse",
    "BalanceTransfer",
    "BalanceTransferResponse",
    "BalanceHistory",
    "BalanceStatistics",
    
    # User schemas
    "UserResponse",
    "UserProfile",
]