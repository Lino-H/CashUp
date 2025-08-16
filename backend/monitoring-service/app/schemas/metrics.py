#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 指标数据模式

定义指标相关的API请求和响应数据模式
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class MetricTypeEnum(str, Enum):
    """指标类型枚举"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricCategoryEnum(str, Enum):
    """指标分类枚举"""
    SYSTEM = "system"
    APPLICATION = "application"
    BUSINESS = "business"
    CUSTOM = "custom"


class MetricStatusEnum(str, Enum):
    """指标状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"


class AggregationTypeEnum(str, Enum):
    """聚合类型枚举"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"


# 指标基础模式
class MetricBase(BaseModel):
    """指标基础模式"""
    name: str = Field(..., description="指标名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="指标描述", max_length=1000)
    metric_type: MetricTypeEnum = Field(..., description="指标类型")
    category: MetricCategoryEnum = Field(..., description="指标分类")
    unit: Optional[str] = Field(None, description="指标单位", max_length=50)
    labels: Optional[Dict[str, str]] = Field(default_factory=dict, description="指标标签")
    help_text: Optional[str] = Field(None, description="帮助文本", max_length=500)
    
    @validator('name')
    def validate_name(cls, v):
        """验证指标名称格式"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Metric name must contain only alphanumeric characters, underscores, and hyphens')
        return v


class MetricCreate(MetricBase):
    """创建指标请求模式"""
    enabled: bool = Field(True, description="是否启用")
    retention_days: Optional[int] = Field(30, description="数据保留天数", ge=1, le=365)
    collection_interval: Optional[int] = Field(60, description="采集间隔(秒)", ge=1, le=3600)
    

class MetricUpdate(BaseModel):
    """更新指标请求模式"""
    description: Optional[str] = Field(None, description="指标描述", max_length=1000)
    unit: Optional[str] = Field(None, description="指标单位", max_length=50)
    labels: Optional[Dict[str, str]] = Field(None, description="指标标签")
    help_text: Optional[str] = Field(None, description="帮助文本", max_length=500)
    enabled: Optional[bool] = Field(None, description="是否启用")
    retention_days: Optional[int] = Field(None, description="数据保留天数", ge=1, le=365)
    collection_interval: Optional[int] = Field(None, description="采集间隔(秒)", ge=1, le=3600)
    status: Optional[MetricStatusEnum] = Field(None, description="指标状态")


class MetricResponse(MetricBase):
    """指标响应模式"""
    id: int = Field(..., description="指标ID")
    enabled: bool = Field(..., description="是否启用")
    status: MetricStatusEnum = Field(..., description="指标状态")
    retention_days: int = Field(..., description="数据保留天数")
    collection_interval: int = Field(..., description="采集间隔(秒)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_collected_at: Optional[datetime] = Field(None, description="最后采集时间")
    value_count: int = Field(0, description="数据点数量")
    
    class Config:
        from_attributes = True


# 指标值模式
class MetricValueBase(BaseModel):
    """指标值基础模式"""
    value: Union[float, int] = Field(..., description="指标值")
    labels: Optional[Dict[str, str]] = Field(default_factory=dict, description="标签")
    timestamp: Optional[datetime] = Field(None, description="时间戳")


class MetricValueCreate(MetricValueBase):
    """创建指标值请求模式"""
    metric_id: int = Field(..., description="指标ID")


class MetricValueBatchCreate(BaseModel):
    """批量创建指标值请求模式"""
    metric_id: int = Field(..., description="指标ID")
    values: List[MetricValueBase] = Field(..., description="指标值列表", min_items=1, max_items=1000)


class MetricValueResponse(MetricValueBase):
    """指标值响应模式"""
    id: int = Field(..., description="值ID")
    metric_id: int = Field(..., description="指标ID")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


# 指标告警模式
class MetricAlertBase(BaseModel):
    """指标告警基础模式"""
    name: str = Field(..., description="告警名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="告警描述", max_length=1000)
    condition: str = Field(..., description="告警条件", max_length=500)
    threshold: float = Field(..., description="阈值")
    comparison_operator: str = Field(..., description="比较操作符")
    evaluation_window: int = Field(300, description="评估窗口(秒)", ge=60, le=3600)
    severity: str = Field("warning", description="严重级别")
    
    @validator('comparison_operator')
    def validate_operator(cls, v):
        """验证比较操作符"""
        valid_operators = ['>', '>=', '<', '<=', '==', '!=']
        if v not in valid_operators:
            raise ValueError(f'Invalid comparison operator. Must be one of: {valid_operators}')
        return v


class MetricAlertCreate(MetricAlertBase):
    """创建指标告警请求模式"""
    metric_id: int = Field(..., description="指标ID")
    enabled: bool = Field(True, description="是否启用")
    notification_channels: Optional[List[int]] = Field(default_factory=list, description="通知渠道ID列表")


class MetricAlertUpdate(BaseModel):
    """更新指标告警请求模式"""
    name: Optional[str] = Field(None, description="告警名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="告警描述", max_length=1000)
    condition: Optional[str] = Field(None, description="告警条件", max_length=500)
    threshold: Optional[float] = Field(None, description="阈值")
    comparison_operator: Optional[str] = Field(None, description="比较操作符")
    evaluation_window: Optional[int] = Field(None, description="评估窗口(秒)", ge=60, le=3600)
    severity: Optional[str] = Field(None, description="严重级别")
    enabled: Optional[bool] = Field(None, description="是否启用")
    notification_channels: Optional[List[int]] = Field(None, description="通知渠道ID列表")


class MetricAlertResponse(MetricAlertBase):
    """指标告警响应模式"""
    id: int = Field(..., description="告警ID")
    metric_id: int = Field(..., description="指标ID")
    enabled: bool = Field(..., description="是否启用")
    status: str = Field(..., description="告警状态")
    last_triggered_at: Optional[datetime] = Field(None, description="最后触发时间")
    trigger_count: int = Field(0, description="触发次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    notification_channels: List[int] = Field(default_factory=list, description="通知渠道ID列表")
    
    class Config:
        from_attributes = True


# 查询和聚合模式
class MetricQueryRequest(BaseModel):
    """指标查询请求模式"""
    metric_ids: Optional[List[int]] = Field(None, description="指标ID列表")
    metric_names: Optional[List[str]] = Field(None, description="指标名称列表")
    labels: Optional[Dict[str, str]] = Field(None, description="标签过滤")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    step: Optional[int] = Field(60, description="步长(秒)", ge=1, le=3600)
    limit: Optional[int] = Field(1000, description="返回数量限制", ge=1, le=10000)
    
    @validator('end_time')
    def validate_time_range(cls, v, values):
        """验证时间范围"""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


class MetricAggregateRequest(BaseModel):
    """指标聚合请求模式"""
    metric_ids: List[int] = Field(..., description="指标ID列表", min_items=1)
    aggregation_type: AggregationTypeEnum = Field(..., description="聚合类型")
    group_by: Optional[List[str]] = Field(None, description="分组字段")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    interval: Optional[str] = Field("1h", description="聚合间隔")
    percentile: Optional[float] = Field(None, description="百分位数", ge=0, le=100)
    
    @validator('percentile')
    def validate_percentile(cls, v, values):
        """验证百分位数"""
        if values.get('aggregation_type') == AggregationTypeEnum.PERCENTILE and v is None:
            raise ValueError('Percentile value is required for percentile aggregation')
        return v


class MetricBatchRequest(BaseModel):
    """指标批量操作请求模式"""
    metric_ids: List[int] = Field(..., description="指标ID列表", min_items=1, max_items=100)
    operation: str = Field(..., description="操作类型")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="操作参数")
    
    @validator('operation')
    def validate_operation(cls, v):
        """验证操作类型"""
        valid_operations = ['enable', 'disable', 'delete', 'update_retention', 'update_interval']
        if v not in valid_operations:
            raise ValueError(f'Invalid operation. Must be one of: {valid_operations}')
        return v


# 统计和分析模式
class MetricStatisticsResponse(BaseModel):
    """指标统计响应模式"""
    total_metrics: int = Field(..., description="总指标数")
    active_metrics: int = Field(..., description="活跃指标数")
    inactive_metrics: int = Field(..., description="非活跃指标数")
    error_metrics: int = Field(..., description="错误指标数")
    total_data_points: int = Field(..., description="总数据点数")
    data_points_today: int = Field(..., description="今日数据点数")
    avg_collection_interval: float = Field(..., description="平均采集间隔")
    storage_usage_mb: float = Field(..., description="存储使用量(MB)")
    category_distribution: Dict[str, int] = Field(..., description="分类分布")
    type_distribution: Dict[str, int] = Field(..., description="类型分布")
    top_metrics_by_volume: List[Dict[str, Any]] = Field(..., description="数据量最大的指标")
    collection_performance: Dict[str, float] = Field(..., description="采集性能统计")
    
    class Config:
        from_attributes = True


class MetricTrendResponse(BaseModel):
    """指标趋势响应模式"""
    metric_id: int = Field(..., description="指标ID")
    metric_name: str = Field(..., description="指标名称")
    time_series: List[Dict[str, Any]] = Field(..., description="时间序列数据")
    trend_direction: str = Field(..., description="趋势方向")
    trend_strength: float = Field(..., description="趋势强度")
    anomalies: List[Dict[str, Any]] = Field(..., description="异常点")
    statistics: Dict[str, float] = Field(..., description="统计信息")
    
    class Config:
        from_attributes = True


class MetricComparisonRequest(BaseModel):
    """指标对比请求模式"""
    metric_ids: List[int] = Field(..., description="指标ID列表", min_items=2, max_items=10)
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    comparison_type: str = Field("absolute", description="对比类型")
    normalize: bool = Field(False, description="是否标准化")
    
    @validator('comparison_type')
    def validate_comparison_type(cls, v):
        """验证对比类型"""
        valid_types = ['absolute', 'relative', 'percentage']
        if v not in valid_types:
            raise ValueError(f'Invalid comparison type. Must be one of: {valid_types}')
        return v


class MetricComparisonResponse(BaseModel):
    """指标对比响应模式"""
    metrics: List[Dict[str, Any]] = Field(..., description="指标信息")
    comparison_data: List[Dict[str, Any]] = Field(..., description="对比数据")
    correlation_matrix: List[List[float]] = Field(..., description="相关性矩阵")
    summary_statistics: Dict[str, Any] = Field(..., description="汇总统计")
    
    class Config:
        from_attributes = True


# 列表响应模式
class MetricListResponse(BaseModel):
    """指标列表响应模式"""
    items: List[MetricResponse] = Field(..., description="指标列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="页大小")
    pages: int = Field(..., description="总页数")
    
    class Config:
        from_attributes = True


class MetricValueListResponse(BaseModel):
    """指标值列表响应模式"""
    items: List[MetricValueResponse] = Field(..., description="指标值列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="页大小")
    pages: int = Field(..., description="总页数")
    
    class Config:
        from_attributes = True


class MetricAggregationResponse(BaseModel):
    """指标聚合响应模式"""
    metric_id: int = Field(..., description="指标ID")
    metric_name: str = Field(..., description="指标名称")
    aggregation_type: str = Field(..., description="聚合类型")
    time_series: List[Dict[str, Any]] = Field(..., description="时间序列数据")
    summary: Dict[str, Any] = Field(..., description="汇总信息")
    
    class Config:
        from_attributes = True


class MetricStatsResponse(BaseModel):
    """指标统计响应模式"""
    metric_id: int = Field(..., description="指标ID")
    metric_name: str = Field(..., description="指标名称")
    count: int = Field(..., description="数据点数量")
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    avg_value: Optional[float] = Field(None, description="平均值")
    sum_value: Optional[float] = Field(None, description="总和")
    std_dev: Optional[float] = Field(None, description="标准差")
    percentiles: Optional[Dict[str, float]] = Field(None, description="百分位数")
    
    class Config:
        from_attributes = True


class MetricCollectionTrigger(BaseModel):
    """指标采集触发器模式"""
    metric_ids: List[int] = Field(..., description="指标ID列表", min_items=1)
    trigger_type: str = Field(..., description="触发类型")
    immediate: bool = Field(False, description="是否立即执行")
    schedule: Optional[str] = Field(None, description="计划时间")
    
    @validator('trigger_type')
    def validate_trigger_type(cls, v):
        """验证触发类型"""
        valid_types = ['manual', 'scheduled', 'event']
        if v not in valid_types:
            raise ValueError(f'Invalid trigger type. Must be one of: {valid_types}')
        return v


class MetricQuery(BaseModel):
    """指标查询参数"""
    name: Optional[str] = Field(None, description="指标名称")
    metric_type: Optional[str] = Field(None, description="指标类型")
    category: Optional[str] = Field(None, description="指标分类")
    source: Optional[str] = Field(None, description="数据源")
    status: Optional[str] = Field(None, description="状态")
    enabled: Optional[bool] = Field(None, description="是否启用")
    tags: Optional[Dict[str, str]] = Field(None, description="标签")
    created_after: Optional[datetime] = Field(None, description="创建时间起始")
    created_before: Optional[datetime] = Field(None, description="创建时间结束")
    order_by: Optional[str] = Field("created_at", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")
    offset: int = Field(0, ge=0, description="偏移量")
    limit: int = Field(20, ge=1, le=100, description="限制数量")
    
    class Config:
        from_attributes = True


class MetricAggregateQuery(BaseModel):
    """指标聚合查询参数"""
    metric_id: int = Field(..., description="指标ID")
    aggregation_type: str = Field(..., description="聚合类型")
    time_range: str = Field(..., description="时间范围")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    group_by: Optional[List[str]] = Field(None, description="分组字段")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    
    class Config:
        from_attributes = True


class AggregationType:
    """聚合类型枚举"""
    AVG = "avg"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    P50 = "p50"
    P90 = "p90"
    P95 = "p95"
    P99 = "p99"