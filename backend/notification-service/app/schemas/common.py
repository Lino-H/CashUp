#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通用API模式

定义通用的API请求和响应模式
"""

from typing import Any, Dict, List, Optional, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# 泛型类型变量
T = TypeVar('T')


class BaseResponse(BaseModel):
    """
    基础响应模式
    """
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = Field(default=True, description="请求是否成功")
    message: str = Field(default="操作成功", description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class ErrorResponse(BaseResponse):
    """
    错误响应模式
    """
    success: bool = Field(default=False, description="请求是否成功")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    error_detail: Optional[str] = Field(default=None, description="错误详情")
    trace_id: Optional[str] = Field(default=None, description="追踪ID")


class PaginationParams(BaseModel):
    """
    分页参数模式
    """
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")
    
    @property
    def offset(self) -> int:
        """
        计算偏移量
        
        Returns:
            int: 偏移量
        """
        return (self.page - 1) * self.size


class PaginationInfo(BaseModel):
    """
    分页信息模式
    """
    page: int = Field(description="当前页码")
    size: int = Field(description="每页大小")
    total: int = Field(description="总记录数")
    pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")
    
    @classmethod
    def create(cls, page: int, size: int, total: int) -> "PaginationInfo":
        """
        创建分页信息
        
        Args:
            page: 当前页码
            size: 每页大小
            total: 总记录数
            
        Returns:
            PaginationInfo: 分页信息
        """
        pages = (total + size - 1) // size if total > 0 else 0
        return cls(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class PaginatedResponse(BaseResponse, Generic[T]):
    """
    分页响应模式
    """
    data: List[T] = Field(description="数据列表")
    pagination: PaginationInfo = Field(description="分页信息")


class HealthResponse(BaseModel):
    """
    健康检查响应模式
    """
    status: str = Field(description="服务状态")
    version: str = Field(description="服务版本")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="检查时间")
    uptime: float = Field(description="运行时间（秒）")
    dependencies: Dict[str, Any] = Field(default_factory=dict, description="依赖服务状态")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="性能指标")


class HealthCheckResponse(HealthResponse):
    """
    健康检查响应模式（别名）
    """
    pass


class FilterParams(BaseModel):
    """
    过滤参数基类
    """
    search: Optional[str] = Field(default=None, description="搜索关键词")
    start_date: Optional[datetime] = Field(default=None, description="开始日期")
    end_date: Optional[datetime] = Field(default=None, description="结束日期")
    created_by: Optional[str] = Field(default=None, description="创建者ID")
    
    def to_filter_dict(self) -> Dict[str, Any]:
        """
        转换为过滤字典
        
        Returns:
            Dict[str, Any]: 过滤条件字典
        """
        filters = {}
        for field, value in self.model_dump(exclude_none=True).items():
            if value is not None:
                filters[field] = value
        return filters


class BulkOperationRequest(BaseModel):
    """
    批量操作请求模式
    """
    ids: List[str] = Field(description="ID列表")
    operation: str = Field(description="操作类型")
    params: Optional[Dict[str, Any]] = Field(default=None, description="操作参数")


class BulkOperationResponse(BaseResponse):
    """
    批量操作响应模式
    """
    total: int = Field(description="总数")
    success_count: int = Field(description="成功数")
    failed_count: int = Field(description="失败数")
    failed_items: List[Dict[str, Any]] = Field(default_factory=list, description="失败项目")
    
    @property
    def success_rate(self) -> float:
        """
        计算成功率
        
        Returns:
            float: 成功率（0-1）
        """
        if self.total == 0:
            return 0.0
        return self.success_count / self.total


class StatisticsResponse(BaseModel):
    """
    统计响应模式
    """
    period: str = Field(description="统计周期")
    start_date: datetime = Field(description="开始日期")
    end_date: datetime = Field(description="结束日期")
    metrics: Dict[str, Any] = Field(description="统计指标")
    charts: Optional[Dict[str, Any]] = Field(default=None, description="图表数据")


class ExportRequest(BaseModel):
    """
    导出请求模式
    """
    format: str = Field(default="csv", pattern="^(csv|excel|json)$", description="导出格式")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")
    fields: Optional[List[str]] = Field(default=None, description="导出字段")
    filename: Optional[str] = Field(default=None, description="文件名")


class ExportResponse(BaseResponse):
    """
    导出响应模式
    """
    download_url: str = Field(description="下载链接")
    filename: str = Field(description="文件名")
    file_size: int = Field(description="文件大小（字节）")
    expires_at: datetime = Field(description="链接过期时间")
    record_count: int = Field(description="记录数")


class ImportRequest(BaseModel):
    """
    导入请求模式
    """
    file_url: str = Field(description="文件URL")
    format: str = Field(default="csv", pattern="^(csv|excel|json)$", description="文件格式")
    options: Optional[Dict[str, Any]] = Field(default=None, description="导入选项")
    validate_only: bool = Field(default=False, description="仅验证不导入")


class ImportResponse(BaseResponse):
    """
    导入响应模式
    """
    task_id: str = Field(description="任务ID")
    total_records: int = Field(description="总记录数")
    valid_records: int = Field(description="有效记录数")
    invalid_records: int = Field(description="无效记录数")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误列表")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="警告列表")


class TaskStatusResponse(BaseModel):
    """
    任务状态响应模式
    """
    task_id: str = Field(description="任务ID")
    status: str = Field(description="任务状态")
    progress: float = Field(description="进度百分比")
    message: Optional[str] = Field(default=None, description="状态消息")
    result: Optional[Dict[str, Any]] = Field(default=None, description="任务结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class WebSocketMessage(BaseModel):
    """
    WebSocket消息模式
    """
    type: str = Field(description="消息类型")
    data: Dict[str, Any] = Field(description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="消息时间")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    channel: Optional[str] = Field(default=None, description="频道")
    
    def to_json(self) -> str:
        """
        转换为JSON字符串
        
        Returns:
            str: JSON字符串
        """
        return self.model_dump_json()


class APIKeyInfo(BaseModel):
    """
    API密钥信息模式
    """
    key_id: str = Field(description="密钥ID")
    name: str = Field(description="密钥名称")
    permissions: List[str] = Field(description="权限列表")
    expires_at: Optional[datetime] = Field(default=None, description="过期时间")
    last_used_at: Optional[datetime] = Field(default=None, description="最后使用时间")
    is_active: bool = Field(description="是否活跃")


class RateLimitInfo(BaseModel):
    """
    速率限制信息模式
    """
    limit: int = Field(description="限制数量")
    remaining: int = Field(description="剩余数量")
    reset_at: datetime = Field(description="重置时间")
    window_seconds: int = Field(description="时间窗口（秒）")
    
    @property
    def is_exceeded(self) -> bool:
        """
        检查是否超出限制
        
        Returns:
            bool: 是否超出限制
        """
        return self.remaining <= 0
    
    @property
    def usage_percentage(self) -> float:
        """
        计算使用百分比
        
        Returns:
            float: 使用百分比（0-1）
        """
        if self.limit == 0:
            return 0.0
        return (self.limit - self.remaining) / self.limit