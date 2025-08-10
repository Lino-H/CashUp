#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知模板模型

定义通知模板相关的数据库模型
"""

import uuid
import enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    String, Integer, DateTime, Boolean, Text, Enum, JSON,
    Index, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from ..core.database import Base


class TemplateType(str, enum.Enum):
    """
    模板类型枚举
    """
    EMAIL = "email"              # 邮件模板
    SMS = "sms"                  # 短信模板
    PUSH = "push"                # 推送模板
    WEBSOCKET = "websocket"      # WebSocket模板
    SYSTEM = "system"            # 系统通知模板


class NotificationTemplate(Base):
    """
    通知模板模型
    
    存储各种类型的通知模板
    """
    __tablename__ = "notification_templates"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="模板ID"
    )
    
    # 模板基本信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="模板名称"
    )
    
    display_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="模板显示名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="模板描述"
    )
    
    # 模板类型和分类
    type: Mapped[TemplateType] = mapped_column(
        Enum(TemplateType),
        nullable=False,
        comment="模板类型"
    )
    
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="模板分类"
    )
    
    # 模板内容
    subject_template: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="主题模板（邮件/推送标题）"
    )
    
    content_template: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="内容模板"
    )
    
    html_template: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="HTML模板（邮件）"
    )
    
    # 模板变量
    variables: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="模板变量列表"
    )
    
    default_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="默认变量值"
    )
    
    # 模板配置
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用"
    )
    
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否为系统模板"
    )
    
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="模板版本"
    )
    
    # 使用统计
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="使用次数"
    )
    
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后使用时间"
    )
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 创建者信息
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="创建者ID"
    )
    
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="更新者ID"
    )
    
    # 元数据
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="元数据"
    )
    
    # 关联关系
    notifications = relationship("Notification", back_populates="template")
    
    # 表约束
    __table_args__ = (
        # 检查约束
        CheckConstraint('version > 0', name='ck_template_version_positive'),
        CheckConstraint('usage_count >= 0', name='ck_template_usage_count_non_negative'),
        
        # 索引
        Index('idx_template_name', 'name'),
        Index('idx_template_type', 'type'),
        Index('idx_template_category', 'category'),
        Index('idx_template_is_active', 'is_active'),
        Index('idx_template_is_system', 'is_system'),
        Index('idx_template_created_at', 'created_at'),
        Index('idx_template_type_category', 'type', 'category'),
        Index('idx_template_created_by', 'created_by'),
    )
    
    def __repr__(self) -> str:
        return f"<NotificationTemplate(id={self.id}, name={self.name}, type={self.type})>"
    
    @property
    def variable_list(self) -> List[str]:
        """
        获取模板变量列表
        
        Returns:
            List[str]: 变量列表
        """
        return self.variables or []
    
    @property
    def default_data(self) -> Dict[str, Any]:
        """
        获取默认变量值
        
        Returns:
            Dict[str, Any]: 默认变量值字典
        """
        return self.default_values or {}
    
    def validate_variables(self, data: Dict[str, Any]) -> List[str]:
        """
        验证模板变量
        
        Args:
            data: 变量数据
            
        Returns:
            List[str]: 缺失的变量列表
        """
        missing_vars = []
        for var in self.variable_list:
            if var not in data and var not in self.default_data:
                missing_vars.append(var)
        return missing_vars
    
    def render_subject(self, data: Dict[str, Any]) -> str:
        """
        渲染主题模板
        
        Args:
            data: 模板数据
            
        Returns:
            str: 渲染后的主题
        """
        if not self.subject_template:
            return ""
        
        # 合并默认值和传入数据
        render_data = {**self.default_data, **data}
        
        try:
            return self.subject_template.format(**render_data)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    def render_content(self, data: Dict[str, Any]) -> str:
        """
        渲染内容模板
        
        Args:
            data: 模板数据
            
        Returns:
            str: 渲染后的内容
        """
        # 合并默认值和传入数据
        render_data = {**self.default_data, **data}
        
        try:
            return self.content_template.format(**render_data)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    def render_html(self, data: Dict[str, Any]) -> Optional[str]:
        """
        渲染HTML模板
        
        Args:
            data: 模板数据
            
        Returns:
            Optional[str]: 渲染后的HTML内容
        """
        if not self.html_template:
            return None
        
        # 合并默认值和传入数据
        render_data = {**self.default_data, **data}
        
        try:
            return self.html_template.format(**render_data)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    def increment_usage(self):
        """
        增加使用次数
        """
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
    
    def get_preview_data(self) -> Dict[str, Any]:
        """
        获取预览数据
        
        Returns:
            Dict[str, Any]: 预览数据
        """
        preview_data = self.default_data.copy()
        
        # 为缺失的变量添加示例值
        for var in self.variable_list:
            if var not in preview_data:
                preview_data[var] = f"{{示例_{var}}}"
        
        return preview_data
    
    def clone(self, new_name: str, created_by: Optional[uuid.UUID] = None) -> 'NotificationTemplate':
        """
        克隆模板
        
        Args:
            new_name: 新模板名称
            created_by: 创建者ID
            
        Returns:
            NotificationTemplate: 新的模板实例
        """
        return NotificationTemplate(
            name=new_name,
            display_name=f"{self.display_name} (副本)",
            description=self.description,
            type=self.type,
            category=self.category,
            subject_template=self.subject_template,
            content_template=self.content_template,
            html_template=self.html_template,
            variables=self.variables.copy() if self.variables else None,
            default_values=self.default_values.copy() if self.default_values else None,
            is_active=False,  # 克隆的模板默认不启用
            is_system=False,  # 克隆的模板不是系统模板
            version=1,
            created_by=created_by,
            metadata=self.metadata.copy() if self.metadata else None
        )