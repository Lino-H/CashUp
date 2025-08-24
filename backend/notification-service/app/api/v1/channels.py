#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 渠道API路由

处理通知渠道相关的API请求
"""

import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user
from ...models.channel import ChannelType, ChannelStatus
from ...schemas.channel import (
    ChannelCreate,
    ChannelUpdate,
    ChannelResponse,
    ChannelListResponse,
    ChannelFilter,
    ChannelTest,
    ChannelTestResponse,
    ChannelStatsResponse,
    ChannelBulkOperation,
    ChannelBulkOperationResponse,
    ChannelConfig,
    ChannelConfigResponse,
    ChannelHealth,
    ChannelHealthResponse,
    ChannelMetrics,
    ChannelMetricsResponse,
    ChannelQuota,
    ChannelQuotaResponse
)
from ...schemas.common import (
    BaseResponse,
    PaginationParams,
    PaginationInfo
)
from ...services.channel_service import ChannelService
from ...services.websocket_service import get_websocket_service

import logging

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# 依赖注入
def get_channel_service() -> ChannelService:
    return ChannelService()


@router.post("/", response_model=ChannelResponse)
async def create_channel(
    channel: ChannelCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    创建渠道
    
    Args:
        channel: 渠道创建请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelResponse: 创建的渠道信息
    """
    try:
        # 创建渠道
        created_channel = await service.create_channel(
            db=db,
            channel_data=channel,
            created_by=current_user["user_id"]
        )
        
        # 发送WebSocket通知
        websocket_service = get_websocket_service()
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "channel_created",
                "channel_id": str(created_channel.id),
                "channel_name": created_channel.name,
                "channel_type": created_channel.type.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return ChannelResponse.from_orm(created_channel)
        
    except Exception as e:
        logger.error(f"Error creating channel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ChannelListResponse)
async def get_channels(
    pagination: PaginationParams = Depends(),
    filters: ChannelFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    获取渠道列表
    
    Args:
        pagination: 分页参数
        filters: 过滤参数
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelListResponse: 渠道列表
    """
    try:
        # 获取渠道列表
        channels, total = await service.get_channels(
            db=db,
            filters=filters,
            page=pagination.page,
            size=pagination.size
        )
        
        return ChannelListResponse(
            success=True,
            message="Channels retrieved successfully",
            data=[ChannelResponse.from_orm(c) for c in channels],
            pagination=PaginationInfo.create(
                page=pagination.page,
                size=pagination.size,
                total=total
            )
        )
        
    except Exception as e:
        logger.error(f"Error getting channels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    获取单个渠道
    
    Args:
        channel_id: 渠道ID
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelResponse: 渠道信息
    """
    try:
        channel = await service.get_channel(db, channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        return ChannelResponse.from_orm(channel)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channel {channel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: uuid.UUID,
    channel_update: ChannelUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    更新渠道
    
    Args:
        channel_id: 渠道ID
        channel_update: 更新数据
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelResponse: 更新后的渠道信息
    """
    try:
        updated_channel = await service.update_channel(
            db=db,
            channel_id=channel_id,
            channel_data=channel_update
        )
        
        if not updated_channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # 发送WebSocket通知
        websocket_service = get_websocket_service()
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "channel_updated",
                "channel_id": str(channel_id),
                "channel_name": updated_channel.name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return ChannelResponse.from_orm(updated_channel)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating channel {channel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{channel_id}", response_model=BaseResponse)
async def delete_channel(
    channel_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    删除渠道
    
    Args:
        channel_id: 渠道ID
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        BaseResponse: 删除结果
    """
    try:
        success = await service.delete_channel(db, channel_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # 发送WebSocket通知
        websocket_service = get_websocket_service()
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "channel_deleted",
                "channel_id": str(channel_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return BaseResponse(
            success=True,
            message="Channel deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting channel {channel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{channel_id}/test", response_model=ChannelTestResponse)
async def test_channel(
    channel_id: uuid.UUID,
    test_request: ChannelTest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    测试渠道
    
    Args:
        channel_id: 渠道ID
        test_request: 测试请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelTestResponse: 测试结果
    """
    try:
        result = await service.test_channel(
            db=db,
            channel_id=channel_id,
            test_message=test_request.test_message,
            test_recipient=test_request.test_recipient
        )
        
        # 发送WebSocket通知
        websocket_service = get_websocket_service()
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "channel_test_completed",
                "channel_id": str(channel_id),
                "success": result["success"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return ChannelTestResponse(**result)
        
    except Exception as e:
        logger.error(f"Error testing channel {channel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{channel_id}/health", response_model=ChannelHealthResponse)
async def get_channel_health(
    channel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    获取渠道健康状态
    
    Args:
        channel_id: 渠道ID
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelHealthResponse: 健康状态信息
    """
    try:
        health_info = await service.get_channel_health(db, channel_id)
        
        return ChannelHealthResponse(**health_info)
        
    except Exception as e:
        logger.error(f"Error getting channel health {channel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{channel_id}/metrics", response_model=ChannelMetricsResponse)
async def get_channel_metrics(
    channel_id: uuid.UUID,
    start_date: Optional[datetime] = Query(None, description="统计开始日期"),
    end_date: Optional[datetime] = Query(None, description="统计结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    获取渠道指标
    
    Args:
        channel_id: 渠道ID
        start_date: 统计开始日期
        end_date: 统计结束日期
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelMetricsResponse: 指标信息
    """
    try:
        metrics = await service.get_channel_metrics(
            db=db,
            channel_id=channel_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return ChannelMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Error getting channel metrics {channel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{channel_id}/quota", response_model=ChannelQuotaResponse)
async def get_channel_quota(
    channel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    获取渠道配额信息
    
    Args:
        channel_id: 渠道ID
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelQuotaResponse: 配额信息
    """
    try:
        # 这里应该实现实际的配额查询逻辑
        # 为了演示，返回模拟数据
        quota_info = {
            "channel_id": str(channel_id),
            "daily_limit": 10000,
            "daily_used": 2500,
            "daily_remaining": 7500,
            "monthly_limit": 300000,
            "monthly_used": 75000,
            "monthly_remaining": 225000,
            "rate_limit": 100,
            "current_rate": 25,
            "quota_reset_time": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
            "is_quota_exceeded": False,
            "warning_threshold": 0.8,
            "is_warning": False
        }
        
        return ChannelQuotaResponse(**quota_info)
        
    except Exception as e:
        logger.error(f"Error getting channel quota {channel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ChannelStatsResponse)
async def get_channel_stats(
    start_date: Optional[datetime] = Query(None, description="统计开始日期"),
    end_date: Optional[datetime] = Query(None, description="统计结束日期"),
    channel_type: Optional[ChannelType] = Query(None, description="渠道类型过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    获取渠道统计信息
    
    Args:
        start_date: 统计开始日期
        end_date: 统计结束日期
        channel_type: 渠道类型过滤
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelStatsResponse: 统计信息
    """
    try:
        stats = await service.get_channel_stats(
            db=db,
            start_date=start_date,
            end_date=end_date,
            channel_type=channel_type
        )
        
        return ChannelStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting channel stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", response_model=ChannelBulkOperationResponse)
async def bulk_channel_operation(
    bulk_request: ChannelBulkOperation,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    批量渠道操作
    
    Args:
        bulk_request: 批量操作请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelBulkOperationResponse: 批量操作结果
    """
    try:
        # 这里应该实现实际的批量操作逻辑
        # 为了演示，返回模拟数据
        result = {
            "operation": bulk_request.operation,
            "total_count": len(bulk_request.channel_ids),
            "success_count": len(bulk_request.channel_ids),
            "failed_count": 0,
            "errors": [],
            "message": f"Bulk {bulk_request.operation} completed successfully"
        }
        
        # 发送WebSocket通知
        websocket_service = get_websocket_service()
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "channel_bulk_operation_completed",
                "operation": bulk_request.operation,
                "success_count": result["success_count"],
                "failed_count": result["failed_count"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return ChannelBulkOperationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error performing bulk channel operation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{channel_id}/config", response_model=ChannelConfigResponse)
async def get_channel_config(
    channel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    获取渠道配置
    
    Args:
        channel_id: 渠道ID
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelConfigResponse: 配置信息
    """
    try:
        channel = await service.get_channel(db, channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # 隐藏敏感信息
        config = channel.config.copy() if channel.config else {}
        sensitive_keys = ['password', 'secret', 'token', 'key', 'api_key']
        
        for key in config:
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                config[key] = "***"
        
        return ChannelConfigResponse(
            channel_id=str(channel_id),
            config=config,
            config_schema=service._get_config_schema(channel.type),
            is_valid=True,
            validation_errors=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channel config {channel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{channel_id}/config", response_model=ChannelConfigResponse)
async def update_channel_config(
    channel_id: uuid.UUID,
    config_request: ChannelConfig,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: ChannelService = Depends(get_channel_service)
):
    """
    更新渠道配置
    
    Args:
        channel_id: 渠道ID
        config_request: 配置请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 渠道服务
        
    Returns:
        ChannelConfigResponse: 更新后的配置信息
    """
    try:
        # 这里应该实现实际的配置更新逻辑
        channel = await service.get_channel(db, channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # 验证配置
        validation_result = service._validate_channel_config(
            channel.type,
            config_request.config
        )
        
        if not validation_result["is_valid"]:
            return ChannelConfigResponse(
                channel_id=str(channel_id),
                config=config_request.config,
                config_schema=service._get_config_schema(channel.type),
                is_valid=False,
                validation_errors=validation_result["errors"]
            )
        
        # 更新配置
        channel.config = config_request.config
        channel.updated_at = datetime.utcnow()
        await db.commit()
        
        # 发送WebSocket通知
        websocket_service = get_websocket_service()
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "channel_config_updated",
                "channel_id": str(channel_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # 隐藏敏感信息
        config = config_request.config.copy()
        sensitive_keys = ['password', 'secret', 'token', 'key', 'api_key']
        
        for key in config:
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                config[key] = "***"
        
        return ChannelConfigResponse(
            channel_id=str(channel_id),
            config=config,
            config_schema=service._get_config_schema(channel.type),
            is_valid=True,
            validation_errors=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating channel config {channel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))