#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 持仓模式定义

定义持仓相关的Pydantic模式，用于API请求和响应验证
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator

from app.models.position import PositionSide, PositionType


class PositionBase(BaseModel):
    """
    持仓基础模式
    """
    symbol: str = Field(..., description="交易对符号", example="BTCUSDT")
    position_type: PositionType = Field(PositionType.SPOT, description="持仓类型")
    side: PositionSide = Field(..., description="持仓方向")
    quantity: Decimal = Field(..., ge=0, description="持仓数量")


class PositionCreate(PositionBase):
    """
    创建持仓模式
    """
    average_price: Decimal = Field(..., gt=0, description="平均成本价格")
    strategy_id: Optional[str] = Field(None, description="策略ID")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    notes: Optional[str] = Field(None, description="备注信息")


class PositionUpdate(BaseModel):
    """
    更新持仓模式
    """
    quantity: Optional[Decimal] = Field(None, ge=0, description="持仓数量")
    available_quantity: Optional[Decimal] = Field(None, ge=0, description="可用数量")
    frozen_quantity: Optional[Decimal] = Field(None, ge=0, description="冻结数量")
    market_price: Optional[Decimal] = Field(None, gt=0, description="市场价格")
    notes: Optional[str] = Field(None, description="备注信息")
    
    @validator('available_quantity')
    def validate_available_quantity(cls, v, values):
        """
        验证可用数量
        """
        quantity = values.get('quantity')
        frozen_quantity = values.get('frozen_quantity', Decimal('0'))
        
        if quantity is not None and v is not None and frozen_quantity is not None:
            if v + frozen_quantity > quantity:
                raise ValueError('可用数量加冻结数量不能超过总数量')
        
        return v


