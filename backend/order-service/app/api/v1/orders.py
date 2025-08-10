#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单API路由

处理订单相关的HTTP请求
"""

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_database_session
from ...schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    OrderCancelRequest, OrderCancelResponse, OrderStatusUpdate,
    OrderExecutionCreate, OrderStatistics, OrderFilter
)
from ...services.order_service import OrderService
from ...core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    创建新订单
    
    Args:
        order_data: 订单创建数据
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        OrderResponse: 创建的订单信息
        
    Raises:
        HTTPException: 创建失败时抛出异常
    """
    try:
        user_id = uuid.UUID(current_user["user_id"])
        order_service = OrderService(db)
        
        order = await order_service.create_order(user_id, order_data)
        return order
        
    except ValueError as e:
        logger.error(f"Invalid order data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    exchange_name: Optional[str] = Query(None, description="交易所名称"),
    symbol: Optional[str] = Query(None, description="交易对"),
    side: Optional[str] = Query(None, description="订单方向"),
    type: Optional[str] = Query(None, description="订单类型"),
    status: Optional[str] = Query(None, description="订单状态"),
    strategy_id: Optional[str] = Query(None, description="策略ID"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    获取订单列表
    
    Args:
        exchange_name: 交易所名称过滤
        symbol: 交易对过滤
        side: 订单方向过滤
        type: 订单类型过滤
        status: 订单状态过滤
        strategy_id: 策略ID过滤
        start_time: 开始时间过滤
        end_time: 结束时间过滤
        page: 页码
        size: 每页大小
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        OrderListResponse: 订单列表响应
    """
    try:
        user_id = uuid.UUID(current_user["user_id"])
        order_service = OrderService(db)
        
        # 构建过滤条件
        filter_params = OrderFilter(
            exchange_name=exchange_name,
            symbol=symbol,
            side=side,
            type=type,
            status=status,
            strategy_id=uuid.UUID(strategy_id) if strategy_id else None,
            start_time=start_time,
            end_time=end_time
        )
        
        orders = await order_service.list_orders(
            user_id=user_id,
            filter_params=filter_params,
            page=page,
            size=size
        )
        
        return orders
        
    except ValueError as e:
        logger.error(f"Invalid filter parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to list orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list orders"
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    获取订单详情
    
    Args:
        order_id: 订单ID
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        OrderResponse: 订单详情
        
    Raises:
        HTTPException: 订单不存在时抛出404异常
    """
    try:
        user_id = uuid.UUID(current_user["user_id"])
        order_service = OrderService(db)
        
        order = await order_service.get_order(user_id, order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order"
        )


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: uuid.UUID,
    order_update: OrderUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    更新订单
    
    Args:
        order_id: 订单ID
        order_update: 订单更新数据
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        OrderResponse: 更新后的订单信息
    """
    try:
        user_id = uuid.UUID(current_user["user_id"])
        order_service = OrderService(db)
        
        # 获取现有订单
        existing_order = await order_service.get_order(user_id, order_id)
        if not existing_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # 检查订单是否可以更新
        if not existing_order.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update inactive order"
            )
        
        # TODO: 实现订单更新逻辑
        # 注意：大多数交易所不支持订单更新，可能需要取消后重新创建
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Order update not implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order"
        )


@router.delete("/{order_id}", response_model=OrderResponse)
async def cancel_order(
    order_id: uuid.UUID,
    cancel_request: Optional[OrderCancelRequest] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    取消订单
    
    Args:
        order_id: 订单ID
        cancel_request: 取消请求数据
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        OrderResponse: 取消后的订单信息
    """
    try:
        user_id = uuid.UUID(current_user["user_id"])
        order_service = OrderService(db)
        
        order = await order_service.cancel_order(user_id, order_id, cancel_request)
        return order
        
    except ValueError as e:
        logger.error(f"Invalid cancel request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to cancel order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        )


@router.post("/{order_id}/executions", response_model=OrderResponse)
async def add_execution(
    order_id: uuid.UUID,
    execution_data: OrderExecutionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    添加订单执行记录
    
    Args:
        order_id: 订单ID
        execution_data: 执行记录数据
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        OrderResponse: 更新后的订单信息
    """
    try:
        # 验证订单ID匹配
        if execution_data.order_id != order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order ID mismatch"
            )
        
        order_service = OrderService(db)
        order = await order_service.add_execution(execution_data)
        
        return order
        
    except ValueError as e:
        logger.error(f"Invalid execution data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to add execution to order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add execution"
        )


@router.get("/statistics/summary", response_model=OrderStatistics)
async def get_order_statistics(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    获取订单统计信息
    
    Args:
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        OrderStatistics: 统计信息
    """
    try:
        user_id = uuid.UUID(current_user["user_id"])
        order_service = OrderService(db)
        
        statistics = await order_service.get_order_statistics(user_id)
        return statistics
        
    except Exception as e:
        logger.error(f"Failed to get order statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order statistics"
        )


@router.post("/status/update", response_model=OrderResponse)
async def update_order_status(
    status_update: OrderStatusUpdate,
    db: AsyncSession = Depends(get_database_session)
):
    """
    更新订单状态（内部API，用于交易所回调）
    
    Args:
        status_update: 状态更新数据
        db: 数据库会话
        
    Returns:
        OrderResponse: 更新后的订单信息
    """
    try:
        order_service = OrderService(db)
        order = await order_service.update_order_status(status_update)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update order status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )