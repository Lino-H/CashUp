#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 余额API路由

提供余额相关的API接口
"""

import logging
from typing import Dict, Any
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user, require_trader_role
from app.core.redis import RedisManager
from app.services.balance_service import BalanceService
from app.schemas.balance import (
    BalanceCreate, BalanceUpdate, BalanceFilter, BalanceResponse,
    BalanceListResponse, BalanceSummary, BalanceOperation,
    BalanceOperationResponse, BalanceTransfer, BalanceTransferResponse
)
from app.schemas.user import UserResponse

logger = logging.getLogger("api.balances")

router = APIRouter(prefix="/balances", tags=["balances"])


# 依赖注入
async def get_balance_service() -> BalanceService:
    """获取余额服务实例"""
    redis_manager = RedisManager()
    return BalanceService(redis_manager)


@router.post("/", response_model=BalanceResponse, status_code=status.HTTP_201_CREATED)
async def create_balance(
    balance_data: BalanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    创建余额记录
    
    - **asset**: 资产符号
    - **balance_type**: 余额类型 (SPOT/MARGIN/FUTURES/SAVINGS)
    - **total_balance**: 总余额
    - **available_balance**: 可用余额
    - **frozen_balance**: 冻结余额
    """
    try:
        logger.info(f"创建余额请求: user_id={current_user.id}, asset={balance_data.asset}")
        
        balance = await balance_service.create_balance(
            db=db,
            user_id=current_user.id,
            balance_data=balance_data
        )
        
        logger.info(f"余额创建成功: balance_id={balance.id}")
        return balance
        
    except ValueError as e:
        logger.warning(f"创建余额失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建余额异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建余额失败"
        )


