#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易记录API路由

提供交易记录相关的API接口
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user, require_trader_role
from app.core.redis import RedisManager
from app.services.trade_service import TradeService
from app.schemas.trade import (
    TradeCreate, TradeFilter, TradeResponse,
    TradeListResponse, TradeSummary, TradeStatistics
)
from app.schemas.user import UserResponse

logger = logging.getLogger("api.trades")

router = APIRouter(prefix="/trades", tags=["trades"])


# 依赖注入
async def get_trade_service() -> TradeService:
    """获取交易服务实例"""
    redis_manager = RedisManager()
    return TradeService(redis_manager)


@router.post("/", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(
    trade_data: TradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    trade_service: TradeService = Depends(get_trade_service)
):
    """
    创建交易记录
    
    - **trade_id**: 外部交易ID
    - **symbol**: 交易对符号
    - **side**: 交易方向 (BUY/SELL)
    - **quantity**: 交易数量
    - **price**: 交易价格
    - **fee**: 手续费
    - **order_id**: 关联订单ID（可选）
    """
    try:
        logger.info(f"创建交易记录请求: user_id={current_user.id}, trade_id={trade_data.trade_id}")
        
        trade = await trade_service.create_trade(
            db=db,
            user_id=current_user.id,
            trade_data=trade_data
        )
        
        logger.info(f"交易记录创建成功: trade_id={trade.id}")
        return trade
        
    except ValueError as e:
        logger.warning(f"创建交易记录失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建交易记录异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建交易记录失败"
        )


@router.get("/", response_model=TradeListResponse)
async def list_trades(
    symbol: str = Query(None, description="交易对符号"),
    base_asset: str = Query(None, description="基础资产"),
    quote_asset: str = Query(None, description="计价资产"),
    trade_type: str = Query(None, description="交易类型"),
    side: str = Query(None, description="交易方向"),
    order_id: int = Query(None, description="关联订单ID"),
    strategy_id: str = Query(None, description="策略ID"),
    strategy_name: str = Query(None, description="策略名称"),
    market_maker: bool = Query(None, description="是否为做市商"),
    liquidity_type: str = Query(None, description="流动性类型"),
    min_quantity: float = Query(None, description="最小数量"),
    max_quantity: float = Query(None, description="最大数量"),
    min_price: float = Query(None, description="最小价格"),
    max_price: float = Query(None, description="最大价格"),
    min_value: float = Query(None, description="最小价值"),
    max_value: float = Query(None, description="最大价值"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    sort_by: str = Query("trade_time", description="排序字段"),
    sort_desc: bool = Query(True, description="是否降序"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    trade_service: TradeService = Depends(get_trade_service)
):
    """
    获取交易记录列表
    
    支持多种过滤条件和分页
    """
    try:
        filter_params = TradeFilter(
            symbol=symbol,
            base_asset=base_asset,
            quote_asset=quote_asset,
            trade_type=trade_type,
            side=side,
            order_id=order_id,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            market_maker=market_maker,
            liquidity_type=liquidity_type,
            min_quantity=min_quantity,
            max_quantity=max_quantity,
            min_price=min_price,
            max_price=max_price,
            min_value=min_value,
            max_value=max_value,
            start_time=start_time,
            end_time=end_time,
            sort_by=sort_by,
            sort_desc=sort_desc,
            page=page,
            size=size
        )
        
        trades = await trade_service.list_trades(
            db=db,
            user_id=current_user.id,
            filter_params=filter_params
        )
        
        return trades
        
    except Exception as e:
        logger.error(f"获取交易记录列表异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取交易记录列表失败"
        )


@router.get("/summary", response_model=TradeSummary)
async def get_trade_summary(
    symbol: str = Query(None, description="交易对符号"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    trade_service: TradeService = Depends(get_trade_service)
):
    """
    获取交易摘要统计
    
    - **symbol**: 交易对符号（可选）
    - **days**: 统计天数，默认30天
    """
    try:
        summary = await trade_service.get_trade_summary(
            db=db,
            user_id=current_user.id,
            symbol=symbol,
            days=days
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"获取交易摘要异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取交易摘要失败"
        )


@router.get("/statistics", response_model=TradeStatistics)
async def get_trade_statistics(
    symbol: str = Query(None, description="交易对符号"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    trade_service: TradeService = Depends(get_trade_service)
):
    """
    获取交易统计数据
    
    - **symbol**: 交易对符号（可选）
    - **days**: 统计天数，默认30天
    """
    try:
        statistics = await trade_service.get_trade_statistics(
            db=db,
            user_id=current_user.id,
            symbol=symbol,
            days=days
        )
        
        return statistics
        
    except Exception as e:
        logger.error(f"获取交易统计异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取交易统计失败"
        )


@router.get("/by-order/{order_id}", response_model=List[TradeResponse])
async def get_trades_by_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    trade_service: TradeService = Depends(get_trade_service)
):
    """
    获取订单相关的交易记录
    
    - **order_id**: 订单ID
    """
    try:
        trades = await trade_service.get_trades_by_order(
            db=db,
            user_id=current_user.id,
            order_id=order_id
        )
        
        return trades
        
    except Exception as e:
        logger.error(f"获取订单交易记录异常: user_id={current_user.id}, order_id={order_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单交易记录失败"
        )


@router.get("/by-trade-id/{trade_id}", response_model=TradeResponse)
async def get_trade_by_trade_id(
    trade_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    trade_service: TradeService = Depends(get_trade_service)
):
    """
    根据外部交易ID获取交易记录
    
    - **trade_id**: 外部交易ID
    """
    try:
        trade = await trade_service.get_trade_by_trade_id(
            db=db,
            user_id=current_user.id,
            trade_id=trade_id
        )
        
        if not trade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易记录不存在"
            )
        
        return trade
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易记录异常: user_id={current_user.id}, trade_id={trade_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取交易记录失败"
        )


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    trade_service: TradeService = Depends(get_trade_service)
):
    """
    获取交易记录详情
    
    - **trade_id**: 交易记录ID
    """
    try:
        trade = await trade_service.get_trade(
            db=db,
            user_id=current_user.id,
            trade_id=trade_id
        )
        
        if not trade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易记录不存在"
            )
        
        return trade
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易记录详情异常: user_id={current_user.id}, trade_id={trade_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取交易记录详情失败"
        )