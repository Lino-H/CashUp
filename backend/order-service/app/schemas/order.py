#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单数据模式

定义订单相关的Pydantic模型
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from ..models.order import OrderStatus, OrderType, OrderSide, TimeInForce


class OrderBase(BaseModel):
    """
    订单基础模式
    """
    symbol: str = Field(..., description="交易对")
    side: OrderSide = Field(..., description="订单方向")
    type: OrderType = Field(..., description="订单类型")
    quantity: Decimal = Field(..., gt=0, description="订单数量")
    price: Optional[Decimal] = Field(None, gt=0, description="订单价格")
    stop_price: Optional[Decimal] = Field(None, gt=0, description="止损价格")
    time_in_force: TimeInForce = Field(TimeInForce.GTC, description="订单有效期类型")
    client_order_id: Optional[str] = Field(None, description="客户端订单ID")
    strategy_id: Optional[uuid.UUID] = Field(None, description="策略ID")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    notes: Optional[str] = Field(None, description="备注")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    @validator('price')
    def validate_price(cls, v, values):
        """
        验证价格字段
        """
        order_type = values.get('type')
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT, OrderType.TAKE_PROFIT_LIMIT]:
            if v is None:
                raise ValueError(f"{order_type} orders require a price")
        return v
    
    @validator('stop_price')
    def validate_stop_price(cls, v, values):
        """
        验证止损价格字段
        """
        order_type = values.get('type')
        if order_type in [OrderType.STOP, OrderType.STOP_LIMIT, OrderType.TAKE_PROFIT, OrderType.TAKE_PROFIT_LIMIT]:
            if v is None:
                raise ValueError(f"{order_type} orders require a stop price")
        return v


class OrderCreate(OrderBase):
    """
    创建订单请求模式
    """
    exchange_name: str = Field(..., description="交易所名称")
    
    class Config:
        schema_extra = {
            "example": {
                "exchange_name": "gateio",
                "symbol": "BTC_USDT",
                "side": "buy",
                "type": "limit",
                "quantity": "0.001",
                "price": "50000.00",
                "time_in_force": "gtc",
                "client_order_id": "my_order_123",
                "notes": "Test order"
            }
        }


