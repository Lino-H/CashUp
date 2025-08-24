#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知API模式

定义通知相关的API请求和响应模式
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, validator
from uuid import UUID

from ..models.notification import NotificationStatus, NotificationPriority, NotificationCategory
from .common import BaseResponse, PaginatedResponse, FilterParams


class NotificationBase(BaseModel):
    """
    通知基础模式
    """
    model_config = ConfigDict(from_attributes=True)
    
    title: str = Field(max_length=200, description="通知标题")
    content: str = Field(description="通知内容")
    category: NotificationCategory = Field(description="通知分类")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="优先级")
    channels: List[str] = Field(description="发送渠道列表")
    recipients: Optional[Dict[str, List[str]]] = Field(default=None, description="收件人信息")
    template_id: Optional[UUID] = Field(default=None, description="模板ID")
    template_variables: Optional[Dict[str, Any]] = Field(default=None, description="模板变量")
    send_config: Optional[Dict[str, Any]] = Field(default=None, description="发送配置")
    scheduled_at: Optional[datetime] = Field(default=None, description="定时发送时间")
    expires_at: Optional[datetime] = Field(default=None, description="过期时间")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class NotificationCreate(NotificationBase):
    """
    创建通知请求模式
    """
    user_id: Optional[UUID] = Field(default=None, description="用户ID")
    
    @validator('recipients')
    def validate_recipients(cls, v, values):
        """
        验证收件人信息
        """
        # 获取渠道列表
        channels = values.get('channels', [])
        
        # 允许为空的渠道列表（这些渠道有默认接收者）
        channels_allow_empty = {'wxpusher', 'pushplus', 'qanotify'}
        
        # 如果所有渠道都允许为空，则recipients可以为None或空字典
        if all(channel in channels_allow_empty for channel in channels):
            if v is None:
                return {}
            if not v:
                return {}
        
        # 如果recipients为None但有需要收件人的渠道，则报错
        if v is None:
            non_empty_channels = [ch for ch in channels if ch not in channels_allow_empty]
            if non_empty_channels:
                raise ValueError(f"Recipients are required for channels: {', '.join(non_empty_channels)}")
            return {}
        
        # 验证每个渠道的收件人格式
        for channel, recipients in v.items():
            # 对于允许为空的渠道，跳过空值检查
            if channel in channels_allow_empty:
                if not isinstance(recipients, list):
                    raise ValueError(f"Recipients for channel {channel} must be a list")
                # 如果有收件人，则验证格式
                if recipients:
                    continue  # 这些渠道暂时不需要特殊格式验证
            else:
                # 其他渠道必须有收件人
                if not isinstance(recipients, list) or not recipients:
                    raise ValueError(f"Recipients for channel {channel} must be a non-empty list")
                
                # 根据渠道类型验证收件人格式
                if channel == 'email':
                    for recipient in recipients:
                        if '@' not in recipient:
                            raise ValueError(f"Invalid email address: {recipient}")
                elif channel == 'sms':
                    for recipient in recipients:
                        if not recipient.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                            raise ValueError(f"Invalid phone number: {recipient}")
        
        return v
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        """
        验证定时发送时间
        """
        if v and v <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        return v
    
    @validator('expires_at')
    def validate_expires_at(cls, v, values):
        """
        验证过期时间
        """
        if v:
            scheduled_at = values.get('scheduled_at')
            if scheduled_at and v <= scheduled_at:
                raise ValueError("Expiration time must be after scheduled time")
            elif not scheduled_at and v <= datetime.utcnow():
                raise ValueError("Expiration time must be in the future")
        return v


class NotificationUpdate(BaseModel):
    """
    更新通知请求模式
    """
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = Field(default=None, max_length=200, description="通知标题")
    content: Optional[str] = Field(default=None, description="通知内容")
    priority: Optional[NotificationPriority] = Field(default=None, description="优先级")
    scheduled_at: Optional[datetime] = Field(default=None, description="定时发送时间")
    expires_at: Optional[datetime] = Field(default=None, description="过期时间")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class NotificationStatusUpdate(BaseModel):
    """
    通知状态更新模式
    """
    status: NotificationStatus = Field(description="新状态")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    retry_attempts: Optional[int] = Field(default=None, description="重试次数")


