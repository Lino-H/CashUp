#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 指标API路由

指标相关的API端点
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permissions
from app.core.logging import get_logger, audit_log
from app.schemas.metrics import (
    MetricCreate, MetricUpdate, MetricResponse, MetricListResponse,
    MetricValueCreate, MetricValueResponse, MetricValueListResponse,
    MetricValueBatchCreate, MetricAggregationResponse,
    MetricStatsResponse, MetricCollectionTrigger
)
from app.schemas.common import PaginationParams, TimeRangeParams
from app.services.metrics_service import MetricsService
from app.models.user import User

# 创建路由器
router = APIRouter()
logger = get_logger(__name__)

# 依赖注入
def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    """获取指标服务"""
    return MetricsService(db)


@router.get("/", response_model=MetricListResponse)
@require_permissions(["metrics:read"])
async def list_metrics(
    pagination: PaginationParams = Depends(),
    name: Optional[str] = Query(None, description="指标名称过滤"),
    metric_type: Optional[str] = Query(None, description="指标类型过滤"),
    tags: Optional[str] = Query(None, description="标签过滤（JSON格式）"),
    active_only: bool = Query(True, description="仅显示活跃指标"),
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """获取指标列表"""
    try:
        # 解析标签过滤
        tags_filter = None
        if tags:
            import json
            tags_filter = json.loads(tags)
        
        result = await service.get_metrics(
            skip=pagination.skip,
            limit=pagination.limit,
            name=name,
            metric_type=metric_type,
            tags=tags_filter,
            active_only=active_only
        )
        
        logger.info(
            f"Listed metrics",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'filters': {
                    'name': name,
                    'metric_type': metric_type,
                    'tags': tags_filter,
                    'active_only': active_only
                }
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取指标列表失败")


@router.post("/", response_model=MetricResponse, status_code=201)
@require_permissions(["metrics:write"])
@audit_log("create_metric", "metric")
async def create_metric(
    metric_data: MetricCreate,
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """创建新指标"""
    try:
        metric = await service.create_metric(metric_data)
        
        logger.info(
            f"Created metric: {metric.name}",
            extra={
                'user_id': current_user.id,
                'metric_id': metric.id,
                'metric_name': metric.name,
                'metric_type': metric.type
            }
        )
        
        return metric
        
    except ValueError as e:
        logger.warning(f"Invalid metric data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create metric: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建指标失败")


@router.get("/{metric_id}", response_model=MetricResponse)
@require_permissions(["metrics:read"])
async def get_metric(
    metric_id: int = Path(..., description="指标ID"),
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """获取指标详情"""
    try:
        metric = await service.get_metric(metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail="指标不存在")
        
        logger.debug(
            f"Retrieved metric: {metric.name}",
            extra={
                'user_id': current_user.id,
                'metric_id': metric_id
            }
        )
        
        return metric
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metric {metric_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取指标详情失败")


@router.put("/{metric_id}", response_model=MetricResponse)
@require_permissions(["metrics:write"])
@audit_log("update_metric", "metric")
async def update_metric(
    metric_id: int = Path(..., description="指标ID"),
    metric_data: MetricUpdate = None,
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """更新指标"""
    try:
        metric = await service.update_metric(metric_id, metric_data)
        if not metric:
            raise HTTPException(status_code=404, detail="指标不存在")
        
        logger.info(
            f"Updated metric: {metric.name}",
            extra={
                'user_id': current_user.id,
                'metric_id': metric_id,
                'metric_name': metric.name
            }
        )
        
        return metric
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid metric update data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update metric {metric_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新指标失败")


@router.delete("/{metric_id}", status_code=204)
@require_permissions(["metrics:delete"])
@audit_log("delete_metric", "metric")
async def delete_metric(
    metric_id: int = Path(..., description="指标ID"),
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """删除指标"""
    try:
        success = await service.delete_metric(metric_id)
        if not success:
            raise HTTPException(status_code=404, detail="指标不存在")
        
        logger.info(
            f"Deleted metric",
            extra={
                'user_id': current_user.id,
                'metric_id': metric_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete metric {metric_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除指标失败")


@router.post("/{metric_id}/values", response_model=MetricValueResponse, status_code=201)
@require_permissions(["metrics:write"])
async def add_metric_value(
    metric_id: int = Path(..., description="指标ID"),
    value_data: MetricValueCreate = None,
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """添加指标值"""
    try:
        value = await service.add_metric_value(metric_id, value_data)
        
        logger.debug(
            f"Added metric value",
            extra={
                'user_id': current_user.id,
                'metric_id': metric_id,
                'value': value_data.value
            }
        )
        
        return value
        
    except ValueError as e:
        logger.warning(f"Invalid metric value data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add metric value: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="添加指标值失败")


@router.post("/values/batch", status_code=201)
@require_permissions(["metrics:write"])
async def add_metric_values_batch(
    batch_data: MetricValueBatchCreate,
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """批量添加指标值"""
    try:
        await service.add_metric_values_batch(batch_data.values)
        
        logger.info(
            f"Added batch metric values",
            extra={
                'user_id': current_user.id,
                'count': len(batch_data.values)
            }
        )
        
        return {"message": f"成功添加 {len(batch_data.values)} 个指标值"}
        
    except ValueError as e:
        logger.warning(f"Invalid batch metric value data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add batch metric values: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="批量添加指标值失败")


@router.get("/{metric_id}/values", response_model=MetricValueListResponse)
@require_permissions(["metrics:read"])
async def get_metric_values(
    metric_id: int = Path(..., description="指标ID"),
    time_range: TimeRangeParams = Depends(),
    pagination: PaginationParams = Depends(),
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """获取指标值"""
    try:
        result = await service.get_metric_values(
            metric_id=metric_id,
            start_time=time_range.start_time,
            end_time=time_range.end_time,
            skip=pagination.skip,
            limit=pagination.limit
        )
        
        logger.debug(
            f"Retrieved metric values",
            extra={
                'user_id': current_user.id,
                'metric_id': metric_id,
                'count': len(result['items'])
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get metric values: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取指标值失败")


@router.get("/{metric_id}/aggregation", response_model=MetricAggregationResponse)
@require_permissions(["metrics:read"])
async def get_metric_aggregation(
    metric_id: int = Path(..., description="指标ID"),
    time_range: TimeRangeParams = Depends(),
    aggregation_type: str = Query("avg", description="聚合类型"),
    interval: Optional[str] = Query(None, description="时间间隔"),
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """获取指标聚合数据"""
    try:
        result = await service.get_metric_aggregation(
            metric_id=metric_id,
            start_time=time_range.start_time,
            end_time=time_range.end_time,
            aggregation_type=aggregation_type,
            interval=interval
        )
        
        logger.debug(
            f"Retrieved metric aggregation",
            extra={
                'user_id': current_user.id,
                'metric_id': metric_id,
                'aggregation_type': aggregation_type,
                'interval': interval
            }
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid aggregation parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get metric aggregation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取指标聚合数据失败")


@router.get("/prometheus", response_class=PlainTextResponse)
@require_permissions(["metrics:read"])
async def get_prometheus_metrics(
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """获取Prometheus格式的指标"""
    try:
        metrics_text = await service.get_prometheus_metrics()
        
        logger.debug(
            f"Retrieved Prometheus metrics",
            extra={
                'user_id': current_user.id,
                'format': 'prometheus'
            }
        )
        
        return metrics_text
        
    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取Prometheus指标失败")


@router.post("/collect", status_code=202)
@require_permissions(["metrics:write"])
@audit_log("trigger_metric_collection", "metrics")
async def trigger_metric_collection(
    collection_data: MetricCollectionTrigger,
    background_tasks: BackgroundTasks,
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """手动触发指标收集"""
    try:
        # 在后台任务中执行收集
        background_tasks.add_task(
            service.trigger_collection,
            collection_data.metric_names,
            collection_data.force
        )
        
        logger.info(
            f"Triggered metric collection",
            extra={
                'user_id': current_user.id,
                'metric_names': collection_data.metric_names,
                'force': collection_data.force
            }
        )
        
        return {"message": "指标收集已触发"}
        
    except Exception as e:
        logger.error(f"Failed to trigger metric collection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="触发指标收集失败")


@router.get("/stats", response_model=MetricStatsResponse)
@require_permissions(["metrics:read"])
async def get_metrics_stats(
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """获取指标统计信息"""
    try:
        stats = await service.get_metrics_stats()
        
        logger.debug(
            f"Retrieved metrics stats",
            extra={
                'user_id': current_user.id,
                'total_metrics': stats.total_metrics
            }
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get metrics stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取指标统计信息失败")


@router.delete("/cleanup", status_code=202)
@require_permissions(["metrics:admin"])
@audit_log("cleanup_metrics", "metrics")
async def cleanup_expired_data(
    days: int = Query(30, description="保留天数"),
    background_tasks: BackgroundTasks,
    service: MetricsService = Depends(get_metrics_service),
    current_user: User = Depends(get_current_user)
):
    """清理过期数据"""
    try:
        # 在后台任务中执行清理
        background_tasks.add_task(service.cleanup_expired_data, days)
        
        logger.info(
            f"Triggered metrics cleanup",
            extra={
                'user_id': current_user.id,
                'retention_days': days
            }
        )
        
        return {"message": f"已触发清理 {days} 天前的过期数据"}
        
    except Exception as e:
        logger.error(f"Failed to trigger metrics cleanup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="触发数据清理失败")