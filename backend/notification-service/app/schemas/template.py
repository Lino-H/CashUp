#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 模板API模式

定义模板相关的API请求和响应模式
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, validator
from uuid import UUID

from ..models.template import TemplateType
from ..models.notification import NotificationCategory
from .common import BaseResponse, PaginatedResponse, FilterParams


class TemplateBase(BaseModel):
    """
    模板基础模式
    """
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(max_length=100, description="模板名称")
    display_name: str = Field(max_length=200, description="模板显示名称")
    description: Optional[str] = Field(default=None, description="模板描述")
    type: TemplateType = Field(description="模板类型")
    category: NotificationCategory = Field(description="通知分类")
    subject: Optional[str] = Field(default=None, max_length=200, description="主题模板")
    content: str = Field(description="内容模板")
    html_content: Optional[str] = Field(default=None, description="HTML内容模板")
    variables: List[str] = Field(default_factory=list, description="模板变量列表")
    config: Optional[Dict[str, Any]] = Field(default=None, description="模板配置")
    is_active: bool = Field(default=True, description="是否启用")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class TemplateCreate(TemplateBase):
    """
    创建模板请求模式
    """
    
    @validator('name')
    def validate_name(cls, v):
        """
        验证模板名称
        """
        if not v or not v.strip():
            raise ValueError("Template name cannot be empty")
        
        # 检查名称格式（只允许字母、数字、下划线、连字符）
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Template name can only contain letters, numbers, underscores, and hyphens")
        
        return v.strip()
    
    @validator('variables')
    def validate_variables(cls, v):
        """
        验证模板变量
        """
        if v:
            # 检查变量名格式
            import re
            for var in v:
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var):
                    raise ValueError(f"Invalid variable name: {var}")
        return v
    
    @validator('content')
    def validate_content(cls, v):
        """
        验证内容模板
        """
        if not v or not v.strip():
            raise ValueError("Template content cannot be empty")
        return v.strip()


