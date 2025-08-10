#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 告警数据库模型

定义告警相关的数据库模型
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from .base import BaseModel, TimestampMixin, SoftDeleteMixin, MetadataMixin, StatusMixin


class Alert(BaseModel, SoftDeleteMixin, MetadataMixin):
    """告警模型"""
    
    __tablename__ = 'alerts'
    
    # 基本信息
    title = Column(
        String(255),
        nullable=False,
        comment="告警标题"
    )
    
    message = Column(
        Text,
        nullable=True,
        comment="告警消息"
    )
    
    # 告警级别
    severity = Column(
        String(20),
        nullable=False,
        default='warning',
        comment="告警级别：critical, warning, info"
    )
    
    # 告警状态
    alert_status = Column(
        String(20),
        nullable=False,
        default='firing',
        comment="告警状态：firing, resolved, silenced, acknowledged"
    )
    
    # 关联信息
    rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey('alert_rules.id', ondelete='SET NULL'),
        nullable=True,
        comment="告警规则ID"
    )
    
    metric_id = Column(
        UUID(as_uuid=True),
        ForeignKey('metrics.id', ondelete='SET NULL'),
        nullable=True,
        comment="关联指标ID"
    )
    
    # 时间信息
    fired_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="触发时间"
    )
    
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="解决时间"
    )
    
    acknowledged_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="确认时间"
    )
    
    silenced_until = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="静默到期时间"
    )
    
    # 值信息
    current_value = Column(
        Float,
        nullable=True,
        comment="当前值"
    )
    
    threshold_value = Column(
        Float,
        nullable=True,
        comment="阈值"
    )
    
    # 标签和注释
    labels = Column(
        JSONB,
        nullable=True,
        comment="标签"
    )
    
    annotations = Column(
        JSONB,
        nullable=True,
        comment="注释"
    )
    
    # 处理信息
    assigned_to = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="分配给用户ID"
    )
    
    acknowledged_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="确认用户ID"
    )
    
    resolved_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="解决用户ID"
    )
    
    # 通知信息
    notification_sent = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已发送通知"
    )
    
    notification_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="通知次数"
    )
    
    last_notification_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后通知时间"
    )
    
    # 关系
    rule = relationship("AlertRule", back_populates="alerts")
    metric = relationship("Metric")
    history = relationship(
        "AlertHistory",
        back_populates="alert",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_alerts_status', 'alert_status'),
        Index('idx_alerts_severity', 'severity'),
        Index('idx_alerts_rule_id', 'rule_id'),
        Index('idx_alerts_metric_id', 'metric_id'),
        Index('idx_alerts_fired_at', 'fired_at'),
        Index('idx_alerts_resolved_at', 'resolved_at'),
        Index('idx_alerts_assigned_to', 'assigned_to'),
        Index('idx_alerts_labels', 'labels', postgresql_using='gin'),
        Index('idx_alerts_deleted', 'is_deleted'),
        CheckConstraint(
            "severity IN ('critical', 'warning', 'info')",
            name='ck_alerts_severity'
        ),
        CheckConstraint(
            "alert_status IN ('firing', 'resolved', 'silenced', 'acknowledged')",
            name='ck_alerts_status'
        ),
    )
    
    def get_labels(self) -> Dict[str, str]:
        """获取标签"""
        return self.labels or {}
    
    def set_labels(self, labels: Dict[str, str]):
        """设置标签"""
        self.labels = labels
    
    def get_annotations(self) -> Dict[str, str]:
        """获取注释"""
        return self.annotations or {}
    
    def set_annotations(self, annotations: Dict[str, str]):
        """设置注释"""
        self.annotations = annotations
    
    def is_firing(self) -> bool:
        """是否正在触发"""
        return self.alert_status == 'firing'
    
    def is_resolved(self) -> bool:
        """是否已解决"""
        return self.alert_status == 'resolved'
    
    def is_acknowledged(self) -> bool:
        """是否已确认"""
        return self.alert_status == 'acknowledged'
    
    def is_silenced(self) -> bool:
        """是否已静默"""
        return self.alert_status == 'silenced' and (
            self.silenced_until is None or self.silenced_until > datetime.utcnow()
        )
    
    def is_critical(self) -> bool:
        """是否为严重告警"""
        return self.severity == 'critical'
    
    def is_warning(self) -> bool:
        """是否为警告告警"""
        return self.severity == 'warning'
    
    def is_info(self) -> bool:
        """是否为信息告警"""
        return self.severity == 'info'
    
    def get_duration(self) -> Optional[timedelta]:
        """获取告警持续时间"""
        if self.resolved_at:
            return self.resolved_at - self.fired_at
        return datetime.utcnow() - self.fired_at
    
    def acknowledge(self, user_id: uuid.UUID, message: Optional[str] = None):
        """确认告警"""
        self.alert_status = 'acknowledged'
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user_id
        if message:
            annotations = self.get_annotations()
            annotations['acknowledgment_message'] = message
            self.set_annotations(annotations)
    
    def resolve(self, user_id: uuid.UUID, message: Optional[str] = None):
        """解决告警"""
        self.alert_status = 'resolved'
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user_id
        if message:
            annotations = self.get_annotations()
            annotations['resolution_message'] = message
            self.set_annotations(annotations)
    
    def silence(self, duration_minutes: int, user_id: uuid.UUID, reason: Optional[str] = None):
        """静默告警"""
        self.alert_status = 'silenced'
        self.silenced_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        if reason:
            annotations = self.get_annotations()
            annotations['silence_reason'] = reason
            annotations['silenced_by'] = str(user_id)
            self.set_annotations(annotations)
    
    def assign_to(self, user_id: uuid.UUID):
        """分配告警"""
        self.assigned_to = user_id


class AlertRule(BaseModel, SoftDeleteMixin, MetadataMixin, StatusMixin):
    """告警规则模型"""
    
    __tablename__ = 'alert_rules'
    
    # 基本信息
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="规则名称"
    )
    
    display_name = Column(
        String(255),
        nullable=True,
        comment="显示名称"
    )
    
    # 规则配置
    expression = Column(
        Text,
        nullable=False,
        comment="规则表达式"
    )
    
    condition = Column(
        String(10),
        nullable=False,
        comment="条件：>, <, >=, <=, ==, !="
    )
    
    threshold = Column(
        Float,
        nullable=False,
        comment="阈值"
    )
    
    # 时间配置
    evaluation_interval = Column(
        Integer,
        nullable=False,
        default=60,
        comment="评估间隔（秒）"
    )
    
    for_duration = Column(
        Integer,
        nullable=False,
        default=300,
        comment="持续时间（秒）"
    )
    
    # 告警配置
    severity = Column(
        String(20),
        nullable=False,
        default='warning',
        comment="告警级别"
    )
    
    alert_template = Column(
        JSONB,
        nullable=True,
        comment="告警模板"
    )
    
    # 通知配置
    notification_channels = Column(
        JSONB,
        nullable=True,
        comment="通知渠道"
    )
    
    notification_interval = Column(
        Integer,
        nullable=False,
        default=3600,
        comment="通知间隔（秒）"
    )
    
    max_notifications = Column(
        Integer,
        nullable=False,
        default=10,
        comment="最大通知次数"
    )
    
    # 标签和注释
    labels = Column(
        JSONB,
        nullable=True,
        comment="标签"
    )
    
    annotations = Column(
        JSONB,
        nullable=True,
        comment="注释"
    )
    
    # 统计信息
    last_evaluation = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后评估时间"
    )
    
    evaluation_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="评估次数"
    )
    
    alert_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="告警次数"
    )
    
    # 关系
    alerts = relationship(
        "Alert",
        back_populates="rule",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_alert_rules_name', 'name'),
        Index('idx_alert_rules_status', 'status'),
        Index('idx_alert_rules_severity', 'severity'),
        Index('idx_alert_rules_last_evaluation', 'last_evaluation'),
        Index('idx_alert_rules_deleted', 'is_deleted'),
        CheckConstraint(
            "severity IN ('critical', 'warning', 'info')",
            name='ck_alert_rules_severity'
        ),
        CheckConstraint(
            "condition IN ('>', '<', '>=', '<=', '==', '!=')",
            name='ck_alert_rules_condition'
        ),
        CheckConstraint(
            "evaluation_interval > 0",
            name='ck_alert_rules_evaluation_interval'
        ),
        CheckConstraint(
            "for_duration >= 0",
            name='ck_alert_rules_for_duration'
        ),
    )
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return self.display_name or self.name
    
    def get_labels(self) -> Dict[str, str]:
        """获取标签"""
        return self.labels or {}
    
    def set_labels(self, labels: Dict[str, str]):
        """设置标签"""
        self.labels = labels
    
    def get_annotations(self) -> Dict[str, str]:
        """获取注释"""
        return self.annotations or {}
    
    def set_annotations(self, annotations: Dict[str, str]):
        """设置注释"""
        self.annotations = annotations
    
    def get_alert_template(self) -> Dict[str, Any]:
        """获取告警模板"""
        return self.alert_template or {}
    
    def set_alert_template(self, template: Dict[str, Any]):
        """设置告警模板"""
        self.alert_template = template
    
    def get_notification_channels(self) -> List[str]:
        """获取通知渠道"""
        return self.notification_channels or []
    
    def set_notification_channels(self, channels: List[str]):
        """设置通知渠道"""
        self.notification_channels = channels
    
    def should_evaluate(self) -> bool:
        """是否应该评估"""
        if not self.is_active():
            return False
        
        if self.last_evaluation is None:
            return True
        
        next_evaluation = self.last_evaluation + timedelta(seconds=self.evaluation_interval)
        return datetime.utcnow() >= next_evaluation
    
    def evaluate_condition(self, value: float) -> bool:
        """评估条件"""
        if self.condition == '>':
            return value > self.threshold
        elif self.condition == '<':
            return value < self.threshold
        elif self.condition == '>=':
            return value >= self.threshold
        elif self.condition == '<=':
            return value <= self.threshold
        elif self.condition == '==':
            return value == self.threshold
        elif self.condition == '!=':
            return value != self.threshold
        return False


class AlertHistory(BaseModel):
    """告警历史模型"""
    
    __tablename__ = 'alert_history'
    
    # 关联告警
    alert_id = Column(
        UUID(as_uuid=True),
        ForeignKey('alerts.id', ondelete='CASCADE'),
        nullable=False,
        comment="告警ID"
    )
    
    # 操作类型
    action = Column(
        String(50),
        nullable=False,
        comment="操作类型：created, acknowledged, resolved, silenced, escalated, assigned"
    )
    
    # 操作用户
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="操作用户ID"
    )
    
    # 操作时间
    action_time = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="操作时间"
    )
    
    # 操作详情
    details = Column(
        JSONB,
        nullable=True,
        comment="操作详情"
    )
    
    # 备注
    comment = Column(
        Text,
        nullable=True,
        comment="备注"
    )
    
    # 关系
    alert = relationship("Alert", back_populates="history")
    
    # 索引
    __table_args__ = (
        Index('idx_alert_history_alert_id', 'alert_id'),
        Index('idx_alert_history_action', 'action'),
        Index('idx_alert_history_user_id', 'user_id'),
        Index('idx_alert_history_action_time', 'action_time'),
        CheckConstraint(
            "action IN ('created', 'acknowledged', 'resolved', 'silenced', 'escalated', 'assigned', 'updated')",
            name='ck_alert_history_action'
        ),
    )
    
    def get_details(self) -> Dict[str, Any]:
        """获取操作详情"""
        return self.details or {}
    
    def set_details(self, details: Dict[str, Any]):
        """设置操作详情"""
        self.details = details


class NotificationChannel(BaseModel, SoftDeleteMixin, StatusMixin):
    """通知渠道模型"""
    
    __tablename__ = 'notification_channels'
    
    # 基本信息
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="渠道名称"
    )
    
    display_name = Column(
        String(255),
        nullable=True,
        comment="显示名称"
    )
    
    # 渠道类型
    channel_type = Column(
        String(50),
        nullable=False,
        comment="渠道类型：email, slack, webhook, sms, dingtalk, wechat"
    )
    
    # 配置信息
    config = Column(
        JSONB,
        nullable=False,
        comment="渠道配置"
    )
    
    # 模板配置
    message_template = Column(
        JSONB,
        nullable=True,
        comment="消息模板"
    )
    
    # 过滤条件
    filters = Column(
        JSONB,
        nullable=True,
        comment="过滤条件"
    )
    
    # 限流配置
    rate_limit = Column(
        Integer,
        nullable=True,
        comment="限流（每小时最大消息数）"
    )
    
    # 统计信息
    total_sent = Column(
        Integer,
        default=0,
        nullable=False,
        comment="总发送数"
    )
    
    total_failed = Column(
        Integer,
        default=0,
        nullable=False,
        comment="总失败数"
    )
    
    last_sent_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后发送时间"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_notification_channels_name', 'name'),
        Index('idx_notification_channels_type', 'channel_type'),
        Index('idx_notification_channels_status', 'status'),
        Index('idx_notification_channels_deleted', 'is_deleted'),
        CheckConstraint(
            "channel_type IN ('email', 'slack', 'webhook', 'sms', 'dingtalk', 'wechat')",
            name='ck_notification_channels_type'
        ),
    )
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return self.display_name or self.name
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config or {}
    
    def set_config(self, config: Dict[str, Any]):
        """设置配置"""
        self.config = config
    
    def get_message_template(self) -> Dict[str, str]:
        """获取消息模板"""
        return self.message_template or {}
    
    def set_message_template(self, template: Dict[str, str]):
        """设置消息模板"""
        self.message_template = template
    
    def get_filters(self) -> Dict[str, Any]:
        """获取过滤条件"""
        return self.filters or {}
    
    def set_filters(self, filters: Dict[str, Any]):
        """设置过滤条件"""
        self.filters = filters
    
    def should_send_alert(self, alert: Alert) -> bool:
        """是否应该发送告警"""
        if not self.is_active():
            return False
        
        filters = self.get_filters()
        if not filters:
            return True
        
        # 检查严重级别过滤
        if 'severities' in filters:
            if alert.severity not in filters['severities']:
                return False
        
        # 检查标签过滤
        if 'labels' in filters:
            alert_labels = alert.get_labels()
            for key, value in filters['labels'].items():
                if alert_labels.get(key) != value:
                    return False
        
        return True
    
    def increment_sent(self):
        """增加发送计数"""
        self.total_sent += 1
        self.last_sent_at = datetime.utcnow()
    
    def increment_failed(self):
        """增加失败计数"""
        self.total_failed += 1