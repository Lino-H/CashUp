#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单模型

定义订单相关的数据库模型
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Integer, Numeric, DateTime, Boolean, Text, Enum,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from ..core.database import Base


class OrderStatus(str, enum.Enum):
    """
    订单状态枚举
    """
    PENDING = "pending"          # 待处理
    SUBMITTED = "submitted"      # 已提交
    PARTIAL_FILLED = "partial_filled"  # 部分成交
    FILLED = "filled"            # 完全成交
    CANCELLED = "cancelled"      # 已取消
    REJECTED = "rejected"        # 已拒绝
    EXPIRED = "expired"          # 已过期
    FAILED = "failed"            # 失败


class OrderType(str, enum.Enum):
    """
    订单类型枚举
    """
    MARKET = "market"            # 市价单
    LIMIT = "limit"              # 限价单
    STOP = "stop"                # 止损单
    STOP_LIMIT = "stop_limit"    # 止损限价单
    TAKE_PROFIT = "take_profit"  # 止盈单
    TAKE_PROFIT_LIMIT = "take_profit_limit"  # 止盈限价单


class OrderSide(str, enum.Enum):
    """
    订单方向枚举
    """
    BUY = "buy"                  # 买入
    SELL = "sell"                # 卖出


class TimeInForce(str, enum.Enum):
    """
    订单有效期类型枚举
    """
    GTC = "gtc"                  # Good Till Cancelled
    IOC = "ioc"                  # Immediate Or Cancel
    FOK = "fok"                  # Fill Or Kill
    GTD = "gtd"                  # Good Till Date


class Order(Base):
    """
    订单模型
    
    存储订单的完整信息和状态
    """
    __tablename__ = "orders"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="订单ID"
    )
    
    # 用户信息
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="用户ID"
    )
    
    # 交易所信息
    exchange_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="交易所名称"
    )
    
    exchange_order_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="交易所订单ID"
    )
    
    client_order_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="客户端订单ID"
    )
    
    # 交易对信息
    symbol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="交易对"
    )
    
    base_asset: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="基础资产"
    )
    
    quote_asset: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="计价资产"
    )
    
    # 订单基本信息
    side: Mapped[OrderSide] = mapped_column(
        Enum(OrderSide),
        nullable=False,
        comment="订单方向"
    )
    
    type: Mapped[OrderType] = mapped_column(
        Enum(OrderType),
        nullable=False,
        comment="订单类型"
    )
    
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
        comment="订单状态"
    )
    
    time_in_force: Mapped[TimeInForce] = mapped_column(
        Enum(TimeInForce),
        nullable=False,
        default=TimeInForce.GTC,
        comment="订单有效期类型"
    )
    
    # 价格和数量
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
    
    # 成交信息
    filled_quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=Decimal('0'),
        comment="已成交数量"
    )
    
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        default=Decimal('0'),
        comment="剩余数量"
    )
    
    avg_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="平均成交价格"
    )
    
    total_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="总成交金额"
    )
    
    # 手续费信息
    fee: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="手续费"
    )
    
    fee_asset: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="手续费资产"
    )
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="提交时间"
    )
    
    filled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="完成时间"
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="过期时间"
    )
    
    # 策略信息
    strategy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="策略ID"
    )
    
    strategy_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="策略名称"
    )
    
    # 备注信息
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    
    # 元数据
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="元数据JSON"
    )
    
    # 关联关系
    executions = relationship("OrderExecution", back_populates="order", cascade="all, delete-orphan")
    
    # 表约束
    __table_args__ = (
        # 检查约束
        CheckConstraint('quantity > 0', name='ck_order_quantity_positive'),
        CheckConstraint('price IS NULL OR price > 0', name='ck_order_price_positive'),
        CheckConstraint('stop_price IS NULL OR stop_price > 0', name='ck_order_stop_price_positive'),
        CheckConstraint('filled_quantity >= 0', name='ck_order_filled_quantity_non_negative'),
        CheckConstraint('remaining_quantity >= 0', name='ck_order_remaining_quantity_non_negative'),
        CheckConstraint('filled_quantity <= quantity', name='ck_order_filled_le_quantity'),
        
        # 索引
        Index('idx_order_user_id', 'user_id'),
        Index('idx_order_exchange_name', 'exchange_name'),
        Index('idx_order_symbol', 'symbol'),
        Index('idx_order_status', 'status'),
        Index('idx_order_created_at', 'created_at'),
        Index('idx_order_user_status', 'user_id', 'status'),
        Index('idx_order_exchange_order_id', 'exchange_name', 'exchange_order_id'),
        Index('idx_order_client_order_id', 'client_order_id'),
        Index('idx_order_strategy_id', 'strategy_id'),
    )
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, symbol={self.symbol}, side={self.side}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """
        检查订单是否处于活跃状态
        
        Returns:
            bool: 订单是否活跃
        """
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILLED]
    
    @property
    def is_completed(self) -> bool:
        """
        检查订单是否已完成
        
        Returns:
            bool: 订单是否完成
        """
        return self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED, OrderStatus.FAILED]
    
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


class OrderExecution(Base):
    """
    订单执行记录模型
    
    记录订单的每次执行（成交）详情
    """
    __tablename__ = "order_executions"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="执行记录ID"
    )
    
    # 关联订单
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        comment="订单ID"
    )
    
    # 交易所执行信息
    exchange_execution_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="交易所执行ID"
    )
    
    # 执行详情
    price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        comment="执行价格"
    )
    
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        comment="执行数量"
    )
    
    value: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        comment="执行金额"
    )
    
    # 手续费信息
    fee: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="手续费"
    )
    
    fee_asset: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="手续费资产"
    )
    
    # 时间信息
    executed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="执行时间"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    # 关联关系
    order = relationship("Order", back_populates="executions")
    
    # 表约束
    __table_args__ = (
        # 检查约束
        CheckConstraint('price > 0', name='ck_execution_price_positive'),
        CheckConstraint('quantity > 0', name='ck_execution_quantity_positive'),
        CheckConstraint('value > 0', name='ck_execution_value_positive'),
        
        # 索引
        Index('idx_execution_order_id', 'order_id'),
        Index('idx_execution_executed_at', 'executed_at'),
        Index('idx_execution_exchange_id', 'exchange_execution_id'),
    )
    
    def __repr__(self) -> str:
        return f"<OrderExecution(id={self.id}, order_id={self.order_id}, price={self.price}, quantity={self.quantity})>"