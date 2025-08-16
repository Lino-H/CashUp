#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 配置模式定义

定义配置相关的Pydantic模式
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator

from ..models.config import ConfigType, ConfigScope, ConfigStatus, ConfigFormat


class ConfigBase(BaseModel):
    """
    配置基础模式
    """
    key: str = Field(..., description="配置键", max_length=200)
    name: str = Field(..., description="配置名称", max_length=100)
    description: Optional[str] = Field(None, description="配置描述")
    type: ConfigType = Field(..., description="配置类型")
    scope: ConfigScope = Field(ConfigScope.GLOBAL, description="配置作用域")
    category: Optional[str] = Field(None, description="配置分类", max_length=50)
    value: Dict[str, Any] = Field(..., description="配置值")
    default_value: Optional[Dict[str, Any]] = Field(None, description="默认值")
    format: ConfigFormat = Field(ConfigFormat.JSON, description="配置格式")
    schema: Optional[Dict[str, Any]] = Field(None, description="配置模式")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    status: ConfigStatus = Field(ConfigStatus.ACTIVE, description="配置状态")
    is_encrypted: bool = Field(False, description="是否加密")
    is_readonly: bool = Field(False, description="是否只读")
    is_required: bool = Field(False, description="是否必需")
    user_id: Optional[uuid.UUID] = Field(None, description="用户ID")
    strategy_id: Optional[uuid.UUID] = Field(None, description="策略ID")
    parent_id: Optional[uuid.UUID] = Field(None, description="父配置ID")
    template_id: Optional[uuid.UUID] = Field(None, description="模板ID")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    tags: Optional[Dict[str, Any]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    @validator('key')
    def validate_key(cls, v):
        """
        验证配置键格式
        """
        if not v or not v.strip():
            raise ValueError('配置键不能为空')
        
        # 配置键只能包含字母、数字、下划线、点号和连字符
        import re
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('配置键只能包含字母、数字、下划线、点号和连字符')
        
        return v.strip()
    
    @validator('value')
    def validate_value(cls, v):
        """
        验证配置值
        """
        if v is None:
            raise ValueError('配置值不能为空')
        return v


class ConfigCreate(ConfigBase):
    """
    创建配置模式
    """
    pass


class ConfigUpdate(BaseModel):
    """
    更新配置模式
    """
    name: Optional[str] = Field(None, description="配置名称", max_length=100)
    description: Optional[str] = Field(None, description="配置描述")
    value: Optional[Dict[str, Any]] = Field(None, description="配置值")
    default_value: Optional[Dict[str, Any]] = Field(None, description="默认值")
    schema: Optional[Dict[str, Any]] = Field(None, description="配置模式")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    status: Optional[ConfigStatus] = Field(None, description="配置状态")
    is_encrypted: Optional[bool] = Field(None, description="是否加密")
    is_readonly: Optional[bool] = Field(None, description="是否只读")
    is_required: Optional[bool] = Field(None, description="是否必需")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    tags: Optional[Dict[str, Any]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ConfigResponse(ConfigBase):
    """
    配置响应模式
    """
    id: uuid.UUID = Field(..., description="配置ID")
    version: int = Field(..., description="配置版本")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[uuid.UUID] = Field(None, description="创建者ID")
    updated_by: Optional[uuid.UUID] = Field(None, description="更新者ID")
    
    class Config:
        from_attributes = True


class ConfigListResponse(BaseModel):
    """
    配置列表响应模式
    """
    items: List[ConfigResponse] = Field(..., description="配置列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class ConfigFilter(BaseModel):
    """
    配置过滤模式
    """
    key: Optional[str] = Field(None, description="配置键")
    name: Optional[str] = Field(None, description="配置名称")
    type: Optional[ConfigType] = Field(None, description="配置类型")
    scope: Optional[ConfigScope] = Field(None, description="配置作用域")
    category: Optional[str] = Field(None, description="配置分类")
    status: Optional[ConfigStatus] = Field(None, description="配置状态")
    user_id: Optional[uuid.UUID] = Field(None, description="用户ID")
    strategy_id: Optional[uuid.UUID] = Field(None, description="策略ID")
    parent_id: Optional[uuid.UUID] = Field(None, description="父配置ID")
    template_id: Optional[uuid.UUID] = Field(None, description="模板ID")
    is_encrypted: Optional[bool] = Field(None, description="是否加密")
    is_readonly: Optional[bool] = Field(None, description="是否只读")
    is_required: Optional[bool] = Field(None, description="是否必需")
    created_after: Optional[datetime] = Field(None, description="创建时间起")
    created_before: Optional[datetime] = Field(None, description="创建时间止")
    updated_after: Optional[datetime] = Field(None, description="更新时间起")
    updated_before: Optional[datetime] = Field(None, description="更新时间止")
    search: Optional[str] = Field(None, description="搜索关键词")


class ConfigBatchOperation(BaseModel):
    """
    配置批量操作模式
    """
    config_ids: List[uuid.UUID] = Field(..., description="配置ID列表")
    operation: str = Field(..., description="操作类型")
    data: Optional[Dict[str, Any]] = Field(None, description="操作数据")


class ConfigValidationRequest(BaseModel):
    """
    配置验证请求模式
    """
    value: Dict[str, Any] = Field(..., description="配置值")
    schema: Optional[Dict[str, Any]] = Field(None, description="验证模式")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")


class ConfigValidationResponse(BaseModel):
    """
    配置验证响应模式
    """
    is_valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")


# 配置模板相关模式
class ConfigTemplateBase(BaseModel):
    """
    配置模板基础模式
    """
    name: str = Field(..., description="模板名称", max_length=100)
    description: Optional[str] = Field(None, description="模板描述")
    template: Dict[str, Any] = Field(..., description="模板内容")
    schema: Optional[Dict[str, Any]] = Field(None, description="模板模式")
    type: ConfigType = Field(..., description="模板类型")
    category: Optional[str] = Field(None, description="模板分类", max_length=50)
    is_active: bool = Field(True, description="是否激活")
    is_default: bool = Field(False, description="是否默认模板")
    version: str = Field("1.0.0", description="模板版本")
    tags: Optional[Dict[str, Any]] = Field(None, description="标签")


class ConfigTemplateCreate(ConfigTemplateBase):
    """
    创建配置模板模式
    """
    pass


class ConfigTemplateUpdate(BaseModel):
    """
    更新配置模板模式
    """
    name: Optional[str] = Field(None, description="模板名称", max_length=100)
    description: Optional[str] = Field(None, description="模板描述")
    template: Optional[Dict[str, Any]] = Field(None, description="模板内容")
    schema: Optional[Dict[str, Any]] = Field(None, description="模板模式")
    category: Optional[str] = Field(None, description="模板分类", max_length=50)
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_default: Optional[bool] = Field(None, description="是否默认模板")
    version: Optional[str] = Field(None, description="模板版本")
    tags: Optional[Dict[str, Any]] = Field(None, description="标签")


class ConfigTemplateResponse(ConfigTemplateBase):
    """
    配置模板响应模式
    """
    id: uuid.UUID = Field(..., description="模板ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[uuid.UUID] = Field(None, description="创建者ID")
    
    class Config:
        from_attributes = True


class ConfigTemplateListResponse(BaseModel):
    """
    配置模板列表响应模式
    """
    items: List[ConfigTemplateResponse] = Field(..., description="模板列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class ConfigTemplateFilter(BaseModel):
    """
    配置模板过滤模式
    """
    name: Optional[str] = Field(None, description="模板名称")
    type: Optional[ConfigType] = Field(None, description="模板类型")
    category: Optional[str] = Field(None, description="模板分类")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_default: Optional[bool] = Field(None, description="是否默认模板")
    version: Optional[str] = Field(None, description="模板版本")
    created_after: Optional[datetime] = Field(None, description="创建时间起")
    created_before: Optional[datetime] = Field(None, description="创建时间止")
    search: Optional[str] = Field(None, description="搜索关键词")


# 配置版本相关模式
class ConfigVersionResponse(BaseModel):
    """
    配置版本响应模式
    """
    id: uuid.UUID = Field(..., description="版本ID")
    config_id: uuid.UUID = Field(..., description="配置ID")
    version: int = Field(..., description="版本号")
    value: Dict[str, Any] = Field(..., description="版本值")
    change_summary: Optional[str] = Field(None, description="变更摘要")
    change_details: Optional[Dict[str, Any]] = Field(None, description="变更详情")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[uuid.UUID] = Field(None, description="创建者ID")
    
    class Config:
        from_attributes = True


class ConfigVersionListResponse(BaseModel):
    """
    配置版本列表响应模式
    """
    items: List[ConfigVersionResponse] = Field(..., description="版本列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


# 配置审计日志相关模式
class ConfigAuditLogResponse(BaseModel):
    """
    配置审计日志响应模式
    """
    id: uuid.UUID = Field(..., description="日志ID")
    config_id: uuid.UUID = Field(..., description="配置ID")
    action: str = Field(..., description="操作类型")
    old_value: Optional[Dict[str, Any]] = Field(None, description="旧值")
    new_value: Optional[Dict[str, Any]] = Field(None, description="新值")
    details: Optional[Dict[str, Any]] = Field(None, description="操作详情")
    created_at: datetime = Field(..., description="创建时间")
    user_id: Optional[uuid.UUID] = Field(None, description="操作者ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    
    class Config:
        from_attributes = True


class ConfigAuditLogListResponse(BaseModel):
    """
    配置审计日志列表响应模式
    """
    items: List[ConfigAuditLogResponse] = Field(..., description="日志列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


# 配置同步相关模式
class ConfigSyncRequest(BaseModel):
    """
    配置同步请求模式
    """
    source: str = Field(..., description="同步源")
    target: str = Field(..., description="同步目标")
    config_keys: Optional[List[str]] = Field(None, description="同步的配置键列表")
    force: bool = Field(False, description="是否强制同步")
    dry_run: bool = Field(False, description="是否试运行")


class ConfigSyncResponse(BaseModel):
    """
    配置同步响应模式
    """
    success: bool = Field(..., description="是否成功")
    synced_count: int = Field(..., description="同步数量")
    failed_count: int = Field(..., description="失败数量")
    details: List[Dict[str, Any]] = Field(default_factory=list, description="同步详情")
    errors: List[str] = Field(default_factory=list, description="错误列表")


# 配置统计相关模式
class ConfigStatistics(BaseModel):
    """
    配置统计模式
    """
    total_configs: int = Field(..., description="总配置数")
    active_configs: int = Field(..., description="激活配置数")
    inactive_configs: int = Field(..., description="未激活配置数")
    expired_configs: int = Field(..., description="过期配置数")
    by_type: Dict[str, int] = Field(..., description="按类型统计")
    by_scope: Dict[str, int] = Field(..., description="按作用域统计")
    by_status: Dict[str, int] = Field(..., description="按状态统计")
    recent_changes: int = Field(..., description="最近变更数")


# 配置导入导出相关模式
class ConfigExportRequest(BaseModel):
    """
    配置导出请求模式
    """
    config_ids: Optional[List[uuid.UUID]] = Field(None, description="配置ID列表")
    filter: Optional[ConfigFilter] = Field(None, description="过滤条件")
    format: ConfigFormat = Field(ConfigFormat.JSON, description="导出格式")
    include_metadata: bool = Field(True, description="是否包含元数据")
    include_versions: bool = Field(False, description="是否包含版本历史")


class ConfigImportRequest(BaseModel):
    """
    配置导入请求模式
    """
    data: Dict[str, Any] = Field(..., description="导入数据")
    format: ConfigFormat = Field(ConfigFormat.JSON, description="数据格式")
    merge_strategy: str = Field("replace", description="合并策略")
    validate_before_import: bool = Field(True, description="导入前验证")
    create_backup: bool = Field(True, description="创建备份")


class ConfigImportResponse(BaseModel):
    """
    配置导入响应模式
    """
    success: bool = Field(..., description="是否成功")
    imported_count: int = Field(..., description="导入数量")
    updated_count: int = Field(..., description="更新数量")
    failed_count: int = Field(..., description="失败数量")
    backup_id: Optional[str] = Field(None, description="备份ID")
    details: List[Dict[str, Any]] = Field(default_factory=list, description="导入详情")
    errors: List[str] = Field(default_factory=list, description="错误列表")


class ConfigStatsResponse(BaseModel):
    """
    配置统计响应模式
    """
    total_configs: int = Field(..., description="总配置数")
    active_configs: int = Field(..., description="激活配置数")
    inactive_configs: int = Field(..., description="未激活配置数")
    expired_configs: int = Field(..., description="过期配置数")
    by_type: Dict[str, int] = Field(..., description="按类型统计")
    by_scope: Dict[str, int] = Field(..., description="按作用域统计")
    by_status: Dict[str, int] = Field(..., description="按状态统计")
    recent_changes: int = Field(..., description="最近变更数")


class ConfigExportResponse(BaseModel):
    """
    配置导出响应模式
    """
    success: bool = Field(..., description="是否成功")
    exported_count: int = Field(..., description="导出数量")
    file_path: Optional[str] = Field(None, description="导出文件路径")
    download_url: Optional[str] = Field(None, description="下载链接")
    format: ConfigFormat = Field(..., description="导出格式")
    size: int = Field(..., description="文件大小")
    checksum: Optional[str] = Field(None, description="文件校验和")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    errors: List[str] = Field(default_factory=list, description="错误列表")