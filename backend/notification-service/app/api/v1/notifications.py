#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知API路由

处理通知相关的API请求
"""

import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user
from ...models.notification import NotificationStatus, NotificationPriority
from ...schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationListResponse,
    NotificationBatchCreate,
    NotificationBatchResponse,
    NotificationFilter,
    NotificationStatsResponse,
    NotificationRetry,
    NotificationRetryResponse,
    NotificationCancel,
    NotificationCancelResponse,
    NotificationPreview,
    NotificationPreviewResponse,
    NotificationStatusUpdate
)
from ...schemas.common import (
    BaseResponse,
    PaginationParams,
    ExportRequest,
    ExportResponse
)
from ...services.notification_service import NotificationService
from ...services.websocket_service import websocket_service

import logging

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# 依赖注入
def get_notification_service() -> NotificationService:
    return NotificationService()


@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    创建通知
    
    Args:
        notification: 通知创建请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        NotificationResponse: 创建的通知信息
    """
    try:
        # 创建通知
        created_notification = await service.create_notification(
            db=db,
            notification_data=notification,
            user_id=current_user["user_id"]
        )
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_notification_update,
            str(created_notification.id),
            {
                "type": "notification_created",
                "notification_id": str(created_notification.id),
                "status": created_notification.status.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return NotificationResponse.from_orm(created_notification)
        
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=NotificationBatchResponse)
async def create_batch_notifications(
    batch_request: NotificationBatchCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    批量创建通知
    
    Args:
        batch_request: 批量创建请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        NotificationBatchResponse: 批量创建结果
    """
    try:
        # 批量创建通知
        result = await service.create_batch_notifications(
            db=db,
            notifications_data=batch_request.notifications,
            user_id=current_user["user_id"]
        )
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "batch_notifications_created",
                "success_count": result["success_count"],
                "failed_count": result["failed_count"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return NotificationBatchResponse(**result)
        
    except Exception as e:
        logger.error(f"Error creating batch notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    pagination: PaginationParams = Depends(),
    filters: NotificationFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    获取通知列表
    
    Args:
        pagination: 分页参数
        filters: 过滤参数
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        NotificationListResponse: 通知列表
    """
    try:
        # 获取通知列表
        notifications, total = await service.get_notifications(
            db=db,
            skip=pagination.skip,
            limit=pagination.limit,
            filters=filters
        )
        
        return NotificationListResponse(
            items=[NotificationResponse.from_orm(n) for n in notifications],
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    获取单个通知
    
    Args:
        notification_id: 通知ID
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        NotificationResponse: 通知信息
    """
    try:
        notification = await service.get_notification(db, notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return NotificationResponse.from_orm(notification)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: uuid.UUID,
    notification_update: NotificationUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    更新通知
    
    Args:
        notification_id: 通知ID
        notification_update: 更新数据
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        NotificationResponse: 更新后的通知信息
    """
    try:
        updated_notification = await service.update_notification(
            db=db,
            notification_id=notification_id,
            notification_data=notification_update
        )
        
        if not updated_notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_notification_update,
            str(notification_id),
            {
                "type": "notification_updated",
                "notification_id": str(notification_id),
                "status": updated_notification.status.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return NotificationResponse.from_orm(updated_notification)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{notification_id}/status", response_model=NotificationResponse)
async def update_notification_status(
    notification_id: uuid.UUID,
    status_update: NotificationStatusUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    更新通知状态
    
    Args:
        notification_id: 通知ID
        status_update: 状态更新数据
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        NotificationResponse: 更新后的通知信息
    """
    try:
        updated_notification = await service.update_notification_status(
            db=db,
            notification_id=notification_id,
            status=status_update.status,
            error_message=status_update.error_message,
            delivery_info=status_update.delivery_info
        )
        
        if not updated_notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_notification_update,
            str(notification_id),
            {
                "type": "notification_status_updated",
                "notification_id": str(notification_id),
                "status": updated_notification.status.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return NotificationResponse.from_orm(updated_notification)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification status {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}", response_model=BaseResponse)
async def delete_notification(
    notification_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    删除通知
    
    Args:
        notification_id: 通知ID
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        BaseResponse: 删除结果
    """
    try:
        success = await service.delete_notification(db, notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_notification_update,
            str(notification_id),
            {
                "type": "notification_deleted",
                "notification_id": str(notification_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return BaseResponse(
            success=True,
            message="Notification deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/retry", response_model=NotificationRetryResponse)
async def retry_notification(
    notification_id: uuid.UUID,
    retry_request: NotificationRetry,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    重试通知发送
    
    Args:
        notification_id: 通知ID
        retry_request: 重试请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        NotificationRetryResponse: 重试结果
    """
    try:
        result = await service.retry_notification(
            db=db,
            notification_id=notification_id,
            channel_ids=retry_request.channel_ids,
            delay_minutes=retry_request.delay_minutes
        )
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_notification_update,
            str(notification_id),
            {
                "type": "notification_retry_scheduled",
                "notification_id": str(notification_id),
                "retry_count": result["retry_count"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return NotificationRetryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error retrying notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/cancel", response_model=NotificationCancelResponse)
async def cancel_notification(
    notification_id: uuid.UUID,
    cancel_request: NotificationCancel,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    取消通知发送
    
    Args:
        notification_id: 通知ID
        cancel_request: 取消请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        NotificationCancelResponse: 取消结果
    """
    try:
        result = await service.cancel_notification(
            db=db,
            notification_id=notification_id,
            reason=cancel_request.reason
        )
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_notification_update,
            str(notification_id),
            {
                "type": "notification_cancelled",
                "notification_id": str(notification_id),
                "reason": cancel_request.reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return NotificationCancelResponse(**result)
        
    except Exception as e:
        logger.error(f"Error cancelling notification {notification_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview", response_model=NotificationPreviewResponse)
async def preview_notification(
    preview_request: NotificationPreview,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    预览通知内容
    
    Args:
        preview_request: 预览请求
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        NotificationPreviewResponse: 预览结果
    """
    try:
        # 这里应该调用模板服务进行预览
        # 为了演示，返回模拟数据
        preview_data = {
            "subject": f"Preview: {preview_request.template_id}",
            "content": "This is a preview of the notification content.",
            "html_content": "<p>This is a preview of the notification content.</p>",
            "variables_used": list(preview_request.variables.keys()) if preview_request.variables else [],
            "estimated_size": 1024
        }
        
        return NotificationPreviewResponse(**preview_data)
        
    except Exception as e:
        logger.error(f"Error previewing notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    start_date: Optional[datetime] = Query(None, description="统计开始日期"),
    end_date: Optional[datetime] = Query(None, description="统计结束日期"),
    channel_id: Optional[uuid.UUID] = Query(None, description="渠道ID过滤"),
    template_id: Optional[uuid.UUID] = Query(None, description="模板ID过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    获取通知统计信息
    
    Args:
        start_date: 统计开始日期
        end_date: 统计结束日期
        channel_id: 渠道ID过滤
        template_id: 模板ID过滤
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        NotificationStatsResponse: 统计信息
    """
    try:
        stats = await service.get_notification_stats(
            db=db,
            start_date=start_date,
            end_date=end_date,
            channel_id=channel_id,
            template_id=template_id
        )
        
        return NotificationStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ExportResponse)
async def export_notifications(
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    导出通知数据
    
    Args:
        export_request: 导出请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 通知服务
        
    Returns:
        ExportResponse: 导出结果
    """
    try:
        # 这里应该实现实际的导出逻辑
        # 为了演示，返回模拟数据
        export_id = str(uuid.uuid4())
        
        # 添加后台任务处理导出
        background_tasks.add_task(
            _process_export,
            export_id,
            export_request,
            current_user["user_id"]
        )
        
        return ExportResponse(
            export_id=export_id,
            status="processing",
            message="Export task has been queued",
            estimated_completion=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error exporting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_export(
    export_id: str,
    export_request: ExportRequest,
    user_id: str
):
    """
    处理导出任务
    
    Args:
        export_id: 导出ID
        export_request: 导出请求
        user_id: 用户ID
    """
    try:
        # 这里应该实现实际的导出逻辑
        await asyncio.sleep(5)  # 模拟处理时间
        
        # 发送完成通知
        await websocket_service.send_user_message(
            user_id,
            {
                "type": "export_completed",
                "export_id": export_id,
                "download_url": f"/api/v1/exports/{export_id}/download",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing export {export_id}: {str(e)}")
        
        # 发送失败通知
        await websocket_service.send_user_message(
            user_id,
            {
                "type": "export_failed",
                "export_id": export_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )