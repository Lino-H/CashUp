#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 渠道API模式

定义渠道相关的API请求和响应模式
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, validator
from uuid import UUID

from ..models.channel import ChannelType, ChannelStatus
from .common import BaseResponse, PaginatedResponse, FilterParams


class ChannelBase(BaseModel):
    """
    渠道基础模式
    """
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(max_length=100, description="渠道名称")
    display_name: str = Field(max_length=200, description="渠道显示名称")
    description: Optional[str] = Field(default=None, description="渠道描述")
    type: ChannelType = Field(description="渠道类型")
    config: Dict[str, Any] = Field(description="渠道配置")
    priority: int = Field(default=100, ge=0, description="渠道优先级")
    rate_limit: Optional[int] = Field(default=None, gt=0, description="速率限制（每分钟）")
    daily_limit: Optional[int] = Field(default=None, gt=0, description="每日发送限制")
    max_retry_attempts: int = Field(default=3, ge=0, description="最大重试次数")
    retry_delay_seconds: int = Field(default=60, gt=0, description="重试延迟时间（秒）")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ChannelCreate(ChannelBase):
    """
    创建渠道请求模式
    """
    
    @validator('name')
    def validate_name(cls, v):
        """
        验证渠道名称
        """
        if not v or not v.strip():
            raise ValueError("Channel name cannot be empty")
        
        # 检查名称格式（只允许字母、数字、下划线、连字符）
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Channel name can only contain letters, numbers, underscores, and hyphens")
        
        return v.strip()
    
    @validator('config')
    def validate_config(cls, v, values):
        """
        验证渠道配置
        """
        if not v:
            raise ValueError("Channel config cannot be empty")
        
        # 根据渠道类型验证必需的配置
        channel_type = values.get('type')
        if channel_type:
            required_keys = cls._get_required_config_keys(channel_type)
            for key in required_keys:
                if key not in v or not v[key]:
                    raise ValueError(f"Missing required config key: {key}")
        
        return v
    
    @staticmethod
    def _get_required_config_keys(channel_type: ChannelType) -> List[str]:
        """
        获取渠道类型的必需配置键
        
        Args:
            channel_type: 渠道类型
            
        Returns:
            List[str]: 必需配置键列表
        """
        config_map = {
            ChannelType.EMAIL: ['host', 'port', 'username', 'password'],
            ChannelType.SMS: ['provider', 'access_key', 'secret_key'],
            ChannelType.WXPUSHER: ['app_token'],
            ChannelType.QANOTIFY: ['key'],
            ChannelType.PUSHPLUS: ['token'],
            ChannelType.TELEGRAM: ['bot_token'],
            ChannelType.WEBHOOK: ['url'],
            ChannelType.WEBSOCKET: [],
            ChannelType.SYSTEM: []
        }
        return config_map.get(channel_type, [])


class ChannelUpdate(BaseModel):
    """
    更新渠道请求模式
    """
    model_config = ConfigDict(from_attributes=True)
    
    display_name: Optional[str] = Field(default=None, max_length=200, description="渠道显示名称")
    description: Optional[str] = Field(default=None, description="渠道描述")
    config: Optional[Dict[str, Any]] = Field(default=None, description="渠道配置")
    status: Optional[ChannelStatus] = Field(default=None, description="渠道状态")
    priority: Optional[int] = Field(default=None, ge=0, description="渠道优先级")
    rate_limit: Optional[int] = Field(default=None, gt=0, description="速率限制（每分钟）")
    daily_limit: Optional[int] = Field(default=None, gt=0, description="每日发送限制")
    max_retry_attempts: Optional[int] = Field(default=None, ge=0, description="最大重试次数")
    retry_delay_seconds: Optional[int] = Field(default=None, gt=0, description="重试延迟时间（秒）")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ChannelResponse(BaseModel):
    """
    渠道响应模式
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(description="渠道ID")
    name: str = Field(description="渠道名称")
    display_name: str = Field(description="渠道显示名称")
    description: Optional[str] = Field(description="渠道描述")
    type: ChannelType = Field(description="渠道类型")
    status: ChannelStatus = Field(description="渠道状态")
    config: Dict[str, Any] = Field(description="渠道配置")
    priority: int = Field(description="渠道优先级")
    rate_limit: Optional[int] = Field(description="速率限制（每分钟）")
    daily_limit: Optional[int] = Field(description="每日发送限制")
    max_retry_attempts: int = Field(description="最大重试次数")
    retry_delay_seconds: int = Field(description="重试延迟时间（秒）")
    total_sent: int = Field(description="总发送数")
    total_failed: int = Field(description="总失败数")
    today_sent: int = Field(description="今日发送数")
    last_sent_at: Optional[datetime] = Field(description="最后发送时间")
    last_error_at: Optional[datetime] = Field(description="最后错误时间")
    last_error_message: Optional[str] = Field(description="最后错误信息")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    created_by: Optional[UUID] = Field(description="创建者ID")
    updated_by: Optional[UUID] = Field(description="更新者ID")
    metadata: Optional[Dict[str, Any]] = Field(description="元数据")
    
    @property
    def is_active(self) -> bool:
        """检查渠道是否活跃"""
        return self.status == ChannelStatus.ACTIVE
    
    @property
    def is_available(self) -> bool:
        """检查渠道是否可用"""
        return self.status in [ChannelStatus.ACTIVE, ChannelStatus.INACTIVE]
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_sent == 0:
            return 0.0
        return (self.total_sent - self.total_failed) / self.total_sent
    
    @property
    def can_send_today(self) -> bool:
        """检查今日是否还能发送"""
        if not self.daily_limit:
            return True
        return self.today_sent < self.daily_limit


class ChannelListResponse(PaginatedResponse[ChannelResponse]):
    """
    渠道列表响应模式
    """
    pass


class ChannelFilter(FilterParams):
    """
    渠道过滤参数模式
    """
    name: Optional[str] = Field(default=None, description="渠道名称")
    type: Optional[ChannelType] = Field(default=None, description="渠道类型")
    status: Optional[ChannelStatus] = Field(default=None, description="渠道状态")
    is_active: Optional[bool] = Field(default=None, description="是否活跃")
    has_rate_limit: Optional[bool] = Field(default=None, description="是否有速率限制")
    has_daily_limit: Optional[bool] = Field(default=None, description="是否有每日限制")
    min_priority: Optional[int] = Field(default=None, description="最小优先级")
    max_priority: Optional[int] = Field(default=None, description="最大优先级")
    has_errors: Optional[bool] = Field(default=None, description="是否有错误")


class ChannelTest(BaseModel):
    """
    渠道测试请求模式
    """
    channel_id: UUID = Field(description="渠道ID")
    test_message: Optional[str] = Field(default=None, description="测试消息")
    test_recipient: str = Field(description="测试收件人")
    test_config: Optional[Dict[str, Any]] = Field(default=None, description="测试配置")
    
    @validator('test_recipient')
    def validate_test_recipient(cls, v):
        """
        验证测试收件人
        """
        if not v or not v.strip():
            raise ValueError("Test recipient cannot be empty")
        return v.strip()


class ChannelTestResponse(BaseResponse):
    """
    渠道测试响应模式
    """
    channel_id: UUID = Field(description="渠道ID")
    test_successful: bool = Field(description="测试是否成功")
    test_message: str = Field(description="测试消息")
    response_time_ms: float = Field(description="响应时间（毫秒）")
    error_message: Optional[str] = Field(description="错误信息")
    test_details: Dict[str, Any] = Field(description="测试详情")
    timestamp: datetime = Field(description="测试时间")


class ChannelStats(BaseModel):
    """
    渠道统计模式
    """
    total: int = Field(description="总数")
    active: int = Field(description="活跃数")
    inactive: int = Field(description="非活跃数")
    error: int = Field(description="错误数")
    maintenance: int = Field(description="维护中数")
    disabled: int = Field(description="已禁用数")
    by_type: Dict[str, int] = Field(description="按类型统计")
    by_status: Dict[str, int] = Field(description="按状态统计")
    total_sent: int = Field(description="总发送数")
    total_failed: int = Field(description="总失败数")
    overall_success_rate: float = Field(description="总体成功率")
    top_performers: List[Dict[str, Any]] = Field(description="表现最佳渠道")
    worst_performers: List[Dict[str, Any]] = Field(description="表现最差渠道")


class ChannelStatsResponse(BaseResponse):
    """
    渠道统计响应模式
    """
    stats: ChannelStats = Field(description="统计数据")
    period: str = Field(description="统计周期")
    start_date: datetime = Field(description="开始日期")
    end_date: datetime = Field(description="结束日期")


class ChannelBulkOperation(BaseModel):
    """
    渠道批量操作请求模式
    """
    channel_ids: List[UUID] = Field(description="渠道ID列表")
    operation: str = Field(description="操作类型")
    params: Optional[Dict[str, Any]] = Field(default=None, description="操作参数")
    
    @validator('channel_ids')
    def validate_channel_ids(cls, v):
        """
        验证渠道ID列表
        """
        if not v:
            raise ValueError("Channel IDs list cannot be empty")
        if len(v) > 50:
            raise ValueError("Cannot operate on more than 50 channels at once")
        return v
    
    @validator('operation')
    def validate_operation(cls, v):
        """
        验证操作类型
        """
        allowed_operations = ['activate', 'deactivate', 'reset_counters', 'test', 'delete']
        if v not in allowed_operations:
            raise ValueError(f"Invalid operation. Allowed: {', '.join(allowed_operations)}")
        return v


class ChannelBulkOperationResponse(BaseResponse):
    """
    渠道批量操作响应模式
    """
    operation: str = Field(description="操作类型")
    total: int = Field(description="总数")
    success_count: int = Field(description="成功数")
    failed_count: int = Field(description="失败数")
    results: List[Dict[str, Any]] = Field(description="操作结果")
    failed_items: List[Dict[str, Any]] = Field(default_factory=list, description="失败项目")


class ChannelConfig(BaseModel):
    """
    渠道配置模式
    """
    channel_type: ChannelType = Field(description="渠道类型")
    config_schema: Dict[str, Any] = Field(description="配置模式")
    required_fields: List[str] = Field(description="必需字段")
    optional_fields: List[str] = Field(description="可选字段")
    field_descriptions: Dict[str, str] = Field(description="字段描述")
    example_config: Dict[str, Any] = Field(description="示例配置")
    validation_rules: Dict[str, Any] = Field(description="验证规则")


class ChannelConfigResponse(BaseResponse):
    """
    渠道配置响应模式
    """
    configs: List[ChannelConfig] = Field(description="渠道配置列表")


class ChannelHealth(BaseModel):
    """
    渠道健康状态模式
    """
    channel_id: UUID = Field(description="渠道ID")
    channel_name: str = Field(description="渠道名称")
    is_healthy: bool = Field(description="是否健康")
    status: ChannelStatus = Field(description="状态")
    last_check_at: datetime = Field(description="最后检查时间")
    response_time_ms: Optional[float] = Field(description="响应时间（毫秒）")
    error_message: Optional[str] = Field(description="错误信息")
    health_score: float = Field(description="健康评分（0-100）")
    issues: List[str] = Field(default_factory=list, description="问题列表")
    recommendations: List[str] = Field(default_factory=list, description="建议列表")


class ChannelHealthResponse(BaseResponse):
    """
    渠道健康检查响应模式
    """
    overall_health: str = Field(description="总体健康状态")
    healthy_count: int = Field(description="健康渠道数")
    unhealthy_count: int = Field(description="不健康渠道数")
    channels: List[ChannelHealth] = Field(description="渠道健康状态列表")
    check_time: datetime = Field(description="检查时间")


class ChannelMetrics(BaseModel):
    """
    渠道指标模式
    """
    channel_id: UUID = Field(description="渠道ID")
    channel_name: str = Field(description="渠道名称")
    period: str = Field(description="统计周期")
    sent_count: int = Field(description="发送数")
    failed_count: int = Field(description="失败数")
    success_rate: float = Field(description="成功率")
    avg_response_time_ms: float = Field(description="平均响应时间（毫秒）")
    error_rate: float = Field(description="错误率")
    throughput_per_minute: float = Field(description="每分钟吞吐量")
    peak_usage_time: Optional[str] = Field(description="峰值使用时间")
    cost_per_message: Optional[float] = Field(description="每条消息成本")
    total_cost: Optional[float] = Field(description="总成本")


class ChannelMetricsResponse(BaseResponse):
    """
    渠道指标响应模式
    """
    metrics: List[ChannelMetrics] = Field(description="渠道指标列表")
    period: str = Field(description="统计周期")
    start_date: datetime = Field(description="开始日期")
    end_date: datetime = Field(description="结束日期")
    summary: Dict[str, Any] = Field(description="汇总信息")


class ChannelQuota(BaseModel):
    """
    渠道配额模式
    """
    channel_id: UUID = Field(description="渠道ID")
    channel_name: str = Field(description="渠道名称")
    daily_limit: Optional[int] = Field(description="每日限制")
    daily_used: int = Field(description="今日已用")
    daily_remaining: int = Field(description="今日剩余")
    rate_limit: Optional[int] = Field(description="速率限制")
    current_rate: float = Field(description="当前速率")
    quota_reset_at: datetime = Field(description="配额重置时间")
    is_quota_exceeded: bool = Field(description="是否超出配额")
    is_rate_limited: bool = Field(description="是否被速率限制")


class ChannelQuotaResponse(BaseResponse):
    """
    渠道配额响应模式
    """
    quotas: List[ChannelQuota] = Field(description="渠道配额列表")
    check_time: datetime = Field(description="检查时间")