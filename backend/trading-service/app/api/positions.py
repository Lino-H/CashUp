#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 持仓API路由

提供持仓相关的API接口
"""

import logging
from typing import Dict, Any
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user, require_trader_role
from app.core.redis import RedisManager
from app.services.position_service import PositionService
from app.schemas.position import (
    PositionCreate, PositionUpdate, PositionFilter, PositionResponse,
    PositionListResponse, PositionSummary, PositionRisk,
    PositionStatistics, PositionCloseRequest, PositionCloseResponse
)
from app.schemas.user import UserResponse

logger = logging.getLogger("api.positions")

router = APIRouter(prefix="/positions", tags=["positions"])


# 依赖注入
async def get_position_service() -> PositionService:
    """获取持仓服务实例"""
    redis_manager = RedisManager()
    return PositionService(redis_manager)


@router.post("/", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    position_data: PositionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    position_service: PositionService = Depends(get_position_service)
):
    """
    创建持仓记录
    
    - **symbol**: 交易对符号
    - **position_side**: 持仓方向 (LONG/SHORT)
    - **position_type**: 持仓类型 (SPOT/MARGIN/FUTURES)
    - **quantity**: 持仓数量
    - **avg_cost_price**: 平均成本价格
    """
    try:
        logger.info(f"创建持仓请求: user_id={current_user.id}, symbol={position_data.symbol}")
        
        position = await position_service.create_position(
            db=db,
            user_id=current_user.id,
            position_data=position_data
        )
        
        logger.info(f"持仓创建成功: position_id={position.id}")
        return position
        
    except ValueError as e:
        logger.warning(f"创建持仓失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建持仓异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建持仓失败"
        )


@router.get("/", response_model=PositionListResponse)
async def list_positions(
    symbol: str = Query(None, description="交易对符号"),
    base_asset: str = Query(None, description="基础资产"),
    quote_asset: str = Query(None, description="计价资产"),
    position_side: str = Query(None, description="持仓方向"),
    position_type: str = Query(None, description="持仓类型"),
    strategy_id: str = Query(None, description="策略ID"),
    strategy_name: str = Query(None, description="策略名称"),
    is_active: bool = Query(None, description="是否活跃"),
    has_quantity: bool = Query(None, description="是否有持仓数量"),
    min_quantity: float = Query(None, description="最小数量"),
    max_quantity: float = Query(None, description="最大数量"),
    min_value: float = Query(None, description="最小价值"),
    max_value: float = Query(None, description="最大价值"),
    min_pnl: float = Query(None, description="最小盈亏"),
    max_pnl: float = Query(None, description="最大盈亏"),
    profit_only: bool = Query(None, description="仅盈利持仓"),
    loss_only: bool = Query(None, description="仅亏损持仓"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    position_service: PositionService = Depends(get_position_service)
):
    """
    获取持仓列表
    
    支持多种过滤条件和分页
    """
    try:
        filter_params = PositionFilter(
            symbol=symbol,
            base_asset=base_asset,
            quote_asset=quote_asset,
            position_side=position_side,
            position_type=position_type,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            is_active=is_active,
            has_quantity=has_quantity,
            min_quantity=min_quantity,
            max_quantity=max_quantity,
            min_value=min_value,
            max_value=max_value,
            min_pnl=min_pnl,
            max_pnl=max_pnl,
            profit_only=profit_only,
            loss_only=loss_only,
            page=page,
            size=size
        )
        
        positions = await position_service.list_positions(
            db=db,
            user_id=current_user.id,
            filter_params=filter_params
        )
        
        return positions
        
    except Exception as e:
        logger.error(f"获取持仓列表异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取持仓列表失败"
        )


@router.get("/summary", response_model=PositionSummary)
async def get_position_summary(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    position_service: PositionService = Depends(get_position_service)
):
    """
    获取持仓摘要统计
    """
    try:
        summary = await position_service.get_position_summary(
            db=db,
            user_id=current_user.id
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"获取持仓摘要异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取持仓摘要失败"
        )


@router.get("/by-symbol/{symbol}", response_model=PositionResponse)
async def get_position_by_symbol(
    symbol: str,
    position_type: str = Query("SPOT", description="持仓类型"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    position_service: PositionService = Depends(get_position_service)
):
    """
    根据交易对获取持仓信息
    
    - **symbol**: 交易对符号
    - **position_type**: 持仓类型，默认SPOT
    """
    try:
        from app.models.position import PositionType
        
        # 转换持仓类型
        try:
            pos_type = PositionType(position_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的持仓类型: {position_type}"
            )
        
        position = await position_service.get_position_by_symbol(
            db=db,
            user_id=current_user.id,
            symbol=symbol,
            position_type=pos_type
        )
        
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="持仓不存在"
            )
        
        return position
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取持仓异常: user_id={current_user.id}, symbol={symbol}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取持仓失败"
        )


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    position_service: PositionService = Depends(get_position_service)
):
    """
    获取持仓详情
    
    - **position_id**: 持仓ID
    """
    try:
        position = await position_service.get_position(
            db=db,
            user_id=current_user.id,
            position_id=position_id
        )
        
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="持仓不存在"
            )
        
        return position
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取持仓详情异常: user_id={current_user.id}, position_id={position_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取持仓详情失败"
        )


@router.get("/{position_id}/risk", response_model=PositionRisk)
async def get_position_risk(
    position_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    position_service: PositionService = Depends(get_position_service)
):
    """
    获取持仓风险信息
    
    - **position_id**: 持仓ID
    """
    try:
        risk = await position_service.get_position_risk(
            db=db,
            user_id=current_user.id,
            position_id=position_id
        )
        
        return risk
        
    except ValueError as e:
        logger.warning(f"获取持仓风险失败: user_id={current_user.id}, position_id={position_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取持仓风险异常: user_id={current_user.id}, position_id={position_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取持仓风险失败"
        )


@router.post("/{position_id}/close", response_model=PositionCloseResponse)
async def close_position(
    position_id: int,
    close_request: PositionCloseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    position_service: PositionService = Depends(get_position_service)
):
    """
    平仓
    
    - **position_id**: 持仓ID
    - **quantity**: 平仓数量（可选，默认全部平仓）
    - **price**: 平仓价格（可选，默认使用最新价格）
    - **reason**: 平仓原因
    """
    try:
        logger.info(f"平仓请求: user_id={current_user.id}, position_id={position_id}")
        
        # 获取持仓信息以设置symbol和position_type
        position = await position_service.get_position(
            db=db,
            user_id=current_user.id,
            position_id=position_id
        )
        
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="持仓不存在"
            )
        
        # 设置close_request的symbol和position_type
        close_request.symbol = position.symbol
        close_request.position_type = position.position_type
        
        result = await position_service.close_position(
            db=db,
            user_id=current_user.id,
            close_request=close_request
        )
        
        logger.info(f"平仓成功: position_id={position_id}, close_id={result.close_id}")
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"平仓失败: user_id={current_user.id}, position_id={position_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"平仓异常: user_id={current_user.id}, position_id={position_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="平仓失败"
        )


@router.post("/update-prices", response_model=dict)
async def update_position_prices(
    price_data: Dict[str, Dict[str, float]] = Body(..., description="价格数据"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    position_service: PositionService = Depends(get_position_service)
):
    """
    批量更新持仓价格
    
    - **price_data**: 价格数据，格式: {"BTCUSDT": {"last_price": 50000, "mark_price": 50010}}
    """
    try:
        logger.info(f"更新持仓价格请求: user_id={current_user.id}, symbols={len(price_data)}")
        
        # 转换价格数据为Decimal
        decimal_price_data = {}
        for symbol, prices in price_data.items():
            decimal_price_data[symbol] = {
                key: Decimal(str(value)) for key, value in prices.items()
            }
        
        await position_service.update_position_prices(
            db=db,
            price_data=decimal_price_data
        )
        
        logger.info(f"持仓价格更新成功: symbols={len(price_data)}")
        
        return {
            "message": "持仓价格更新成功",
            "updated_symbols": len(price_data)
        }
        
    except Exception as e:
        logger.error(f"更新持仓价格异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新持仓价格失败"
        )