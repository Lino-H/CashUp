#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 系统API路由

系统管理相关的API端点
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.core.database import get_db
from app.core.security import get_current_user, require_permissions
from app.core.logging import get_logger, audit_log
from app.schemas.system import (
    SystemInfoResponse, SystemStatusResponse, SystemResourceResponse,
    SystemPerformanceResponse, SystemConfigResponse, SystemConfigUpdate,
    SystemLogResponse, SystemLogListResponse, SystemBackupResponse,
    SystemBackupListResponse, SystemBackupCreate, SystemMaintenanceResponse,
    SystemMaintenanceListResponse, SystemSecurityResponse, SystemSecurityScanRequest,
    SystemOperationRequest, SystemCleanupRequest
)
from app.schemas.common import PaginationParams, TimeRangeParams
from app.services.system_service import SystemService
from app.models.user import User

# 创建路由器
router = APIRouter()
logger = get_logger(__name__)

# 依赖注入
def get_system_service(db: Session = Depends(get_db)) -> SystemService:
    """获取系统服务"""
    return SystemService(db)


# ==================== 系统信息 ====================

@router.get("/info", response_model=SystemInfoResponse)
@require_permissions(["system:read"])
async def get_system_info(
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统信息"""
    try:
        info = await service.get_system_info()
        
        logger.debug(
            f"Retrieved system info",
            extra={'user_id': current_user.id}
        )
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get system info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取系统信息失败")


@router.get("/status", response_model=SystemStatusResponse)
@require_permissions(["system:read"])
async def get_system_status(
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统状态"""
    try:
        status = await service.get_system_status()
        
        logger.debug(
            f"Retrieved system status",
            extra={'user_id': current_user.id}
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取系统状态失败")


@router.get("/resources", response_model=SystemResourceResponse)
@require_permissions(["system:read"])
async def get_system_resources(
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统资源使用情况"""
    try:
        resources = await service.get_system_resources()
        
        logger.debug(
            f"Retrieved system resources",
            extra={'user_id': current_user.id}
        )
        
        return resources
        
    except Exception as e:
        logger.error(f"Failed to get system resources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取系统资源失败")


@router.get("/performance", response_model=SystemPerformanceResponse)
@require_permissions(["system:read"])
async def get_system_performance(
    time_range: TimeRangeParams = Depends(),
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统性能指标"""
    try:
        performance = await service.get_system_performance(
            start_time=time_range.start_time,
            end_time=time_range.end_time
        )
        
        logger.debug(
            f"Retrieved system performance",
            extra={
                'user_id': current_user.id,
                'start_time': time_range.start_time,
                'end_time': time_range.end_time
            }
        )
        
        return performance
        
    except Exception as e:
        logger.error(f"Failed to get system performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取系统性能失败")


# ==================== 系统配置 ====================

@router.get("/config", response_model=SystemConfigResponse)
@require_permissions(["system:config:read"])
async def get_system_config(
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统配置"""
    try:
        config = await service.get_system_config()
        
        logger.debug(
            f"Retrieved system config",
            extra={'user_id': current_user.id}
        )
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to get system config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取系统配置失败")


@router.put("/config", response_model=SystemConfigResponse)
@require_permissions(["system:config:write"])
@audit_log("update_system_config", "system_config")
async def update_system_config(
    config_data: SystemConfigUpdate,
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """更新系统配置"""
    try:
        config = await service.update_system_config(config_data)
        
        logger.info(
            f"Updated system config",
            extra={
                'user_id': current_user.id,
                'config_keys': list(config_data.dict(exclude_unset=True).keys())
            }
        )
        
        return config
        
    except ValueError as e:
        logger.warning(f"Invalid config data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update system config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新系统配置失败")


@router.post("/config/reload", status_code=204)
@require_permissions(["system:config:write"])
@audit_log("reload_system_config", "system_config")
async def reload_system_config(
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """重新加载系统配置"""
    try:
        await service.reload_system_config()
        
        logger.info(
            f"Reloaded system config",
            extra={'user_id': current_user.id}
        )
        
    except Exception as e:
        logger.error(f"Failed to reload system config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="重新加载系统配置失败")


@router.post("/config/validate")
@require_permissions(["system:config:read"])
async def validate_system_config(
    config_data: SystemConfigUpdate,
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """验证系统配置"""
    try:
        result = await service.validate_system_config(config_data)
        
        logger.debug(
            f"Validated system config",
            extra={
                'user_id': current_user.id,
                'is_valid': result['is_valid']
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to validate system config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="验证系统配置失败")


# ==================== 系统日志 ====================

@router.get("/logs", response_model=SystemLogListResponse)
@require_permissions(["system:logs:read"])
async def get_system_logs(
    pagination: PaginationParams = Depends(),
    time_range: TimeRangeParams = Depends(),
    level: Optional[str] = Query(None, description="日志级别过滤"),
    module: Optional[str] = Query(None, description="模块过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统日志"""
    try:
        result = await service.get_system_logs(
            skip=pagination.skip,
            limit=pagination.limit,
            start_time=time_range.start_time,
            end_time=time_range.end_time,
            level=level,
            module=module,
            keyword=keyword
        )
        
        logger.debug(
            f"Retrieved system logs",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'filters': {
                    'level': level,
                    'module': module,
                    'keyword': keyword
                }
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取系统日志失败")


@router.get("/logs/{log_id}", response_model=SystemLogResponse)
@require_permissions(["system:logs:read"])
async def get_system_log(
    log_id: int = Path(..., description="日志ID"),
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统日志详情"""
    try:
        log = await service.get_system_log(log_id)
        if not log:
            raise HTTPException(status_code=404, detail="日志不存在")
        
        logger.debug(
            f"Retrieved system log",
            extra={
                'user_id': current_user.id,
                'log_id': log_id
            }
        )
        
        return log
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system log {log_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取日志详情失败")


@router.post("/logs/export")
@require_permissions(["system:logs:export"])
@audit_log("export_system_logs", "system_logs")
async def export_system_logs(
    time_range: TimeRangeParams = Depends(),
    level: Optional[str] = Query(None, description="日志级别过滤"),
    module: Optional[str] = Query(None, description="模块过滤"),
    format: str = Query("csv", description="导出格式 (csv, json)"),
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """导出系统日志"""
    try:
        export_data = await service.export_system_logs(
            start_time=time_range.start_time,
            end_time=time_range.end_time,
            level=level,
            module=module,
            format=format
        )
        
        logger.info(
            f"Exported system logs",
            extra={
                'user_id': current_user.id,
                'format': format,
                'filters': {
                    'level': level,
                    'module': module
                }
            }
        )
        
        # 创建文件流响应
        filename = f"system_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        media_type = "text/csv" if format == "csv" else "application/json"
        
        return StreamingResponse(
            io.BytesIO(export_data.encode()),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export system logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="导出系统日志失败")


# ==================== 系统备份 ====================

@router.get("/backups", response_model=SystemBackupListResponse)
@require_permissions(["system:backup:read"])
async def list_system_backups(
    pagination: PaginationParams = Depends(),
    backup_type: Optional[str] = Query(None, description="备份类型过滤"),
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统备份列表"""
    try:
        result = await service.get_system_backups(
            skip=pagination.skip,
            limit=pagination.limit,
            backup_type=backup_type
        )
        
        logger.debug(
            f"Listed system backups",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'backup_type': backup_type
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list system backups: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取系统备份列表失败")


@router.post("/backups", response_model=SystemBackupResponse, status_code=201)
@require_permissions(["system:backup:write"])
@audit_log("create_system_backup", "system_backup")
async def create_system_backup(
    backup_data: SystemBackupCreate,
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """创建系统备份"""
    try:
        backup = await service.create_system_backup(
            backup_data.backup_type,
            backup_data.description,
            backup_data.include_data,
            current_user.id
        )
        
        logger.info(
            f"Created system backup",
            extra={
                'user_id': current_user.id,
                'backup_id': backup.id,
                'backup_type': backup.backup_type,
                'include_data': backup_data.include_data
            }
        )
        
        return backup
        
    except ValueError as e:
        logger.warning(f"Invalid backup data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create system backup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建系统备份失败")


@router.get("/backups/{backup_id}", response_model=SystemBackupResponse)
@require_permissions(["system:backup:read"])
async def get_system_backup(
    backup_id: int = Path(..., description="备份ID"),
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统备份详情"""
    try:
        backup = await service.get_system_backup(backup_id)
        if not backup:
            raise HTTPException(status_code=404, detail="备份不存在")
        
        logger.debug(
            f"Retrieved system backup",
            extra={
                'user_id': current_user.id,
                'backup_id': backup_id
            }
        )
        
        return backup
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system backup {backup_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取备份详情失败")


@router.post("/backups/{backup_id}/restore", status_code=204)
@require_permissions(["system:backup:restore"])
@audit_log("restore_system_backup", "system_backup")
async def restore_system_backup(
    backup_id: int = Path(..., description="备份ID"),
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """恢复系统备份"""
    try:
        await service.restore_system_backup(backup_id)
        
        logger.info(
            f"Restored system backup",
            extra={
                'user_id': current_user.id,
                'backup_id': backup_id
            }
        )
        
    except ValueError as e:
        logger.warning(f"Invalid backup restore: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to restore system backup {backup_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="恢复系统备份失败")


# ==================== 系统维护 ====================

@router.get("/maintenance", response_model=SystemMaintenanceListResponse)
@require_permissions(["system:maintenance:read"])
async def get_maintenance_tasks(
    pagination: PaginationParams = Depends(),
    task_type: Optional[str] = Query(None, description="任务类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统维护任务"""
    try:
        result = await service.get_maintenance_tasks(
            skip=pagination.skip,
            limit=pagination.limit,
            task_type=task_type,
            status=status
        )
        
        logger.debug(
            f"Retrieved maintenance tasks",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'filters': {
                    'task_type': task_type,
                    'status': status
                }
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get maintenance tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取维护任务失败")


@router.post("/maintenance/{task_type}/execute", response_model=SystemMaintenanceResponse)
@require_permissions(["system:maintenance:execute"])
@audit_log("execute_maintenance_task", "system_maintenance")
async def execute_maintenance_task(
    task_type: str = Path(..., description="任务类型"),
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """执行系统维护任务"""
    try:
        task = await service.execute_maintenance_task(task_type, current_user.id)
        
        logger.info(
            f"Executed maintenance task: {task_type}",
            extra={
                'user_id': current_user.id,
                'task_type': task_type,
                'task_id': task.id
            }
        )
        
        return task
        
    except ValueError as e:
        logger.warning(f"Invalid maintenance task: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute maintenance task {task_type}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="执行维护任务失败")


# ==================== 系统安全 ====================

@router.get("/security", response_model=SystemSecurityResponse)
@require_permissions(["system:security:read"])
async def get_security_status(
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """获取系统安全状态"""
    try:
        security = await service.get_security_status()
        
        logger.debug(
            f"Retrieved security status",
            extra={'user_id': current_user.id}
        )
        
        return security
        
    except Exception as e:
        logger.error(f"Failed to get security status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取安全状态失败")


@router.post("/security/scan", response_model=SystemSecurityResponse)
@require_permissions(["system:security:scan"])
@audit_log("security_scan", "system_security")
async def perform_security_scan(
    scan_request: SystemSecurityScanRequest,
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """执行安全扫描"""
    try:
        result = await service.perform_security_scan(
            scan_request.scan_type,
            scan_request.targets
        )
        
        logger.info(
            f"Performed security scan",
            extra={
                'user_id': current_user.id,
                'scan_type': scan_request.scan_type,
                'targets': scan_request.targets
            }
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid security scan request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to perform security scan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="执行安全扫描失败")


# ==================== 系统操作 ====================

@router.post("/restart", status_code=204)
@require_permissions(["system:admin"])
@audit_log("restart_system", "system_operation")
async def restart_system(
    operation_request: SystemOperationRequest,
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """重启系统"""
    try:
        await service.restart_system(
            operation_request.force,
            operation_request.delay_seconds
        )
        
        logger.warning(
            f"System restart initiated",
            extra={
                'user_id': current_user.id,
                'force': operation_request.force,
                'delay_seconds': operation_request.delay_seconds
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to restart system: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="重启系统失败")


@router.post("/shutdown", status_code=204)
@require_permissions(["system:admin"])
@audit_log("shutdown_system", "system_operation")
async def shutdown_system(
    operation_request: SystemOperationRequest,
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """关闭系统"""
    try:
        await service.shutdown_system(
            operation_request.force,
            operation_request.delay_seconds
        )
        
        logger.warning(
            f"System shutdown initiated",
            extra={
                'user_id': current_user.id,
                'force': operation_request.force,
                'delay_seconds': operation_request.delay_seconds
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to shutdown system: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="关闭系统失败")


@router.post("/cleanup", status_code=204)
@require_permissions(["system:maintenance:execute"])
@audit_log("cleanup_system", "system_operation")
async def cleanup_system(
    cleanup_request: SystemCleanupRequest,
    service: SystemService = Depends(get_system_service),
    current_user: User = Depends(get_current_user)
):
    """清理系统"""
    try:
        await service.cleanup_system(
            cleanup_request.cleanup_types,
            cleanup_request.force
        )
        
        logger.info(
            f"System cleanup completed",
            extra={
                'user_id': current_user.id,
                'cleanup_types': cleanup_request.cleanup_types,
                'force': cleanup_request.force
            }
        )
        
    except ValueError as e:
        logger.warning(f"Invalid cleanup request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cleanup system: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="清理系统失败")