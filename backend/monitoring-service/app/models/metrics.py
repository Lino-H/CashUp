#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 指标数据库模型

定义指标相关的数据库模型
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from .base import BaseModel, TimestampMixin, SoftDeleteMixin, MetadataMixin, StatusMixin


class Metric(BaseModel, SoftDeleteMixin, MetadataMixin, StatusMixin):
    """指标模型"""
    
    __tablename__ = 'metrics'
    
    # 基本信息
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="指标名称"
    )
    
    display_name = Column(
        String(255),
        nullable=True,
        comment="显示名称"
    )
    
    metric_type = Column(
        String(50),
        nullable=False,
        default='gauge',
        comment="指标类型：gauge, counter, histogram, summary"
    )
    
    unit = Column(
        String(50),
        nullable=True,
        comment="单位"
    )
    
    # 数据源信息
    source_type = Column(
        String(100),
        nullable=False,
        comment="数据源类型"
    )
    
    source_config = Column(
        JSONB,
        nullable=True,
        comment="数据源配置"
    )
    
    # 收集配置
    collection_interval = Column(
        Integer,
        nullable=False,
        default=60,
        comment="收集间隔（秒）"
    )
    
    retention_days = Column(
        Integer,
        nullable=False,
        default=30,
        comment="数据保留天数"
    )
    
    # 聚合配置
    aggregation_config = Column(
        JSONB,
        nullable=True,
        comment="聚合配置"
    )
    
    # 启用状态
    enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )

    # 告警配置
    alert_enabled = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否启用告警"
    )

    alert_rules = Column(
        JSONB,
        nullable=True,
        comment="告警规则"
    )
    
    # 关系
    values = relationship(
        "MetricValue",
        back_populates="metric",
        cascade="all, delete-orphan"
    )
    
    tags = relationship(
        "MetricTag",
        back_populates="metric",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_metrics_name', 'name'),
        Index('idx_metrics_type', 'metric_type'),
        Index('idx_metrics_source_type', 'source_type'),
        Index('idx_metrics_status', 'status'),
        Index('idx_metrics_deleted', 'is_deleted'),
        CheckConstraint(
            "metric_type IN ('gauge', 'counter', 'histogram', 'summary')",
            name='ck_metrics_type'
        ),
        CheckConstraint(
            "collection_interval > 0",
            name='ck_metrics_collection_interval'
        ),
        CheckConstraint(
            "retention_days > 0",
            name='ck_metrics_retention_days'
        ),
    )
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return self.display_name or self.name
    
    def get_source_config(self) -> Dict[str, Any]:
        """获取数据源配置"""
        return self.source_config or {}
    
    def set_source_config(self, config: Dict[str, Any]):
        """设置数据源配置"""
        self.source_config = config
    
    def get_aggregation_config(self) -> Dict[str, Any]:
        """获取聚合配置"""
        return self.aggregation_config or {}
    
    def set_aggregation_config(self, config: Dict[str, Any]):
        """设置聚合配置"""
        self.aggregation_config = config
    
    def get_alert_rules(self) -> List[Dict[str, Any]]:
        """获取告警规则"""
        return self.alert_rules or []
    
    def set_alert_rules(self, rules: List[Dict[str, Any]]):
        """设置告警规则"""
        self.alert_rules = rules
    
    def is_counter(self) -> bool:
        """是否为计数器类型"""
        return self.metric_type == 'counter'
    
    def is_gauge(self) -> bool:
        """是否为仪表类型"""
        return self.metric_type == 'gauge'
    
    def is_histogram(self) -> bool:
        """是否为直方图类型"""
        return self.metric_type == 'histogram'
    
    def is_summary(self) -> bool:
        """是否为摘要类型"""
        return self.metric_type == 'summary'


