#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 系统API端点

提供系统信息、配置管理和运维操作的API接口
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....core.config import get_settings
from ....schemas.system import (
    SystemInfoResponse,
    SystemConfigResponse,
    SystemConfigUpdate,
    SystemStatusResponse,
    SystemResourceResponse,
    SystemLogResponse,
    SystemBackupRequest,
    SystemBackupResponse,
    SystemMaintenanceRequest,
    SystemMaintenanceResponse,
    SystemPerformanceResponse,
    SystemSecurityResponse
)
from ....services.system import SystemService
from ....core.exceptions import (
    ConfigurationError,
    ServiceUnavailableError
)

logger = logging.getLogger(__name__)

router = APIRouter()


# 系统信息
@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info(
    db: Session = Depends(get_db)
):
    """
    获取系统信息
    
    Args:
        db: 数据库会话
        
    Returns:
        SystemInfoResponse: 系统信息
    """
    try:
        system_service = SystemService(db)
        info = await system_service.get_system_info()
        return info
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system info")


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    include_details: bool = Query(False, description="是否包含详细信息"),
    db: Session = Depends(get_db)
):
    """
    获取系统状态
    
    Args:
        include_details: 是否包含详细信息
        db: 数据库会话
        
    Returns:
        SystemStatusResponse: 系统状态
    """
    try:
        system_service = SystemService(db)
        status = await system_service.get_system_status(include_details)
        return status
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")


@router.get("/resources", response_model=SystemResourceResponse)
async def get_system_resources(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    interval: Optional[str] = Query("5m", description="时间间隔"),
    db: Session = Depends(get_db)
):
    """
    获取系统资源使用情况
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        interval: 时间间隔
        db: 数据库会话
        
    Returns:
        SystemResourceResponse: 系统资源信息
    """
    try:
        # 设置默认时间范围
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=1)
        
        system_service = SystemService(db)
        resources = await system_service.get_system_resources(
            start_time=start_time,
            end_time=end_time,
            interval=interval
        )
        return resources
    except Exception as e:
        logger.error(f"Failed to get system resources: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system resources")


@router.get("/performance", response_model=SystemPerformanceResponse)
async def get_system_performance(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    metrics: Optional[List[str]] = Query(None, description="指标列表"),
    db: Session = Depends(get_db)
):
    """
    获取系统性能指标
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        metrics: 指标列表
        db: 数据库会话
        
    Returns:
        SystemPerformanceResponse: 系统性能信息
    """
    try:
        # 设置默认时间范围
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        system_service = SystemService(db)
        performance = await system_service.get_system_performance(
            start_time=start_time,
            end_time=end_time,
            metrics=metrics
        )
        return performance
    except Exception as e:
        logger.error(f"Failed to get system performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system performance")


# 系统配置
@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config(
    section: Optional[str] = Query(None, description="配置节"),
    db: Session = Depends(get_db)
):
    """
    获取系统配置
    
    Args:
        section: 配置节过滤
        db: 数据库会话
        
    Returns:
        SystemConfigResponse: 系统配置
    """
    try:
        system_service = SystemService(db)
        config = await system_service.get_system_config(section)
        return config
    except Exception as e:
        logger.error(f"Failed to get system config: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system config")


