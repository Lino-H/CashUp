#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 告警数据模式

定义告警相关的API请求和响应数据模式
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class AlertStatusEnum(str, Enum):
    """告警状态枚举"""
    PENDING = "pending"
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SILENCED = "silenced"
    EXPIRED = "expired"


class AlertSeverityEnum(str, Enum):
    """告警严重级别枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertTypeEnum(str, Enum):
    """告警类型枚举"""
    METRIC = "metric"
    SYSTEM = "system"
    APPLICATION = "application"
    BUSINESS = "business"
    CUSTOM = "custom"


class ChannelTypeEnum(str, Enum):
    """通知渠道类型枚举"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DINGTALK = "dingtalk"
    WECHAT = "wechat"
    TELEGRAM = "telegram"


# 告警基础模式
class AlertBase(BaseModel):
    """告警基础模式"""
    title: str = Field(..., description="告警标题", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="告警描述", max_length=1000)
    severity: AlertSeverityEnum = Field(..., description="严重级别")
    alert_type: AlertTypeEnum = Field(..., description="告警类型")
    source: str = Field(..., description="告警源", max_length=255)
    labels: Optional[Dict[str, str]] = Field(default_factory=dict, description="告警标签")
    annotations: Optional[Dict[str, str]] = Field(default_factory=dict, description="告警注释")


class AlertCreate(AlertBase):
    """创建告警请求模式"""
    rule_id: Optional[int] = Field(None, description="关联规则ID")
    metric_id: Optional[int] = Field(None, description="关联指标ID")
    value: Optional[float] = Field(None, description="触发值")
    threshold: Optional[float] = Field(None, description="阈值")
    assignee: Optional[str] = Field(None, description="处理人", max_length=100)
    notification_channels: Optional[List[int]] = Field(default_factory=list, description="通知渠道ID列表")


class AlertUpdate(BaseModel):
    """更新告警请求模式"""
    title: Optional[str] = Field(None, description="告警标题", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="告警描述", max_length=1000)
    severity: Optional[AlertSeverityEnum] = Field(None, description="严重级别")
    status: Optional[AlertStatusEnum] = Field(None, description="告警状态")
    assignee: Optional[str] = Field(None, description="处理人", max_length=100)
    labels: Optional[Dict[str, str]] = Field(None, description="告警标签")
    annotations: Optional[Dict[str, str]] = Field(None, description="告警注释")
    notification_channels: Optional[List[int]] = Field(None, description="通知渠道ID列表")


