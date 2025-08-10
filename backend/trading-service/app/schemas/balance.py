#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 余额模式定义

定义余额相关的Pydantic模式，用于API请求和响应验证
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator

from app.models.balance import BalanceType


class BalanceBase(BaseModel):
    """
    余额基础模式
    """
    asset: str = Field(..., description="资产符号", example="BTC")
    balance_type: BalanceType = Field(BalanceType.SPOT, description="余额类型")
    total_balance: Decimal = Field(..., ge=0, description="总余额")
    available_balance: Decimal = Field(..., ge=0, description="可用余额")
    frozen_balance: Decimal = Field(Decimal('0'), ge=0, description="冻结余额")
    
    @validator('available_balance')
    def validate_available_balance(cls, v, values):
        """
        验证可用余额
        """
        total_balance = values.get('total_balance', Decimal('0'))
        frozen_balance = values.get('frozen_balance', Decimal('0'))
        
        if v + frozen_balance > total_balance:
            raise ValueError('可用余额加冻结余额不能超过总余额')
        
        return v


class BalanceCreate(BalanceBase):
    """
    创建余额模式
    """
    asset_name: Optional[str] = Field(None, description="资产名称")
    notes: Optional[str] = Field(None, description="备注信息")


class BalanceUpdate(BaseModel):
    """
    更新余额模式
    """
    total_balance: Optional[Decimal] = Field(None, ge=0, description="总余额")
    available_balance: Optional[Decimal] = Field(None, ge=0, description="可用余额")
    frozen_balance: Optional[Decimal] = Field(None, ge=0, description="冻结余额")
    usd_value: Optional[Decimal] = Field(None, ge=0, description="USD价值")
    btc_value: Optional[Decimal] = Field(None, ge=0, description="BTC价值")
    notes: Optional[str] = Field(None, description="备注信息")
    
    @validator('available_balance')
    def validate_available_balance(cls, v, values):
        """
        验证可用余额
        """
        total_balance = values.get('total_balance')
        frozen_balance = values.get('frozen_balance')
        
        if total_balance is not None and frozen_balance is not None and v is not None:
            if v + frozen_balance > total_balance:
                raise ValueError('可用余额加冻结余额不能超过总余额')
        
        return v


