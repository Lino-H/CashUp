#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 配置模板服务

提供配置模板的管理功能
"""

import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.exceptions import (
    ConfigNotFoundError,
    ConfigValidationError,
    ConfigPermissionError
)
from ..models.config import ConfigTemplate, ConfigType
from ..schemas.config import (
    ConfigTemplateCreate,
    ConfigTemplateUpdate
)


class TemplateService:
    """
    配置模板服务
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    async def create_template(
        self,
        db: AsyncSession,
        template_data: ConfigTemplateCreate,
        user_id: Optional[uuid.UUID] = None
    ) -> ConfigTemplate:
        """
        创建配置模板
        """
        # 检查模板名称是否已存在
        existing = await self.get_template_by_name(db, template_data.name, template_data.type)
        if existing:
            raise ConfigValidationError(f"模板名称 '{template_data.name}' 已存在")
        
        # 验证模板内容
        await self._validate_template_content(template_data.template, template_data.schema)
        
        # 如果设置为默认模板，需要取消其他默认模板
        if template_data.is_default:
            await self._unset_default_templates(db, template_data.type)
        
        # 创建模板
        template = ConfigTemplate(
            **template_data.dict(),
            created_by=user_id
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        return template
    
    async def get_template_by_id(
        self,
        db: AsyncSession,
        template_id: uuid.UUID
    ) -> Optional[ConfigTemplate]:
        """
        根据ID获取配置模板
        """
        stmt = select(ConfigTemplate).where(ConfigTemplate.id == template_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_template_by_name(
        self,
        db: AsyncSession,
        name: str,
        template_type: ConfigType
    ) -> Optional[ConfigTemplate]:
        """
        根据名称和类型获取配置模板
        """
        stmt = select(ConfigTemplate).where(
            and_(
                ConfigTemplate.name == name,
                ConfigTemplate.type == template_type
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_template(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        template_data: ConfigTemplateUpdate,
        user_id: Optional[uuid.UUID] = None
    ) -> ConfigTemplate:
        """
        更新配置模板
        """
        # 获取现有模板
        template = await self.get_template_by_id(db, template_id)
        if not template:
            raise ConfigNotFoundError(f"模板 {template_id} 不存在")
        
        # 更新字段
        update_data = template_data.dict(exclude_unset=True)
        
        # 验证模板内容
        if 'template' in update_data:
            schema = update_data.get('schema', template.schema)
            await self._validate_template_content(update_data['template'], schema)
        
        # 如果设置为默认模板，需要取消其他默认模板
        if update_data.get('is_default'):
            await self._unset_default_templates(db, template.type)
        
        # 更新模板
        for field, value in update_data.items():
            setattr(template, field, value)
        
        template.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(template)
        
        return template
    
    async def delete_template(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> bool:
        """
        删除配置模板
        """
        # 获取模板
        template = await self.get_template_by_id(db, template_id)
        if not template:
            raise ConfigNotFoundError(f"模板 {template_id} 不存在")
        
        # 检查是否有配置在使用此模板
        from ..models.config import Config
        stmt = select(func.count(Config.id)).where(Config.template_id == template_id)
        result = await db.execute(stmt)
        usage_count = result.scalar()
        
        if usage_count > 0:
            raise ConfigPermissionError(f"模板正在被 {usage_count} 个配置使用，无法删除")
        
        # 删除模板
        await db.delete(template)
        await db.commit()
        
        return True
    
    async def list_templates(
        self,
        db: AsyncSession,
        template_type: Optional[ConfigType] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[ConfigTemplate], int]:
        """
        获取配置模板列表
        """
        # 构建查询条件
        conditions = []
        
        if template_type:
            conditions.append(ConfigTemplate.type == template_type)
        if category:
            conditions.append(ConfigTemplate.category == category)
        if is_active is not None:
            conditions.append(ConfigTemplate.is_active == is_active)
        
        # 搜索关键词
        if search:
            search_conditions = [
                ConfigTemplate.name.ilike(f"%{search}%"),
                ConfigTemplate.description.ilike(f"%{search}%")
            ]
            conditions.append(or_(*search_conditions))
        
        # 查询总数
        count_stmt = select(func.count(ConfigTemplate.id)).where(and_(*conditions))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # 查询数据
        offset = (page - 1) * size
        stmt = (
            select(ConfigTemplate)
            .where(and_(*conditions))
            .order_by(ConfigTemplate.is_default.desc(), ConfigTemplate.updated_at.desc())
            .offset(offset)
            .limit(size)
        )
        
        result = await db.execute(stmt)
        templates = result.scalars().all()
        
        return list(templates), total
    
    async def get_default_template(
        self,
        db: AsyncSession,
        template_type: ConfigType
    ) -> Optional[ConfigTemplate]:
        """
        获取指定类型的默认模板
        """
        stmt = select(ConfigTemplate).where(
            and_(
                ConfigTemplate.type == template_type,
                ConfigTemplate.is_default == True,
                ConfigTemplate.is_active == True
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def apply_template(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        user_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        应用模板生成配置值
        """
        # 获取模板
        template = await self.get_template_by_id(db, template_id)
        if not template:
            raise ConfigNotFoundError(f"模板 {template_id} 不存在")
        
        if not template.is_active:
            raise ConfigValidationError("模板未激活")
        
        # 合并模板值和用户值
        result = template.template.copy()
        if user_values:
            result.update(user_values)
        
        # 验证最终结果
        if template.schema:
            await self._validate_template_content(result, template.schema)
        
        return result
    
    async def clone_template(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        new_name: str,
        user_id: Optional[uuid.UUID] = None
    ) -> ConfigTemplate:
        """
        克隆配置模板
        """
        # 获取原模板
        original = await self.get_template_by_id(db, template_id)
        if not original:
            raise ConfigNotFoundError(f"模板 {template_id} 不存在")
        
        # 检查新名称是否已存在
        existing = await self.get_template_by_name(db, new_name, original.type)
        if existing:
            raise ConfigValidationError(f"模板名称 '{new_name}' 已存在")
        
        # 创建新模板
        new_template = ConfigTemplate(
            name=new_name,
            description=f"克隆自 {original.name}",
            template=original.template.copy(),
            schema=original.schema.copy() if original.schema else None,
            type=original.type,
            category=original.category,
            is_active=True,
            is_default=False,  # 克隆的模板不设为默认
            version=original.version,
            tags=original.tags.copy() if original.tags else None,
            created_by=user_id
        )
        
        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        
        return new_template
    
    async def get_template_usage(
        self,
        db: AsyncSession,
        template_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        获取模板使用情况
        """
        from ..models.config import Config
        
        # 统计使用此模板的配置数量
        stmt = select(func.count(Config.id)).where(Config.template_id == template_id)
        result = await db.execute(stmt)
        usage_count = result.scalar()
        
        # 获取最近使用的配置
        recent_stmt = (
            select(Config.id, Config.key, Config.name, Config.created_at)
            .where(Config.template_id == template_id)
            .order_by(Config.created_at.desc())
            .limit(5)
        )
        recent_result = await db.execute(recent_stmt)
        recent_configs = [
            {
                "id": str(row.id),
                "key": row.key,
                "name": row.name,
                "created_at": row.created_at.isoformat()
            }
            for row in recent_result.fetchall()
        ]
        
        return {
            "usage_count": usage_count,
            "recent_configs": recent_configs
        }
    
    async def validate_template(
        self,
        template_content: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        验证模板内容
        """
        errors = []
        warnings = []
        
        try:
            await self._validate_template_content(template_content, schema)
        except Exception as e:
            errors.append(str(e))
        
        # 检查模板完整性
        if not template_content:
            errors.append("模板内容不能为空")
        
        if not isinstance(template_content, dict):
            errors.append("模板内容必须是字典类型")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    # 私有方法
    async def _validate_template_content(
        self,
        template: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        验证模板内容
        """
        if not isinstance(template, dict):
            raise ConfigValidationError("模板内容必须是字典类型")
        
        if not template:
            raise ConfigValidationError("模板内容不能为空")
        
        # JSON Schema验证
        if schema:
            import jsonschema
            try:
                jsonschema.validate(template, schema)
            except jsonschema.ValidationError as e:
                raise ConfigValidationError(f"模板Schema验证失败: {e.message}")
    
    async def _unset_default_templates(
        self,
        db: AsyncSession,
        template_type: ConfigType
    ) -> None:
        """
        取消指定类型的所有默认模板
        """
        stmt = (
            update(ConfigTemplate)
            .where(
                and_(
                    ConfigTemplate.type == template_type,
                    ConfigTemplate.is_default == True
                )
            )
            .values(is_default=False)
        )
        await db.execute(stmt)
        await db.commit()
    
    def get_builtin_templates(self) -> Dict[ConfigType, List[Dict[str, Any]]]:
        """
        获取内置模板
        """
        return {
            ConfigType.SYSTEM: [
                {
                    "name": "基础系统配置",
                    "description": "系统基础配置模板",
                    "template": {
                        "database": {
                            "host": "localhost",
                            "port": 5432,
                            "name": "cashup",
                            "pool_size": 10
                        },
                        "redis": {
                            "host": "localhost",
                            "port": 6379,
                            "db": 0
                        },
                        "logging": {
                            "level": "INFO",
                            "format": "json"
                        }
                    },
                    "schema": {
                        "type": "object",
                        "properties": {
                            "database": {
                                "type": "object",
                                "properties": {
                                    "host": {"type": "string"},
                                    "port": {"type": "integer"},
                                    "name": {"type": "string"},
                                    "pool_size": {"type": "integer"}
                                },
                                "required": ["host", "port", "name"]
                            }
                        },
                        "required": ["database"]
                    }
                }
            ],
            ConfigType.TRADING: [
                {
                    "name": "基础交易配置",
                    "description": "交易策略基础配置模板",
                    "template": {
                        "risk_management": {
                            "max_position_size": 0.1,
                            "stop_loss_pct": 0.02,
                            "take_profit_pct": 0.04
                        },
                        "execution": {
                            "order_type": "limit",
                            "timeout_seconds": 30
                        }
                    },
                    "schema": {
                        "type": "object",
                        "properties": {
                            "risk_management": {
                                "type": "object",
                                "properties": {
                                    "max_position_size": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1
                                    },
                                    "stop_loss_pct": {
                                        "type": "number",
                                        "minimum": 0
                                    }
                                }
                            }
                        }
                    }
                }
            ],
            ConfigType.USER: [
                {
                    "name": "用户偏好设置",
                    "description": "用户个人偏好配置模板",
                    "template": {
                        "ui": {
                            "theme": "dark",
                            "language": "zh-CN",
                            "timezone": "Asia/Shanghai"
                        },
                        "notifications": {
                            "email": True,
                            "sms": False,
                            "push": True
                        }
                    }
                }
            ],
            ConfigType.STRATEGY: [
                {
                    "name": "网格交易策略",
                    "description": "网格交易策略配置模板",
                    "template": {
                        "grid_count": 10,
                        "price_range": {
                            "upper": 1.1,
                            "lower": 0.9
                        },
                        "base_amount": 100,
                        "profit_ratio": 0.01
                    }
                },
                {
                    "name": "DCA策略",
                    "description": "定投策略配置模板",
                    "template": {
                        "interval_hours": 24,
                        "amount_per_order": 50,
                        "max_orders": 10,
                        "price_deviation_pct": 0.05
                    }
                }
            ]
        }