@router.put("/config", response_model=SystemConfigResponse)
async def update_system_config(
    config_update: SystemConfigUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新系统配置
    
    Args:
        config_update: 配置更新数据
        db: 数据库会话
        
    Returns:
        SystemConfigResponse: 更新后的系统配置
    """
    try:
        system_service = SystemService(db)
        updated_config = await system_service.update_system_config(config_update)
        return updated_config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update system config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update system config")


@router.post("/config/reload")
async def reload_system_config(
    db: Session = Depends(get_db)
):
    """
    重新加载系统配置
    
    Args:
        db: 数据库会话
        
    Returns:
        dict: 重新加载结果
    """
    try:
        system_service = SystemService(db)
        result = await system_service.reload_system_config()
        return result
    except Exception as e:
        logger.error(f"Failed to reload system config: {e}")
        raise HTTPException(status_code=500, detail="Failed to reload system config")


@router.post("/config/validate")
async def validate_system_config(
    config_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    验证系统配置
    
    Args:
        config_data: 配置数据
        db: 数据库会话
        
    Returns:
        dict: 验证结果
    """
    try:
        system_service = SystemService(db)
        result = await system_service.validate_system_config(config_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to validate system config: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate system config")


# 系统日志
@router.get("/logs", response_model=List[SystemLogResponse])
async def get_system_logs(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    level: Optional[str] = Query(None, description="日志级别"),
    component: Optional[str] = Query(None, description="组件名称"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取系统日志
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        level: 日志级别过滤
        component: 组件名称过滤
        start_time: 开始时间
        end_time: 结束时间
        search: 搜索关键词
        db: 数据库会话
        
    Returns:
        List[SystemLogResponse]: 系统日志列表
    """
    try:
        # 设置默认时间范围
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        system_service = SystemService(db)
        logs = await system_service.get_system_logs(
            skip=skip,
            limit=limit,
            level=level,
            component=component,
            start_time=start_time,
            end_time=end_time,
            search=search
        )
        return logs
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system logs")


@router.post("/logs/export")
async def export_system_logs(
    start_time: Optional[datetime] = Body(None, description="开始时间"),
    end_time: Optional[datetime] = Body(None, description="结束时间"),
    level: Optional[str] = Body(None, description="日志级别"),
    component: Optional[str] = Body(None, description="组件名称"),
    format: str = Body("json", description="导出格式"),
    db: Session = Depends(get_db)
):
    """
    导出系统日志
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        level: 日志级别
        component: 组件名称
        format: 导出格式
        db: 数据库会话
        
    Returns:
        dict: 导出结果
    """
    try:
        # 设置默认时间范围
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        system_service = SystemService(db)
        result = await system_service.export_system_logs(
            start_time=start_time,
            end_time=end_time,
            level=level,
            component=component,
            format=format
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to export system logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to export system logs")


# 系统备份
@router.get("/backups", response_model=List[SystemBackupResponse])
async def list_system_backups(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    backup_type: Optional[str] = Query(None, description="备份类型"),
    db: Session = Depends(get_db)
):
    """
    获取系统备份列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        backup_type: 备份类型过滤
        db: 数据库会话
        
    Returns:
        List[SystemBackupResponse]: 备份列表
    """
    try:
        system_service = SystemService(db)
        backups = await system_service.list_system_backups(
            skip=skip,
            limit=limit,
            backup_type=backup_type
        )
        return backups
    except Exception as e:
        logger.error(f"Failed to list system backups: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system backups")


@router.post("/backups", response_model=SystemBackupResponse)
async def create_system_backup(
    request: SystemBackupRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    创建系统备份
    
    Args:
        request: 备份请求
        db: 数据库会话
        
    Returns:
        SystemBackupResponse: 创建的备份
    """
    try:
        system_service = SystemService(db)
        backup = await system_service.create_system_backup(request)
        return backup
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create system backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to create system backup")


@router.get("/backups/{backup_id}", response_model=SystemBackupResponse)
async def get_system_backup(
    backup_id: int = Path(..., description="备份ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定系统备份详情
    
    Args:
        backup_id: 备份ID
        db: 数据库会话
        
    Returns:
        SystemBackupResponse: 备份详情
    """
    try:
        system_service = SystemService(db)
        backup = await system_service.get_system_backup(backup_id)
        if not backup:
            raise HTTPException(status_code=404, detail="Backup not found")
        return backup
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system backup {backup_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system backup")


@router.post("/backups/{backup_id}/restore")
async def restore_system_backup(
    backup_id: int = Path(..., description="备份ID"),
    confirm: bool = Body(False, description="确认恢复"),
    db: Session = Depends(get_db)
):
    """
    恢复系统备份
    
    Args:
        backup_id: 备份ID
        confirm: 确认恢复
        db: 数据库会话
        
    Returns:
        dict: 恢复结果
    """
    try:
        if not confirm:
            raise HTTPException(status_code=400, detail="Restore operation requires confirmation")
        
        system_service = SystemService(db)
        result = await system_service.restore_system_backup(backup_id)
        if not result:
            raise HTTPException(status_code=404, detail="Backup not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore system backup {backup_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore system backup")


@router.delete("/backups/{backup_id}")
async def delete_system_backup(
    backup_id: int = Path(..., description="备份ID"),
    db: Session = Depends(get_db)
):
    """
    删除系统备份
    
    Args:
        backup_id: 备份ID
        db: 数据库会话
        
    Returns:
        dict: 删除结果
    """
    try:
        system_service = SystemService(db)
        success = await system_service.delete_system_backup(backup_id)
        if not success:
            raise HTTPException(status_code=404, detail="Backup not found")
        return {"message": "Backup deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete system backup {backup_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete system backup")


# 系统维护
@router.get("/maintenance", response_model=List[SystemMaintenanceResponse])
async def list_maintenance_tasks(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    status: Optional[str] = Query(None, description="任务状态"),
    task_type: Optional[str] = Query(None, description="任务类型"),
    db: Session = Depends(get_db)
):
    """
    获取维护任务列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        status: 任务状态过滤
        task_type: 任务类型过滤
        db: 数据库会话
        
    Returns:
        List[SystemMaintenanceResponse]: 维护任务列表
    """
    try:
        system_service = SystemService(db)
        tasks = await system_service.list_maintenance_tasks(
            skip=skip,
            limit=limit,
            status=status,
            task_type=task_type
        )
        return tasks
    except Exception as e:
        logger.error(f"Failed to list maintenance tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve maintenance tasks")


@router.post("/maintenance", response_model=SystemMaintenanceResponse)
async def create_maintenance_task(
    request: SystemMaintenanceRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    创建维护任务
    
    Args:
        request: 维护任务请求
        db: 数据库会话
        
    Returns:
        SystemMaintenanceResponse: 创建的维护任务
    """
    try:
        system_service = SystemService(db)
        task = await system_service.create_maintenance_task(request)
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create maintenance task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create maintenance task")


@router.get("/maintenance/{task_id}", response_model=SystemMaintenanceResponse)
async def get_maintenance_task(
    task_id: int = Path(..., description="任务ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定维护任务详情
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        
    Returns:
        SystemMaintenanceResponse: 维护任务详情
    """
    try:
        system_service = SystemService(db)
        task = await system_service.get_maintenance_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Maintenance task not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get maintenance task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve maintenance task")


@router.post("/maintenance/{task_id}/execute")
async def execute_maintenance_task(
    task_id: int = Path(..., description="任务ID"),
    db: Session = Depends(get_db)
):
    """
    执行维护任务
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        
    Returns:
        dict: 执行结果
    """
    try:
        system_service = SystemService(db)
        result = await system_service.execute_maintenance_task(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="Maintenance task not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute maintenance task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute maintenance task")


# 系统安全
@router.get("/security", response_model=SystemSecurityResponse)
async def get_system_security(
    db: Session = Depends(get_db)
):
    """
    获取系统安全状态
    
    Args:
        db: 数据库会话
        
    Returns:
        SystemSecurityResponse: 系统安全状态
    """
    try:
        system_service = SystemService(db)
        security = await system_service.get_system_security()
        return security
    except Exception as e:
        logger.error(f"Failed to get system security: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system security")


@router.post("/security/scan")
async def scan_system_security(
    scan_type: str = Body("full", description="扫描类型"),
    db: Session = Depends(get_db)
):
    """
    执行系统安全扫描
    
    Args:
        scan_type: 扫描类型
        db: 数据库会话
        
    Returns:
        dict: 扫描结果
    """
    try:
        system_service = SystemService(db)
        result = await system_service.scan_system_security(scan_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to scan system security: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan system security")


# 系统操作
@router.post("/restart")
async def restart_system(
    component: Optional[str] = Body(None, description="组件名称"),
    confirm: bool = Body(False, description="确认重启"),
    db: Session = Depends(get_db)
):
    """
    重启系统或组件
    
    Args:
        component: 组件名称
        confirm: 确认重启
        db: 数据库会话
        
    Returns:
        dict: 重启结果
    """
    try:
        if not confirm:
            raise HTTPException(status_code=400, detail="Restart operation requires confirmation")
        
        system_service = SystemService(db)
        result = await system_service.restart_system(component)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart system: {e}")
        raise HTTPException(status_code=500, detail="Failed to restart system")


@router.post("/shutdown")
async def shutdown_system(
    confirm: bool = Body(False, description="确认关闭"),
    delay: int = Body(0, description="延迟时间(秒)"),
    db: Session = Depends(get_db)
):
    """
    关闭系统
    
    Args:
        confirm: 确认关闭
        delay: 延迟时间
        db: 数据库会话
        
    Returns:
        dict: 关闭结果
    """
    try:
        if not confirm:
            raise HTTPException(status_code=400, detail="Shutdown operation requires confirmation")
        
        system_service = SystemService(db)
        result = await system_service.shutdown_system(delay)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to shutdown system: {e}")
        raise HTTPException(status_code=500, detail="Failed to shutdown system")


@router.post("/cleanup")
async def cleanup_system(
    cleanup_type: str = Body("temp", description="清理类型"),
    confirm: bool = Body(False, description="确认清理"),
    db: Session = Depends(get_db)
):
    """
    清理系统
    
    Args:
        cleanup_type: 清理类型
        confirm: 确认清理
        db: 数据库会话
        
    Returns:
        dict: 清理结果
    """
    try:
        if not confirm:
            raise HTTPException(status_code=400, detail="Cleanup operation requires confirmation")
        
        system_service = SystemService(db)
        result = await system_service.cleanup_system(cleanup_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cleanup system: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup system")