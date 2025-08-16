#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测管理API路由

提供回测任务的创建、执行、查询和管理等API接口。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.strategy import (
    BacktestCreate, BacktestResponse, BacktestDetailResponse,
    BacktestListResponse, BacktestQueryParams
)
from ...services.backtest_service import BacktestService
from ...models.strategy import BacktestStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("/", response_model=BacktestResponse, status_code=201)
async def create_backtest(
    backtest_data: BacktestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    创建回测任务
    
    Args:
        backtest_data: 回测创建数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        BacktestResponse: 创建的回测信息
    """
    try:
        service = BacktestService(db)
        backtest = service.create_backtest(backtest_data, current_user["id"])
        
        logger.info(f"用户 {current_user['id']} 创建回测任务: {backtest.id} - {backtest.name}")
        return backtest
        
    except ValueError as e:
        logger.warning(f"创建回测任务失败 - 参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建回测任务失败: {e}")
        raise HTTPException(status_code=500, detail="创建回测任务失败")


@router.get("/", response_model=BacktestListResponse)
async def list_backtests(
    strategy_id: Optional[int] = Query(None, description="策略ID过滤"),
    status: Optional[BacktestStatus] = Query(None, description="回测状态过滤"),
    start_date: Optional[datetime] = Query(None, description="创建开始日期"),
    end_date: Optional[datetime] = Query(None, description="创建结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    sort_by: Optional[str] = Query("created_at", description="排序字段"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取回测列表
    
    Args:
        strategy_id: 策略ID过滤
        status: 回测状态过滤
        start_date: 创建开始日期
        end_date: 创建结束日期
        page: 页码
        size: 每页大小
        sort_by: 排序字段
        sort_order: 排序方向
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        BacktestListResponse: 回测列表响应
    """
    try:
        params = BacktestQueryParams(
            strategy_id=strategy_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        service = BacktestService(db)
        result = service.list_backtests(params, current_user["id"])
        
        return result
        
    except Exception as e:
        logger.error(f"获取回测列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取回测列表失败")


@router.get("/{backtest_id}", response_model=BacktestDetailResponse)
async def get_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取回测详情
    
    Args:
        backtest_id: 回测ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        BacktestDetailResponse: 回测详情
    """
    try:
        service = BacktestService(db)
        backtest = service.get_backtest(backtest_id, current_user["id"])
        
        if not backtest:
            raise HTTPException(status_code=404, detail="回测任务不存在")
        
        return backtest
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取回测详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取回测详情失败")


@router.post("/{backtest_id}/run", status_code=200)
async def run_backtest(
    backtest_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    执行回测任务
    
    Args:
        backtest_id: 回测ID
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 执行结果
    """
    try:
        service = BacktestService(db)
        success = await service.run_backtest(backtest_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="回测任务不存在或无法执行")
        
        logger.info(f"用户 {current_user['id']} 启动回测任务: {backtest_id}")
        return {"message": "回测任务启动成功", "backtest_id": backtest_id}
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"执行回测任务失败 - 参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"执行回测任务失败: {e}")
        raise HTTPException(status_code=500, detail="执行回测任务失败")


@router.post("/{backtest_id}/cancel", status_code=200)
async def cancel_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    取消回测任务
    
    Args:
        backtest_id: 回测ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 取消结果
    """
    try:
        service = BacktestService(db)
        success = service.cancel_backtest(backtest_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="回测任务不存在或无法取消")
        
        logger.info(f"用户 {current_user['id']} 取消回测任务: {backtest_id}")
        return {"message": "回测任务取消成功", "backtest_id": backtest_id}
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"取消回测任务失败 - 参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"取消回测任务失败: {e}")
        raise HTTPException(status_code=500, detail="取消回测任务失败")


@router.get("/{backtest_id}/status", status_code=200)
async def get_backtest_status(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取回测任务状态
    
    Args:
        backtest_id: 回测ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 回测状态信息
    """
    try:
        service = BacktestService(db)
        backtest = service.get_backtest(backtest_id, current_user["id"])
        
        if not backtest:
            raise HTTPException(status_code=404, detail="回测任务不存在")
        
        # 计算进度信息
        progress_info = {}
        if backtest.status == BacktestStatus.RUNNING:
            # 这里可以添加实际的进度计算逻辑
            progress_info = {
                "estimated_completion": None,
                "progress_percentage": None,
                "current_step": "执行中"
            }
        
        return {
            "backtest_id": backtest_id,
            "status": backtest.status,
            "started_at": backtest.started_at.isoformat() if backtest.started_at else None,
            "completed_at": backtest.completed_at.isoformat() if backtest.completed_at else None,
            "execution_time": backtest.execution_time,
            "error_message": backtest.error_message,
            "progress_info": progress_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取回测状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取回测状态失败")


@router.get("/{backtest_id}/results", status_code=200)
async def get_backtest_results(
    backtest_id: int,
    include_trades: bool = Query(True, description="是否包含交易记录"),
    include_equity_curve: bool = Query(True, description="是否包含资金曲线"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取回测结果
    
    Args:
        backtest_id: 回测ID
        include_trades: 是否包含交易记录
        include_equity_curve: 是否包含资金曲线
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 回测结果
    """
    try:
        service = BacktestService(db)
        backtest = service.get_backtest(backtest_id, current_user["id"])
        
        if not backtest:
            raise HTTPException(status_code=404, detail="回测任务不存在")
        
        if backtest.status != BacktestStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="回测任务尚未完成")
        
        # 构建结果数据
        results = {
            "backtest_id": backtest_id,
            "strategy_id": backtest.strategy_id,
            "performance_metrics": backtest.performance_metrics,
            "final_capital": backtest.final_capital,
            "total_return": backtest.total_return,
            "annual_return": backtest.annual_return,
            "max_drawdown": backtest.max_drawdown,
            "sharpe_ratio": backtest.sharpe_ratio,
            "sortino_ratio": backtest.sortino_ratio,
            "calmar_ratio": backtest.calmar_ratio,
            "total_trades": backtest.total_trades,
            "winning_trades": backtest.winning_trades,
            "losing_trades": backtest.losing_trades,
            "win_rate": backtest.win_rate,
            "avg_win": backtest.avg_win,
            "avg_loss": backtest.avg_loss,
            "profit_factor": backtest.profit_factor
        }
        
        # 可选包含交易记录
        if include_trades and backtest.trades_data:
            results["trades"] = backtest.trades_data
        
        # 可选包含资金曲线
        if include_equity_curve and backtest.equity_curve:
            results["equity_curve"] = backtest.equity_curve
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取回测结果失败: {e}")
        raise HTTPException(status_code=500, detail="获取回测结果失败")


@router.get("/{backtest_id}/report", status_code=200)
async def get_backtest_report(
    backtest_id: int,
    format: str = Query("json", regex="^(json|html|pdf)$", description="报告格式"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取回测报告
    
    Args:
        backtest_id: 回测ID
        format: 报告格式
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 回测报告
    """
    try:
        service = BacktestService(db)
        backtest = service.get_backtest(backtest_id, current_user["id"])
        
        if not backtest:
            raise HTTPException(status_code=404, detail="回测任务不存在")
        
        if backtest.status != BacktestStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="回测任务尚未完成")
        
        # 生成报告
        if format == "json":
            report = {
                "backtest_info": {
                    "id": backtest.id,
                    "name": backtest.name,
                    "strategy_id": backtest.strategy_id,
                    "start_date": backtest.start_date.isoformat(),
                    "end_date": backtest.end_date.isoformat(),
                    "initial_capital": backtest.initial_capital,
                    "final_capital": backtest.final_capital,
                    "execution_time": backtest.execution_time
                },
                "performance_summary": {
                    "total_return": backtest.total_return,
                    "annual_return": backtest.annual_return,
                    "max_drawdown": backtest.max_drawdown,
                    "sharpe_ratio": backtest.sharpe_ratio,
                    "sortino_ratio": backtest.sortino_ratio,
                    "calmar_ratio": backtest.calmar_ratio
                },
                "trading_summary": {
                    "total_trades": backtest.total_trades,
                    "winning_trades": backtest.winning_trades,
                    "losing_trades": backtest.losing_trades,
                    "win_rate": backtest.win_rate,
                    "avg_win": backtest.avg_win,
                    "avg_loss": backtest.avg_loss,
                    "profit_factor": backtest.profit_factor
                },
                "detailed_metrics": backtest.performance_metrics,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return report
        
        elif format == "html":
            # 这里可以生成HTML格式的报告
            return {"message": "HTML报告生成功能待实现"}
        
        elif format == "pdf":
            # 这里可以生成PDF格式的报告
            return {"message": "PDF报告生成功能待实现"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取回测报告失败: {e}")
        raise HTTPException(status_code=500, detail="获取回测报告失败")


@router.get("/strategy/{strategy_id}", response_model=BacktestListResponse)
async def list_strategy_backtests(
    strategy_id: int,
    status: Optional[BacktestStatus] = Query(None, description="回测状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定策略的回测列表
    
    Args:
        strategy_id: 策略ID
        status: 回测状态过滤
        page: 页码
        size: 每页大小
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        BacktestListResponse: 回测列表响应
    """
    try:
        params = BacktestQueryParams(
            strategy_id=strategy_id,
            status=status,
            page=page,
            size=size,
            sort_by="created_at",
            sort_order="desc"
        )
        
        service = BacktestService(db)
        result = service.list_backtests(params, current_user["id"])
        
        return result
        
    except Exception as e:
        logger.error(f"获取策略回测列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略回测列表失败")


@router.delete("/{backtest_id}", status_code=204)
async def delete_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    删除回测任务
    
    Args:
        backtest_id: 回测ID
        db: 数据库会话
        current_user: 当前用户
    """
    try:
        service = BacktestService(db)
        backtest = service.get_backtest(backtest_id, current_user["id"])
        
        if not backtest:
            raise HTTPException(status_code=404, detail="回测任务不存在")
        
        # 检查是否可以删除
        if backtest.status == BacktestStatus.RUNNING:
            raise HTTPException(status_code=400, detail="无法删除正在运行的回测任务")
        
        # 执行删除（这里需要在BacktestService中实现delete_backtest方法）
        # success = service.delete_backtest(backtest_id, current_user["id"])
        
        logger.info(f"用户 {current_user['id']} 删除回测任务: {backtest_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除回测任务失败: {e}")
        raise HTTPException(status_code=500, detail="删除回测任务失败")


@router.post("/compare", status_code=200)
async def compare_backtests(
    backtest_ids: List[int],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    比较多个回测结果
    
    Args:
        backtest_ids: 回测ID列表
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        dict: 比较结果
    """
    try:
        if len(backtest_ids) < 2:
            raise HTTPException(status_code=400, detail="至少需要2个回测进行比较")
        
        if len(backtest_ids) > 10:
            raise HTTPException(status_code=400, detail="最多支持比较10个回测")
        
        service = BacktestService(db)
        comparison_data = []
        
        for backtest_id in backtest_ids:
            backtest = service.get_backtest(backtest_id, current_user["id"])
            if not backtest:
                raise HTTPException(status_code=404, detail=f"回测任务 {backtest_id} 不存在")
            
            if backtest.status != BacktestStatus.COMPLETED:
                raise HTTPException(status_code=400, detail=f"回测任务 {backtest_id} 尚未完成")
            
            comparison_data.append({
                "backtest_id": backtest.id,
                "name": backtest.name,
                "strategy_id": backtest.strategy_id,
                "total_return": backtest.total_return,
                "annual_return": backtest.annual_return,
                "max_drawdown": backtest.max_drawdown,
                "sharpe_ratio": backtest.sharpe_ratio,
                "sortino_ratio": backtest.sortino_ratio,
                "calmar_ratio": backtest.calmar_ratio,
                "win_rate": backtest.win_rate,
                "profit_factor": backtest.profit_factor,
                "total_trades": backtest.total_trades
            })
        
        # 计算排名
        metrics = ["total_return", "annual_return", "sharpe_ratio", "sortino_ratio", "calmar_ratio"]
        rankings = {}
        
        for metric in metrics:
            sorted_data = sorted(comparison_data, key=lambda x: x.get(metric, 0) or 0, reverse=True)
            rankings[metric] = [item["backtest_id"] for item in sorted_data]
        
        return {
            "comparison_data": comparison_data,
            "rankings": rankings,
            "comparison_time": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"比较回测结果失败: {e}")
        raise HTTPException(status_code=500, detail="比较回测结果失败")