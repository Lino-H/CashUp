#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 告警API端点

提供告警管理、规则配置和通知的API接口
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....schemas.alerts import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertChannelCreate,
    AlertChannelUpdate,
    AlertChannelResponse,
    AlertHistoryResponse,
    AlertSilenceRequest,
    AlertAcknowledgeRequest,
    AlertEscalateRequest,
    AlertBatchRequest,
    AlertStatisticsResponse
)
from ....services.alerts import AlertService
from ....services.notifications import NotificationService
from ....core.exceptions import (
    AlertProcessingError,
    ConfigurationError,
    ServiceUnavailableError
)

logger = logging.getLogger(__name__)

router = APIRouter()


# 告警实例管理
@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    status: Optional[str] = Query(None, description="告警状态"),
    severity: Optional[str] = Query(None, description="严重级别"),
    assignee: Optional[str] = Query(None, description="处理人"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取告警列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        status: 告警状态过滤
        severity: 严重级别过滤
        assignee: 处理人过滤
        start_time: 开始时间过滤
        end_time: 结束时间过滤
        search: 搜索关键词
        db: 数据库会话
        
    Returns:
        List[AlertResponse]: 告警列表
    """
    try:
        alert_service = AlertService(db)
        alerts = await alert_service.list_alerts(
            skip=skip,
            limit=limit,
            status=status,
            severity=severity,
            assignee=assignee,
            start_time=start_time,
            end_time=end_time,
            search=search
        )
        return alerts
    except Exception as e:
        logger.error(f"Failed to list alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db)
):
    """
    创建新告警
    
    Args:
        alert: 告警创建数据
        db: 数据库会话
        
    Returns:
        AlertResponse: 创建的告警
    """
    try:
        alert_service = AlertService(db)
        created_alert = await alert_service.create_alert(alert)
        return created_alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int = Path(..., description="告警ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定告警详情
    
    Args:
        alert_id: 告警ID
        db: 数据库会话
        
    Returns:
        AlertResponse: 告警详情
    """
    try:
        alert_service = AlertService(db)
        alert = await alert_service.get_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert")


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int = Path(..., description="告警ID"),
    alert_update: AlertUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新告警
    
    Args:
        alert_id: 告警ID
        alert_update: 告警更新数据
        db: 数据库会话
        
    Returns:
        AlertResponse: 更新后的告警
    """
    try:
        alert_service = AlertService(db)
        updated_alert = await alert_service.update_alert(alert_id, alert_update)
        if not updated_alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return updated_alert
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert")


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int = Path(..., description="告警ID"),
    db: Session = Depends(get_db)
):
    """
    删除告警
    
    Args:
        alert_id: 告警ID
        db: 数据库会话
        
    Returns:
        dict: 删除结果
    """
    try:
        alert_service = AlertService(db)
        success = await alert_service.delete_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert")


# 告警操作
@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int = Path(..., description="告警ID"),
    request: AlertAcknowledgeRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    确认告警
    
    Args:
        alert_id: 告警ID
        request: 确认请求
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        alert_service = AlertService(db)
        success = await alert_service.acknowledge_alert(
            alert_id,
            request.operator,
            request.reason
        )
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert acknowledged successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int = Path(..., description="告警ID"),
    request: AlertAcknowledgeRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    解决告警
    
    Args:
        alert_id: 告警ID
        request: 解决请求
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        alert_service = AlertService(db)
        success = await alert_service.resolve_alert(
            alert_id,
            request.operator,
            request.reason
        )
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert resolved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


@router.post("/{alert_id}/silence")
async def silence_alert(
    alert_id: int = Path(..., description="告警ID"),
    request: AlertSilenceRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    静默告警
    
    Args:
        alert_id: 告警ID
        request: 静默请求
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        alert_service = AlertService(db)
        success = await alert_service.silence_alert(
            alert_id,
            request.duration,
            request.operator,
            request.reason
        )
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert silenced successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to silence alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to silence alert")


@router.post("/{alert_id}/escalate")
async def escalate_alert(
    alert_id: int = Path(..., description="告警ID"),
    request: AlertEscalateRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    升级告警
    
    Args:
        alert_id: 告警ID
        request: 升级请求
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        alert_service = AlertService(db)
        success = await alert_service.escalate_alert(
            alert_id,
            request.level,
            request.operator,
            request.reason
        )
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"message": "Alert escalated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to escalate alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to escalate alert")


# 批量操作
@router.post("/batch/acknowledge")
async def batch_acknowledge_alerts(
    request: AlertBatchRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    批量确认告警
    
    Args:
        request: 批量操作请求
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        alert_service = AlertService(db)
        result = await alert_service.batch_acknowledge_alerts(
            request.alert_ids,
            request.operator,
            request.reason
        )
        return result
    except Exception as e:
        logger.error(f"Failed to batch acknowledge alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch acknowledge alerts")


@router.post("/batch/resolve")
async def batch_resolve_alerts(
    request: AlertBatchRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    批量解决告警
    
    Args:
        request: 批量操作请求
        db: 数据库会话
        
    Returns:
        dict: 操作结果
    """
    try:
        alert_service = AlertService(db)
        result = await alert_service.batch_resolve_alerts(
            request.alert_ids,
            request.operator,
            request.reason
        )
        return result
    except Exception as e:
        logger.error(f"Failed to batch resolve alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch resolve alerts")


# 告警规则管理
@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    enabled: Optional[bool] = Query(None, description="是否启用"),
    alert_type: Optional[str] = Query(None, description="告警类型"),
    severity: Optional[str] = Query(None, description="严重级别"),
    db: Session = Depends(get_db)
):
    """
    获取告警规则列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        enabled: 是否启用过滤
        alert_type: 告警类型过滤
        severity: 严重级别过滤
        db: 数据库会话
        
    Returns:
        List[AlertRuleResponse]: 告警规则列表
    """
    try:
        alert_service = AlertService(db)
        rules = await alert_service.list_alert_rules(
            skip=skip,
            limit=limit,
            enabled=enabled,
            alert_type=alert_type,
            severity=severity
        )
        return rules
    except Exception as e:
        logger.error(f"Failed to list alert rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert rules")


