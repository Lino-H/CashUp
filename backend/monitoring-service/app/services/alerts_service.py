#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 告警服务

告警管理、规则处理和通知的业务逻辑
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from app.core.database import get_db
from app.core.cache import CacheManager
from app.core.exceptions import AlertProcessingError, ServiceUnavailableError
from app.models.alerts import Alert, AlertRule, AlertHistory, AlertChannel, AlertStatus, AlertSeverity
from app.schemas.alerts import (
    AlertCreate, AlertUpdate, AlertRuleCreate, AlertRuleUpdate,
    AlertChannelCreate, AlertChannelUpdate, AlertSilenceRequest,
    AlertAcknowledgeRequest, AlertEscalateRequest, AlertBatchRequest
)

logger = logging.getLogger(__name__)


class AlertsService:
    """告警服务类"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.notification_queue = asyncio.Queue()
        self.processing_tasks = {}
        
    async def create_alert(self, db: Session, alert_data: AlertCreate) -> Alert:
        """创建告警"""
        try:
            # 检查是否存在相同的活跃告警
            existing_alert = db.query(Alert).filter(
                and_(
                    Alert.title == alert_data.title,
                    Alert.source == alert_data.source,
                    Alert.status.in_([AlertStatus.PENDING, AlertStatus.FIRING])
                )
            ).first()
            
            if existing_alert:
                # 更新现有告警而不是创建新的
                existing_alert.description = alert_data.description
                existing_alert.value = alert_data.value
                existing_alert.threshold = alert_data.threshold
                existing_alert.updated_at = datetime.utcnow()
                existing_alert.notification_count += 1
                
                db.commit()
                db.refresh(existing_alert)
                
                logger.info(f"Updated existing alert: {existing_alert.title} (ID: {existing_alert.id})")
                return existing_alert
            
            # 创建新告警
            alert = Alert(
                title=alert_data.title,
                description=alert_data.description,
                severity=alert_data.severity,
                alert_type=alert_data.alert_type,
                source=alert_data.source,
                rule_id=alert_data.rule_id,
                metric_id=alert_data.metric_id,
                value=alert_data.value,
                threshold=alert_data.threshold,
                assignee=alert_data.assignee,
                labels=alert_data.labels or {},
                annotations=alert_data.annotations or {},
                status=AlertStatus.PENDING
            )
            
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            # 记录告警历史
            await self._create_alert_history(
                db, alert.id, AlertStatus.PENDING, None, "system", "Alert created"
            )
            
            # 触发告警
            await self._fire_alert(db, alert)
            
            # 发送通知
            if alert_data.notification_channels:
                await self._send_notifications(db, alert, alert_data.notification_channels)
            
            # 清除相关缓存
            await self.cache.clear_pattern("alerts:*")
            
            logger.info(f"Created alert: {alert.title} (ID: {alert.id})")
            return alert
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create alert: {e}")
            raise AlertProcessingError(f"Failed to create alert: {e}")
    
    async def get_alert(self, db: Session, alert_id: int) -> Optional[Alert]:
        """获取告警详情"""
        cache_key = f"alerts:detail:{alert_id}"
        
        # 尝试从缓存获取
        cached_alert = await self.cache.get(cache_key)
        if cached_alert:
            return cached_alert
        
        # 从数据库获取
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if alert:
            # 缓存结果
            await self.cache.set(cache_key, alert, ttl=300)
        
        return alert
    
    async def get_alerts(self, db: Session, 
                        status: Optional[AlertStatus] = None,
                        severity: Optional[AlertSeverity] = None,
                        assignee: Optional[str] = None,
                        source: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: int = 100,
                        offset: int = 0) -> Tuple[List[Alert], int]:
        """获取告警列表"""
        try:
            # 构建查询
            query = db.query(Alert)
            
            # 应用过滤条件
            if status:
                query = query.filter(Alert.status == status)
            
            if severity:
                query = query.filter(Alert.severity == severity)
            
            if assignee:
                query = query.filter(Alert.assignee == assignee)
            
            if source:
                query = query.filter(Alert.source.ilike(f"%{source}%"))
            
            if start_time:
                query = query.filter(Alert.created_at >= start_time)
            
            if end_time:
                query = query.filter(Alert.created_at <= end_time)
            
            # 获取总数
            total = query.count()
            
            # 应用排序和分页
            alerts = query.order_by(desc(Alert.created_at)).offset(offset).limit(limit).all()
            
            return alerts, total
            
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            raise AlertProcessingError(f"Failed to get alerts: {e}")
    
    async def update_alert(self, db: Session, alert_id: int, alert_data: AlertUpdate) -> Optional[Alert]:
        """更新告警"""
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return None
            
            # 记录状态变更
            old_status = alert.status
            
            # 更新字段
            update_data = alert_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(alert, field, value)
            
            alert.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(alert)
            
            # 记录历史
            if alert.status != old_status:
                await self._create_alert_history(
                    db, alert.id, alert.status, old_status, "system", "Alert updated"
                )
            
            # 清除相关缓存
            await self.cache.delete(f"alerts:detail:{alert_id}")
            await self.cache.clear_pattern("alerts:*")
            
            logger.info(f"Updated alert: {alert.title} (ID: {alert.id})")
            return alert
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update alert: {e}")
            raise AlertProcessingError(f"Failed to update alert: {e}")
    
    async def acknowledge_alert(self, db: Session, alert_id: int, request: AlertAcknowledgeRequest) -> Optional[Alert]:
        """确认告警"""
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return None
            
            if alert.status in [AlertStatus.RESOLVED, AlertStatus.ACKNOWLEDGED]:
                raise ValueError(f"Alert is already {alert.status.value}")
            
            # 更新告警状态
            old_status = alert.status
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.assignee = request.operator
            alert.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(alert)
            
            # 记录历史
            await self._create_alert_history(
                db, alert.id, AlertStatus.ACKNOWLEDGED, old_status, 
                request.operator, request.reason or "Alert acknowledged"
            )
            
            # 清除相关缓存
            await self.cache.delete(f"alerts:detail:{alert_id}")
            await self.cache.clear_pattern("alerts:*")
            
            logger.info(f"Acknowledged alert: {alert.title} (ID: {alert.id}) by {request.operator}")
            return alert
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to acknowledge alert: {e}")
            raise AlertProcessingError(f"Failed to acknowledge alert: {e}")
    
    async def resolve_alert(self, db: Session, alert_id: int, operator: str, reason: Optional[str] = None) -> Optional[Alert]:
        """解决告警"""
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return None
            
            if alert.status == AlertStatus.RESOLVED:
                raise ValueError("Alert is already resolved")
            
            # 更新告警状态
            old_status = alert.status
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.assignee = operator
            alert.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(alert)
            
            # 记录历史
            await self._create_alert_history(
                db, alert.id, AlertStatus.RESOLVED, old_status, 
                operator, reason or "Alert resolved"
            )
            
            # 清除相关缓存
            await self.cache.delete(f"alerts:detail:{alert_id}")
            await self.cache.clear_pattern("alerts:*")
            
            logger.info(f"Resolved alert: {alert.title} (ID: {alert.id}) by {operator}")
            return alert
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to resolve alert: {e}")
            raise AlertProcessingError(f"Failed to resolve alert: {e}")
    
    async def silence_alert(self, db: Session, alert_id: int, request: AlertSilenceRequest) -> Optional[Alert]:
        """静默告警"""
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return None
            
            if alert.status == AlertStatus.RESOLVED:
                raise ValueError("Cannot silence resolved alert")
            
            # 更新告警状态
            old_status = alert.status
            alert.status = AlertStatus.SILENCED
            alert.silenced_until = datetime.utcnow() + timedelta(seconds=request.duration)
            alert.assignee = request.operator
            alert.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(alert)
            
            # 记录历史
            await self._create_alert_history(
                db, alert.id, AlertStatus.SILENCED, old_status, 
                request.operator, request.reason or f"Alert silenced for {request.duration} seconds"
            )
            
            # 清除相关缓存
            await self.cache.delete(f"alerts:detail:{alert_id}")
            await self.cache.clear_pattern("alerts:*")
            
            logger.info(f"Silenced alert: {alert.title} (ID: {alert.id}) by {request.operator} for {request.duration}s")
            return alert
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to silence alert: {e}")
            raise AlertProcessingError(f"Failed to silence alert: {e}")
    
    async def escalate_alert(self, db: Session, alert_id: int, request: AlertEscalateRequest) -> Optional[Alert]:
        """升级告警"""
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return None
            
            if alert.status == AlertStatus.RESOLVED:
                raise ValueError("Cannot escalate resolved alert")
            
            # 更新告警级别
            old_level = alert.escalation_level
            alert.escalation_level = request.level
            alert.assignee = request.operator
            alert.updated_at = datetime.utcnow()
            
            # 可能需要提升严重级别
            if request.level > 2 and alert.severity != AlertSeverity.CRITICAL:
                alert.severity = AlertSeverity.CRITICAL
            
            db.commit()
            db.refresh(alert)
            
            # 记录历史
            await self._create_alert_history(
                db, alert.id, alert.status, None, 
                request.operator, 
                request.reason or f"Alert escalated from level {old_level} to {request.level}",
                {"escalation_level": request.level, "old_level": old_level}
            )
            
            # 发送升级通知
            if request.notification_channels:
                await self._send_escalation_notifications(db, alert, request.notification_channels)
            
            # 清除相关缓存
            await self.cache.delete(f"alerts:detail:{alert_id}")
            await self.cache.clear_pattern("alerts:*")
            
            logger.info(f"Escalated alert: {alert.title} (ID: {alert.id}) to level {request.level} by {request.operator}")
            return alert
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to escalate alert: {e}")
            raise AlertProcessingError(f"Failed to escalate alert: {e}")
    
    async def batch_acknowledge_alerts(self, db: Session, request: AlertBatchRequest) -> Dict[str, Any]:
        """批量确认告警"""
        try:
            results = {"success": [], "failed": []}
            
            for alert_id in request.alert_ids:
                try:
                    alert = db.query(Alert).filter(Alert.id == alert_id).first()
                    if not alert:
                        results["failed"].append({"id": alert_id, "error": "Alert not found"})
                        continue
                    
                    if alert.status in [AlertStatus.RESOLVED, AlertStatus.ACKNOWLEDGED]:
                        results["failed"].append({"id": alert_id, "error": f"Alert is already {alert.status.value}"})
                        continue
                    
                    # 更新告警状态
                    old_status = alert.status
                    alert.status = AlertStatus.ACKNOWLEDGED
                    alert.acknowledged_at = datetime.utcnow()
                    alert.assignee = request.operator
                    alert.updated_at = datetime.utcnow()
                    
                    # 记录历史
                    await self._create_alert_history(
                        db, alert.id, AlertStatus.ACKNOWLEDGED, old_status, 
                        request.operator, request.reason or "Batch acknowledgment"
                    )
                    
                    results["success"].append(alert_id)
                    
                except Exception as e:
                    results["failed"].append({"id": alert_id, "error": str(e)})
            
            db.commit()
            
            # 清除相关缓存
            await self.cache.clear_pattern("alerts:*")
            
            logger.info(f"Batch acknowledged {len(results['success'])} alerts by {request.operator}")
            return results
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to batch acknowledge alerts: {e}")
            raise AlertProcessingError(f"Failed to batch acknowledge alerts: {e}")
    
    async def batch_resolve_alerts(self, db: Session, request: AlertBatchRequest) -> Dict[str, Any]:
        """批量解决告警"""
        try:
            results = {"success": [], "failed": []}
            
            for alert_id in request.alert_ids:
                try:
                    alert = db.query(Alert).filter(Alert.id == alert_id).first()
                    if not alert:
                        results["failed"].append({"id": alert_id, "error": "Alert not found"})
                        continue
                    
                    if alert.status == AlertStatus.RESOLVED:
                        results["failed"].append({"id": alert_id, "error": "Alert is already resolved"})
                        continue
                    
                    # 更新告警状态
                    old_status = alert.status
                    alert.status = AlertStatus.RESOLVED
                    alert.resolved_at = datetime.utcnow()
                    alert.assignee = request.operator
                    alert.updated_at = datetime.utcnow()
                    
                    # 记录历史
                    await self._create_alert_history(
                        db, alert.id, AlertStatus.RESOLVED, old_status, 
                        request.operator, request.reason or "Batch resolution"
                    )
                    
                    results["success"].append(alert_id)
                    
                except Exception as e:
                    results["failed"].append({"id": alert_id, "error": str(e)})
            
            db.commit()
            
            # 清除相关缓存
            await self.cache.clear_pattern("alerts:*")
            
            logger.info(f"Batch resolved {len(results['success'])} alerts by {request.operator}")
            return results
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to batch resolve alerts: {e}")
            raise AlertProcessingError(f"Failed to batch resolve alerts: {e}")
    
    # 告警规则管理
    async def create_alert_rule(self, db: Session, rule_data: AlertRuleCreate) -> AlertRule:
        """创建告警规则"""
        try:
            # 检查规则名称是否已存在
            existing = db.query(AlertRule).filter(AlertRule.name == rule_data.name).first()
            if existing:
                raise ValueError(f"Alert rule '{rule_data.name}' already exists")
            
            # 创建告警规则
            rule = AlertRule(
                name=rule_data.name,
                description=rule_data.description,
                alert_type=rule_data.alert_type,
                severity=rule_data.severity,
                condition=rule_data.condition,
                threshold=rule_data.threshold,
                comparison_operator=rule_data.comparison_operator,
                evaluation_window=rule_data.evaluation_window,
                evaluation_interval=rule_data.evaluation_interval,
                metric_id=rule_data.metric_id,
                enabled=rule_data.enabled,
                notification_channels=rule_data.notification_channels or [],
                escalation_rules=rule_data.escalation_rules or [],
                silence_duration=rule_data.silence_duration,
                max_notifications=rule_data.max_notifications,
                labels=rule_data.labels or {}
            )
            
            db.add(rule)
            db.commit()
            db.refresh(rule)
            
            # 清除相关缓存
            await self.cache.clear_pattern("alert_rules:*")
            
            logger.info(f"Created alert rule: {rule.name} (ID: {rule.id})")
            return rule
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create alert rule: {e}")
            raise AlertProcessingError(f"Failed to create alert rule: {e}")
    
    # 通知渠道管理
    async def create_alert_channel(self, db: Session, channel_data: AlertChannelCreate) -> AlertChannel:
        """创建通知渠道"""
        try:
            # 检查渠道名称是否已存在
            existing = db.query(AlertChannel).filter(AlertChannel.name == channel_data.name).first()
            if existing:
                raise ValueError(f"Alert channel '{channel_data.name}' already exists")
            
            # 创建通知渠道
            channel = AlertChannel(
                name=channel_data.name,
                description=channel_data.description,
                channel_type=channel_data.channel_type,
                config=channel_data.config,
                enabled=channel_data.enabled,
                retry_count=channel_data.retry_count,
                retry_interval=channel_data.retry_interval,
                timeout=channel_data.timeout
            )
            
            db.add(channel)
            db.commit()
            db.refresh(channel)
            
            # 清除相关缓存
            await self.cache.clear_pattern("alert_channels:*")
            
            logger.info(f"Created alert channel: {channel.name} (ID: {channel.id})")
            return channel
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create alert channel: {e}")
            raise AlertProcessingError(f"Failed to create alert channel: {e}")
    
    async def test_alert_channel(self, db: Session, channel_id: int) -> Dict[str, Any]:
        """测试通知渠道"""
        try:
            channel = db.query(AlertChannel).filter(AlertChannel.id == channel_id).first()
            if not channel:
                raise ValueError(f"Alert channel with ID {channel_id} not found")
            
            # 发送测试消息
            test_message = {
                "title": "Test Alert",
                "message": "This is a test message from CashUp monitoring system",
                "severity": "info",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self._send_notification(channel, test_message)
            
            # 更新渠道统计
            if result["success"]:
                channel.success_count += 1
                channel.last_used_at = datetime.utcnow()
            else:
                channel.failure_count += 1
            
            db.commit()
            
            logger.info(f"Tested alert channel: {channel.name} (ID: {channel.id})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to test alert channel: {e}")
            raise AlertProcessingError(f"Failed to test alert channel: {e}")
    
    async def get_alert_statistics(self, db: Session) -> Dict[str, Any]:
        """获取告警统计信息"""
        try:
            cache_key = "alerts:statistics"
            
            # 尝试从缓存获取
            cached_stats = await self.cache.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # 基础统计
            total_alerts = db.query(Alert).count()
            active_alerts = db.query(Alert).filter(
                Alert.status.in_([AlertStatus.PENDING, AlertStatus.FIRING])
            ).count()
            resolved_alerts = db.query(Alert).filter(Alert.status == AlertStatus.RESOLVED).count()
            acknowledged_alerts = db.query(Alert).filter(Alert.status == AlertStatus.ACKNOWLEDGED).count()
            silenced_alerts = db.query(Alert).filter(Alert.status == AlertStatus.SILENCED).count()
            
            # 按严重级别统计
            severity_stats = db.query(
                Alert.severity,
                func.count(Alert.id)
            ).group_by(Alert.severity).all()
            
            # 按类型统计
            type_stats = db.query(
                Alert.alert_type,
                func.count(Alert.id)
            ).group_by(Alert.alert_type).all()
            
            # 按来源统计
            source_stats = db.query(
                Alert.source,
                func.count(Alert.id)
            ).group_by(Alert.source).all()
            
            # 计算平均解决时间
            resolved_with_time = db.query(Alert).filter(
                and_(
                    Alert.status == AlertStatus.RESOLVED,
                    Alert.resolved_at.isnot(None)
                )
            ).all()
            
            avg_resolution_time = 0
            if resolved_with_time:
                total_resolution_time = sum(
                    (alert.resolved_at - alert.created_at).total_seconds() / 60
                    for alert in resolved_with_time
                )
                avg_resolution_time = total_resolution_time / len(resolved_with_time)
            
            # 计算平均确认时间
            acknowledged_with_time = db.query(Alert).filter(
                and_(
                    Alert.acknowledged_at.isnot(None)
                )
            ).all()
            
            avg_acknowledgment_time = 0
            if acknowledged_with_time:
                total_ack_time = sum(
                    (alert.acknowledged_at - alert.created_at).total_seconds() / 60
                    for alert in acknowledged_with_time
                )
                avg_acknowledgment_time = total_ack_time / len(acknowledged_with_time)
            
            stats = {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "resolved_alerts": resolved_alerts,
                "acknowledged_alerts": acknowledged_alerts,
                "silenced_alerts": silenced_alerts,
                "critical_alerts": dict(severity_stats).get(AlertSeverity.CRITICAL, 0),
                "high_alerts": dict(severity_stats).get(AlertSeverity.HIGH, 0),
                "medium_alerts": dict(severity_stats).get(AlertSeverity.MEDIUM, 0),
                "low_alerts": dict(severity_stats).get(AlertSeverity.LOW, 0),
                "avg_resolution_time": avg_resolution_time,
                "avg_acknowledgment_time": avg_acknowledgment_time,
                "severity_distribution": dict(severity_stats),
                "type_distribution": dict(type_stats),
                "source_distribution": dict(source_stats)
            }
            
            # 缓存结果
            await self.cache.set(cache_key, stats, ttl=300)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get alert statistics: {e}")
            raise AlertProcessingError(f"Failed to get alert statistics: {e}")
    
    async def _fire_alert(self, db: Session, alert: Alert):
        """触发告警"""
        try:
            alert.status = AlertStatus.FIRING
            alert.fired_at = datetime.utcnow()
            alert.updated_at = datetime.utcnow()
            
            db.commit()
            
            # 记录历史
            await self._create_alert_history(
                db, alert.id, AlertStatus.FIRING, AlertStatus.PENDING, "system", "Alert fired"
            )
            
            logger.info(f"Fired alert: {alert.title} (ID: {alert.id})")
            
        except Exception as e:
            logger.error(f"Failed to fire alert: {e}")
    
    async def _create_alert_history(self, db: Session, alert_id: int, status: AlertStatus, 
                                   previous_status: Optional[AlertStatus], operator: str, 
                                   reason: str, details: Optional[Dict[str, Any]] = None):
        """创建告警历史记录"""
        try:
            history = AlertHistory(
                alert_id=alert_id,
                status=status,
                previous_status=previous_status,
                operator=operator,
                reason=reason,
                details=details or {}
            )
            
            db.add(history)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create alert history: {e}")
    
    async def _send_notifications(self, db: Session, alert: Alert, channel_ids: List[int]):
        """发送通知"""
        try:
            channels = db.query(AlertChannel).filter(
                and_(
                    AlertChannel.id.in_(channel_ids),
                    AlertChannel.enabled == True
                )
            ).all()
            
            message = {
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "source": alert.source,
                "value": alert.value,
                "threshold": alert.threshold,
                "timestamp": alert.created_at.isoformat(),
                "alert_id": alert.id
            }
            
            for channel in channels:
                try:
                    await self._send_notification(channel, message)
                    
                    # 更新通知统计
                    alert.notification_count += 1
                    alert.last_notification_at = datetime.utcnow()
                    
                    channel.success_count += 1
                    channel.last_used_at = datetime.utcnow()
                    
                except Exception as e:
                    logger.error(f"Failed to send notification via channel {channel.id}: {e}")
                    channel.failure_count += 1
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
    
    async def _send_notification(self, channel: AlertChannel, message: Dict[str, Any]) -> Dict[str, Any]:
        """发送单个通知"""
        try:
            # 根据渠道类型发送通知
            formatted_message = channel.format_message(message)
            
            # 这里应该实现具体的通知发送逻辑
            # 根据channel.channel_type调用相应的发送方法
            
            # 示例实现
            logger.info(f"Sending notification via {channel.channel_type}: {formatted_message}")
            
            return {
                "success": True,
                "message": "Notification sent successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _send_escalation_notifications(self, db: Session, alert: Alert, channel_ids: List[int]):
        """发送升级通知"""
        try:
            channels = db.query(AlertChannel).filter(
                and_(
                    AlertChannel.id.in_(channel_ids),
                    AlertChannel.enabled == True
                )
            ).all()
            
            message = {
                "title": f"ESCALATED: {alert.title}",
                "description": f"Alert has been escalated to level {alert.escalation_level}. {alert.description}",
                "severity": "critical",
                "source": alert.source,
                "escalation_level": alert.escalation_level,
                "timestamp": datetime.utcnow().isoformat(),
                "alert_id": alert.id
            }
            
            for channel in channels:
                try:
                    await self._send_notification(channel, message)
                except Exception as e:
                    logger.error(f"Failed to send escalation notification via channel {channel.id}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to send escalation notifications: {e}")