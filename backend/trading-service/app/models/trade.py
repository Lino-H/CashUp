#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易记录数据模型

定义交易记录相关的数据模型
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from app.core.database import Base
from .order import OrderSide


class TradeType(str, Enum):
    """
    交易类型枚举
    """
    SPOT = "spot"  # 现货交易
    MARGIN = "margin"  # 保证金交易
    FUTURES = "futures"  # 期货交易
    OPTIONS = "options"  # 期权交易


class Trade(Base):
    """
    交易记录模型
    
    存储实际成交的交易记录
    """
    __tablename__ = "trades"
    
    # 基本信息
    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    # 关联订单
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
        comment="订单ID"
    )
    
    # 交易标识
    trade_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="交易ID"
    )
    exchange_trade_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        index=True,
        nullable=True,
        comment="交易所交易ID"
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
    
    # 交易信息
    trade_type: Mapped[TradeType] = mapped_column(
        String(20),
        default=TradeType.SPOT,
        nullable=False,
        comment="交易类型"
    )
    side: Mapped[OrderSide] = mapped_column(
        String(10),
        nullable=False,
        comment="交易方向"
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        comment="交易数量"
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
        comment="交易价格"
    )
    
    # 费用信息
    commission: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="手续费"
    )
    commission_asset: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="手续费资产"
    )
    
    # 时间信息
    trade_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="交易时间"
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
    
    # 市场信息
    is_maker: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为做市商"
    )
    is_best_match: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为最优匹配"
    )
    
    # 盈亏信息
    realized_pnl: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="已实现盈亏"
    )
    
    # 备注信息
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息"
    )
    
    # 关联关系
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="trades"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_user_symbol_time', 'user_id', 'symbol', 'trade_time'),
        Index('idx_user_time', 'user_id', 'trade_time'),
        Index('idx_symbol_time', 'symbol', 'trade_time'),
        Index('idx_strategy_time', 'strategy_id', 'trade_time'),
    )
    
    def __repr__(self) -> str:
        return f"<Trade(id={self.id}, trade_id='{self.trade_id}', symbol='{self.symbol}', side='{self.side}')>"
    
    @property
    def total_value(self) -> Decimal:
        """
        计算交易总价值
        
        Returns:
            Decimal: 交易总价值
        """
        return self.quantity * self.price
    
    @property
    def net_value(self) -> Decimal:
        """
        计算交易净价值（扣除手续费）
        
        Returns:
            Decimal: 交易净价值
        """
        total = self.total_value
        if self.commission_asset == self.quote_asset:
            return total - self.commission
        return total
    
    @property
    def commission_rate(self) -> Decimal:
        """
        计算手续费率
        
        Returns:
            Decimal: 手续费率
        """
        if self.total_value == 0:
            return Decimal('0')
        
        if self.commission_asset == self.quote_asset:
            return self.commission / self.total_value
        elif self.commission_asset == self.base_asset:
            return self.commission / self.quantity
        
        return Decimal('0')