@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule: AlertRuleCreate,
    db: Session = Depends(get_db)
):
    """
    创建告警规则
    
    Args:
        rule: 告警规则创建数据
        db: 数据库会话
        
    Returns:
        AlertRuleResponse: 创建的告警规则
    """
    try:
        alert_service = AlertService(db)
        created_rule = await alert_service.create_alert_rule(rule)
        return created_rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert rule")


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: int = Path(..., description="规则ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定告警规则详情
    
    Args:
        rule_id: 规则ID
        db: 数据库会话
        
    Returns:
        AlertRuleResponse: 告警规则详情
    """
    try:
        alert_service = AlertService(db)
        rule = await alert_service.get_alert_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert rule")


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int = Path(..., description="规则ID"),
    rule_update: AlertRuleUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新告警规则
    
    Args:
        rule_id: 规则ID
        rule_update: 规则更新数据
        db: 数据库会话
        
    Returns:
        AlertRuleResponse: 更新后的告警规则
    """
    try:
        alert_service = AlertService(db)
        updated_rule = await alert_service.update_alert_rule(rule_id, rule_update)
        if not updated_rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        return updated_rule
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update alert rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert rule")


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int = Path(..., description="规则ID"),
    db: Session = Depends(get_db)
):
    """
    删除告警规则
    
    Args:
        rule_id: 规则ID
        db: 数据库会话
        
    Returns:
        dict: 删除结果
    """
    try:
        alert_service = AlertService(db)
        success = await alert_service.delete_alert_rule(rule_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        return {"message": "Alert rule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert rule")


# 通知渠道管理
@router.get("/channels", response_model=List[AlertChannelResponse])
async def list_alert_channels(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    channel_type: Optional[str] = Query(None, description="渠道类型"),
    enabled: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db)
):
    """
    获取告警通知渠道列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        channel_type: 渠道类型过滤
        enabled: 是否启用过滤
        db: 数据库会话
        
    Returns:
        List[AlertChannelResponse]: 通知渠道列表
    """
    try:
        alert_service = AlertService(db)
        channels = await alert_service.list_alert_channels(
            skip=skip,
            limit=limit,
            channel_type=channel_type,
            enabled=enabled
        )
        return channels
    except Exception as e:
        logger.error(f"Failed to list alert channels: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert channels")


