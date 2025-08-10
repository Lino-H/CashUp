#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 健康检查API端点

提供系统健康状态监控和服务可用性检查的API接口
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....schemas.health import (
    HealthCheckCreate,
    HealthCheckUpdate,
    HealthCheckResponse,
    ServiceStatusResponse,
    HealthSummaryResponse,
    HealthHistoryResponse,
    HealthConfigResponse,
    HealthTestRequest,
    HealthBatchRequest
)
from ....services.health import HealthService
from ....core.exceptions import (
    ServiceUnavailableError,
    ConfigurationError
)

logger = logging.getLogger(__name__)

router = APIRouter()


# 健康检查配置管理
@router.get("/checks", response_model=List[HealthCheckResponse])
async def list_health_checks(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    service_type: Optional[str] = Query(None, description="服务类型"),
    check_type: Optional[str] = Query(None, description="检查类型"),
    enabled: Optional[bool] = Query(None, description="是否启用"),
    status: Optional[str] = Query(None, description="健康状态"),
    db: Session = Depends(get_db)
):
    """
    获取健康检查配置列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        service_type: 服务类型过滤
        check_type: 检查类型过滤
        enabled: 是否启用过滤
        status: 健康状态过滤
        db: 数据库会话
        
    Returns:
        List[HealthCheckResponse]: 健康检查配置列表
    """
    try:
        health_service = HealthService(db)
        checks = await health_service.list_health_checks(
            skip=skip,
            limit=limit,
            service_type=service_type,
            check_type=check_type,
            enabled=enabled,
            status=status
        )
        return checks
    except Exception as e:
        logger.error(f"Failed to list health checks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health checks")


@router.post("/checks", response_model=HealthCheckResponse)
async def create_health_check(
    check: HealthCheckCreate,
    db: Session = Depends(get_db)
):
    """
    创建健康检查配置
    
    Args:
        check: 健康检查创建数据
        db: 数据库会话
        
    Returns:
        HealthCheckResponse: 创建的健康检查配置
    """
    try:
        health_service = HealthService(db)
        created_check = await health_service.create_health_check(check)
        return created_check
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create health check: {e}")
        raise HTTPException(status_code=500, detail="Failed to create health check")


