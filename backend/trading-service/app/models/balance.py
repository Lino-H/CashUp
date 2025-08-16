#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 账户余额数据模型

定义账户余额相关的数据模型
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime, Boolean, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum

from app.core.database import Base


class BalanceType(str, Enum):
    """
    余额类型枚举
    """
    SPOT = "spot"  # 现货余额
    MARGIN = "margin"  # 保证金余额
    FUTURES = "futures"  # 期货余额
    OPTIONS = "options"  # 期权余额
    SAVINGS = "savings"  # 储蓄余额


class Balance(Base):
    """
    账户余额模型
    
    存储用户的资产余额信息
    """
    __tablename__ = "balances"
    
    # 基本信息
    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    # 资产信息
    asset: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="资产符号"
    )
    asset_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="资产名称"
    )
    
    # 余额类型
    balance_type: Mapped[BalanceType] = mapped_column(
        String(20),
        default=BalanceType.SPOT,
        nullable=False,
        comment="余额类型"
    )
    
    # 余额信息
    total_balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="总余额"
    )
    available_balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="可用余额"
    )
    frozen_balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="冻结余额"
    )
    
    # 保证金信息（仅适用于保证金和期货账户）
    margin_balance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="保证金余额"
    )
    margin_ratio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="保证金比例"
    )
    maintenance_margin: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="维持保证金"
    )
    
    # 价值信息
    usd_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="USD价值"
    )
    btc_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="BTC价值"
    )
    
    # 历史信息
    yesterday_balance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        comment="昨日余额"
    )
    balance_change_24h: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="24小时余额变化"
    )
    balance_change_percentage_24h: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        default=Decimal('0'),
        nullable=False,
        comment="24小时余额变化百分比"
    )
    
    # 利息信息（仅适用于储蓄账户）
    interest_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 6),
        nullable=True,
        comment="利率"
    )
    accrued_interest: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal('0'),
        nullable=False,
        comment="累计利息"
    )
    last_interest_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后计息时间"
    )
    
    # 时间信息
    last_update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="最后更新时间"
    )
    last_transaction_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后交易时间"
    )
    
    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否活跃"
    )
    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否锁定"
    )
    
    # 备注信息
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_balance_user_asset_type', 'user_id', 'asset', 'balance_type', unique=True),
        Index('idx_balance_user_active', 'user_id', 'is_active'),
        Index('idx_balance_asset_active', 'asset', 'is_active'),
        Index('idx_balance_type', 'balance_type'),
    )
    
    def __repr__(self) -> str:
        return f"<Balance(id={self.id}, user_id={self.user_id}, asset='{self.asset}', total={self.total_balance})>"
    
    @property
    def is_sufficient(self) -> bool:
        """
        检查余额是否充足（可用余额大于0）
        
        Returns:
            bool: 余额是否充足
        """
        return self.available_balance > 0
    
    @property
    def utilization_rate(self) -> Decimal:
        """
        计算余额使用率
        
        Returns:
            Decimal: 使用率百分比
        """
        if self.total_balance <= 0:
            return Decimal('0')
        return (self.frozen_balance / self.total_balance) * 100
    
    @property
    def is_margin_call(self) -> bool:
        """
        检查是否需要追加保证金
        
        Returns:
            bool: 是否需要追加保证金
        """
        if self.balance_type not in [BalanceType.MARGIN, BalanceType.FUTURES]:
            return False
        
        if self.maintenance_margin is None or self.margin_balance is None:
            return False
        
        return self.margin_balance < self.maintenance_margin
    
    def freeze_balance(self, amount: Decimal) -> bool:
        """
        冻结余额
        
        Args:
            amount: 冻结金额
            
        Returns:
            bool: 是否成功冻结
        """
        if amount <= 0:
            return False
        
        if self.available_balance < amount:
            return False
        
        self.available_balance -= amount
        self.frozen_balance += amount
        self.last_update_time = datetime.utcnow()
        
        return True
    
    def unfreeze_balance(self, amount: Decimal) -> bool:
        """
        解冻余额
        
        Args:
            amount: 解冻金额
            
        Returns:
            bool: 是否成功解冻
        """
        if amount <= 0:
            return False
        
        if self.frozen_balance < amount:
            return False
        
        self.frozen_balance -= amount
        self.available_balance += amount
        self.last_update_time = datetime.utcnow()
        
        return True
    
    def add_balance(self, amount: Decimal, update_available: bool = True) -> None:
        """
        增加余额
        
        Args:
            amount: 增加金额
            update_available: 是否同时更新可用余额
        """
        if amount <= 0:
            return
        
        self.total_balance += amount
        if update_available:
            self.available_balance += amount
        
        self.last_update_time = datetime.utcnow()
        self.last_transaction_time = datetime.utcnow()
    
    def subtract_balance(self, amount: Decimal, from_available: bool = True) -> bool:
        """
        减少余额
        
        Args:
            amount: 减少金额
            from_available: 是否从可用余额中扣除
            
        Returns:
            bool: 是否成功扣除
        """
        if amount <= 0:
            return False
        
        if from_available:
            if self.available_balance < amount:
                return False
            self.available_balance -= amount
        else:
            if self.frozen_balance < amount:
                return False
            self.frozen_balance -= amount
        
        self.total_balance -= amount
        self.last_update_time = datetime.utcnow()
        self.last_transaction_time = datetime.utcnow()
        
        return True
    
    def update_market_value(self, usd_price: Optional[Decimal] = None, btc_price: Optional[Decimal] = None) -> None:
        """
        更新市场价值
        
        Args:
            usd_price: USD价格
            btc_price: BTC价格
        """
        if usd_price is not None:
            self.usd_value = self.total_balance * usd_price
        
        if btc_price is not None:
            self.btc_value = self.total_balance * btc_price
        
        self.last_update_time = datetime.utcnow()
    
    def calculate_daily_change(self) -> None:
        """
        计算24小时变化
        """
        if self.yesterday_balance is not None and self.yesterday_balance > 0:
            self.balance_change_24h = self.total_balance - self.yesterday_balance
            self.balance_change_percentage_24h = (self.balance_change_24h / self.yesterday_balance) * 100
        else:
            self.balance_change_24h = Decimal('0')
            self.balance_change_percentage_24h = Decimal('0')
        
        self.last_update_time = datetime.utcnow()
    
    def accrue_interest(self) -> Decimal:
        """
        计算并累计利息
        
        Returns:
            Decimal: 本次计息金额
        """
        if self.balance_type != BalanceType.SAVINGS or self.interest_rate is None:
            return Decimal('0')
        
        current_time = datetime.utcnow()
        
        if self.last_interest_time is None:
            self.last_interest_time = current_time
            return Decimal('0')
        
        # 计算时间差（天数）
        time_diff = current_time - self.last_interest_time
        days = Decimal(str(time_diff.total_seconds() / 86400))  # 86400秒 = 1天
        
        # 计算利息（年化利率转日利率）
        daily_rate = self.interest_rate / 365
        interest = self.total_balance * daily_rate * days
        
        if interest > 0:
            self.accrued_interest += interest
            self.add_balance(interest, update_available=True)
            self.last_interest_time = current_time
        
        return interest