class BalanceResponse(BaseModel):
    """
    余额响应模式
    """
    id: int = Field(..., description="余额ID")
    user_id: int = Field(..., description="用户ID")
    
    asset: str = Field(..., description="资产符号")
    asset_name: Optional[str] = Field(None, description="资产名称")
    balance_type: BalanceType = Field(..., description="余额类型")
    
    total_balance: Decimal = Field(..., description="总余额")
    available_balance: Decimal = Field(..., description="可用余额")
    frozen_balance: Decimal = Field(..., description="冻结余额")
    
    margin_balance: Optional[Decimal] = Field(None, description="保证金余额")
    margin_ratio: Optional[Decimal] = Field(None, description="保证金比例")
    maintenance_margin: Optional[Decimal] = Field(None, description="维持保证金")
    
    usd_value: Optional[Decimal] = Field(None, description="USD价值")
    btc_value: Optional[Decimal] = Field(None, description="BTC价值")
    
    yesterday_balance: Optional[Decimal] = Field(None, description="昨日余额")
    balance_change_24h: Decimal = Field(..., description="24小时余额变化")
    balance_change_percentage_24h: Decimal = Field(..., description="24小时余额变化百分比")
    
    interest_rate: Optional[Decimal] = Field(None, description="利率")
    accrued_interest: Decimal = Field(..., description="累计利息")
    last_interest_time: Optional[datetime] = Field(None, description="最后计息时间")
    
    last_update_time: datetime = Field(..., description="最后更新时间")
    last_transaction_time: Optional[datetime] = Field(None, description="最后交易时间")
    
    is_active: bool = Field(..., description="是否活跃")
    is_locked: bool = Field(..., description="是否锁定")
    is_sufficient: bool = Field(..., description="余额是否充足")
    utilization_rate: Decimal = Field(..., description="使用率")
    is_margin_call: bool = Field(..., description="是否需要追加保证金")
    
    notes: Optional[str] = Field(None, description="备注信息")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class BalanceListResponse(BaseModel):
    """
    余额列表响应模式
    """
    balances: List[BalanceResponse] = Field(..., description="余额列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class BalanceSummary(BaseModel):
    """
    余额摘要模式
    """
    total_assets: int = Field(..., description="总资产种类数")
    active_assets: int = Field(..., description="活跃资产数")
    
    total_usd_value: Decimal = Field(..., description="总USD价值")
    total_btc_value: Decimal = Field(..., description="总BTC价值")
    
    spot_value: Decimal = Field(..., description="现货价值")
    margin_value: Decimal = Field(..., description="保证金价值")
    futures_value: Decimal = Field(..., description="期货价值")
    savings_value: Decimal = Field(..., description="储蓄价值")
    
    total_frozen_value: Decimal = Field(..., description="总冻结价值")
    total_available_value: Decimal = Field(..., description="总可用价值")
    
    daily_change_value: Decimal = Field(..., description="日变化价值")
    daily_change_percentage: Decimal = Field(..., description="日变化百分比")
    
    total_accrued_interest: Decimal = Field(..., description="总累计利息")
    
    largest_asset_value: Decimal = Field(..., description="最大资产价值")
    largest_asset: Optional[str] = Field(None, description="最大资产")


class BalanceFilter(BaseModel):
    """
    余额过滤模式
    """
    asset: Optional[str] = Field(None, description="资产符号")
    balance_type: Optional[BalanceType] = Field(None, description="余额类型")
    is_active: Optional[bool] = Field(None, description="是否活跃")
    is_locked: Optional[bool] = Field(None, description="是否锁定")
    min_balance: Optional[Decimal] = Field(None, gt=0, description="最小余额")
    max_balance: Optional[Decimal] = Field(None, gt=0, description="最大余额")
    min_value: Optional[Decimal] = Field(None, gt=0, description="最小价值")
    max_value: Optional[Decimal] = Field(None, gt=0, description="最大价值")
    has_frozen: Optional[bool] = Field(None, description="是否有冻结余额")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")
    
    @validator('max_balance')
    def validate_max_balance(cls, v, values):
        """
        验证最大余额
        """
        min_balance = values.get('min_balance')
        if min_balance and v and v <= min_balance:
            raise ValueError('最大余额必须大于最小余额')
        return v
    
    @validator('max_value')
    def validate_max_value(cls, v, values):
        """
        验证最大价值
        """
        min_value = values.get('min_value')
        if min_value and v and v <= min_value:
            raise ValueError('最大价值必须大于最小价值')
        return v


class BalanceOperation(BaseModel):
    """
    余额操作模式
    """
    operation_type: str = Field(..., description="操作类型", pattern="^(freeze|unfreeze|add|subtract)$")
    amount: Decimal = Field(..., gt=0, description="操作金额")
    reason: Optional[str] = Field(None, description="操作原因")
    reference_id: Optional[str] = Field(None, description="关联ID")
    
    @validator('operation_type')
    def validate_operation_type(cls, v):
        """
        验证操作类型
        """
        allowed_types = ['freeze', 'unfreeze', 'add', 'subtract']
        if v not in allowed_types:
            raise ValueError(f'操作类型必须是以下之一: {", ".join(allowed_types)}')
        return v


class BalanceOperationResponse(BaseModel):
    """
    余额操作响应模式
    """
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作结果消息")
    balance_before: Decimal = Field(..., description="操作前余额")
    balance_after: Decimal = Field(..., description="操作后余额")
    operation_amount: Decimal = Field(..., description="操作金额")
    operation_time: datetime = Field(..., description="操作时间")


class BalanceTransfer(BaseModel):
    """
    余额转账模式
    """
    from_balance_type: BalanceType = Field(..., description="源余额类型")
    to_balance_type: BalanceType = Field(..., description="目标余额类型")
    asset: str = Field(..., description="资产符号")
    amount: Decimal = Field(..., gt=0, description="转账金额")
    notes: Optional[str] = Field(None, description="备注信息")
    
    @validator('to_balance_type')
    def validate_transfer_types(cls, v, values):
        """
        验证转账类型
        """
        from_type = values.get('from_balance_type')
        if from_type and v == from_type:
            raise ValueError('源余额类型和目标余额类型不能相同')
        return v


class BalanceTransferResponse(BaseModel):
    """
    余额转账响应模式
    """
    transfer_id: str = Field(..., description="转账ID")
    success: bool = Field(..., description="转账是否成功")
    message: str = Field(..., description="转账结果消息")
    
    from_balance_before: Decimal = Field(..., description="源余额转账前")
    from_balance_after: Decimal = Field(..., description="源余额转账后")
    to_balance_before: Decimal = Field(..., description="目标余额转账前")
    to_balance_after: Decimal = Field(..., description="目标余额转账后")
    
    transfer_amount: Decimal = Field(..., description="转账金额")
    transfer_time: datetime = Field(..., description="转账时间")


class BalanceHistory(BaseModel):
    """
    余额历史模式
    """
    date: str = Field(..., description="日期")
    asset: str = Field(..., description="资产符号")
    balance_type: BalanceType = Field(..., description="余额类型")
    
    opening_balance: Decimal = Field(..., description="期初余额")
    closing_balance: Decimal = Field(..., description="期末余额")
    
    total_deposits: Decimal = Field(..., description="总充值")
    total_withdrawals: Decimal = Field(..., description="总提现")
    total_trades: Decimal = Field(..., description="总交易")
    total_fees: Decimal = Field(..., description="总手续费")
    total_interest: Decimal = Field(..., description="总利息")
    
    net_change: Decimal = Field(..., description="净变化")
    change_percentage: Decimal = Field(..., description="变化百分比")
    
    max_balance: Decimal = Field(..., description="最高余额")
    min_balance: Decimal = Field(..., description="最低余额")
    
    transaction_count: int = Field(..., description="交易次数")


class BalanceStatistics(BaseModel):
    """
    余额统计模式
    """
    asset: str = Field(..., description="资产符号")
    period: str = Field(..., description="统计周期")
    
    # 基础统计
    avg_balance: Decimal = Field(..., description="平均余额")
    max_balance: Decimal = Field(..., description="最高余额")
    min_balance: Decimal = Field(..., description="最低余额")
    
    # 变化统计
    total_deposits: Decimal = Field(..., description="总充值")
    total_withdrawals: Decimal = Field(..., description="总提现")
    net_flow: Decimal = Field(..., description="净流入")
    
    # 交易统计
    total_trade_volume: Decimal = Field(..., description="总交易量")
    total_fees_paid: Decimal = Field(..., description="总手续费")
    total_interest_earned: Decimal = Field(..., description="总利息收入")
    
    # 使用率统计
    avg_utilization_rate: Decimal = Field(..., description="平均使用率")
    max_utilization_rate: Decimal = Field(..., description="最高使用率")
    
    # 时间统计
    active_days: int = Field(..., description="活跃天数")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")