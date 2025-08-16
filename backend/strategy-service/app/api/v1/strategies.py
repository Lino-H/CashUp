#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略管理API路由

提供策略的CRUD操作、启动停止、性能查询等API接口。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.strategy import (
    StrategyCreate, StrategyUpdate, StrategyResponse, StrategyDetailResponse,
    StrategyListResponse, StrategyQueryParams, PerformanceRecordResponse
)
from ...services.strategy_service import StrategyService
from ...models.strategy import StrategyStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.post("/", response_model=StrategyResponse, status_code=201)
async def create_strategy(
    strategy_data: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    创建新策略
    
    Args:
        strategy_data: 策略创建数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        StrategyResponse: 创建的策略信息
    """
    try:
        service = StrategyService(db)
        strategy = service.create_strategy(strategy_data, current_user["id"])
        
        logger.info(f"用户 {current_user['id']} 创建策略: {strategy.id} - {strategy.name}")
        return strategy
        
    except ValueError as e:
        logger.warning(f"创建策略失败 - 参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(status_code=500, detail="创建策略失败")


@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    name: Optional[str] = Query(None, description="策略名称过滤"),
    strategy_type: Optional[str] = Query(None, description="策略类型过滤"),
    status: Optional[StrategyStatus] = Query(None, description="策略状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    sort_by: Optional[str] = Query("created_at", description="排序字段"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取策略列表
    
    Args:
        name: 策略名称过滤
        strategy_type: 策略类型过滤
        status: 策略状态过滤
        page: 页码
        size: 每页大小
        sort_by: 排序字段
        sort_order: 排序方向
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        StrategyListResponse: 策略列表响应
    """
    try:
        params = StrategyQueryParams(
            name=name,
            strategy_type=strategy_type,
            status=status,
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        service = StrategyService(db)
        result = service.list_strategies(params, current_user["id"])
        
        return result
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略列表失败")


@router.get("/{strategy_id}", response_model=StrategyDetailResponse)
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取策略详情
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        StrategyDetailResponse: 策略详情
    """
    try:
        service = StrategyService(db)
        strategy = service.get_strategy(strategy_id, current_user["id"])
        
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        return strategy
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略详情失败")


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_data: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    更新策略
    
    Args:
        strategy_id: 策略ID
        strategy_data: 策略更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        StrategyResponse: 更新后的策略信息
    """
    try:
        service = StrategyService(db)
        strategy = service.update_strategy(strategy_id, strategy_data, current_user["id"])
        
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        logger.info(f"用户 {current_user['id']} 更新策略: {strategy_id}")
        return strategy
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"更新策略失败 - 参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        raise HTTPException(status_code=500, detail="更新策略失败")


@router.delete("/{strategy_id}", status_code=204)
async def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    删除策略
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
        current_user: 当前用户
    """
    try:
        service = StrategyService(db)
        success = service.delete_strategy(strategy_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        logger.info(f"用户 {current_user['id']} 删除策略: {strategy_id}")
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"删除策略失败 - 参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(status_code=500, detail="删除策略失败")


@router.post("/{strategy_id}/start", status_code=200)
async def start_strategy(
    strategy_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    启动策略
    
    Args:
        strategy_id: 策略ID
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 启动结果
    """
    try:
        service = StrategyService(db)
        success = await service.start_strategy(strategy_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="策略不存在或无法启动")
        
        logger.info(f"用户 {current_user['id']} 启动策略: {strategy_id}")
        return {"message": "策略启动成功", "strategy_id": strategy_id}
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"启动策略失败 - 参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启动策略失败: {e}")
        raise HTTPException(status_code=500, detail="启动策略失败")


@router.post("/{strategy_id}/stop", status_code=200)
async def stop_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    停止策略
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 停止结果
    """
    try:
        service = StrategyService(db)
        success = service.stop_strategy(strategy_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="策略不存在或无法停止")
        
        logger.info(f"用户 {current_user['id']} 停止策略: {strategy_id}")
        return {"message": "策略停止成功", "strategy_id": strategy_id}
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"停止策略失败 - 参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"停止策略失败: {e}")
        raise HTTPException(status_code=500, detail="停止策略失败")


@router.get("/{strategy_id}/performance", response_model=List[PerformanceRecordResponse])
async def get_strategy_performance(
    strategy_id: int,
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(100, ge=1, le=1000, description="记录数量限制"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取策略性能记录
    
    Args:
        strategy_id: 策略ID
        start_date: 开始日期
        end_date: 结束日期
        limit: 记录数量限制
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        List[PerformanceRecordResponse]: 性能记录列表
    """
    try:
        service = StrategyService(db)
        
        # 验证策略是否存在且属于用户
        strategy = service.get_strategy(strategy_id, current_user["id"])
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 获取性能记录
        records = service.get_performance_records(
            strategy_id, start_date, end_date, limit
        )
        
        return records
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略性能记录失败: {e}")
        raise HTTPException(status_code=500, detail="获取性能记录失败")


@router.get("/{strategy_id}/status", status_code=200)
async def get_strategy_status(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取策略运行状态
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 策略状态信息
    """
    try:
        service = StrategyService(db)
        
        # 验证策略是否存在且属于用户
        strategy = service.get_strategy(strategy_id, current_user["id"])
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 获取详细状态
        status_info = service.get_strategy_status(strategy_id)
        
        return {
            "strategy_id": strategy_id,
            "status": strategy.status,
            "last_updated": strategy.updated_at.isoformat() if strategy.updated_at else None,
            "runtime_info": status_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略状态失败")


@router.post("/{strategy_id}/validate", status_code=200)
async def validate_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    验证策略配置
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 验证结果
    """
    try:
        service = StrategyService(db)
        
        # 验证策略是否存在且属于用户
        strategy = service.get_strategy(strategy_id, current_user["id"])
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 执行策略验证
        validation_result = service.validate_strategy_config(strategy_id)
        
        return {
            "strategy_id": strategy_id,
            "is_valid": validation_result["is_valid"],
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "validation_time": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证策略配置失败: {e}")
        raise HTTPException(status_code=500, detail="验证策略配置失败")


@router.get("/{strategy_id}/metrics", status_code=200)
async def get_strategy_metrics(
    strategy_id: int,
    period: str = Query("1d", regex="^(1h|4h|1d|1w|1m)$", description="统计周期"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取策略关键指标
    
    Args:
        strategy_id: 策略ID
        period: 统计周期
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 策略关键指标
    """
    try:
        service = StrategyService(db)
        
        # 验证策略是否存在且属于用户
        strategy = service.get_strategy(strategy_id, current_user["id"])
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        # 计算关键指标
        metrics = service.calculate_strategy_metrics(strategy_id, period)
        
        return {
            "strategy_id": strategy_id,
            "period": period,
            "metrics": metrics,
            "calculation_time": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略指标失败")


@router.post("/{strategy_id}/clone", response_model=StrategyResponse, status_code=201)
async def clone_strategy(
    strategy_id: int,
    name: str = Query(..., description="新策略名称"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    克隆策略
    
    Args:
        strategy_id: 源策略ID
        name: 新策略名称
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        StrategyResponse: 克隆的策略信息
    """
    try:
        service = StrategyService(db)
        
        # 验证源策略是否存在且属于用户
        source_strategy = service.get_strategy(strategy_id, current_user["id"])
        if not source_strategy:
            raise HTTPException(status_code=404, detail="源策略不存在")
        
        # 执行克隆
        cloned_strategy = service.clone_strategy(strategy_id, name, current_user["id"])
        
        logger.info(f"用户 {current_user['id']} 克隆策略: {strategy_id} -> {cloned_strategy.id}")
        return cloned_strategy
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"克隆策略失败 - 参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"克隆策略失败: {e}")
        raise HTTPException(status_code=500, detail="克隆策略失败")