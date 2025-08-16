#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 监控服务通用数据模式

定义通用的请求和响应数据模式
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class PaginationParams(BaseModel):
    """分页参数模式"""
    page: int = Field(1, description="页码", ge=1)
    size: int = Field(20, description="每页大小", ge=1, le=100)
    
    @property
    def skip(self) -> int:
        """计算跳过的记录数"""
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        """获取限制数量"""
        return self.size


class TimeRangeParams(BaseModel):
    """时间范围参数模式"""
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    
    @validator('end_time')
    def validate_time_range(cls, v, values):
        """验证时间范围"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class SortParams(BaseModel):
    """排序参数模式"""
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序顺序")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """验证排序顺序"""
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be "asc" or "desc"')
        return v


class FilterParams(BaseModel):
    """过滤参数模式"""
    search: Optional[str] = Field(None, description="搜索关键词")
    status: Optional[str] = Field(None, description="状态过滤")
    category: Optional[str] = Field(None, description="分类过滤")
    tags: Optional[str] = Field(None, description="标签过滤")


class ResponseMetadata(BaseModel):
    """响应元数据模式"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class SuccessResponse(BaseModel):
    """成功响应模式"""
    success: bool = Field(True, description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")


class ErrorResponse(BaseModel):
    """错误响应模式"""
    success: bool = Field(False, description="是否成功")
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    details: Optional[dict] = Field(None, description="错误详情")