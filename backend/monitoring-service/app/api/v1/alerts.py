#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 告警API路由

告警相关的API端点
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_permissions
from app.core.logging import get_logger, audit_log
from app.schemas.alerts import (
    AlertCreate, AlertUpdate, AlertResponse, AlertListResponse,
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse, AlertRuleListResponse,
    NotificationChannelCreate, NotificationChannelUpdate, NotificationChannelResponse,
    NotificationChannelListResponse, AlertAcknowledgeRequest, AlertResolveRequest,
    AlertSilenceRequest, AlertEscalateRequest, AlertBatchRequest,
    AlertStatsResponse, NotificationTestRequest
)
from app.schemas.common import PaginationParams, TimeRangeParams
from app.services.alerts_service import AlertsService
from app.models.user import User

# 创建路由器
router = APIRouter()
logger = get_logger(__name__)

# 依赖注入
def get_alerts_service(db: Session = Depends(get_db)) -> AlertsService:
    """获取告警服务"""
    return AlertsService(db)


# ==================== 告警管理 ====================

@router.get("/", response_model=AlertListResponse)
@require_permissions(["alerts:read"])
async def list_alerts(
    pagination: PaginationParams = Depends(),
    status: Optional[str] = Query(None, description="告警状态过滤"),
    severity: Optional[str] = Query(None, description="严重程度过滤"),
    source: Optional[str] = Query(None, description="告警源过滤"),
    time_range: TimeRangeParams = Depends(),
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """获取告警列表"""
    try:
        result = await service.get_alerts(
            skip=pagination.skip,
            limit=pagination.limit,
            status=status,
            severity=severity,
            source=source,
            start_time=time_range.start_time,
            end_time=time_range.end_time
        )
        
        logger.info(
            f"Listed alerts",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'filters': {
                    'status': status,
                    'severity': severity,
                    'source': source
                }
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取告警列表失败")


@router.post("/", response_model=AlertResponse, status_code=201)
@require_permissions(["alerts:write"])
@audit_log("create_alert", "alert")
async def create_alert(
    alert_data: AlertCreate,
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """创建新告警"""
    try:
        alert = await service.create_alert(alert_data)
        
        logger.info(
            f"Created alert: {alert.title}",
            extra={
                'user_id': current_user.id,
                'alert_id': alert.id,
                'alert_title': alert.title,
                'severity': alert.severity
            }
        )
        
        return alert
        
    except ValueError as e:
        logger.warning(f"Invalid alert data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建告警失败")


@router.get("/{alert_id}", response_model=AlertResponse)
@require_permissions(["alerts:read"])
async def get_alert(
    alert_id: int = Path(..., description="告警ID"),
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """获取告警详情"""
    try:
        alert = await service.get_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        logger.debug(
            f"Retrieved alert: {alert.title}",
            extra={
                'user_id': current_user.id,
                'alert_id': alert_id
            }
        )
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取告警详情失败")


@router.put("/{alert_id}", response_model=AlertResponse)
@require_permissions(["alerts:write"])
@audit_log("update_alert", "alert")
async def update_alert(
    alert_id: int = Path(..., description="告警ID"),
    alert_data: AlertUpdate = None,
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """更新告警"""
    try:
        alert = await service.update_alert(alert_id, alert_data)
        if not alert:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        logger.info(
            f"Updated alert: {alert.title}",
            extra={
                'user_id': current_user.id,
                'alert_id': alert_id,
                'alert_title': alert.title
            }
        )
        
        return alert
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid alert update data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新告警失败")


@router.delete("/{alert_id}", status_code=204)
@require_permissions(["alerts:delete"])
@audit_log("delete_alert", "alert")
async def delete_alert(
    alert_id: int = Path(..., description="告警ID"),
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """删除告警"""
    try:
        success = await service.delete_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        logger.info(
            f"Deleted alert",
            extra={
                'user_id': current_user.id,
                'alert_id': alert_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除告警失败")


# ==================== 告警操作 ====================

@router.post("/{alert_id}/acknowledge")
@require_permissions(["alerts:write"])
@audit_log("acknowledge_alert", "alert")
async def acknowledge_alert(
    alert_id: int = Path(..., description="告警ID"),
    ack_data: AlertAcknowledgeRequest,
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """确认告警"""
    try:
        success = await service.acknowledge_alert(alert_id, current_user.id, ack_data.comment)
        if not success:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        logger.info(
            f"Acknowledged alert",
            extra={
                'user_id': current_user.id,
                'alert_id': alert_id,
                'comment': ack_data.comment
            }
        )
        
        return {"message": "告警已确认"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="确认告警失败")


@router.post("/{alert_id}/resolve")
@require_permissions(["alerts:write"])
@audit_log("resolve_alert", "alert")
async def resolve_alert(
    alert_id: int = Path(..., description="告警ID"),
    resolve_data: AlertResolveRequest,
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """解决告警"""
    try:
        success = await service.resolve_alert(alert_id, current_user.id, resolve_data.resolution)
        if not success:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        logger.info(
            f"Resolved alert",
            extra={
                'user_id': current_user.id,
                'alert_id': alert_id,
                'resolution': resolve_data.resolution
            }
        )
        
        return {"message": "告警已解决"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="解决告警失败")


@router.post("/{alert_id}/silence")
@require_permissions(["alerts:write"])
@audit_log("silence_alert", "alert")
async def silence_alert(
    alert_id: int = Path(..., description="告警ID"),
    silence_data: AlertSilenceRequest,
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """静默告警"""
    try:
        success = await service.silence_alert(
            alert_id, 
            current_user.id, 
            silence_data.duration, 
            silence_data.reason
        )
        if not success:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        logger.info(
            f"Silenced alert",
            extra={
                'user_id': current_user.id,
                'alert_id': alert_id,
                'duration': silence_data.duration,
                'reason': silence_data.reason
            }
        )
        
        return {"message": "告警已静默"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to silence alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="静默告警失败")


@router.post("/{alert_id}/escalate")
@require_permissions(["alerts:write"])
@audit_log("escalate_alert", "alert")
async def escalate_alert(
    alert_id: int = Path(..., description="告警ID"),
    escalate_data: AlertEscalateRequest,
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """升级告警"""
    try:
        success = await service.escalate_alert(
            alert_id, 
            current_user.id, 
            escalate_data.new_severity, 
            escalate_data.reason
        )
        if not success:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        logger.info(
            f"Escalated alert",
            extra={
                'user_id': current_user.id,
                'alert_id': alert_id,
                'new_severity': escalate_data.new_severity,
                'reason': escalate_data.reason
            }
        )
        
        return {"message": "告警已升级"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to escalate alert {alert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="升级告警失败")


@router.post("/batch")
@require_permissions(["alerts:write"])
@audit_log("batch_alert_operation", "alerts")
async def batch_alert_operation(
    batch_data: AlertBatchRequest,
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """批量告警操作"""
    try:
        result = await service.batch_alert_operation(
            batch_data.alert_ids,
            batch_data.operation,
            current_user.id,
            batch_data.data
        )
        
        logger.info(
            f"Batch alert operation",
            extra={
                'user_id': current_user.id,
                'operation': batch_data.operation,
                'alert_count': len(batch_data.alert_ids),
                'success_count': result['success_count']
            }
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid batch operation data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to perform batch alert operation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="批量操作失败")


# ==================== 告警规则管理 ====================

@router.get("/rules", response_model=AlertRuleListResponse)
@require_permissions(["alerts:read"])
async def list_alert_rules(
    pagination: PaginationParams = Depends(),
    enabled_only: bool = Query(True, description="仅显示启用的规则"),
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """获取告警规则列表"""
    try:
        result = await service.get_alert_rules(
            skip=pagination.skip,
            limit=pagination.limit,
            enabled_only=enabled_only
        )
        
        logger.info(
            f"Listed alert rules",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'enabled_only': enabled_only
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list alert rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取告警规则列表失败")


@router.post("/rules", response_model=AlertRuleResponse, status_code=201)
@require_permissions(["alerts:admin"])
@audit_log("create_alert_rule", "alert_rule")
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """创建告警规则"""
    try:
        rule = await service.create_alert_rule(rule_data)
        
        logger.info(
            f"Created alert rule: {rule.name}",
            extra={
                'user_id': current_user.id,
                'rule_id': rule.id,
                'rule_name': rule.name
            }
        )
        
        return rule
        
    except ValueError as e:
        logger.warning(f"Invalid alert rule data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建告警规则失败")


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
@require_permissions(["alerts:read"])
async def get_alert_rule(
    rule_id: int = Path(..., description="规则ID"),
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """获取告警规则详情"""
    try:
        rule = await service.get_alert_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="告警规则不存在")
        
        logger.debug(
            f"Retrieved alert rule: {rule.name}",
            extra={
                'user_id': current_user.id,
                'rule_id': rule_id
            }
        )
        
        return rule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取告警规则详情失败")


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
@require_permissions(["alerts:admin"])
@audit_log("update_alert_rule", "alert_rule")
async def update_alert_rule(
    rule_id: int = Path(..., description="规则ID"),
    rule_data: AlertRuleUpdate = None,
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """更新告警规则"""
    try:
        rule = await service.update_alert_rule(rule_id, rule_data)
        if not rule:
            raise HTTPException(status_code=404, detail="告警规则不存在")
        
        logger.info(
            f"Updated alert rule: {rule.name}",
            extra={
                'user_id': current_user.id,
                'rule_id': rule_id,
                'rule_name': rule.name
            }
        )
        
        return rule
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid alert rule update data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update alert rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新告警规则失败")


@router.delete("/rules/{rule_id}", status_code=204)
@require_permissions(["alerts:admin"])
@audit_log("delete_alert_rule", "alert_rule")
async def delete_alert_rule(
    rule_id: int = Path(..., description="规则ID"),
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """删除告警规则"""
    try:
        success = await service.delete_alert_rule(rule_id)
        if not success:
            raise HTTPException(status_code=404, detail="告警规则不存在")
        
        logger.info(
            f"Deleted alert rule",
            extra={
                'user_id': current_user.id,
                'rule_id': rule_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除告警规则失败")


@router.post("/rules/{rule_id}/test")
@require_permissions(["alerts:admin"])
async def test_alert_rule(
    rule_id: int = Path(..., description="规则ID"),
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """测试告警规则"""
    try:
        result = await service.test_alert_rule(rule_id)
        
        logger.info(
            f"Tested alert rule",
            extra={
                'user_id': current_user.id,
                'rule_id': rule_id,
                'test_result': result['triggered']
            }
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid rule test: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to test alert rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="测试告警规则失败")


# ==================== 通知渠道管理 ====================

@router.get("/channels", response_model=NotificationChannelListResponse)
@require_permissions(["alerts:read"])
async def list_notification_channels(
    pagination: PaginationParams = Depends(),
    channel_type: Optional[str] = Query(None, description="渠道类型过滤"),
    enabled_only: bool = Query(True, description="仅显示启用的渠道"),
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """获取通知渠道列表"""
    try:
        result = await service.get_notification_channels(
            skip=pagination.skip,
            limit=pagination.limit,
            channel_type=channel_type,
            enabled_only=enabled_only
        )
        
        logger.info(
            f"Listed notification channels",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'channel_type': channel_type,
                'enabled_only': enabled_only
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list notification channels: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取通知渠道列表失败")


@router.post("/channels", response_model=NotificationChannelResponse, status_code=201)
@require_permissions(["alerts:admin"])
@audit_log("create_notification_channel", "notification_channel")
async def create_notification_channel(
    channel_data: NotificationChannelCreate,
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """创建通知渠道"""
    try:
        channel = await service.create_notification_channel(channel_data)
        
        logger.info(
            f"Created notification channel: {channel.name}",
            extra={
                'user_id': current_user.id,
                'channel_id': channel.id,
                'channel_name': channel.name,
                'channel_type': channel.type
            }
        )
        
        return channel
        
    except ValueError as e:
        logger.warning(f"Invalid notification channel data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create notification channel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建通知渠道失败")


@router.post("/channels/{channel_id}/test")
@require_permissions(["alerts:admin"])
async def test_notification_channel(
    channel_id: int = Path(..., description="渠道ID"),
    test_data: NotificationTestRequest,
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """测试通知渠道"""
    try:
        result = await service.test_notification_channel(channel_id, test_data.message)
        
        logger.info(
            f"Tested notification channel",
            extra={
                'user_id': current_user.id,
                'channel_id': channel_id,
                'test_result': result['success']
            }
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid channel test: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to test notification channel {channel_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="测试通知渠道失败")


# ==================== 统计信息 ====================

@router.get("/stats", response_model=AlertStatsResponse)
@require_permissions(["alerts:read"])
async def get_alerts_stats(
    time_range: TimeRangeParams = Depends(),
    service: AlertsService = Depends(get_alerts_service),
    current_user: User = Depends(get_current_user)
):
    """获取告警统计信息"""
    try:
        stats = await service.get_alerts_stats(
            start_time=time_range.start_time,
            end_time=time_range.end_time
        )
        
        logger.debug(
            f"Retrieved alerts stats",
            extra={
                'user_id': current_user.id,
                'total_alerts': stats.total_alerts
            }
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get alerts stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取告警统计信息失败")