class PositionResponse(BaseModel):
    """
    持仓响应模式
    """
    id: int = Field(..., description="持仓ID")
    user_id: int = Field(..., description="用户ID")
    
    symbol: str = Field(..., description="交易对符号")
    base_asset: str = Field(..., description="基础资产")
    quote_asset: str = Field(..., description="计价资产")
    
    position_type: PositionType = Field(..., description="持仓类型")
    side: PositionSide = Field(..., description="持仓方向")
    
    quantity: Decimal = Field(..., description="持仓数量")
    available_quantity: Decimal = Field(..., description="可用数量")
    frozen_quantity: Decimal = Field(..., description="冻结数量")
    
    average_price: Decimal = Field(..., description="平均成本价格")
    total_cost: Decimal = Field(..., description="总成本")
    
    market_price: Optional[Decimal] = Field(None, description="当前市场价格")
    market_value: Optional[Decimal] = Field(None, description="当前市场价值")
    position_value: Decimal = Field(..., description="持仓价值")
    available_value: Decimal = Field(..., description="可用价值")
    
    unrealized_pnl: Decimal = Field(..., description="未实现盈亏")
    unrealized_pnl_percentage: Decimal = Field(..., description="未实现盈亏百分比")
    realized_pnl: Decimal = Field(..., description="已实现盈亏")
    
    strategy_id: Optional[str] = Field(None, description="策略ID")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    
    risk_level: Optional[str] = Field(None, description="风险等级")
    margin_ratio: Optional[Decimal] = Field(None, description="保证金比例")
    liquidation_price: Optional[Decimal] = Field(None, description="强平价格")
    
    first_trade_time: Optional[datetime] = Field(None, description="首次交易时间")
    last_trade_time: Optional[datetime] = Field(None, description="最后交易时间")
    last_update_time: datetime = Field(..., description="最后更新时间")
    
    is_active: bool = Field(..., description="是否活跃")
    is_hedged: bool = Field(..., description="是否已对冲")
    is_long: bool = Field(..., description="是否为多头")
    is_short: bool = Field(..., description="是否为空头")
    is_flat: bool = Field(..., description="是否为平仓")
    
    notes: Optional[str] = Field(None, description="备注信息")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class PositionListResponse(BaseModel):
    """
    持仓列表响应模式
    """
    positions: List[PositionResponse] = Field(..., description="持仓列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class PositionSummary(BaseModel):
    """
    持仓摘要模式
    """
    total_positions: int = Field(..., description="总持仓数")
    active_positions: int = Field(..., description="活跃持仓数")
    long_positions: int = Field(..., description="多头持仓数")
    short_positions: int = Field(..., description="空头持仓数")
    
    total_market_value: Decimal = Field(..., description="总市场价值")
    total_cost: Decimal = Field(..., description="总成本")
    total_unrealized_pnl: Decimal = Field(..., description="总未实现盈亏")
    total_realized_pnl: Decimal = Field(..., description="总已实现盈亏")
    
    avg_unrealized_pnl_percentage: Decimal = Field(..., description="平均未实现盈亏百分比")
    
    largest_position_value: Decimal = Field(..., description="最大持仓价值")
    largest_position_symbol: Optional[str] = Field(None, description="最大持仓交易对")


class PositionFilter(BaseModel):
    """
    持仓过滤模式
    """
    symbol: Optional[str] = Field(None, description="交易对符号")
    position_type: Optional[PositionType] = Field(None, description="持仓类型")
    side: Optional[PositionSide] = Field(None, description="持仓方向")
    strategy_id: Optional[str] = Field(None, description="策略ID")
    is_active: Optional[bool] = Field(None, description="是否活跃")
    is_hedged: Optional[bool] = Field(None, description="是否已对冲")
    min_quantity: Optional[Decimal] = Field(None, gt=0, description="最小数量")
    max_quantity: Optional[Decimal] = Field(None, gt=0, description="最大数量")
    min_value: Optional[Decimal] = Field(None, gt=0, description="最小价值")
    max_value: Optional[Decimal] = Field(None, gt=0, description="最大价值")
    min_pnl: Optional[Decimal] = Field(None, description="最小盈亏")
    max_pnl: Optional[Decimal] = Field(None, description="最大盈亏")
    risk_level: Optional[str] = Field(None, description="风险等级")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")
    
    @validator('max_quantity')
    def validate_max_quantity(cls, v, values):
        """
        验证最大数量
        """
        min_quantity = values.get('min_quantity')
        if min_quantity and v and v <= min_quantity:
            raise ValueError('最大数量必须大于最小数量')
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
    
    @validator('max_pnl')
    def validate_max_pnl(cls, v, values):
        """
        验证最大盈亏
        """
        min_pnl = values.get('min_pnl')
        if min_pnl and v and v <= min_pnl:
            raise ValueError('最大盈亏必须大于最小盈亏')
        return v


class PositionRisk(BaseModel):
    """
    持仓风险模式
    """
    position_id: int = Field(..., description="持仓ID")
    symbol: str = Field(..., description="交易对符号")
    
    # 风险指标
    risk_level: str = Field(..., description="风险等级")
    risk_score: Decimal = Field(..., description="风险评分")
    
    # 保证金信息
    margin_ratio: Optional[Decimal] = Field(None, description="保证金比例")
    maintenance_margin: Optional[Decimal] = Field(None, description="维持保证金")
    liquidation_price: Optional[Decimal] = Field(None, description="强平价格")
    
    # 风险提醒
    is_margin_call: bool = Field(..., description="是否需要追加保证金")
    is_liquidation_risk: bool = Field(..., description="是否有强平风险")
    
    # 建议操作
    suggested_action: Optional[str] = Field(None, description="建议操作")
    max_additional_quantity: Optional[Decimal] = Field(None, description="最大可增加数量")
    

class PositionStatistics(BaseModel):
    """
    持仓统计模式
    """
    symbol: str = Field(..., description="交易对符号")
    period: str = Field(..., description="统计周期")
    
    # 基础统计
    avg_quantity: Decimal = Field(..., description="平均持仓数量")
    max_quantity: Decimal = Field(..., description="最大持仓数量")
    min_quantity: Decimal = Field(..., description="最小持仓数量")
    
    # 价值统计
    avg_value: Decimal = Field(..., description="平均持仓价值")
    max_value: Decimal = Field(..., description="最大持仓价值")
    min_value: Decimal = Field(..., description="最小持仓价值")
    
    # 盈亏统计
    total_realized_pnl: Decimal = Field(..., description="总已实现盈亏")
    avg_unrealized_pnl: Decimal = Field(..., description="平均未实现盈亏")
    max_unrealized_pnl: Decimal = Field(..., description="最大未实现盈亏")
    min_unrealized_pnl: Decimal = Field(..., description="最小未实现盈亏")
    
    # 持仓时间统计
    avg_holding_time: float = Field(..., description="平均持仓时间（小时）")
    max_holding_time: float = Field(..., description="最长持仓时间（小时）")
    min_holding_time: float = Field(..., description="最短持仓时间（小时）")
    
    # 时间范围
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")


class PositionCloseRequest(BaseModel):
    """
    平仓请求模式
    """
    quantity: Optional[Decimal] = Field(None, gt=0, description="平仓数量，不指定则全部平仓")
    price: Optional[Decimal] = Field(None, gt=0, description="平仓价格，不指定则市价平仓")
    reason: Optional[str] = Field(None, description="平仓原因")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        """
        验证平仓数量
        """
        if v is not None and v <= 0:
            raise ValueError('平仓数量必须大于0')
        return v


class PositionCloseResponse(BaseModel):
    """
    平仓响应模式
    """
    position_id: int = Field(..., description="持仓ID")
    order_id: Optional[int] = Field(None, description="平仓订单ID")
    closed_quantity: Decimal = Field(..., description="已平仓数量")
    remaining_quantity: Decimal = Field(..., description="剩余数量")
    avg_close_price: Optional[Decimal] = Field(None, description="平均平仓价格")
    realized_pnl: Decimal = Field(..., description="已实现盈亏")
    is_fully_closed: bool = Field(..., description="是否完全平仓")
    close_time: datetime = Field(..., description="平仓时间")