@router.post("/channels", response_model=AlertChannelResponse)
async def create_alert_channel(
    channel: AlertChannelCreate,
    db: Session = Depends(get_db)
):
    """
    创建告警通知渠道
    
    Args:
        channel: 通知渠道创建数据
        db: 数据库会话
        
    Returns:
        AlertChannelResponse: 创建的通知渠道
    """
    try:
        alert_service = AlertService(db)
        created_channel = await alert_service.create_alert_channel(channel)
        return created_channel
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create alert channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert channel")


@router.get("/channels/{channel_id}", response_model=AlertChannelResponse)
async def get_alert_channel(
    channel_id: int = Path(..., description="渠道ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定告警通知渠道详情
    
    Args:
        channel_id: 渠道ID
        db: 数据库会话
        
    Returns:
        AlertChannelResponse: 通知渠道详情
    """
    try:
        alert_service = AlertService(db)
        channel = await alert_service.get_alert_channel(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Alert channel not found")
        return channel
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert channel")


@router.put("/channels/{channel_id}", response_model=AlertChannelResponse)
async def update_alert_channel(
    channel_id: int = Path(..., description="渠道ID"),
    channel_update: AlertChannelUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新告警通知渠道
    
    Args:
        channel_id: 渠道ID
        channel_update: 渠道更新数据
        db: 数据库会话
        
    Returns:
        AlertChannelResponse: 更新后的通知渠道
    """
    try:
        alert_service = AlertService(db)
        updated_channel = await alert_service.update_alert_channel(channel_id, channel_update)
        if not updated_channel:
            raise HTTPException(status_code=404, detail="Alert channel not found")
        return updated_channel
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update alert channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert channel")


@router.delete("/channels/{channel_id}")
async def delete_alert_channel(
    channel_id: int = Path(..., description="渠道ID"),
    db: Session = Depends(get_db)
):
    """
    删除告警通知渠道
    
    Args:
        channel_id: 渠道ID
        db: 数据库会话
        
    Returns:
        dict: 删除结果
    """
    try:
        alert_service = AlertService(db)
        success = await alert_service.delete_alert_channel(channel_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert channel not found")
        return {"message": "Alert channel deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert channel")


@router.post("/channels/{channel_id}/test")
async def test_alert_channel(
    channel_id: int = Path(..., description="渠道ID"),
    db: Session = Depends(get_db)
):
    """
    测试告警通知渠道
    
    Args:
        channel_id: 渠道ID
        db: 数据库会话
        
    Returns:
        dict: 测试结果
    """
    try:
        alert_service = AlertService(db)
        result = await alert_service.test_alert_channel(channel_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test alert channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to test alert channel")


# 告警历史
@router.get("/{alert_id}/history", response_model=List[AlertHistoryResponse])
async def get_alert_history(
    alert_id: int = Path(..., description="告警ID"),
    db: Session = Depends(get_db)
):
    """
    获取告警历史记录
    
    Args:
        alert_id: 告警ID
        db: 数据库会话
        
    Returns:
        List[AlertHistoryResponse]: 告警历史记录
    """
    try:
        alert_service = AlertService(db)
        history = await alert_service.get_alert_history(alert_id)
        return history
    except Exception as e:
        logger.error(f"Failed to get alert history for alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert history")


# 告警统计
@router.get("/statistics", response_model=AlertStatisticsResponse)
async def get_alert_statistics(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    group_by: Optional[str] = Query("status", description="分组字段"),
    db: Session = Depends(get_db)
):
    """
    获取告警统计信息
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        group_by: 分组字段 (status, severity, type)
        db: 数据库会话
        
    Returns:
        AlertStatisticsResponse: 告警统计信息
    """
    try:
        # 设置默认时间范围
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=7)
        
        alert_service = AlertService(db)
        statistics = await alert_service.get_alert_statistics(
            start_time=start_time,
            end_time=end_time,
            group_by=group_by
        )
        return statistics
    except Exception as e:
        logger.error(f"Failed to get alert statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert statistics")