class AlertResponse(AlertBase):
    """告警响应模式"""
    id: int = Field(..., description="告警ID")
    status: AlertStatusEnum = Field(..., description="告警状态")
    rule_id: Optional[int] = Field(None, description="关联规则ID")
    metric_id: Optional[int] = Field(None, description="关联指标ID")
    value: Optional[float] = Field(None, description="触发值")
    threshold: Optional[float] = Field(None, description="阈值")
    assignee: Optional[str] = Field(None, description="处理人")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    fired_at: Optional[datetime] = Field(None, description="触发时间")
    acknowledged_at: Optional[datetime] = Field(None, description="确认时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    silenced_until: Optional[datetime] = Field(None, description="静默到期时间")
    escalation_level: int = Field(0, description="升级级别")
    notification_count: int = Field(0, description="通知次数")
    last_notification_at: Optional[datetime] = Field(None, description="最后通知时间")
    
    class Config:
        from_attributes = True


# 告警规则模式
class AlertRuleBase(BaseModel):
    """告警规则基础模式"""
    name: str = Field(..., description="规则名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="规则描述", max_length=1000)
    alert_type: AlertTypeEnum = Field(..., description="告警类型")
    severity: AlertSeverityEnum = Field(..., description="严重级别")
    condition: str = Field(..., description="告警条件", max_length=1000)
    threshold: float = Field(..., description="阈值")
    comparison_operator: str = Field(..., description="比较操作符")
    evaluation_window: int = Field(300, description="评估窗口(秒)", ge=60, le=3600)
    evaluation_interval: int = Field(60, description="评估间隔(秒)", ge=30, le=600)
    
    @validator('comparison_operator')
    def validate_operator(cls, v):
        """验证比较操作符"""
        valid_operators = ['>', '>=', '<', '<=', '==', '!=']
        if v not in valid_operators:
            raise ValueError(f'Invalid comparison operator. Must be one of: {valid_operators}')
        return v


class AlertRuleCreate(AlertRuleBase):
    """创建告警规则请求模式"""
    metric_id: Optional[int] = Field(None, description="关联指标ID")
    enabled: bool = Field(True, description="是否启用")
    notification_channels: Optional[List[int]] = Field(default_factory=list, description="通知渠道ID列表")
    escalation_rules: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="升级规则")
    silence_duration: Optional[int] = Field(None, description="静默时长(秒)", ge=60)
    max_notifications: Optional[int] = Field(None, description="最大通知次数", ge=1, le=100)
    labels: Optional[Dict[str, str]] = Field(default_factory=dict, description="规则标签")


class AlertRuleUpdate(BaseModel):
    """更新告警规则请求模式"""
    name: Optional[str] = Field(None, description="规则名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="规则描述", max_length=1000)
    severity: Optional[AlertSeverityEnum] = Field(None, description="严重级别")
    condition: Optional[str] = Field(None, description="告警条件", max_length=1000)
    threshold: Optional[float] = Field(None, description="阈值")
    comparison_operator: Optional[str] = Field(None, description="比较操作符")
    evaluation_window: Optional[int] = Field(None, description="评估窗口(秒)", ge=60, le=3600)
    evaluation_interval: Optional[int] = Field(None, description="评估间隔(秒)", ge=30, le=600)
    enabled: Optional[bool] = Field(None, description="是否启用")
    notification_channels: Optional[List[int]] = Field(None, description="通知渠道ID列表")
    escalation_rules: Optional[List[Dict[str, Any]]] = Field(None, description="升级规则")
    silence_duration: Optional[int] = Field(None, description="静默时长(秒)", ge=60)
    max_notifications: Optional[int] = Field(None, description="最大通知次数", ge=1, le=100)
    labels: Optional[Dict[str, str]] = Field(None, description="规则标签")


class AlertRuleResponse(AlertRuleBase):
    """告警规则响应模式"""
    id: int = Field(..., description="规则ID")
    metric_id: Optional[int] = Field(None, description="关联指标ID")
    enabled: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_evaluated_at: Optional[datetime] = Field(None, description="最后评估时间")
    last_triggered_at: Optional[datetime] = Field(None, description="最后触发时间")
    trigger_count: int = Field(0, description="触发次数")
    notification_channels: List[int] = Field(default_factory=list, description="通知渠道ID列表")
    escalation_rules: List[Dict[str, Any]] = Field(default_factory=list, description="升级规则")
    silence_duration: Optional[int] = Field(None, description="静默时长(秒)")
    max_notifications: Optional[int] = Field(None, description="最大通知次数")
    labels: Dict[str, str] = Field(default_factory=dict, description="规则标签")
    
    class Config:
        from_attributes = True


# 通知渠道模式
class AlertChannelBase(BaseModel):
    """通知渠道基础模式"""
    name: str = Field(..., description="渠道名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="渠道描述", max_length=1000)
    channel_type: ChannelTypeEnum = Field(..., description="渠道类型")
    config: Dict[str, Any] = Field(..., description="渠道配置")
    
    @validator('config')
    def validate_config(cls, v, values):
        """验证渠道配置"""
        channel_type = values.get('channel_type')
        if channel_type == ChannelTypeEnum.EMAIL:
            required_fields = ['smtp_host', 'smtp_port', 'username', 'password', 'recipients']
        elif channel_type == ChannelTypeEnum.WEBHOOK:
            required_fields = ['url', 'method']
        elif channel_type == ChannelTypeEnum.SLACK:
            required_fields = ['webhook_url', 'channel']
        else:
            required_fields = []
        
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field "{field}" for {channel_type} channel')
        
        return v


class AlertChannelCreate(AlertChannelBase):
    """创建通知渠道请求模式"""
    enabled: bool = Field(True, description="是否启用")
    retry_count: int = Field(3, description="重试次数", ge=0, le=10)
    retry_interval: int = Field(60, description="重试间隔(秒)", ge=30, le=600)
    timeout: int = Field(30, description="超时时间(秒)", ge=5, le=300)


class AlertChannelUpdate(BaseModel):
    """更新通知渠道请求模式"""
    name: Optional[str] = Field(None, description="渠道名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="渠道描述", max_length=1000)
    config: Optional[Dict[str, Any]] = Field(None, description="渠道配置")
    enabled: Optional[bool] = Field(None, description="是否启用")
    retry_count: Optional[int] = Field(None, description="重试次数", ge=0, le=10)
    retry_interval: Optional[int] = Field(None, description="重试间隔(秒)", ge=30, le=600)
    timeout: Optional[int] = Field(None, description="超时时间(秒)", ge=5, le=300)


class AlertChannelResponse(AlertChannelBase):
    """通知渠道响应模式"""
    id: int = Field(..., description="渠道ID")
    enabled: bool = Field(..., description="是否启用")
    retry_count: int = Field(..., description="重试次数")
    retry_interval: int = Field(..., description="重试间隔(秒)")
    timeout: int = Field(..., description="超时时间(秒)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    success_count: int = Field(0, description="成功次数")
    failure_count: int = Field(0, description="失败次数")
    
    class Config:
        from_attributes = True


# 告警历史模式
class AlertHistoryResponse(BaseModel):
    """告警历史响应模式"""
    id: int = Field(..., description="历史ID")
    alert_id: int = Field(..., description="告警ID")
    status: AlertStatusEnum = Field(..., description="状态")
    previous_status: Optional[AlertStatusEnum] = Field(None, description="前一状态")
    operator: Optional[str] = Field(None, description="操作人")
    reason: Optional[str] = Field(None, description="操作原因")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


# 告警操作请求模式
class AlertSilenceRequest(BaseModel):
    """告警静默请求模式"""
    duration: int = Field(..., description="静默时长(秒)", ge=60, le=86400)
    operator: str = Field(..., description="操作人", max_length=100)
    reason: Optional[str] = Field(None, description="静默原因", max_length=500)


class AlertAcknowledgeRequest(BaseModel):
    """告警确认请求模式"""
    operator: str = Field(..., description="操作人", max_length=100)
    reason: Optional[str] = Field(None, description="确认原因", max_length=500)


class AlertEscalateRequest(BaseModel):
    """告警升级请求模式"""
    level: int = Field(..., description="升级级别", ge=1, le=5)
    operator: str = Field(..., description="操作人", max_length=100)
    reason: Optional[str] = Field(None, description="升级原因", max_length=500)
    notification_channels: Optional[List[int]] = Field(None, description="额外通知渠道")


class AlertBatchRequest(BaseModel):
    """告警批量操作请求模式"""
    alert_ids: List[int] = Field(..., description="告警ID列表", min_items=1, max_items=100)
    operator: str = Field(..., description="操作人", max_length=100)
    reason: Optional[str] = Field(None, description="操作原因", max_length=500)


# 告警统计模式
class AlertStatisticsResponse(BaseModel):
    """告警统计响应模式"""
    total_alerts: int = Field(..., description="总告警数")
    active_alerts: int = Field(..., description="活跃告警数")
    resolved_alerts: int = Field(..., description="已解决告警数")
    acknowledged_alerts: int = Field(..., description="已确认告警数")
    silenced_alerts: int = Field(..., description="静默告警数")
    critical_alerts: int = Field(..., description="严重告警数")
    high_alerts: int = Field(..., description="高级告警数")
    medium_alerts: int = Field(..., description="中级告警数")
    low_alerts: int = Field(..., description="低级告警数")
    avg_resolution_time: float = Field(..., description="平均解决时间(分钟)")
    avg_acknowledgment_time: float = Field(..., description="平均确认时间(分钟)")
    alert_frequency: Dict[str, int] = Field(..., description="告警频率分布")
    severity_distribution: Dict[str, int] = Field(..., description="严重级别分布")
    type_distribution: Dict[str, int] = Field(..., description="类型分布")
    source_distribution: Dict[str, int] = Field(..., description="来源分布")
    top_alert_sources: List[Dict[str, Any]] = Field(..., description="告警最多的来源")
    escalation_statistics: Dict[str, Any] = Field(..., description="升级统计")
    notification_statistics: Dict[str, Any] = Field(..., description="通知统计")
    
    class Config:
        from_attributes = True


class AlertTrendResponse(BaseModel):
    """告警趋势响应模式"""
    time_series: List[Dict[str, Any]] = Field(..., description="时间序列数据")
    trend_direction: str = Field(..., description="趋势方向")
    trend_strength: float = Field(..., description="趋势强度")
    peak_hours: List[int] = Field(..., description="高峰时段")
    seasonal_patterns: Dict[str, Any] = Field(..., description="季节性模式")
    anomalies: List[Dict[str, Any]] = Field(..., description="异常点")
    
    class Config:
        from_attributes = True