#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 指标API端点

提供指标收集、查询和管理的API接口
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from ....core.database import get_db
from ....schemas.metrics import (
    MetricCreate,
    MetricUpdate,
    MetricResponse,
    MetricValueCreate,
    MetricValueResponse,
    MetricQueryRequest,
    MetricQueryResponse,
    MetricAlertCreate,
    MetricAlertUpdate,
    MetricAlertResponse
)
from ....services.metrics import MetricsService
from ....services.prometheus import PrometheusService
from ....core.exceptions import (
    MetricsCollectionError,
    DataStorageError,
    ConfigurationError
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[MetricResponse])
async def list_metrics(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    category: Optional[str] = Query(None, description="指标分类"),
    status: Optional[str] = Query(None, description="指标状态"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取指标列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        category: 指标分类过滤
        status: 指标状态过滤
        search: 搜索关键词
        db: 数据库会话
        
    Returns:
        List[MetricResponse]: 指标列表
    """
    try:
        metrics_service = MetricsService(db)
        metrics = await metrics_service.list_metrics(
            skip=skip,
            limit=limit,
            category=category,
            status=status,
            search=search
        )
        return metrics
    except Exception as e:
        logger.error(f"Failed to list metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.post("/", response_model=MetricResponse)
async def create_metric(
    metric: MetricCreate,
    db: Session = Depends(get_db)
):
    """
    创建新指标
    
    Args:
        metric: 指标创建数据
        db: 数据库会话
        
    Returns:
        MetricResponse: 创建的指标
    """
    try:
        metrics_service = MetricsService(db)
        created_metric = await metrics_service.create_metric(metric)
        return created_metric
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create metric: {e}")
        raise HTTPException(status_code=500, detail="Failed to create metric")


@router.get("/{metric_id}", response_model=MetricResponse)
async def get_metric(
    metric_id: int = Path(..., description="指标ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定指标详情
    
    Args:
        metric_id: 指标ID
        db: 数据库会话
        
    Returns:
        MetricResponse: 指标详情
    """
    try:
        metrics_service = MetricsService(db)
        metric = await metrics_service.get_metric(metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail="Metric not found")
        return metric
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metric {metric_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metric")


@router.put("/{metric_id}", response_model=MetricResponse)
async def update_metric(
    metric_id: int = Path(..., description="指标ID"),
    metric_update: MetricUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新指标
    
    Args:
        metric_id: 指标ID
        metric_update: 指标更新数据
        db: 数据库会话
        
    Returns:
        MetricResponse: 更新后的指标
    """
    try:
        metrics_service = MetricsService(db)
        updated_metric = await metrics_service.update_metric(metric_id, metric_update)
        if not updated_metric:
            raise HTTPException(status_code=404, detail="Metric not found")
        return updated_metric
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update metric {metric_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update metric")


@router.delete("/{metric_id}")
async def delete_metric(
    metric_id: int = Path(..., description="指标ID"),
    db: Session = Depends(get_db)
):
    """
    删除指标
    
    Args:
        metric_id: 指标ID
        db: 数据库会话
        
    Returns:
        dict: 删除结果
    """
    try:
        metrics_service = MetricsService(db)
        success = await metrics_service.delete_metric(metric_id)
        if not success:
            raise HTTPException(status_code=404, detail="Metric not found")
        return {"message": "Metric deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete metric {metric_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete metric")


@router.post("/{metric_id}/values", response_model=MetricValueResponse)
async def add_metric_value(
    metric_id: int = Path(..., description="指标ID"),
    value: MetricValueCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    添加指标值
    
    Args:
        metric_id: 指标ID
        value: 指标值数据
        db: 数据库会话
        
    Returns:
        MetricValueResponse: 添加的指标值
    """
    try:
        metrics_service = MetricsService(db)
        metric_value = await metrics_service.add_metric_value(metric_id, value)
        return metric_value
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataStorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add metric value for metric {metric_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add metric value")


@router.post("/values/batch")
async def add_metric_values_batch(
    values: List[MetricValueCreate] = Body(...),
    db: Session = Depends(get_db)
):
    """
    批量添加指标值
    
    Args:
        values: 指标值列表
        db: 数据库会话
        
    Returns:
        dict: 批量添加结果
    """
    try:
        metrics_service = MetricsService(db)
        result = await metrics_service.add_metric_values_batch(values)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataStorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add metric values batch: {e}")
        raise HTTPException(status_code=500, detail="Failed to add metric values")


@router.get("/{metric_id}/values", response_model=List[MetricValueResponse])
async def get_metric_values(
    metric_id: int = Path(..., description="指标ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=10000, description="返回的记录数"),
    aggregation: Optional[str] = Query(None, description="聚合方式"),
    interval: Optional[str] = Query(None, description="聚合间隔"),
    db: Session = Depends(get_db)
):
    """
    获取指标值
    
    Args:
        metric_id: 指标ID
        start_time: 开始时间
        end_time: 结束时间
        limit: 返回的记录数
        aggregation: 聚合方式 (avg, sum, min, max, count)
        interval: 聚合间隔 (1m, 5m, 1h, 1d)
        db: 数据库会话
        
    Returns:
        List[MetricValueResponse]: 指标值列表
    """
    try:
        # 设置默认时间范围
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        metrics_service = MetricsService(db)
        values = await metrics_service.get_metric_values(
            metric_id=metric_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            aggregation=aggregation,
            interval=interval
        )
        return values
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get metric values for metric {metric_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metric values")


@router.post("/query", response_model=MetricQueryResponse)
async def query_metrics(
    query: MetricQueryRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    查询指标数据
    
    Args:
        query: 查询请求
        db: 数据库会话
        
    Returns:
        MetricQueryResponse: 查询结果
    """
    try:
        metrics_service = MetricsService(db)
        result = await metrics_service.query_metrics(query)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to query metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to query metrics")


@router.get("/{metric_id}/alerts", response_model=List[MetricAlertResponse])
async def get_metric_alerts(
    metric_id: int = Path(..., description="指标ID"),
    db: Session = Depends(get_db)
):
    """
    获取指标告警规则
    
    Args:
        metric_id: 指标ID
        db: 数据库会话
        
    Returns:
        List[MetricAlertResponse]: 告警规则列表
    """
    try:
        metrics_service = MetricsService(db)
        alerts = await metrics_service.get_metric_alerts(metric_id)
        return alerts
    except Exception as e:
        logger.error(f"Failed to get metric alerts for metric {metric_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metric alerts")


@router.post("/{metric_id}/alerts", response_model=MetricAlertResponse)
async def create_metric_alert(
    metric_id: int = Path(..., description="指标ID"),
    alert: MetricAlertCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    创建指标告警规则
    
    Args:
        metric_id: 指标ID
        alert: 告警规则数据
        db: 数据库会话
        
    Returns:
        MetricAlertResponse: 创建的告警规则
    """
    try:
        metrics_service = MetricsService(db)
        created_alert = await metrics_service.create_metric_alert(metric_id, alert)
        return created_alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create metric alert for metric {metric_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create metric alert")


@router.put("/alerts/{alert_id}", response_model=MetricAlertResponse)
async def update_metric_alert(
    alert_id: int = Path(..., description="告警ID"),
    alert_update: MetricAlertUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新指标告警规则
    
    Args:
        alert_id: 告警ID
        alert_update: 告警更新数据
        db: 数据库会话
        
    Returns:
        MetricAlertResponse: 更新后的告警规则
    """
    try:
        metrics_service = MetricsService(db)
        updated_alert = await metrics_service.update_metric_alert(alert_id, alert_update)
        if not updated_alert:
            raise HTTPException(status_code=404, detail="Metric alert not found")
        return updated_alert
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update metric alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update metric alert")


@router.delete("/alerts/{alert_id}")
async def delete_metric_alert(
    alert_id: int = Path(..., description="告警ID"),
    db: Session = Depends(get_db)
):
    """
    删除指标告警规则
    
    Args:
        alert_id: 告警ID
        db: 数据库会话
        
    Returns:
        dict: 删除结果
    """
    try:
        metrics_service = MetricsService(db)
        success = await metrics_service.delete_metric_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="Metric alert not found")
        return {"message": "Metric alert deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete metric alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete metric alert")


@router.get("/prometheus")
async def get_prometheus_metrics():
    """
    获取Prometheus格式的指标
    
    Returns:
        Response: Prometheus格式的指标数据
    """
    try:
        prometheus_service = PrometheusService()
        metrics_data = generate_latest()
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Prometheus metrics")


@router.post("/collect")
async def collect_metrics(
    force: bool = Query(False, description="是否强制收集"),
    db: Session = Depends(get_db)
):
    """
    手动触发指标收集
    
    Args:
        force: 是否强制收集
        db: 数据库会话
        
    Returns:
        dict: 收集结果
    """
    try:
        metrics_service = MetricsService(db)
        result = await metrics_service.collect_metrics(force=force)
        return result
    except MetricsCollectionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to collect metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect metrics")


@router.get("/statistics")
async def get_metrics_statistics(
    db: Session = Depends(get_db)
):
    """
    获取指标统计信息
    
    Args:
        db: 数据库会话
        
    Returns:
        dict: 统计信息
    """
    try:
        metrics_service = MetricsService(db)
        statistics = await metrics_service.get_metrics_statistics()
        return statistics
    except Exception as e:
        logger.error(f"Failed to get metrics statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics statistics")


@router.post("/cleanup")
async def cleanup_old_metrics(
    days: int = Query(30, ge=1, le=365, description="保留天数"),
    db: Session = Depends(get_db)
):
    """
    清理过期指标数据
    
    Args:
        days: 保留天数
        db: 数据库会话
        
    Returns:
        dict: 清理结果
    """
    try:
        metrics_service = MetricsService(db)
        result = await metrics_service.cleanup_old_metrics(days)
        return result
    except Exception as e:
        logger.error(f"Failed to cleanup old metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup old metrics")