class OrderUpdate(BaseModel):
    """
    更新订单请求模式
    """
    quantity: Optional[Decimal] = Field(None, gt=0, description="订单数量")
    price: Optional[Decimal] = Field(None, gt=0, description="订单价格")
    stop_price: Optional[Decimal] = Field(None, gt=0, description="止损价格")
    notes: Optional[str] = Field(None, description="备注")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class OrderExecutionResponse(BaseModel):
    """
    订单执行记录响应模式
    """
    id: uuid.UUID = Field(..., description="执行记录ID")
    order_id: uuid.UUID = Field(..., description="订单ID")
    exchange_execution_id: Optional[str] = Field(None, description="交易所执行ID")
    price: Decimal = Field(..., description="执行价格")
    quantity: Decimal = Field(..., description="执行数量")
    value: Decimal = Field(..., description="执行金额")
    fee: Optional[Decimal] = Field(None, description="手续费")
    fee_asset: Optional[str] = Field(None, description="手续费资产")
    executed_at: datetime = Field(..., description="执行时间")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """
    订单响应模式
    """
    id: uuid.UUID = Field(..., description="订单ID")
    user_id: uuid.UUID = Field(..., description="用户ID")
    exchange_name: str = Field(..., description="交易所名称")
    exchange_order_id: Optional[str] = Field(None, description="交易所订单ID")
    client_order_id: Optional[str] = Field(None, description="客户端订单ID")
    symbol: str = Field(..., description="交易对")
    base_asset: str = Field(..., description="基础资产")
    quote_asset: str = Field(..., description="计价资产")
    side: OrderSide = Field(..., description="订单方向")
    type: OrderType = Field(..., description="订单类型")
    status: OrderStatus = Field(..., description="订单状态")
    time_in_force: TimeInForce = Field(..., description="订单有效期类型")
    quantity: Decimal = Field(..., description="订单数量")
    price: Optional[Decimal] = Field(None, description="订单价格")
    stop_price: Optional[Decimal] = Field(None, description="止损价格")
    filled_quantity: Decimal = Field(..., description="已成交数量")
    remaining_quantity: Decimal = Field(..., description="剩余数量")
    avg_price: Optional[Decimal] = Field(None, description="平均成交价格")
    total_value: Optional[Decimal] = Field(None, description="总成交金额")
    fee: Optional[Decimal] = Field(None, description="手续费")
    fee_asset: Optional[str] = Field(None, description="手续费资产")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    submitted_at: Optional[datetime] = Field(None, description="提交时间")
    filled_at: Optional[datetime] = Field(None, description="完成时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    strategy_id: Optional[uuid.UUID] = Field(None, description="策略ID")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    notes: Optional[str] = Field(None, description="备注")
    error_message: Optional[str] = Field(None, description="错误信息")
    is_active: bool = Field(..., description="是否活跃")
    is_completed: bool = Field(..., description="是否完成")
    fill_percentage: float = Field(..., description="成交百分比")
    executions: List[OrderExecutionResponse] = Field(default=[], description="执行记录")
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """
    订单列表响应模式
    """
    orders: List[OrderResponse] = Field(..., description="订单列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class OrderCancelRequest(BaseModel):
    """
    取消订单请求模式
    """
    reason: Optional[str] = Field(None, description="取消原因")


class OrderCancelResponse(BaseModel):
    """
    取消订单响应模式
    """
    order_id: uuid.UUID = Field(..., description="订单ID")
    status: OrderStatus = Field(..., description="订单状态")
    cancelled_at: datetime = Field(..., description="取消时间")
    message: str = Field(..., description="响应消息")


class OrderStatusUpdate(BaseModel):
    """
    订单状态更新模式
    """
    order_id: uuid.UUID = Field(..., description="订单ID")
    status: OrderStatus = Field(..., description="新状态")
    exchange_order_id: Optional[str] = Field(None, description="交易所订单ID")
    filled_quantity: Optional[Decimal] = Field(None, description="已成交数量")
    remaining_quantity: Optional[Decimal] = Field(None, description="剩余数量")
    avg_price: Optional[Decimal] = Field(None, description="平均成交价格")
    total_value: Optional[Decimal] = Field(None, description="总成交金额")
    fee: Optional[Decimal] = Field(None, description="手续费")
    fee_asset: Optional[str] = Field(None, description="手续费资产")
    error_message: Optional[str] = Field(None, description="错误信息")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")


class OrderExecutionCreate(BaseModel):
    """
    创建订单执行记录模式
    """
    order_id: uuid.UUID = Field(..., description="订单ID")
    exchange_execution_id: Optional[str] = Field(None, description="交易所执行ID")
    price: Decimal = Field(..., gt=0, description="执行价格")
    quantity: Decimal = Field(..., gt=0, description="执行数量")
    value: Decimal = Field(..., gt=0, description="执行金额")
    fee: Optional[Decimal] = Field(None, description="手续费")
    fee_asset: Optional[str] = Field(None, description="手续费资产")
    executed_at: datetime = Field(default_factory=datetime.utcnow, description="执行时间")


class OrderStatistics(BaseModel):
    """
    订单统计信息模式
    """
    total_orders: int = Field(..., description="总订单数")
    active_orders: int = Field(..., description="活跃订单数")
    completed_orders: int = Field(..., description="已完成订单数")
    cancelled_orders: int = Field(..., description="已取消订单数")
    failed_orders: int = Field(..., description="失败订单数")
    total_volume: Decimal = Field(..., description="总交易量")
    total_value: Decimal = Field(..., description="总交易金额")
    avg_fill_rate: float = Field(..., description="平均成交率")
    success_rate: float = Field(..., description="成功率")


class OrderFilter(BaseModel):
    """
    订单过滤条件模式
    """
    exchange_name: Optional[str] = Field(None, description="交易所名称")
    symbol: Optional[str] = Field(None, description="交易对")
    side: Optional[OrderSide] = Field(None, description="订单方向")
    type: Optional[OrderType] = Field(None, description="订单类型")
    status: Optional[OrderStatus] = Field(None, description="订单状态")
    strategy_id: Optional[uuid.UUID] = Field(None, description="策略ID")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    min_quantity: Optional[Decimal] = Field(None, description="最小数量")
    max_quantity: Optional[Decimal] = Field(None, description="最大数量")
    min_price: Optional[Decimal] = Field(None, description="最小价格")
    max_price: Optional[Decimal] = Field(None, description="最大价格")