#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易记录模式定义

定义交易记录相关的Pydantic模式，用于API请求和响应验证
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator

from app.models.trade import TradeType
from app.models.order import OrderSide


class TradeBase(BaseModel):
    """
    交易记录基础模式
    """
    symbol: str = Field(..., description="交易对符号", example="BTCUSDT")
    trade_type: TradeType = Field(..., description="交易类型")
    side: OrderSide = Field(..., description="交易方向")
    quantity: Decimal = Field(..., gt=0, description="交易数量")
    price: Decimal = Field(..., gt=0, description="交易价格")
    commission: Decimal = Field(Decimal('0'), ge=0, description="手续费")


class TradeCreate(TradeBase):
    """
    创建交易记录模式
    """
    order_id: int = Field(..., description="关联订单ID")
    trade_id: str = Field(..., description="交易ID")
    commission_asset: Optional[str] = Field(None, description="手续费资产")
    strategy_id: Optional[str] = Field(None, description="策略ID")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    market_maker: Optional[bool] = Field(None, description="是否为做市商")
    notes: Optional[str] = Field(None, description="备注信息")


class TradeResponse(BaseModel):
    """
    交易记录响应模式
    """
    id: int = Field(..., description="交易记录ID")
    user_id: int = Field(..., description="用户ID")
    order_id: int = Field(..., description="关联订单ID")
    trade_id: str = Field(..., description="交易ID")
    
    symbol: str = Field(..., description="交易对符号")
    base_asset: str = Field(..., description="基础资产")
    quote_asset: str = Field(..., description="计价资产")
    
    trade_type: TradeType = Field(..., description="交易类型")
    side: OrderSide = Field(..., description="交易方向")
    
    quantity: Decimal = Field(..., description="交易数量")
    price: Decimal = Field(..., description="交易价格")
    total_value: Decimal = Field(..., description="交易总价值")
    net_value: Decimal = Field(..., description="净价值")
    
    commission: Decimal = Field(..., description="手续费")
    commission_asset: Optional[str] = Field(None, description="手续费资产")
    commission_rate: Decimal = Field(..., description="手续费率")
    
    trade_time: datetime = Field(..., description="交易时间")
    
    strategy_id: Optional[str] = Field(None, description="策略ID")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    
    market_maker: Optional[bool] = Field(None, description="是否为做市商")
    
    realized_pnl: Optional[Decimal] = Field(None, description="已实现盈亏")
    
    notes: Optional[str] = Field(None, description="备注信息")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class TradeListResponse(BaseModel):
    """
    交易记录列表响应模式
    """
    trades: List[TradeResponse] = Field(..., description="交易记录列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class TradeSummary(BaseModel):
    """
    交易摘要模式
    """
    total_trades: int = Field(..., description="总交易数")
    total_volume: Decimal = Field(..., description="总交易量")
    total_value: Decimal = Field(..., description="总交易额")
    total_commission: Decimal = Field(..., description="总手续费")
    avg_price: Decimal = Field(..., description="平均价格")
    avg_commission_rate: Decimal = Field(..., description="平均手续费率")
    buy_volume: Decimal = Field(..., description="买入量")
    sell_volume: Decimal = Field(..., description="卖出量")
    buy_value: Decimal = Field(..., description="买入额")
    sell_value: Decimal = Field(..., description="卖出额")
    net_volume: Decimal = Field(..., description="净交易量")
    net_value: Decimal = Field(..., description="净交易额")
    total_realized_pnl: Decimal = Field(..., description="总已实现盈亏")


class TradeFilter(BaseModel):
    """
    交易记录过滤模式
    """
    symbol: Optional[str] = Field(None, description="交易对符号")
    trade_type: Optional[TradeType] = Field(None, description="交易类型")
    side: Optional[OrderSide] = Field(None, description="交易方向")
    strategy_id: Optional[str] = Field(None, description="策略ID")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    min_quantity: Optional[Decimal] = Field(None, gt=0, description="最小数量")
    max_quantity: Optional[Decimal] = Field(None, gt=0, description="最大数量")
    min_price: Optional[Decimal] = Field(None, gt=0, description="最小价格")
    max_price: Optional[Decimal] = Field(None, gt=0, description="最大价格")
    min_value: Optional[Decimal] = Field(None, gt=0, description="最小交易额")
    max_value: Optional[Decimal] = Field(None, gt=0, description="最大交易额")
    market_maker: Optional[bool] = Field(None, description="是否为做市商")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """
        验证结束时间
        """
        start_time = values.get('start_time')
        if start_time and v and v <= start_time:
            raise ValueError('结束时间必须大于开始时间')
        return v
    
    @validator('max_quantity')
    def validate_max_quantity(cls, v, values):
        """
        验证最大数量
        """
        min_quantity = values.get('min_quantity')
        if min_quantity and v and v <= min_quantity:
            raise ValueError('最大数量必须大于最小数量')
        return v
    
    @validator('max_price')
    def validate_max_price(cls, v, values):
        """
        验证最大价格
        """
        min_price = values.get('min_price')
        if min_price and v and v <= min_price:
            raise ValueError('最大价格必须大于最小价格')
        return v
    
    @validator('max_value')
    def validate_max_value(cls, v, values):
        """
        验证最大交易额
        """
        min_value = values.get('min_value')
        if min_value and v and v <= min_value:
            raise ValueError('最大交易额必须大于最小交易额')
        return v


class TradeStatistics(BaseModel):
    """
    交易统计模式
    """
    symbol: str = Field(..., description="交易对符号")
    period: str = Field(..., description="统计周期")
    
    # 基础统计
    trade_count: int = Field(..., description="交易次数")
    total_volume: Decimal = Field(..., description="总交易量")
    total_value: Decimal = Field(..., description="总交易额")
    
    # 买卖统计
    buy_count: int = Field(..., description="买入次数")
    sell_count: int = Field(..., description="卖出次数")
    buy_volume: Decimal = Field(..., description="买入量")
    sell_volume: Decimal = Field(..., description="卖出量")
    buy_value: Decimal = Field(..., description="买入额")
    sell_value: Decimal = Field(..., description="卖出额")
    
    # 价格统计
    avg_price: Decimal = Field(..., description="平均价格")
    max_price: Decimal = Field(..., description="最高价格")
    min_price: Decimal = Field(..., description="最低价格")
    price_volatility: Decimal = Field(..., description="价格波动率")
    
    # 手续费统计
    total_commission: Decimal = Field(..., description="总手续费")
    avg_commission_rate: Decimal = Field(..., description="平均手续费率")
    
    # 盈亏统计
    total_realized_pnl: Decimal = Field(..., description="总已实现盈亏")
    positive_pnl_count: int = Field(..., description="盈利交易次数")
    negative_pnl_count: int = Field(..., description="亏损交易次数")
    win_rate: Decimal = Field(..., description="胜率")
    
    # 时间统计
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    

class DailyTradeReport(BaseModel):
    """
    日交易报告模式
    """
    date: str = Field(..., description="日期")
    total_trades: int = Field(..., description="总交易数")
    total_volume: Decimal = Field(..., description="总交易量")
    total_value: Decimal = Field(..., description="总交易额")
    total_commission: Decimal = Field(..., description="总手续费")
    total_realized_pnl: Decimal = Field(..., description="总已实现盈亏")
    
    # 按交易对分组的统计
    symbol_stats: List[TradeStatistics] = Field(..., description="按交易对统计")
    
    # 按策略分组的统计
    strategy_stats: List[dict] = Field(..., description="按策略统计")