class NotificationResponse(BaseModel):
    """
    通知响应模式
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(description="通知ID")
    user_id: Optional[UUID] = Field(description="用户ID")
    title: str = Field(description="通知标题")
    content: str = Field(description="通知内容")
    category: NotificationCategory = Field(description="通知分类")
    priority: NotificationPriority = Field(description="优先级")
    status: NotificationStatus = Field(description="状态")
    channels: List[str] = Field(description="发送渠道列表")
    recipients: Dict[str, List[str]] = Field(description="收件人信息")
    template_id: Optional[UUID] = Field(description="模板ID")
    template_variables: Optional[Dict[str, Any]] = Field(description="模板变量")
    send_config: Optional[Dict[str, Any]] = Field(description="发送配置")
    scheduled_at: Optional[datetime] = Field(description="定时发送时间")
    sent_at: Optional[datetime] = Field(description="发送时间")
    expires_at: Optional[datetime] = Field(description="过期时间")
    retry_attempts: int = Field(description="重试次数")
    max_retry_attempts: int = Field(description="最大重试次数")
    error_message: Optional[str] = Field(description="错误信息")
    delivery_status: Dict[str, Any] = Field(description="投递状态")
    read_status: Dict[str, Any] = Field(description="阅读状态")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    metadata: Optional[Dict[str, Any]] = Field(description="元数据")
    
    @property
    def is_pending(self) -> bool:
        """检查是否为待发送状态"""
        return self.status == NotificationStatus.PENDING
    
    @property
    def is_sent(self) -> bool:
        """检查是否已发送"""
        return self.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED, NotificationStatus.READ]
    
    @property
    def is_failed(self) -> bool:
        """检查是否发送失败"""
        return self.status == NotificationStatus.FAILED
    
    @property
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.is_failed and self.retry_attempts < self.max_retry_attempts


class NotificationListResponse(PaginatedResponse[NotificationResponse]):
    """
    通知列表响应模式
    """
    pass


class NotificationBatchCreate(BaseModel):
    """
    批量创建通知请求模式
    """
    notifications: List[NotificationCreate] = Field(description="通知列表")
    batch_config: Optional[Dict[str, Any]] = Field(default=None, description="批量配置")
    
    @validator('notifications')
    def validate_notifications(cls, v):
        """
        验证通知列表
        """
        if not v:
            raise ValueError("Notifications list cannot be empty")
        if len(v) > 100:
            raise ValueError("Cannot create more than 100 notifications at once")
        return v


class NotificationBatchResponse(BaseResponse):
    """
    批量创建通知响应模式
    """
    total: int = Field(description="总数")
    success_count: int = Field(description="成功数")
    failed_count: int = Field(description="失败数")
    notifications: List[NotificationResponse] = Field(description="创建的通知列表")
    failed_items: List[Dict[str, Any]] = Field(default_factory=list, description="失败项目")


class NotificationFilter(FilterParams):
    """
    通知过滤参数模式
    """
    user_id: Optional[UUID] = Field(default=None, description="用户ID")
    category: Optional[NotificationCategory] = Field(default=None, description="通知分类")
    priority: Optional[NotificationPriority] = Field(default=None, description="优先级")
    status: Optional[NotificationStatus] = Field(default=None, description="状态")
    channel: Optional[str] = Field(default=None, description="发送渠道")
    template_id: Optional[UUID] = Field(default=None, description="模板ID")
    is_scheduled: Optional[bool] = Field(default=None, description="是否定时发送")
    is_expired: Optional[bool] = Field(default=None, description="是否已过期")
    has_error: Optional[bool] = Field(default=None, description="是否有错误")


class NotificationStats(BaseModel):
    """
    通知统计模式
    """
    total: int = Field(description="总数")
    pending: int = Field(description="待发送数")
    sent: int = Field(description="已发送数")
    delivered: int = Field(description="已投递数")
    read: int = Field(description="已阅读数")
    failed: int = Field(description="失败数")
    expired: int = Field(description="过期数")
    by_category: Dict[str, int] = Field(description="按分类统计")
    by_priority: Dict[str, int] = Field(description="按优先级统计")
    by_channel: Dict[str, int] = Field(description="按渠道统计")
    success_rate: float = Field(description="成功率")
    
    @property
    def total_processed(self) -> int:
        """已处理总数"""
        return self.sent + self.delivered + self.read + self.failed + self.expired


class NotificationStatsResponse(BaseResponse):
    """
    通知统计响应模式
    """
    stats: NotificationStats = Field(description="统计数据")
    period: str = Field(description="统计周期")
    start_date: datetime = Field(description="开始日期")
    end_date: datetime = Field(description="结束日期")


class NotificationRetry(BaseModel):
    """
    通知重试请求模式
    """
    notification_ids: List[UUID] = Field(description="通知ID列表")
    force: bool = Field(default=False, description="是否强制重试")
    reset_retry_attempts: bool = Field(default=False, description="是否重置重试次数")


class NotificationRetryResponse(BaseResponse):
    """
    通知重试响应模式
    """
    total: int = Field(description="总数")
    success_count: int = Field(description="成功数")
    failed_count: int = Field(description="失败数")
    skipped_count: int = Field(description="跳过数")
    results: List[Dict[str, Any]] = Field(description="重试结果")


class NotificationCancel(BaseModel):
    """
    取消通知请求模式
    """
    notification_ids: List[UUID] = Field(description="通知ID列表")
    reason: Optional[str] = Field(default=None, description="取消原因")


class NotificationCancelResponse(BaseResponse):
    """
    取消通知响应模式
    """
    total: int = Field(description="总数")
    success_count: int = Field(description="成功数")
    failed_count: int = Field(description="失败数")
    results: List[Dict[str, Any]] = Field(description="取消结果")


class NotificationPreview(BaseModel):
    """
    通知预览请求模式
    """
    title: str = Field(description="通知标题")
    content: str = Field(description="通知内容")
    template_id: Optional[UUID] = Field(default=None, description="模板ID")
    template_variables: Optional[Dict[str, Any]] = Field(default=None, description="模板变量")
    channel: str = Field(description="预览渠道")


class NotificationPreviewResponse(BaseResponse):
    """
    通知预览响应模式
    """
    rendered_title: str = Field(description="渲染后标题")
    rendered_content: str = Field(description="渲染后内容")
    rendered_html: Optional[str] = Field(default=None, description="渲染后HTML")
    channel: str = Field(description="预览渠道")
    preview_data: Dict[str, Any] = Field(description="预览数据")


class NotificationDeliveryStatus(BaseModel):
    """
    通知投递状态模式
    """
    notification_id: UUID = Field(description="通知ID")
    channel: str = Field(description="渠道")
    recipient: str = Field(description="收件人")
    status: str = Field(description="投递状态")
    delivered_at: Optional[datetime] = Field(description="投递时间")
    read_at: Optional[datetime] = Field(description="阅读时间")
    error_message: Optional[str] = Field(description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(description="元数据")


class NotificationReadStatus(BaseModel):
    """
    通知阅读状态模式
    """
    notification_id: UUID = Field(description="通知ID")
    user_id: UUID = Field(description="用户ID")
    channel: str = Field(description="渠道")
    read_at: datetime = Field(description="阅读时间")
    ip_address: Optional[str] = Field(description="IP地址")
    user_agent: Optional[str] = Field(description="用户代理")
    metadata: Optional[Dict[str, Any]] = Field(description="元数据")


class NotificationWebhook(BaseModel):
    """
    通知Webhook模式
    """
    event: str = Field(description="事件类型")
    notification_id: UUID = Field(description="通知ID")
    user_id: Optional[UUID] = Field(description="用户ID")
    status: NotificationStatus = Field(description="状态")
    channel: str = Field(description="渠道")
    recipient: str = Field(description="收件人")
    timestamp: datetime = Field(description="时间戳")
    data: Dict[str, Any] = Field(description="事件数据")
    
    def to_webhook_payload(self) -> Dict[str, Any]:
        """
        转换为Webhook负载
        
        Returns:
            Dict[str, Any]: Webhook负载
        """
        return {
            "event": self.event,
            "notification_id": str(self.notification_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "status": self.status.value,
            "channel": self.channel,
            "recipient": self.recipient,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }