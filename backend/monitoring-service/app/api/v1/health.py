#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 健康检查API路由

健康检查相关的API端点
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permissions
from app.core.logging import get_logger, audit_log
from app.schemas.health import (
    HealthCheckCreate, HealthCheckUpdate, HealthCheckResponse, HealthCheckListResponse,
    HealthCheckExecuteRequest, HealthCheckBatchRequest, ServiceStatusResponse,
    ServiceStatusListResponse, ServiceStatusUpdate, SystemHealthResponse,
    HealthCheckHistoryResponse, HealthCheckHistoryListResponse,
    HealthCheckStatsResponse
)
from app.schemas.common import PaginationParams, TimeRangeParams
from app.services.health_service import HealthService
from app.models.user import User

# 创建路由器
router = APIRouter()
logger = get_logger(__name__)

# 依赖注入
def get_health_service(db: Session = Depends(get_db)) -> HealthService:
    """获取健康检查服务"""
    return HealthService(db)


# ==================== 健康检查配置管理 ====================

@router.get("/checks", response_model=HealthCheckListResponse)
@require_permissions(["health:read"])
async def list_health_checks(
    pagination: PaginationParams = Depends(),
    check_type: Optional[str] = Query(None, description="检查类型过滤"),
    enabled_only: bool = Query(True, description="仅显示启用的检查"),
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """获取健康检查配置列表"""
    try:
        result = await service.get_health_checks(
            skip=pagination.skip,
            limit=pagination.limit,
            check_type=check_type,
            enabled_only=enabled_only
        )
        
        logger.info(
            f"Listed health checks",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'filters': {
                    'check_type': check_type,
                    'enabled_only': enabled_only
                }
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list health checks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取健康检查列表失败")


@router.post("/checks", response_model=HealthCheckResponse, status_code=201)
@require_permissions(["health:write"])
@audit_log("create_health_check", "health_check")
async def create_health_check(
    check_data: HealthCheckCreate,
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """创建健康检查配置"""
    try:
        check = await service.create_health_check(check_data)
        
        logger.info(
            f"Created health check: {check.name}",
            extra={
                'user_id': current_user.id,
                'check_id': check.id,
                'check_name': check.name,
                'check_type': check.type
            }
        )
        
        return check
        
    except ValueError as e:
        logger.warning(f"Invalid health check data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create health check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建健康检查失败")


@router.get("/checks/{check_id}", response_model=HealthCheckResponse)
@require_permissions(["health:read"])
async def get_health_check(
    check_id: int = Path(..., description="检查ID"),
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """获取健康检查配置详情"""
    try:
        check = await service.get_health_check(check_id)
        if not check:
            raise HTTPException(status_code=404, detail="健康检查不存在")
        
        logger.debug(
            f"Retrieved health check: {check.name}",
            extra={
                'user_id': current_user.id,
                'check_id': check_id
            }
        )
        
        return check
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health check {check_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取健康检查详情失败")


@router.put("/checks/{check_id}", response_model=HealthCheckResponse)
@require_permissions(["health:write"])
@audit_log("update_health_check", "health_check")
async def update_health_check(
    check_id: int = Path(..., description="检查ID"),
    check_data: HealthCheckUpdate = None,
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """更新健康检查配置"""
    try:
        check = await service.update_health_check(check_id, check_data)
        if not check:
            raise HTTPException(status_code=404, detail="健康检查不存在")
        
        logger.info(
            f"Updated health check: {check.name}",
            extra={
                'user_id': current_user.id,
                'check_id': check_id,
                'check_name': check.name
            }
        )
        
        return check
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid health check update data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update health check {check_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新健康检查失败")


@router.delete("/checks/{check_id}", status_code=204)
@require_permissions(["health:delete"])
@audit_log("delete_health_check", "health_check")
async def delete_health_check(
    check_id: int = Path(..., description="检查ID"),
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """删除健康检查配置"""
    try:
        success = await service.delete_health_check(check_id)
        if not success:
            raise HTTPException(status_code=404, detail="健康检查不存在")
        
        logger.info(
            f"Deleted health check",
            extra={
                'user_id': current_user.id,
                'check_id': check_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete health check {check_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除健康检查失败")


# ==================== 健康检查执行 ====================

@router.post("/checks/{check_id}/execute")
@require_permissions(["health:execute"])
@audit_log("execute_health_check", "health_check")
async def execute_health_check(
    check_id: int = Path(..., description="检查ID"),
    execute_data: HealthCheckExecuteRequest = None,
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """手动执行健康检查"""
    try:
        result = await service.execute_health_check(
            check_id, 
            execute_data.force if execute_data else False
        )
        
        logger.info(
            f"Executed health check",
            extra={
                'user_id': current_user.id,
                'check_id': check_id,
                'result': result['status'],
                'force': execute_data.force if execute_data else False
            }
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid health check execution: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute health check {check_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="执行健康检查失败")


@router.post("/checks/execute/batch")
@require_permissions(["health:execute"])
@audit_log("batch_execute_health_checks", "health_checks")
async def batch_execute_health_checks(
    batch_data: HealthCheckBatchRequest,
    background_tasks: BackgroundTasks,
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """批量执行健康检查"""
    try:
        # 在后台任务中执行批量检查
        background_tasks.add_task(
            service.batch_execute_health_checks,
            batch_data.check_ids,
            batch_data.force
        )
        
        logger.info(
            f"Triggered batch health check execution",
            extra={
                'user_id': current_user.id,
                'check_count': len(batch_data.check_ids),
                'force': batch_data.force
            }
        )
        
        return {"message": f"已触发 {len(batch_data.check_ids)} 个健康检查"}
        
    except Exception as e:
        logger.error(f"Failed to trigger batch health check execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="批量执行健康检查失败")


# ==================== 服务状态管理 ====================

@router.get("/services", response_model=ServiceStatusListResponse)
@require_permissions(["health:read"])
async def list_service_status(
    pagination: PaginationParams = Depends(),
    status: Optional[str] = Query(None, description="状态过滤"),
    service_type: Optional[str] = Query(None, description="服务类型过滤"),
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """获取服务状态列表"""
    try:
        result = await service.get_service_status(
            skip=pagination.skip,
            limit=pagination.limit,
            status=status,
            service_type=service_type
        )
        
        logger.info(
            f"Listed service status",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'filters': {
                    'status': status,
                    'service_type': service_type
                }
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list service status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取服务状态列表失败")


@router.get("/services/{service_name}", response_model=ServiceStatusResponse)
@require_permissions(["health:read"])
async def get_service_status(
    service_name: str = Path(..., description="服务名称"),
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """获取特定服务状态"""
    try:
        status = await service.get_service_status_by_name(service_name)
        if not status:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        logger.debug(
            f"Retrieved service status: {service_name}",
            extra={
                'user_id': current_user.id,
                'service_name': service_name
            }
        )
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service status {service_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取服务状态失败")


@router.put("/services/{service_name}", response_model=ServiceStatusResponse)
@require_permissions(["health:write"])
@audit_log("update_service_status", "service_status")
async def update_service_status(
    service_name: str = Path(..., description="服务名称"),
    status_data: ServiceStatusUpdate = None,
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """更新服务状态"""
    try:
        status = await service.update_service_status(service_name, status_data)
        
        logger.info(
            f"Updated service status: {service_name}",
            extra={
                'user_id': current_user.id,
                'service_name': service_name,
                'new_status': status_data.status if status_data else None
            }
        )
        
        return status
        
    except ValueError as e:
        logger.warning(f"Invalid service status update data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update service status {service_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新服务状态失败")


@router.post("/services/refresh", status_code=202)
@require_permissions(["health:execute"])
@audit_log("refresh_service_status", "service_status")
async def refresh_service_status(
    background_tasks: BackgroundTasks,
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """刷新所有服务状态"""
    try:
        # 在后台任务中刷新状态
        background_tasks.add_task(service.refresh_all_service_status)
        
        logger.info(
            f"Triggered service status refresh",
            extra={
                'user_id': current_user.id
            }
        )
        
        return {"message": "已触发服务状态刷新"}
        
    except Exception as e:
        logger.error(f"Failed to trigger service status refresh: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="刷新服务状态失败")


# ==================== 系统健康状态 ====================

@router.get("/system", response_model=SystemHealthResponse)
@require_permissions(["health:read"])
async def get_system_health(
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统整体健康状态"""
    try:
        health = await service.get_system_health()
        
        logger.debug(
            f"Retrieved system health",
            extra={
                'user_id': current_user.id,
                'overall_status': health.overall_status
            }
        )
        
        return health
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取系统健康状态失败")


# ==================== 健康检查历史 ====================

@router.get("/history", response_model=HealthCheckHistoryListResponse)
@require_permissions(["health:read"])
async def get_health_check_history(
    pagination: PaginationParams = Depends(),
    time_range: TimeRangeParams = Depends(),
    check_id: Optional[int] = Query(None, description="检查ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """获取健康检查历史记录"""
    try:
        result = await service.get_health_check_history(
            skip=pagination.skip,
            limit=pagination.limit,
            start_time=time_range.start_time,
            end_time=time_range.end_time,
            check_id=check_id,
            status=status
        )
        
        logger.info(
            f"Listed health check history",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'filters': {
                    'check_id': check_id,
                    'status': status
                }
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get health check history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取健康检查历史失败")


@router.get("/history/{history_id}", response_model=HealthCheckHistoryResponse)
@require_permissions(["health:read"])
async def get_health_check_history_detail(
    history_id: int = Path(..., description="历史记录ID"),
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """获取健康检查历史记录详情"""
    try:
        history = await service.get_health_check_history_detail(history_id)
        if not history:
            raise HTTPException(status_code=404, detail="历史记录不存在")
        
        logger.debug(
            f"Retrieved health check history detail",
            extra={
                'user_id': current_user.id,
                'history_id': history_id
            }
        )
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health check history detail {history_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取历史记录详情失败")


# ==================== 统计信息 ====================

@router.get("/stats", response_model=HealthCheckStatsResponse)
@require_permissions(["health:read"])
async def get_health_check_stats(
    time_range: TimeRangeParams = Depends(),
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """获取健康检查统计信息"""
    try:
        stats = await service.get_health_check_stats(
            start_time=time_range.start_time,
            end_time=time_range.end_time
        )
        
        logger.debug(
            f"Retrieved health check stats",
            extra={
                'user_id': current_user.id,
                'total_checks': stats.total_checks
            }
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get health check stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取健康检查统计信息失败")


# ==================== 健康检查任务管理 ====================

@router.post("/tasks/start", status_code=202)
@require_permissions(["health:admin"])
@audit_log("start_health_check_tasks", "health_tasks")
async def start_health_check_tasks(
    background_tasks: BackgroundTasks,
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """启动定期健康检查任务"""
    try:
        # 在后台任务中启动定期检查
        background_tasks.add_task(service.start_periodic_health_checks)
        
        logger.info(
            f"Started health check tasks",
            extra={
                'user_id': current_user.id
            }
        )
        
        return {"message": "已启动定期健康检查任务"}
        
    except Exception as e:
        logger.error(f"Failed to start health check tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="启动健康检查任务失败")


@router.post("/tasks/stop", status_code=202)
@require_permissions(["health:admin"])
@audit_log("stop_health_check_tasks", "health_tasks")
async def stop_health_check_tasks(
    service: HealthService = Depends(get_health_service),
    current_user: User = Depends(get_current_user)
):
    """停止定期健康检查任务"""
    try:
        await service.stop_periodic_health_checks()
        
        logger.info(
            f"Stopped health check tasks",
            extra={
                'user_id': current_user.id
            }
        )
        
        return {"message": "已停止定期健康检查任务"}
        
    except Exception as e:
        logger.error(f"Failed to stop health check tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="停止健康检查任务失败")


# ==================== 简单健康检查端点 ====================

@router.get("/ping")
async def health_ping():
    """简单的健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "monitoring-service"
    }


@router.get("/ready")
async def health_ready(
    service: HealthService = Depends(get_health_service)
):
    """就绪状态检查"""
    try:
        # 检查关键服务是否就绪
        ready = await service.check_readiness()
        
        if ready:
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/live")
async def health_live():
    """存活状态检查"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }