#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 数据库基础模型

定义所有数据库模型的基础类和混入类
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

# 创建基础模型类
Base = declarative_base()


class TimestampMixin:
    """时间戳混入类"""
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )


class SoftDeleteMixin:
    """软删除混入类"""
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="删除时间"
    )
    
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已删除"
    )
    
    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """恢复"""
        self.is_deleted = False
        self.deleted_at = None


class BaseModel(Base, TimestampMixin):
    """基础模型类"""
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="主键ID"
    )
    
    def to_dict(self, exclude: Optional[set] = None) -> Dict[str, Any]:
        """转换为字典"""
        exclude = exclude or set()
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    value = str(value)
                result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[set] = None):
        """从字典更新"""
        exclude = exclude or {'id', 'created_at', 'updated_at'}
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def create(cls, db: Session, **kwargs) -> 'BaseModel':
        """创建实例"""
        instance = cls(**kwargs)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance
    
    def update(self, db: Session, **kwargs) -> 'BaseModel':
        """更新实例"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        db.commit()
        db.refresh(self)
        return self
    
    def delete(self, db: Session):
        """删除实例"""
        db.delete(self)
        db.commit()
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"


class AuditMixin:
    """审计混入类"""
    
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="创建者ID"
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="更新者ID"
    )
    
    version = Column(
        Integer,
        default=1,
        nullable=False,
        comment="版本号"
    )
    
    def increment_version(self):
        """增加版本号"""
        self.version += 1


class MetadataMixin:
    """元数据混入类"""
    
    metadata_json = Column(
        Text,
        nullable=True,
        comment="元数据JSON"
    )
    
    tags = Column(
        Text,
        nullable=True,
        comment="标签（逗号分隔）"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="描述"
    )
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取元数据"""
        if self.metadata_json:
            import json
            try:
                return json.loads(self.metadata_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_metadata(self, metadata: Dict[str, Any]):
        """设置元数据"""
        import json
        self.metadata_json = json.dumps(metadata, ensure_ascii=False)
    
    def get_tags(self) -> list:
        """获取标签列表"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def set_tags(self, tags: list):
        """设置标签"""
        self.tags = ','.join(str(tag).strip() for tag in tags if str(tag).strip())
    
    def add_tag(self, tag: str):
        """添加标签"""
        current_tags = self.get_tags()
        if tag not in current_tags:
            current_tags.append(tag)
            self.set_tags(current_tags)
    
    def remove_tag(self, tag: str):
        """移除标签"""
        current_tags = self.get_tags()
        if tag in current_tags:
            current_tags.remove(tag)
            self.set_tags(current_tags)


class StatusMixin:
    """状态混入类"""
    
    status = Column(
        String(50),
        nullable=False,
        default='active',
        comment="状态"
    )
    
    status_message = Column(
        Text,
        nullable=True,
        comment="状态消息"
    )
    
    def is_active(self) -> bool:
        """是否激活"""
        return self.status == 'active'
    
    def is_inactive(self) -> bool:
        """是否非激活"""
        return self.status == 'inactive'
    
    def is_pending(self) -> bool:
        """是否待处理"""
        return self.status == 'pending'
    
    def activate(self, message: Optional[str] = None):
        """激活"""
        self.status = 'active'
        self.status_message = message
    
    def deactivate(self, message: Optional[str] = None):
        """停用"""
        self.status = 'inactive'
        self.status_message = message
    
    def set_pending(self, message: Optional[str] = None):
        """设置为待处理"""
        self.status = 'pending'
        self.status_message = message


class NameMixin:
    """名称混入类"""
    
    name = Column(
        String(255),
        nullable=False,
        comment="名称"
    )
    
    display_name = Column(
        String(255),
        nullable=True,
        comment="显示名称"
    )
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return self.display_name or self.name


class ConfigMixin:
    """配置混入类"""
    
    config_json = Column(
        Text,
        nullable=True,
        comment="配置JSON"
    )
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        if self.config_json:
            import json
            try:
                return json.loads(self.config_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_config(self, config: Dict[str, Any]):
        """设置配置"""
        import json
        self.config_json = json.dumps(config, ensure_ascii=False)
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        config = self.get_config()
        return config.get(key, default)
    
    def set_config_value(self, key: str, value: Any):
        """设置配置值"""
        config = self.get_config()
        config[key] = value
        self.set_config(config)
    
    def remove_config_value(self, key: str):
        """移除配置值"""
        config = self.get_config()
        if key in config:
            del config[key]
            self.set_config(config)