class MetricValue(BaseModel):
    """指标值模型"""
    
    __tablename__ = 'metric_values'
    
    # 关联指标
    metric_id = Column(
        UUID(as_uuid=True),
        ForeignKey('metrics.id', ondelete='CASCADE'),
        nullable=False,
        comment="指标ID"
    )
    
    # 时间戳
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="时间戳"
    )
    
    # 值
    value = Column(
        Float,
        nullable=False,
        comment="指标值"
    )
    
    # 标签
    labels = Column(
        JSONB,
        nullable=True,
        comment="标签"
    )
    
    # 额外数据（用于histogram和summary）
    extra_data = Column(
        JSONB,
        nullable=True,
        comment="额外数据"
    )
    
    # 数据质量
    quality_score = Column(
        Float,
        nullable=True,
        comment="数据质量评分"
    )
    
    # 关系
    metric = relationship("Metric", back_populates="values")
    
    # 索引
    __table_args__ = (
        Index('idx_metric_values_metric_id', 'metric_id'),
        Index('idx_metric_values_timestamp', 'timestamp'),
        Index('idx_metric_values_metric_timestamp', 'metric_id', 'timestamp'),
        Index('idx_metric_values_labels', 'labels', postgresql_using='gin'),
        UniqueConstraint(
            'metric_id', 'timestamp', 'labels',
            name='uq_metric_values_metric_timestamp_labels'
        ),
    )
    
    def get_labels(self) -> Dict[str, str]:
        """获取标签"""
        return self.labels or {}
    
    def set_labels(self, labels: Dict[str, str]):
        """设置标签"""
        self.labels = labels
    
    def get_extra_data(self) -> Dict[str, Any]:
        """获取额外数据"""
        return self.extra_data or {}
    
    def set_extra_data(self, data: Dict[str, Any]):
        """设置额外数据"""
        self.extra_data = data
    
    def has_label(self, key: str, value: Optional[str] = None) -> bool:
        """检查是否有指定标签"""
        labels = self.get_labels()
        if value is None:
            return key in labels
        return labels.get(key) == value
    
    def get_label_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取标签值"""
        return self.get_labels().get(key, default)


class MetricTag(BaseModel):
    """指标标签模型"""
    
    __tablename__ = 'metric_tags'
    
    # 关联指标
    metric_id = Column(
        UUID(as_uuid=True),
        ForeignKey('metrics.id', ondelete='CASCADE'),
        nullable=False,
        comment="指标ID"
    )
    
    # 标签键
    key = Column(
        String(255),
        nullable=False,
        comment="标签键"
    )
    
    # 标签值
    value = Column(
        String(255),
        nullable=False,
        comment="标签值"
    )
    
    # 标签类型
    tag_type = Column(
        String(50),
        nullable=False,
        default='custom',
        comment="标签类型：system, custom, auto"
    )
    
    # 关系
    metric = relationship("Metric", back_populates="tags")
    
    # 索引
    __table_args__ = (
        Index('idx_metric_tags_metric_id', 'metric_id'),
        Index('idx_metric_tags_key', 'key'),
        Index('idx_metric_tags_value', 'value'),
        Index('idx_metric_tags_type', 'tag_type'),
        UniqueConstraint(
            'metric_id', 'key',
            name='uq_metric_tags_metric_key'
        ),
        CheckConstraint(
            "tag_type IN ('system', 'custom', 'auto')",
            name='ck_metric_tags_type'
        ),
    )


class MetricAggregation(BaseModel):
    """指标聚合模型"""
    
    __tablename__ = 'metric_aggregations'
    
    # 关联指标
    metric_id = Column(
        UUID(as_uuid=True),
        ForeignKey('metrics.id', ondelete='CASCADE'),
        nullable=False,
        comment="指标ID"
    )
    
    # 聚合类型
    aggregation_type = Column(
        String(50),
        nullable=False,
        comment="聚合类型：avg, sum, min, max, count, p50, p90, p95, p99"
    )
    
    # 时间窗口
    time_window = Column(
        String(50),
        nullable=False,
        comment="时间窗口：1m, 5m, 15m, 1h, 6h, 1d, 7d, 30d"
    )
    
    # 时间戳
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="时间戳"
    )
    
    # 聚合值
    value = Column(
        Float,
        nullable=False,
        comment="聚合值"
    )
    
    # 样本数量
    sample_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="样本数量"
    )
    
    # 标签
    labels = Column(
        JSONB,
        nullable=True,
        comment="标签"
    )
    
    # 关系
    metric = relationship("Metric")
    
    # 索引
    __table_args__ = (
        Index('idx_metric_agg_metric_id', 'metric_id'),
        Index('idx_metric_agg_type', 'aggregation_type'),
        Index('idx_metric_agg_window', 'time_window'),
        Index('idx_metric_agg_timestamp', 'timestamp'),
        Index('idx_metric_agg_metric_type_window_timestamp', 
              'metric_id', 'aggregation_type', 'time_window', 'timestamp'),
        UniqueConstraint(
            'metric_id', 'aggregation_type', 'time_window', 'timestamp', 'labels',
            name='uq_metric_agg_unique'
        ),
        CheckConstraint(
            "aggregation_type IN ('avg', 'sum', 'min', 'max', 'count', 'p50', 'p90', 'p95', 'p99')",
            name='ck_metric_agg_type'
        ),
        CheckConstraint(
            "time_window IN ('1m', '5m', '15m', '1h', '6h', '1d', '7d', '30d')",
            name='ck_metric_agg_window'
        ),
    )
    
    def get_labels(self) -> Dict[str, str]:
        """获取标签"""
        return self.labels or {}
    
    def set_labels(self, labels: Dict[str, str]):
        """设置标签"""
        self.labels = labels


class MetricThreshold(BaseModel, StatusMixin):
    """指标阈值模型"""
    
    __tablename__ = 'metric_thresholds'
    
    # 关联指标
    metric_id = Column(
        UUID(as_uuid=True),
        ForeignKey('metrics.id', ondelete='CASCADE'),
        nullable=False,
        comment="指标ID"
    )
    
    # 阈值名称
    name = Column(
        String(255),
        nullable=False,
        comment="阈值名称"
    )
    
    # 阈值类型
    threshold_type = Column(
        String(50),
        nullable=False,
        comment="阈值类型：warning, critical, info"
    )
    
    # 比较操作符
    operator = Column(
        String(10),
        nullable=False,
        comment="比较操作符：>, <, >=, <=, ==, !="
    )
    
    # 阈值
    threshold_value = Column(
        Float,
        nullable=False,
        comment="阈值"
    )
    
    # 持续时间
    duration_seconds = Column(
        Integer,
        nullable=False,
        default=60,
        comment="持续时间（秒）"
    )
    
    # 条件
    conditions = Column(
        JSONB,
        nullable=True,
        comment="额外条件"
    )
    
    # 关系
    metric = relationship("Metric")
    
    # 索引
    __table_args__ = (
        Index('idx_metric_thresholds_metric_id', 'metric_id'),
        Index('idx_metric_thresholds_type', 'threshold_type'),
        Index('idx_metric_thresholds_status', 'status'),
        UniqueConstraint(
            'metric_id', 'name',
            name='uq_metric_thresholds_metric_name'
        ),
        CheckConstraint(
            "threshold_type IN ('warning', 'critical', 'info')",
            name='ck_metric_thresholds_type'
        ),
        CheckConstraint(
            "operator IN ('>', '<', '>=', '<=', '==', '!=')",
            name='ck_metric_thresholds_operator'
        ),
        CheckConstraint(
            "duration_seconds > 0",
            name='ck_metric_thresholds_duration'
        ),
    )
    
    def get_conditions(self) -> Dict[str, Any]:
        """获取条件"""
        return self.conditions or {}
    
    def set_conditions(self, conditions: Dict[str, Any]):
        """设置条件"""
        self.conditions = conditions
    
    def evaluate(self, value: float) -> bool:
        """评估阈值"""
        if self.operator == '>':
            return value > self.threshold_value
        elif self.operator == '<':
            return value < self.threshold_value
        elif self.operator == '>=':
            return value >= self.threshold_value
        elif self.operator == '<=':
            return value <= self.threshold_value
        elif self.operator == '==':
            return value == self.threshold_value
        elif self.operator == '!=':
            return value != self.threshold_value
        return False


class MetricAlert(BaseModel, TimestampMixin, StatusMixin):
    """指标告警模型"""
    
    __tablename__ = 'metric_alerts'
    
    # 关联指标
    metric_id = Column(
        UUID(as_uuid=True),
        ForeignKey('metrics.id', ondelete='CASCADE'),
        nullable=False,
        comment="指标ID"
    )
    
    # 告警名称
    name = Column(
        String(255),
        nullable=False,
        comment="告警名称"
    )
    
    # 告警级别
    severity = Column(
        String(50),
        nullable=False,
        default='warning',
        comment="告警级别：info, warning, critical"
    )
    
    # 告警规则
    rule_expression = Column(
        Text,
        nullable=False,
        comment="告警规则表达式"
    )
    
    # 告警条件
    conditions = Column(
        JSONB,
        nullable=True,
        comment="告警条件"
    )
    
    # 触发时间
    triggered_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="触发时间"
    )
    
    # 恢复时间
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="恢复时间"
    )
    
    # 告警状态
    alert_status = Column(
        String(50),
        nullable=False,
        default='pending',
        comment="告警状态：pending, firing, resolved"
    )
    
    # 告警消息
    message = Column(
        Text,
        nullable=True,
        comment="告警消息"
    )
    
    # 标签
    labels = Column(
        JSONB,
        nullable=True,
        comment="标签"
    )
    
    # 注释
    annotations = Column(
        JSONB,
        nullable=True,
        comment="注释"
    )
    
    # 关系
    metric = relationship("Metric")
    
    # 索引
    __table_args__ = (
        Index('idx_metric_alerts_metric_id', 'metric_id'),
        Index('idx_metric_alerts_severity', 'severity'),
        Index('idx_metric_alerts_status', 'alert_status'),
        Index('idx_metric_alerts_triggered_at', 'triggered_at'),
        Index('idx_metric_alerts_resolved_at', 'resolved_at'),
        CheckConstraint(
            "severity IN ('info', 'warning', 'critical')",
            name='ck_metric_alerts_severity'
        ),
        CheckConstraint(
            "alert_status IN ('pending', 'firing', 'resolved')",
            name='ck_metric_alerts_status'
        ),
    )
    
    def get_conditions(self) -> Dict[str, Any]:
        """获取告警条件"""
        return self.conditions or {}
    
    def set_conditions(self, conditions: Dict[str, Any]):
        """设置告警条件"""
        self.conditions = conditions
    
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
        """是否正在告警"""
        return self.alert_status == 'firing'
    
    def is_resolved(self) -> bool:
        """是否已恢复"""
        return self.alert_status == 'resolved'
    
    def is_pending(self) -> bool:
        """是否待处理"""
        return self.alert_status == 'pending'
    
    def trigger(self, message: str = None):
        """触发告警"""
        self.alert_status = 'firing'
        self.triggered_at = func.now()
        if message:
            self.message = message
    
    def resolve(self, message: str = None):
        """恢复告警"""
        self.alert_status = 'resolved'
        self.resolved_at = func.now()
        if message:
            self.message = message


# 枚举类型
class MetricType:
    """指标类型枚举"""
    GAUGE = 'gauge'
    COUNTER = 'counter'
    HISTOGRAM = 'histogram'
    SUMMARY = 'summary'


class MetricStatus:
    """指标状态枚举"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    DISABLED = 'disabled'
    ERROR = 'error'