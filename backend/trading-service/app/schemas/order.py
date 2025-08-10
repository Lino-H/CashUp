#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单模式定义

定义订单相关的Pydantic模式，用于API请求和响应验证
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator

from app.models.order import OrderType, OrderSide, OrderStatus, TimeInForce


class OrderBase(BaseModel):
    """
    订单基础模式
    """
    symbol: str = Field(..., description="交易对符号", example="BTCUSDT")
    order_type: OrderType = Field(..., description="订单类型")
    side: OrderSide = Field(..., description="订单方向")
    quantity: Decimal = Field(..., gt=0, description="订单数量")
    price: Optional[Decimal] = Field(None, gt=0, description="订单价格")
    time_in_force: TimeInForce = Field(TimeInForce.GTC, description="订单有效期")
    
    @validator('price')
    def validate_price(cls, v, values):
        """
        验证价格字段
        """
        order_type = values.get('order_type')
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and v is None:
            raise ValueError('限价订单和止损限价订单必须指定价格')
        return v


class OrderCreate(OrderBase):
    """
    创建订单模式
    """
    stop_price: Optional[Decimal] = Field(None, gt=0, description="止损价格")
    iceberg_qty: Optional[Decimal] = Field(None, gt=0, description="冰山订单数量")
    strategy_id: Optional[str] = Field(None, description="策略ID")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    client_order_id: Optional[str] = Field(None, description="客户端订单ID")
    notes: Optional[str] = Field(None, description="备注信息")
    
    @validator('stop_price')
    def validate_stop_price(cls, v, values):
        """
        验证止损价格
        """
        order_type = values.get('order_type')
        if order_type in [OrderType.STOP_MARKET, OrderType.STOP_LIMIT] and v is None:
            raise ValueError('止损订单必须指定止损价格')
        return v


class OrderUpdate(BaseModel):
    """
    更新订单模式
    """
    quantity: Optional[Decimal] = Field(None, gt=0, description="订单数量")
    price: Optional[Decimal] = Field(None, gt=0, description="订单价格")
    stop_price: Optional[Decimal] = Field(None, gt=0, description="止损价格")
    time_in_force: Optional[TimeInForce] = Field(None, description="订单有效期")
    notes: Optional[str] = Field(None, description="备注信息")


class OrderCancel(BaseModel):
    """
    取消订单模式
    """
    reason: Optional[str] = Field(None, description="取消原因")


class OrderResponse(BaseModel):
    """
    订单响应模式
    """
    id: int = Field(..., description="订单ID")
    user_id: int = Field(..., description="用户ID")
    order_id: str = Field(..., description="订单唯一标识")
    client_order_id: Optional[str] = Field(None, description="客户端订单ID")
    symbol: str = Field(..., description="交易对符号")
    base_asset: str = Field(..., description="基础资产")
    quote_asset: str = Field(..., description="计价资产")
    
    order_type: OrderType = Field(..., description="订单类型")
    side: OrderSide = Field(..., description="订单方向")
    status: OrderStatus = Field(..., description="订单状态")
    time_in_force: TimeInForce = Field(..., description="订单有效期")
    
    quantity: Decimal = Field(..., description="订单数量")
    price: Optional[Decimal] = Field(None, description="订单价格")
    stop_price: Optional[Decimal] = Field(None, description="止损价格")
    iceberg_qty: Optional[Decimal] = Field(None, description="冰山订单数量")
    
    executed_quantity: Decimal = Field(..., description="已成交数量")
    remaining_quantity: Decimal = Field(..., description="剩余数量")
    avg_price: Optional[Decimal] = Field(None, description="平均成交价格")
    
    commission: Decimal = Field(..., description="手续费")
    commission_asset: Optional[str] = Field(None, description="手续费资产")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    executed_at: Optional[datetime] = Field(None, description="成交时间")
    
    strategy_id: Optional[str] = Field(None, description="策略ID")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    
    notes: Optional[str] = Field(None, description="备注信息")
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """
    订单列表响应模式
    """
    orders: List[OrderResponse] = Field(..., description="订单列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class OrderSummary(BaseModel):
    """
    订单摘要模式
    """
    total_orders: int = Field(..., description="总订单数")
    active_orders: int = Field(..., description="活跃订单数")
    completed_orders: int = Field(..., description="已完成订单数")
    cancelled_orders: int = Field(..., description="已取消订单数")
    total_volume: Decimal = Field(..., description="总交易量")
    total_value: Decimal = Field(..., description="总交易额")
    avg_execution_time: Optional[float] = Field(None, description="平均执行时间（秒）")


class OrderFilter(BaseModel):
    """
    订单过滤模式
    """
    symbol: Optional[str] = Field(None, description="交易对符号")
    order_type: Optional[OrderType] = Field(None, description="订单类型")
    side: Optional[OrderSide] = Field(None, description="订单方向")
    status: Optional[OrderStatus] = Field(None, description="订单状态")
    strategy_id: Optional[str] = Field(None, description="策略ID")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    min_quantity: Optional[Decimal] = Field(None, gt=0, description="最小数量")
    max_quantity: Optional[Decimal] = Field(None, gt=0, description="最大数量")
    min_price: Optional[Decimal] = Field(None, gt=0, description="最小价格")
    max_price: Optional[Decimal] = Field(None, gt=0, description="最大价格")
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


class BatchOrderCreate(BaseModel):
    """
    批量创建订单模式
    """
    orders: List[OrderCreate] = Field(..., min_items=1, max_items=10, description="订单列表")
    
    @validator('orders')
    def validate_orders(cls, v):
        """
        验证订单列表
        """
        if len(v) > 10:
            raise ValueError('单次最多只能创建10个订单')
        return v


class BatchOrderResponse(BaseModel):
    """
    批量订单响应模式
    """
    success_orders: List[OrderResponse] = Field(..., description="成功创建的订单")
    failed_orders: List[dict] = Field(..., description="创建失败的订单")
    total_count: int = Field(..., description="总订单数")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")