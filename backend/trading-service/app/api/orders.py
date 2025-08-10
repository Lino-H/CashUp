#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单API路由

提供订单相关的API接口
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user, require_trader_role
from app.core.redis import RedisManager
from app.services.order_service import OrderService
from app.services.balance_service import BalanceService
from app.services.position_service import PositionService
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderCancel, OrderResponse,
    OrderListResponse, OrderSummary, OrderFilter,
    BatchOrderCreate, BatchOrderResponse
)
from app.schemas.user import UserResponse

logger = logging.getLogger("api.orders")

router = APIRouter(prefix="/orders", tags=["orders"])


# 依赖注入
async def get_order_service() -> OrderService:
    """获取订单服务实例"""
    redis_manager = RedisManager()
    return OrderService(redis_manager)


async def get_balance_service() -> BalanceService:
    """获取余额服务实例"""
    redis_manager = RedisManager()
    return BalanceService(redis_manager)


async def get_position_service() -> PositionService:
    """获取持仓服务实例"""
    redis_manager = RedisManager()
    return PositionService(redis_manager)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    order_service: OrderService = Depends(get_order_service),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    创建订单
    
    - **symbol**: 交易对符号
    - **side**: 订单方向 (BUY/SELL)
    - **order_type**: 订单类型 (MARKET/LIMIT/STOP/STOP_LIMIT)
    - **quantity**: 订单数量
    - **price**: 订单价格（限价单必填）
    - **time_in_force**: 订单有效期类型
    """
    try:
        logger.info(f"创建订单请求: user_id={current_user.id}, symbol={order_data.symbol}")
        
        order = await order_service.create_order(
            db=db,
            user_id=current_user.id,
            order_data=order_data,
            balance_service=balance_service
        )
        
        logger.info(f"订单创建成功: order_id={order.id}")
        return order
        
    except ValueError as e:
        logger.warning(f"创建订单失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建订单异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建订单失败"
        )


@router.post("/batch", response_model=BatchOrderResponse)
async def create_batch_orders(
    batch_data: BatchOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    order_service: OrderService = Depends(get_order_service),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    批量创建订单
    
    - **orders**: 订单列表
    - **fail_on_error**: 是否在遇到错误时停止处理
    """
    try:
        logger.info(f"批量创建订单请求: user_id={current_user.id}, count={len(batch_data.orders)}")
        
        result = await order_service.create_batch_orders(
            db=db,
            user_id=current_user.id,
            batch_data=batch_data,
            balance_service=balance_service
        )
        
        logger.info(f"批量订单创建完成: success={result.success_count}, failed={result.failed_count}")
        return result
        
    except Exception as e:
        logger.error(f"批量创建订单异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量创建订单失败"
        )


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    symbol: str = Query(None, description="交易对符号"),
    side: str = Query(None, description="订单方向"),
    order_type: str = Query(None, description="订单类型"),
    status: str = Query(None, description="订单状态"),
    strategy_id: str = Query(None, description="策略ID"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    获取订单列表
    
    支持多种过滤条件和分页
    """
    try:
        filter_params = OrderFilter(
            symbol=symbol,
            side=side,
            order_type=order_type,
            status=status,
            strategy_id=strategy_id,
            start_time=start_time,
            end_time=end_time,
            page=page,
            size=size
        )
        
        orders = await order_service.list_orders(
            db=db,
            user_id=current_user.id,
            filter_params=filter_params
        )
        
        return orders
        
    except Exception as e:
        logger.error(f"获取订单列表异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单列表失败"
        )


@router.get("/summary", response_model=OrderSummary)
async def get_order_summary(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    获取订单摘要统计
    
    - **days**: 统计天数，默认30天
    """
    try:
        summary = await order_service.get_order_summary(
            db=db,
            user_id=current_user.id,
            days=days
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"获取订单摘要异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单摘要失败"
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    获取订单详情
    
    - **order_id**: 订单ID
    """
    try:
        order = await order_service.get_order(db, current_user.id, order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订单详情异常: user_id={current_user.id}, order_id={order_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单详情失败"
        )


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    order_service: OrderService = Depends(get_order_service)
):
    """
    更新订单
    
    - **order_id**: 订单ID
    - **quantity**: 新的订单数量
    - **price**: 新的订单价格
    - **stop_price**: 新的止损价格
    """
    try:
        logger.info(f"更新订单请求: user_id={current_user.id}, order_id={order_id}")
        
        order = await order_service.update_order(
            db=db,
            user_id=current_user.id,
            order_id=order_id,
            order_update=order_update
        )
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        logger.info(f"订单更新成功: order_id={order_id}")
        return order
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"更新订单失败: user_id={current_user.id}, order_id={order_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新订单异常: user_id={current_user.id}, order_id={order_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新订单失败"
        )


@router.delete("/{order_id}", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    cancel_data: OrderCancel = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    order_service: OrderService = Depends(get_order_service),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    取消订单
    
    - **order_id**: 订单ID
    - **reason**: 取消原因（可选）
    """
    try:
        logger.info(f"取消订单请求: user_id={current_user.id}, order_id={order_id}")
        
        if not cancel_data:
            cancel_data = OrderCancel(reason="用户取消")
        
        order = await order_service.cancel_order(
            db=db,
            user_id=current_user.id,
            order_id=order_id,
            cancel_data=cancel_data,
            balance_service=balance_service
        )
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        logger.info(f"订单取消成功: order_id={order_id}")
        return order
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"取消订单失败: user_id={current_user.id}, order_id={order_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"取消订单异常: user_id={current_user.id}, order_id={order_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消订单失败"
        )


@router.post("/{order_id}/execute", response_model=OrderResponse)
async def execute_order(
    order_id: int,
    execution_price: float = Query(..., description="执行价格"),
    execution_quantity: float = Query(None, description="执行数量"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    order_service: OrderService = Depends(get_order_service),
    balance_service: BalanceService = Depends(get_balance_service),
    position_service: PositionService = Depends(get_position_service)
):
    """
    执行订单（模拟成交）
    
    - **order_id**: 订单ID
    - **execution_price**: 执行价格
    - **execution_quantity**: 执行数量（可选，默认为订单剩余数量）
    """
    try:
        logger.info(f"执行订单请求: user_id={current_user.id}, order_id={order_id}")
        
        order = await order_service.execute_order(
            db=db,
            user_id=current_user.id,
            order_id=order_id,
            execution_price=execution_price,
            execution_quantity=execution_quantity,
            balance_service=balance_service,
            position_service=position_service
        )
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        logger.info(f"订单执行成功: order_id={order_id}")
        return order
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"执行订单失败: user_id={current_user.id}, order_id={order_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"执行订单异常: user_id={current_user.id}, order_id={order_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="执行订单失败"
        )


@router.delete("/", response_model=dict)
async def cancel_all_orders(
    symbol: str = Query(None, description="交易对符号（可选）"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    order_service: OrderService = Depends(get_order_service),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    取消所有订单
    
    - **symbol**: 交易对符号（可选，不指定则取消所有订单）
    """
    try:
        logger.info(f"取消所有订单请求: user_id={current_user.id}, symbol={symbol}")
        
        # 获取待取消的订单
        filter_params = OrderFilter(
            symbol=symbol,
            status="NEW,PARTIALLY_FILLED",
            page=1,
            size=1000
        )
        
        orders_response = await order_service.list_orders(
            db=db,
            user_id=current_user.id,
            filter_params=filter_params
        )
        
        cancelled_count = 0
        failed_count = 0
        
        for order in orders_response.orders:
            try:
                cancel_data = OrderCancel(reason="批量取消")
                await order_service.cancel_order(
                    db=db,
                    user_id=current_user.id,
                    order_id=order.id,
                    cancel_data=cancel_data,
                    balance_service=balance_service
                )
                cancelled_count += 1
            except Exception as e:
                logger.warning(f"取消订单失败: order_id={order.id}, error={str(e)}")
                failed_count += 1
        
        logger.info(f"批量取消订单完成: cancelled={cancelled_count}, failed={failed_count}")
        
        return {
            "message": "批量取消订单完成",
            "cancelled_count": cancelled_count,
            "failed_count": failed_count,
            "total_count": cancelled_count + failed_count
        }
        
    except Exception as e:
        logger.error(f"批量取消订单异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量取消订单失败"
        )