@router.get("/checks/{check_id}", response_model=HealthCheckResponse)
async def get_health_check(
    check_id: int = Path(..., description="检查ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定健康检查配置详情
    
    Args:
        check_id: 检查ID
        db: 数据库会话
        
    Returns:
        HealthCheckResponse: 健康检查配置详情
    """
    try:
        health_service = HealthService(db)
        check = await health_service.get_health_check(check_id)
        if not check:
            raise HTTPException(status_code=404, detail="Health check not found")
        return check
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health check {check_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health check")


@router.put("/checks/{check_id}", response_model=HealthCheckResponse)
async def update_health_check(
    check_id: int = Path(..., description="检查ID"),
    check_update: HealthCheckUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新健康检查配置
    
    Args:
        check_id: 检查ID
        check_update: 检查更新数据
        db: 数据库会话
        
    Returns:
        HealthCheckResponse: 更新后的健康检查配置
    """
    try:
        health_service = HealthService(db)
        updated_check = await health_service.update_health_check(check_id, check_update)
        if not updated_check:
            raise HTTPException(status_code=404, detail="Health check not found")
        return updated_check
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update health check {check_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update health check")


@router.delete("/checks/{check_id}")
async def delete_health_check(
    check_id: int = Path(..., description="检查ID"),
    db: Session = Depends(get_db)
):
    """
    删除健康检查配置
    
    Args:
        check_id: 检查ID
        db: 数据库会话
        
    Returns:
        dict: 删除结果
    """
    try:
        health_service = HealthService(db)
        success = await health_service.delete_health_check(check_id)
        if not success:
            raise HTTPException(status_code=404, detail="Health check not found")
        return {"message": "Health check deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete health check {check_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete health check")


# 健康检查执行
@router.post("/checks/{check_id}/run")
async def run_health_check(
    check_id: int = Path(..., description="检查ID"),
    db: Session = Depends(get_db)
):
    """
    手动执行健康检查
    
    Args:
        check_id: 检查ID
        db: 数据库会话
        
    Returns:
        dict: 检查结果
    """
    try:
        health_service = HealthService(db)
        result = await health_service.run_health_check(check_id)
        if not result:
            raise HTTPException(status_code=404, detail="Health check not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run health check {check_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to run health check")


@router.post("/checks/run-all")
async def run_all_health_checks(
    service_type: Optional[str] = Query(None, description="服务类型过滤"),
    db: Session = Depends(get_db)
):
    """
    执行所有健康检查
    
    Args:
        service_type: 服务类型过滤
        db: 数据库会话
        
    Returns:
        dict: 检查结果汇总
    """
    try:
        health_service = HealthService(db)
        results = await health_service.run_all_health_checks(service_type)
        return results
    except Exception as e:
        logger.error(f"Failed to run all health checks: {e}")
        raise HTTPException(status_code=500, detail="Failed to run all health checks")


@router.post("/checks/test")
async def test_health_check(
    request: HealthTestRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    测试健康检查配置
    
    Args:
        request: 测试请求
        db: 数据库会话
        
    Returns:
        dict: 测试结果
    """
    try:
        health_service = HealthService(db)
        result = await health_service.test_health_check(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to test health check: {e}")
        raise HTTPException(status_code=500, detail="Failed to test health check")


# 服务状态管理
@router.get("/services", response_model=List[ServiceStatusResponse])
async def list_service_status(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    service_type: Optional[str] = Query(None, description="服务类型"),
    status: Optional[str] = Query(None, description="服务状态"),
    db: Session = Depends(get_db)
):
    """
    获取服务状态列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        service_type: 服务类型过滤
        status: 服务状态过滤
        db: 数据库会话
        
    Returns:
        List[ServiceStatusResponse]: 服务状态列表
    """
    try:
        health_service = HealthService(db)
        services = await health_service.list_service_status(
            skip=skip,
            limit=limit,
            service_type=service_type,
            status=status
        )
        return services
    except Exception as e:
        logger.error(f"Failed to list service status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve service status")


@router.get("/services/{service_name}", response_model=ServiceStatusResponse)
async def get_service_status(
    service_name: str = Path(..., description="服务名称"),
    db: Session = Depends(get_db)
):
    """
    获取指定服务状态详情
    
    Args:
        service_name: 服务名称
        db: 数据库会话
        
    Returns:
        ServiceStatusResponse: 服务状态详情
    """
    try:
        health_service = HealthService(db)
        service = await health_service.get_service_status(service_name)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service status for {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve service status")


@router.post("/services/{service_name}/refresh")
async def refresh_service_status(
    service_name: str = Path(..., description="服务名称"),
    db: Session = Depends(get_db)
):
    """
    刷新服务状态
    
    Args:
        service_name: 服务名称
        db: 数据库会话
        
    Returns:
        dict: 刷新结果
    """
    try:
        health_service = HealthService(db)
        result = await health_service.refresh_service_status(service_name)
        return result
    except Exception as e:
        logger.error(f"Failed to refresh service status for {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh service status")


# 健康状态汇总
@router.get("/summary", response_model=HealthSummaryResponse)
async def get_health_summary(
    include_details: bool = Query(False, description="是否包含详细信息"),
    db: Session = Depends(get_db)
):
    """
    获取系统健康状态汇总
    
    Args:
        include_details: 是否包含详细信息
        db: 数据库会话
        
    Returns:
        HealthSummaryResponse: 健康状态汇总
    """
    try:
        health_service = HealthService(db)
        summary = await health_service.get_health_summary(include_details)
        return summary
    except Exception as e:
        logger.error(f"Failed to get health summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health summary")


@router.get("/overview")
async def get_health_overview(
    db: Session = Depends(get_db)
):
    """
    获取健康状态概览
    
    Args:
        db: 数据库会话
        
    Returns:
        dict: 健康状态概览
    """
    try:
        health_service = HealthService(db)
        overview = await health_service.get_health_overview()
        return overview
    except Exception as e:
        logger.error(f"Failed to get health overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health overview")


# 健康检查历史
@router.get("/checks/{check_id}/history", response_model=List[HealthHistoryResponse])
async def get_health_check_history(
    check_id: int = Path(..., description="检查ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db)
):
    """
    获取健康检查历史记录
    
    Args:
        check_id: 检查ID
        start_time: 开始时间
        end_time: 结束时间
        limit: 返回的记录数
        db: 数据库会话
        
    Returns:
        List[HealthHistoryResponse]: 健康检查历史记录
    """
    try:
        # 设置默认时间范围
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=7)
        
        health_service = HealthService(db)
        history = await health_service.get_health_check_history(
            check_id=check_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return history
    except Exception as e:
        logger.error(f"Failed to get health check history for check {check_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health check history")


@router.get("/services/{service_name}/history", response_model=List[HealthHistoryResponse])
async def get_service_health_history(
    service_name: str = Path(..., description="服务名称"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db)
):
    """
    获取服务健康历史记录
    
    Args:
        service_name: 服务名称
        start_time: 开始时间
        end_time: 结束时间
        limit: 返回的记录数
        db: 数据库会话
        
    Returns:
        List[HealthHistoryResponse]: 服务健康历史记录
    """
    try:
        # 设置默认时间范围
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=7)
        
        health_service = HealthService(db)
        history = await health_service.get_service_health_history(
            service_name=service_name,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return history
    except Exception as e:
        logger.error(f"Failed to get service health history for {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve service health history")


# 健康检查配置
@router.get("/config", response_model=HealthConfigResponse)
async def get_health_config(
    db: Session = Depends(get_db)
):
    """
    获取健康检查配置
    
    Args:
        db: 数据库会话
        
    Returns:
        HealthConfigResponse: 健康检查配置
    """
    try:
        health_service = HealthService(db)
        config = await health_service.get_health_config()
        return config
    except Exception as e:
        logger.error(f"Failed to get health config: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health config")


@router.put("/config", response_model=HealthConfigResponse)
async def update_health_config(
    config_update: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新健康检查配置
    
    Args:
        config_update: 配置更新数据
        db: 数据库会话
        
    Returns:
        HealthConfigResponse: 更新后的健康检查配置
    """
    try:
        health_service = HealthService(db)
        updated_config = await health_service.update_health_config(config_update)
        return updated_config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update health config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update health config")


# 批量操作
@router.post("/checks/batch/enable")
async def batch_enable_health_checks(
    request: HealthBatchRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    批量启用健康检查
    
    Args:
        request: 批量操作请求
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        health_service = HealthService(db)
        result = await health_service.batch_enable_health_checks(request.check_ids)
        return result
    except Exception as e:
        logger.error(f"Failed to batch enable health checks: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch enable health checks")


@router.post("/checks/batch/disable")
async def batch_disable_health_checks(
    request: HealthBatchRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    批量禁用健康检查
    
    Args:
        request: 批量操作请求
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        health_service = HealthService(db)
        result = await health_service.batch_disable_health_checks(request.check_ids)
        return result
    except Exception as e:
        logger.error(f"Failed to batch disable health checks: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch disable health checks")


@router.post("/checks/batch/run")
async def batch_run_health_checks(
    request: HealthBatchRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    批量执行健康检查
    
    Args:
        request: 批量操作请求
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        health_service = HealthService(db)
        result = await health_service.batch_run_health_checks(request.check_ids)
        return result
    except Exception as e:
        logger.error(f"Failed to batch run health checks: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch run health checks")


# 健康检查统计
@router.get("/statistics")
async def get_health_statistics(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    group_by: Optional[str] = Query("status", description="分组字段"),
    db: Session = Depends(get_db)
):
    """
    获取健康检查统计信息
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        group_by: 分组字段 (status, service_type, check_type)
        db: 数据库会话
        
    Returns:
        dict: 健康检查统计信息
    """
    try:
        # 设置默认时间范围
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=7)
        
        health_service = HealthService(db)
        statistics = await health_service.get_health_statistics(
            start_time=start_time,
            end_time=end_time,
            group_by=group_by
        )
        return statistics
    except Exception as e:
        logger.error(f"Failed to get health statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health statistics")