@router.get("/", response_model=BalanceListResponse)
async def list_balances(
    asset: str = Query(None, description="资产符号"),
    balance_type: str = Query(None, description="余额类型"),
    is_active: bool = Query(None, description="是否活跃"),
    is_locked: bool = Query(None, description="是否锁定"),
    min_balance: float = Query(None, description="最小余额"),
    max_balance: float = Query(None, description="最大余额"),
    min_value: float = Query(None, description="最小价值"),
    max_value: float = Query(None, description="最大价值"),
    has_frozen: bool = Query(None, description="是否有冻结余额"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    获取余额列表
    
    支持多种过滤条件和分页
    """
    try:
        filter_params = BalanceFilter(
            asset=asset,
            balance_type=balance_type,
            is_active=is_active,
            is_locked=is_locked,
            min_balance=min_balance,
            max_balance=max_balance,
            min_value=min_value,
            max_value=max_value,
            has_frozen=has_frozen,
            page=page,
            size=size
        )
        
        balances = await balance_service.list_balances(
            db=db,
            user_id=current_user.id,
            filter_params=filter_params
        )
        
        return balances
        
    except Exception as e:
        logger.error(f"获取余额列表异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取余额列表失败"
        )


@router.get("/summary", response_model=BalanceSummary)
async def get_balance_summary(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    获取余额摘要统计
    """
    try:
        summary = await balance_service.get_balance_summary(
            db=db,
            user_id=current_user.id
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"获取余额摘要异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取余额摘要失败"
        )


@router.get("/{asset}", response_model=BalanceResponse)
async def get_balance(
    asset: str,
    balance_type: str = Query("SPOT", description="余额类型"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    获取指定资产的余额信息
    
    - **asset**: 资产符号
    - **balance_type**: 余额类型，默认SPOT
    """
    try:
        from app.models.balance import BalanceType
        
        # 转换余额类型
        try:
            bal_type = BalanceType(balance_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的余额类型: {balance_type}"
            )
        
        balance = await balance_service.get_balance(
            db=db,
            user_id=current_user.id,
            asset=asset,
            balance_type=bal_type
        )
        
        if not balance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="余额记录不存在"
            )
        
        return balance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取余额异常: user_id={current_user.id}, asset={asset}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取余额失败"
        )


@router.post("/freeze", response_model=BalanceOperationResponse)
async def freeze_balance(
    operation: BalanceOperation,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    冻结余额
    
    - **asset**: 资产符号
    - **amount**: 冻结金额
    - **balance_type**: 余额类型，默认SPOT
    - **reason**: 冻结原因
    """
    try:
        from app.models.balance import BalanceType
        
        logger.info(f"冻结余额请求: user_id={current_user.id}, asset={operation.asset}, amount={operation.amount}")
        
        # 转换余额类型
        balance_type = BalanceType.SPOT
        if operation.balance_type:
            try:
                balance_type = BalanceType(operation.balance_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的余额类型: {operation.balance_type}"
                )
        
        result = await balance_service.freeze_balance(
            db=db,
            user_id=current_user.id,
            asset=operation.asset,
            amount=Decimal(str(operation.amount)),
            balance_type=balance_type
        )
        
        logger.info(f"余额冻结成功: user_id={current_user.id}, asset={operation.asset}")
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"冻结余额失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"冻结余额异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="冻结余额失败"
        )


@router.post("/unfreeze", response_model=BalanceOperationResponse)
async def unfreeze_balance(
    operation: BalanceOperation,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    解冻余额
    
    - **asset**: 资产符号
    - **amount**: 解冻金额
    - **balance_type**: 余额类型，默认SPOT
    - **reason**: 解冻原因
    """
    try:
        from app.models.balance import BalanceType
        
        logger.info(f"解冻余额请求: user_id={current_user.id}, asset={operation.asset}, amount={operation.amount}")
        
        # 转换余额类型
        balance_type = BalanceType.SPOT
        if operation.balance_type:
            try:
                balance_type = BalanceType(operation.balance_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的余额类型: {operation.balance_type}"
                )
        
        result = await balance_service.unfreeze_balance(
            db=db,
            user_id=current_user.id,
            asset=operation.asset,
            amount=Decimal(str(operation.amount)),
            balance_type=balance_type
        )
        
        logger.info(f"余额解冻成功: user_id={current_user.id}, asset={operation.asset}")
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"解冻余额失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"解冻余额异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="解冻余额失败"
        )


@router.post("/add", response_model=BalanceOperationResponse)
async def add_balance(
    operation: BalanceOperation,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    增加余额
    
    - **asset**: 资产符号
    - **amount**: 增加金额
    - **balance_type**: 余额类型，默认SPOT
    - **reason**: 增加原因
    """
    try:
        from app.models.balance import BalanceType
        
        logger.info(f"增加余额请求: user_id={current_user.id}, asset={operation.asset}, amount={operation.amount}")
        
        # 转换余额类型
        balance_type = BalanceType.SPOT
        if operation.balance_type:
            try:
                balance_type = BalanceType(operation.balance_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的余额类型: {operation.balance_type}"
                )
        
        result = await balance_service.add_balance(
            db=db,
            user_id=current_user.id,
            asset=operation.asset,
            amount=Decimal(str(operation.amount)),
            balance_type=balance_type
        )
        
        logger.info(f"余额增加成功: user_id={current_user.id}, asset={operation.asset}")
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"增加余额失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"增加余额异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="增加余额失败"
        )


@router.post("/subtract", response_model=BalanceOperationResponse)
async def subtract_balance(
    operation: BalanceOperation,
    from_available: bool = Query(True, description="是否从可用余额扣除"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    减少余额
    
    - **asset**: 资产符号
    - **amount**: 减少金额
    - **balance_type**: 余额类型，默认SPOT
    - **from_available**: 是否从可用余额扣除
    - **reason**: 减少原因
    """
    try:
        from app.models.balance import BalanceType
        
        logger.info(f"减少余额请求: user_id={current_user.id}, asset={operation.asset}, amount={operation.amount}")
        
        # 转换余额类型
        balance_type = BalanceType.SPOT
        if operation.balance_type:
            try:
                balance_type = BalanceType(operation.balance_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的余额类型: {operation.balance_type}"
                )
        
        result = await balance_service.subtract_balance(
            db=db,
            user_id=current_user.id,
            asset=operation.asset,
            amount=Decimal(str(operation.amount)),
            from_available=from_available,
            balance_type=balance_type
        )
        
        logger.info(f"余额减少成功: user_id={current_user.id}, asset={operation.asset}")
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"减少余额失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"减少余额异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="减少余额失败"
        )


@router.post("/transfer", response_model=BalanceTransferResponse)
async def transfer_balance(
    transfer_data: BalanceTransfer,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    余额转账
    
    - **asset**: 资产符号
    - **amount**: 转账金额
    - **from_balance_type**: 源余额类型
    - **to_balance_type**: 目标余额类型
    - **notes**: 转账备注
    """
    try:
        logger.info(f"余额转账请求: user_id={current_user.id}, asset={transfer_data.asset}, amount={transfer_data.amount}")
        
        result = await balance_service.transfer_balance(
            db=db,
            user_id=current_user.id,
            transfer_data=transfer_data
        )
        
        logger.info(f"余额转账成功: user_id={current_user.id}, transfer_id={result.transfer_id}")
        return result
        
    except ValueError as e:
        logger.warning(f"余额转账失败: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"余额转账异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="余额转账失败"
        )


@router.post("/update-market-values", response_model=dict)
async def update_market_values(
    price_data: Dict[str, Dict[str, float]] = Body(..., description="价格数据"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_trader_role),
    balance_service: BalanceService = Depends(get_balance_service)
):
    """
    批量更新市场价值
    
    - **price_data**: 价格数据，格式: {"BTC": {"usd": 50000, "btc": 1}}
    """
    try:
        logger.info(f"更新市场价值请求: user_id={current_user.id}, assets={len(price_data)}")
        
        # 转换价格数据为Decimal
        decimal_price_data = {}
        for asset, prices in price_data.items():
            decimal_price_data[asset] = {
                key: Decimal(str(value)) for key, value in prices.items()
            }
        
        await balance_service.update_market_values(
            db=db,
            price_data=decimal_price_data
        )
        
        logger.info(f"市场价值更新成功: assets={len(price_data)}")
        
        return {
            "message": "市场价值更新成功",
            "updated_assets": len(price_data)
        }
        
    except Exception as e:
        logger.error(f"更新市场价值异常: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新市场价值失败"
        )