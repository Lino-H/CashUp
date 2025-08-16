#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 持仓数据模型

定义持仓相关的数据模型
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime, Boolean, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum

from app.core.database import Base


class PositionSide(str, Enum):
    """
    持仓方向枚举
    """
    LONG = "long"  # 多头
    SHORT = "short"  # 空头
    FLAT = "flat"  # 平仓


class PositionType(str, Enum):
    """
    持仓类型枚举
    """
    SPOT = "spot"  # 现货持仓
    MARGIN = "margin"  # 保证金持仓
    FUTURES = "futures"  # 期货持仓
    OPTIONS = "options"  # 期权持仓


class Position(Base):
    """
    持仓模型
    
    存储用户的持仓信息
    """
    __tablename__ = "positions"
    
    # 基本信息
    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="用户ID"
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
    
    # 持仓信息
    position_type: Mapped[PositionType] = mapped_column(
        String(20),
        default=PositionType.SPOT,
        nullable=False,
        comment="持仓类型"
    )
    side: Mapped[PositionSide] = mapped_column(
        String(10),
        default=PositionSide.FLAT,
        nullable=False,
        comment="持仓方向"
    )
    
    # 数量信息
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="持仓数量"
    )
    available_quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="可用数量"
    )
    frozen_quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="冻结数量"
    )
    
    # 成本信息
    average_price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="平均成本价格"
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="总成本"
    )
    
    # 市场信息
    market_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="当前市场价格"
    )
    market_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="当前市场价值"
    )
    
    # 盈亏信息
    unrealized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="未实现盈亏"
    )
    unrealized_pnl_percentage: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        default=Decimal('0'),
        nullable=False,
        comment="未实现盈亏百分比"
    )
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="已实现盈亏"
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
    
    # 风险信息
    risk_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="风险等级"
    )
    margin_ratio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="保证金比例"
    )
    liquidation_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="强平价格"
    )
    
    # 时间信息
    first_trade_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="首次交易时间"
    )
    last_trade_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后交易时间"
    )
    last_update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="最后更新时间"
    )
    
    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否活跃"
    )
    is_hedged: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已对冲"
    )
    
    # 备注信息
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_position_user_symbol', 'user_id', 'symbol', unique=True),
        Index('idx_position_user_active', 'user_id', 'is_active'),
        Index('idx_position_strategy_active', 'strategy_id', 'is_active'),
        Index('idx_position_symbol_active', 'symbol', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<Position(id={self.id}, user_id={self.user_id}, symbol='{self.symbol}', quantity={self.quantity})>"
    
    @property
    def is_long(self) -> bool:
        """
        检查是否为多头持仓
        
        Returns:
            bool: 是否为多头
        """
        return self.side == PositionSide.LONG and self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """
        检查是否为空头持仓
        
        Returns:
            bool: 是否为空头
        """
        return self.side == PositionSide.SHORT and self.quantity > 0
    
    @property
    def is_flat(self) -> bool:
        """
        检查是否为平仓状态
        
        Returns:
            bool: 是否为平仓
        """
        return self.quantity == 0 or self.side == PositionSide.FLAT
    
    @property
    def position_value(self) -> Decimal:
        """
        计算持仓价值
        
        Returns:
            Decimal: 持仓价值
        """
        if self.market_price is not None:
            return self.quantity * self.market_price
        return self.quantity * self.average_price
    
    @property
    def available_value(self) -> Decimal:
        """
        计算可用价值
        
        Returns:
            Decimal: 可用价值
        """
        if self.market_price is not None:
            return self.available_quantity * self.market_price
        return self.available_quantity * self.average_price
    
    def update_market_data(self, market_price: Decimal) -> None:
        """
        更新市场数据
        
        Args:
            market_price: 当前市场价格
        """
        self.market_price = market_price
        self.market_value = self.quantity * market_price
        
        # 计算未实现盈亏
        if self.quantity > 0:
            if self.side == PositionSide.LONG:
                self.unrealized_pnl = (market_price - self.average_price) * self.quantity
            elif self.side == PositionSide.SHORT:
                self.unrealized_pnl = (self.average_price - market_price) * self.quantity
            
            # 计算盈亏百分比
            if self.total_cost > 0:
                self.unrealized_pnl_percentage = (self.unrealized_pnl / self.total_cost) * 100
        
        self.last_update_time = datetime.utcnow()
    
    def add_trade(self, side: str, quantity: Decimal, price: Decimal, commission: Decimal = Decimal('0')) -> None:
        """
        添加交易记录并更新持仓
        
        Args:
            side: 交易方向
            quantity: 交易数量
            price: 交易价格
            commission: 手续费
        """
        if side == "buy":
            # 买入增加持仓
            old_total_cost = self.total_cost
            old_quantity = self.quantity
            
            new_quantity = old_quantity + quantity
            new_total_cost = old_total_cost + (quantity * price) + commission
            
            if new_quantity > 0:
                self.average_price = new_total_cost / new_quantity
                self.side = PositionSide.LONG
            
            self.quantity = new_quantity
            self.total_cost = new_total_cost
            self.available_quantity = self.quantity - self.frozen_quantity
            
        elif side == "sell":
            # 卖出减少持仓
            if quantity <= self.quantity:
                # 部分或全部平仓
                sold_cost = (quantity / self.quantity) * self.total_cost if self.quantity > 0 else Decimal('0')
                realized_pnl = (quantity * price) - sold_cost - commission
                
                self.quantity -= quantity
                self.total_cost -= sold_cost
                self.realized_pnl += realized_pnl
                self.available_quantity = self.quantity - self.frozen_quantity
                
                if self.quantity == 0:
                    self.side = PositionSide.FLAT
                    self.average_price = Decimal('0')
                    self.total_cost = Decimal('0')
            else:
                # 超量卖出，转为空头
                excess_quantity = quantity - self.quantity
                
                # 先平掉多头
                if self.quantity > 0:
                    realized_pnl = (self.quantity * price) - self.total_cost - commission
                    self.realized_pnl += realized_pnl
                
                # 建立空头
                self.quantity = excess_quantity
                self.total_cost = excess_quantity * price
                self.average_price = price
                self.side = PositionSide.SHORT
                self.available_quantity = self.quantity - self.frozen_quantity
        
        # 更新时间
        current_time = datetime.utcnow()
        if self.first_trade_time is None:
            self.first_trade_time = current_time
        self.last_trade_time = current_time
        self.last_update_time = current_time