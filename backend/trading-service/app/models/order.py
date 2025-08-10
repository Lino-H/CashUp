#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单数据模型

定义订单相关的数据模型
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from app.core.database import Base


class OrderType(str, Enum):
    """
    订单类型枚举
    """
    MARKET = "market"  # 市价单
    LIMIT = "limit"  # 限价单
    STOP = "stop"  # 止损单
    STOP_LIMIT = "stop_limit"  # 止损限价单
    TAKE_PROFIT = "take_profit"  # 止盈单
    TAKE_PROFIT_LIMIT = "take_profit_limit"  # 止盈限价单


class OrderSide(str, Enum):
    """
    订单方向枚举
    """
    BUY = "buy"  # 买入
    SELL = "sell"  # 卖出


class OrderStatus(str, Enum):
    """
    订单状态枚举
    """
    PENDING = "pending"  # 待处理
    SUBMITTED = "submitted"  # 已提交
    PARTIAL_FILLED = "partial_filled"  # 部分成交
    FILLED = "filled"  # 完全成交
    CANCELLED = "cancelled"  # 已取消
    REJECTED = "rejected"  # 已拒绝
    EXPIRED = "expired"  # 已过期


class TimeInForce(str, Enum):
    """
    订单有效期类型枚举
    """
    GTC = "gtc"  # Good Till Cancelled - 撤销前有效
    IOC = "ioc"  # Immediate Or Cancel - 立即成交或取消
    FOK = "fok"  # Fill Or Kill - 全部成交或取消
    GTD = "gtd"  # Good Till Date - 指定日期前有效


class Order(Base):
    """
    订单模型
    
    存储交易订单的详细信息
    """
    __tablename__ = "orders"
    
    # 基本信息
    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    # 订单标识
    client_order_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="客户端订单ID"
    )
    exchange_order_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        index=True,
        nullable=True,
        comment="交易所订单ID"
    )
    
    # 交易对信息
    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="交易对符号"
    )
    base_asset: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="基础资产"
    )
    quote_asset: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="计价资产"
    )
    
    # 订单参数
    order_type: Mapped[OrderType] = mapped_column(
        String(20),
        nullable=False,
        comment="订单类型"
    )
    side: Mapped[OrderSide] = mapped_column(
        String(10),
        nullable=False,
        comment="订单方向"
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        comment="订单数量"
    )
    price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="订单价格"
    )
    stop_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="止损价格"
    )
    
    # 执行信息
    status: Mapped[OrderStatus] = mapped_column(
        String(20),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True,
        comment="订单状态"
    )
    filled_quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="已成交数量"
    )
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        comment="剩余数量"
    )
    average_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="平均成交价格"
    )
    
    # 费用信息
    commission: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="手续费"
    )
    commission_asset: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="手续费资产"
    )
    
    # 时间信息
    time_in_force: Mapped[TimeInForce] = mapped_column(
        String(10),
        default=TimeInForce.GTC,
        nullable=False,
        comment="订单有效期类型"
    )
    expire_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="过期时间"
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="提交时间"
    )
    filled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间"
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="取消时间"
    )
    
    # 策略信息
    strategy_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="策略ID"
    )
    strategy_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="策略名称"
    )
    
    # 风险控制
    risk_checked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已进行风险检查"
    )
    risk_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="风险评分"
    )
    
    # 备注信息
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    
    # 关联关系
    trades: Mapped[list["Trade"]] = relationship(
        "Trade",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_user_symbol_status', 'user_id', 'symbol', 'status'),
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_symbol_created', 'symbol', 'created_at'),
        Index('idx_strategy_created', 'strategy_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, client_order_id='{self.client_order_id}', symbol='{self.symbol}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """
        检查订单是否处于活跃状态
        
        Returns:
            bool: 是否活跃
        """
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILLED]
    
    @property
    def is_completed(self) -> bool:
        """
        检查订单是否已完成
        
        Returns:
            bool: 是否已完成
        """
        return self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED]
    
    @property
    def fill_percentage(self) -> float:
        """
        计算订单成交百分比
        
        Returns:
            float: 成交百分比
        """
        if self.quantity == 0:
            return 0.0
        return float(self.filled_quantity / self.quantity * 100)
    
    @property
    def total_value(self) -> Optional[Decimal]:
        """
        计算订单总价值
        
        Returns:
            Optional[Decimal]: 订单总价值
        """
        if self.average_price is not None:
            return self.filled_quantity * self.average_price
        elif self.price is not None:
            return self.quantity * self.price
        return None