class TemplateUpdate(BaseModel):
    """
    更新模板请求模式
    """
    model_config = ConfigDict(from_attributes=True)
    
    display_name: Optional[str] = Field(default=None, max_length=200, description="模板显示名称")
    description: Optional[str] = Field(default=None, description="模板描述")
    subject: Optional[str] = Field(default=None, max_length=200, description="主题模板")
    content: Optional[str] = Field(default=None, description="内容模板")
    html_content: Optional[str] = Field(default=None, description="HTML内容模板")
    variables: Optional[List[str]] = Field(default=None, description="模板变量列表")
    config: Optional[Dict[str, Any]] = Field(default=None, description="模板配置")
    is_active: Optional[bool] = Field(default=None, description="是否启用")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class TemplateResponse(BaseModel):
    """
    模板响应模式
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(description="模板ID")
    name: str = Field(description="模板名称")
    display_name: str = Field(description="模板显示名称")
    description: Optional[str] = Field(description="模板描述")
    type: TemplateType = Field(description="模板类型")
    category: NotificationCategory = Field(description="通知分类")
    subject: Optional[str] = Field(description="主题模板")
    content: str = Field(description="内容模板")
    html_content: Optional[str] = Field(description="HTML内容模板")
    variables: List[str] = Field(description="模板变量列表")
    config: Optional[Dict[str, Any]] = Field(description="模板配置")
    is_active: bool = Field(description="是否启用")
    usage_count: int = Field(description="使用次数")
    last_used_at: Optional[datetime] = Field(description="最后使用时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    created_by: Optional[UUID] = Field(description="创建者ID")
    updated_by: Optional[UUID] = Field(description="更新者ID")
    metadata: Optional[Dict[str, Any]] = Field(description="元数据")
    
    @property
    def has_html(self) -> bool:
        """检查是否有HTML内容"""
        return bool(self.html_content)
    
    @property
    def has_subject(self) -> bool:
        """检查是否有主题"""
        return bool(self.subject)
    
    @property
    def variable_count(self) -> int:
        """获取变量数量"""
        return len(self.variables) if self.variables else 0


class TemplateListResponse(PaginatedResponse[TemplateResponse]):
    """
    模板列表响应模式
    """
    pass


class TemplateFilter(FilterParams):
    """
    模板过滤参数模式
    """
    name: Optional[str] = Field(default=None, description="模板名称")
    type: Optional[TemplateType] = Field(default=None, description="模板类型")
    category: Optional[NotificationCategory] = Field(default=None, description="通知分类")
    is_active: Optional[bool] = Field(default=None, description="是否启用")
    has_html: Optional[bool] = Field(default=None, description="是否有HTML内容")
    has_subject: Optional[bool] = Field(default=None, description="是否有主题")
    min_usage: Optional[int] = Field(default=None, description="最小使用次数")
    max_usage: Optional[int] = Field(default=None, description="最大使用次数")


class TemplateRender(BaseModel):
    """
    模板渲染请求模式
    """
    template_id: UUID = Field(description="模板ID")
    variables: Dict[str, Any] = Field(description="模板变量")
    render_html: bool = Field(default=True, description="是否渲染HTML")
    
    @validator('variables')
    def validate_variables(cls, v):
        """
        验证模板变量
        """
        if not isinstance(v, dict):
            raise ValueError("Variables must be a dictionary")
        return v


class TemplateRenderResponse(BaseResponse):
    """
    模板渲染响应模式
    """
    template_id: UUID = Field(description="模板ID")
    rendered_subject: Optional[str] = Field(description="渲染后主题")
    rendered_content: str = Field(description="渲染后内容")
    rendered_html: Optional[str] = Field(description="渲染后HTML")
    variables_used: List[str] = Field(description="使用的变量")
    variables_missing: List[str] = Field(description="缺失的变量")
    render_time_ms: float = Field(description="渲染耗时（毫秒）")


class TemplatePreview(BaseModel):
    """
    模板预览请求模式
    """
    subject: Optional[str] = Field(default=None, description="主题模板")
    content: str = Field(description="内容模板")
    html_content: Optional[str] = Field(default=None, description="HTML内容模板")
    variables: Optional[Dict[str, Any]] = Field(default=None, description="预览变量")
    type: TemplateType = Field(description="模板类型")


class TemplatePreviewResponse(BaseResponse):
    """
    模板预览响应模式
    """
    rendered_subject: Optional[str] = Field(description="渲染后主题")
    rendered_content: str = Field(description="渲染后内容")
    rendered_html: Optional[str] = Field(description="渲染后HTML")
    detected_variables: List[str] = Field(description="检测到的变量")
    sample_data: Dict[str, Any] = Field(description="示例数据")


class TemplateClone(BaseModel):
    """
    模板克隆请求模式
    """
    source_template_id: UUID = Field(description="源模板ID")
    new_name: str = Field(max_length=100, description="新模板名称")
    new_display_name: Optional[str] = Field(default=None, max_length=200, description="新模板显示名称")
    copy_config: bool = Field(default=True, description="是否复制配置")
    copy_metadata: bool = Field(default=False, description="是否复制元数据")
    
    @validator('new_name')
    def validate_new_name(cls, v):
        """
        验证新模板名称
        """
        if not v or not v.strip():
            raise ValueError("New template name cannot be empty")
        
        # 检查名称格式
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Template name can only contain letters, numbers, underscores, and hyphens")
        
        return v.strip()


class TemplateCloneResponse(BaseResponse):
    """
    模板克隆响应模式
    """
    source_template_id: UUID = Field(description="源模板ID")
    new_template: TemplateResponse = Field(description="新模板信息")


class TemplateValidation(BaseModel):
    """
    模板验证请求模式
    """
    subject: Optional[str] = Field(default=None, description="主题模板")
    content: str = Field(description="内容模板")
    html_content: Optional[str] = Field(default=None, description="HTML内容模板")
    variables: Optional[List[str]] = Field(default=None, description="预期变量列表")
    type: TemplateType = Field(description="模板类型")


class TemplateValidationResponse(BaseResponse):
    """
    模板验证响应模式
    """
    is_valid: bool = Field(description="是否有效")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    detected_variables: List[str] = Field(description="检测到的变量")
    unused_variables: List[str] = Field(description="未使用的变量")
    missing_variables: List[str] = Field(description="缺失的变量")
    syntax_check: Dict[str, Any] = Field(description="语法检查结果")


class TemplateStats(BaseModel):
    """
    模板统计模式
    """
    total: int = Field(description="总数")
    active: int = Field(description="启用数")
    inactive: int = Field(description="禁用数")
    by_type: Dict[str, int] = Field(description="按类型统计")
    by_category: Dict[str, int] = Field(description="按分类统计")
    most_used: List[Dict[str, Any]] = Field(description="最常用模板")
    least_used: List[Dict[str, Any]] = Field(description="最少用模板")
    recent_created: List[Dict[str, Any]] = Field(description="最近创建")
    total_usage: int = Field(description="总使用次数")
    average_usage: float = Field(description="平均使用次数")


class TemplateStatsResponse(BaseResponse):
    """
    模板统计响应模式
    """
    stats: TemplateStats = Field(description="统计数据")
    period: str = Field(description="统计周期")
    start_date: datetime = Field(description="开始日期")
    end_date: datetime = Field(description="结束日期")


class TemplateBulkOperation(BaseModel):
    """
    模板批量操作请求模式
    """
    template_ids: List[UUID] = Field(description="模板ID列表")
    operation: str = Field(description="操作类型")
    params: Optional[Dict[str, Any]] = Field(default=None, description="操作参数")
    
    @validator('template_ids')
    def validate_template_ids(cls, v):
        """
        验证模板ID列表
        """
        if not v:
            raise ValueError("Template IDs list cannot be empty")
        if len(v) > 100:
            raise ValueError("Cannot operate on more than 100 templates at once")
        return v
    
    @validator('operation')
    def validate_operation(cls, v):
        """
        验证操作类型
        """
        allowed_operations = ['activate', 'deactivate', 'delete', 'export', 'clone']
        if v not in allowed_operations:
            raise ValueError(f"Invalid operation. Allowed: {', '.join(allowed_operations)}")
        return v


class TemplateBulkOperationResponse(BaseResponse):
    """
    模板批量操作响应模式
    """
    operation: str = Field(description="操作类型")
    total: int = Field(description="总数")
    success_count: int = Field(description="成功数")
    failed_count: int = Field(description="失败数")
    results: List[Dict[str, Any]] = Field(description="操作结果")
    failed_items: List[Dict[str, Any]] = Field(default_factory=list, description="失败项目")


class TemplateExport(BaseModel):
    """
    模板导出请求模式
    """
    template_ids: Optional[List[UUID]] = Field(default=None, description="模板ID列表")
    filters: Optional[TemplateFilter] = Field(default=None, description="过滤条件")
    format: str = Field(default="json", pattern="^(json|yaml|csv)$", description="导出格式")
    include_metadata: bool = Field(default=True, description="是否包含元数据")
    include_stats: bool = Field(default=False, description="是否包含统计信息")


class TemplateExportResponse(BaseResponse):
    """
    模板导出响应模式
    """
    download_url: str = Field(description="下载链接")
    filename: str = Field(description="文件名")
    file_size: int = Field(description="文件大小（字节）")
    template_count: int = Field(description="模板数量")
    format: str = Field(description="导出格式")
    expires_at: datetime = Field(description="链接过期时间")


class TemplateImport(BaseModel):
    """
    模板导入请求模式
    """
    file_url: str = Field(description="文件URL")
    format: str = Field(default="json", pattern="^(json|yaml|csv)$", description="文件格式")
    overwrite_existing: bool = Field(default=False, description="是否覆盖已存在的模板")
    validate_only: bool = Field(default=False, description="仅验证不导入")
    import_config: Optional[Dict[str, Any]] = Field(default=None, description="导入配置")


class TemplateImportResponse(BaseResponse):
    """
    模板导入响应模式
    """
    task_id: str = Field(description="任务ID")
    total_templates: int = Field(description="总模板数")
    valid_templates: int = Field(description="有效模板数")
    invalid_templates: int = Field(description="无效模板数")
    imported_templates: int = Field(description="已导入模板数")
    skipped_templates: int = Field(description="跳过模板数")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误列表")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="警告列表")