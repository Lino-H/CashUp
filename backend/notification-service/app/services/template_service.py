#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 模板服务业务逻辑

处理通知模板的管理、渲染等业务逻辑
"""

import uuid
import re
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from jinja2 import Template, Environment, BaseLoader, TemplateError

from ..models.template import NotificationTemplate, TemplateType
from ..models.notification import NotificationCategory
from ..schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateFilter,
    TemplateRender, TemplatePreview, TemplateValidation
)
from ..core.exceptions import (
    TemplateNotFoundError, InvalidTemplateError, TemplateRenderError
)
from ..core.config import get_config

import logging

logger = logging.getLogger(__name__)
config = get_config()


class TemplateService:
    """
    模板服务业务逻辑类
    
    负责处理通知模板的管理、渲染等业务逻辑
    """
    
    def __init__(self):
        # 初始化Jinja2环境
        self.jinja_env = Environment(
            loader=BaseLoader(),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 添加自定义过滤器
        self._setup_custom_filters()
    
    def _setup_custom_filters(self):
        """
        设置自定义Jinja2过滤器
        """
        @self.jinja_env.filter('currency')
        def currency_filter(value, currency='USD'):
            """货币格式化过滤器"""
            try:
                return f"{float(value):,.2f} {currency}"
            except (ValueError, TypeError):
                return str(value)
        
        @self.jinja_env.filter('percentage')
        def percentage_filter(value, decimals=2):
            """百分比格式化过滤器"""
            try:
                return f"{float(value):.{decimals}f}%"
            except (ValueError, TypeError):
                return str(value)
        
        @self.jinja_env.filter('datetime_format')
        def datetime_format_filter(value, format='%Y-%m-%d %H:%M:%S'):
            """日期时间格式化过滤器"""
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    return str(value)
            
            if isinstance(value, datetime):
                return value.strftime(format)
            return str(value)
    
    async def create_template(
        self,
        db: AsyncSession,
        template_data: TemplateCreate,
        created_by: Optional[uuid.UUID] = None
    ) -> NotificationTemplate:
        """
        创建模板
        
        Args:
            db: 数据库会话
            template_data: 模板创建数据
            created_by: 创建者ID
            
        Returns:
            NotificationTemplate: 创建的模板
            
        Raises:
            InvalidTemplateError: 无效的模板数据
        """
        try:
            # 检查模板名称是否已存在
            existing = await self.get_template_by_name(db, template_data.name)
            if existing:
                raise InvalidTemplateError(f"Template with name '{template_data.name}' already exists")
            
            # 验证模板语法
            validation_result = await self._validate_template_syntax(
                template_data.subject,
                template_data.content,
                template_data.html_content
            )
            
            if not validation_result["is_valid"]:
                raise InvalidTemplateError(f"Template syntax errors: {', '.join(validation_result['errors'])}")
            
            # 检测模板变量
            detected_variables = self._extract_template_variables(
                template_data.subject,
                template_data.content,
                template_data.html_content
            )
            
            # 创建模板对象
            template = NotificationTemplate(
                id=uuid.uuid4(),
                name=template_data.name,
                display_name=template_data.display_name,
                description=template_data.description,
                type=template_data.type,
                category=template_data.category,
                subject=template_data.subject,
                content=template_data.content,
                html_content=template_data.html_content,
                variables=template_data.variables or detected_variables,
                config=template_data.config or {},
                is_active=template_data.is_active,
                usage_count=0,
                created_by=created_by,
                metadata=template_data.metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # 保存到数据库
            db.add(template)
            await db.commit()
            await db.refresh(template)
            
            logger.info(f"Created template {template.id} with name '{template.name}'")
            return template
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create template: {str(e)}")
            raise
    
    async def get_template(
        self,
        db: AsyncSession,
        template_id: uuid.UUID
    ) -> Optional[NotificationTemplate]:
        """
        获取模板详情
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            
        Returns:
            Optional[NotificationTemplate]: 模板对象
        """
        result = await db.execute(
            select(NotificationTemplate)
            .where(NotificationTemplate.id == template_id)
        )
        return result.scalar_one_or_none()
    
    async def get_template_by_name(
        self,
        db: AsyncSession,
        name: str
    ) -> Optional[NotificationTemplate]:
        """
        根据名称获取模板
        
        Args:
            db: 数据库会话
            name: 模板名称
            
        Returns:
            Optional[NotificationTemplate]: 模板对象
        """
        result = await db.execute(
            select(NotificationTemplate)
            .where(NotificationTemplate.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_templates(
        self,
        db: AsyncSession,
        filters: TemplateFilter,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[NotificationTemplate], int]:
        """
        获取模板列表
        
        Args:
            db: 数据库会话
            filters: 过滤条件
            page: 页码
            size: 每页大小
            
        Returns:
            Tuple[List[NotificationTemplate], int]: 模板列表和总数
        """
        # 构建查询条件
        conditions = []
        
        if filters.name:
            conditions.append(NotificationTemplate.name.ilike(f"%{filters.name}%"))
        
        if filters.type:
            conditions.append(NotificationTemplate.type == filters.type)
        
        if filters.category:
            conditions.append(NotificationTemplate.category == filters.category)
        
        if filters.is_active is not None:
            conditions.append(NotificationTemplate.is_active == filters.is_active)
        
        if filters.has_html is not None:
            if filters.has_html:
                conditions.append(NotificationTemplate.html_content.isnot(None))
            else:
                conditions.append(NotificationTemplate.html_content.is_(None))
        
        if filters.has_subject is not None:
            if filters.has_subject:
                conditions.append(NotificationTemplate.subject.isnot(None))
            else:
                conditions.append(NotificationTemplate.subject.is_(None))
        
        if filters.min_usage is not None:
            conditions.append(NotificationTemplate.usage_count >= filters.min_usage)
        
        if filters.max_usage is not None:
            conditions.append(NotificationTemplate.usage_count <= filters.max_usage)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    NotificationTemplate.name.ilike(search_term),
                    NotificationTemplate.display_name.ilike(search_term),
                    NotificationTemplate.description.ilike(search_term),
                    NotificationTemplate.content.ilike(search_term)
                )
            )
        
        if filters.start_date:
            conditions.append(NotificationTemplate.created_at >= filters.start_date)
        
        if filters.end_date:
            conditions.append(NotificationTemplate.created_at <= filters.end_date)
        
        if filters.created_by:
            conditions.append(NotificationTemplate.created_by == uuid.UUID(filters.created_by))
        
        # 查询总数
        count_query = select(func.count(NotificationTemplate.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 查询数据
        query = select(NotificationTemplate)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(NotificationTemplate.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        return list(templates), total
    
    async def update_template(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        update_data: TemplateUpdate,
        updated_by: Optional[uuid.UUID] = None
    ) -> Optional[NotificationTemplate]:
        """
        更新模板
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            update_data: 更新数据
            updated_by: 更新者ID
            
        Returns:
            Optional[NotificationTemplate]: 更新后的模板
            
        Raises:
            TemplateNotFoundError: 模板不存在
            InvalidTemplateError: 无效的更新数据
        """
        template = await self.get_template(db, template_id)
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")
        
        # 验证更新的模板语法（如果有内容更新）
        if update_data.content or update_data.subject or update_data.html_content:
            subject = update_data.subject if update_data.subject is not None else template.subject
            content = update_data.content if update_data.content is not None else template.content
            html_content = update_data.html_content if update_data.html_content is not None else template.html_content
            
            validation_result = await self._validate_template_syntax(subject, content, html_content)
            if not validation_result["is_valid"]:
                raise InvalidTemplateError(f"Template syntax errors: {', '.join(validation_result['errors'])}")
        
        # 更新字段
        update_fields = update_data.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(template, field, value)
        
        # 重新检测变量（如果内容有更新）
        if update_data.content or update_data.subject or update_data.html_content:
            detected_variables = self._extract_template_variables(
                template.subject,
                template.content,
                template.html_content
            )
            if update_data.variables is None:
                template.variables = detected_variables
        
        template.updated_by = updated_by
        template.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Updated template {template_id}")
        return template
    
    async def delete_template(
        self,
        db: AsyncSession,
        template_id: uuid.UUID
    ) -> bool:
        """
        删除模板
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            
        Returns:
            bool: 是否删除成功
        """
        result = await db.execute(
            delete(NotificationTemplate).where(NotificationTemplate.id == template_id)
        )
        await db.commit()
        
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted template {template_id}")
        
        return deleted
    
    async def render_template(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        渲染模板
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            variables: 模板变量
            
        Returns:
            Dict[str, Any]: 渲染结果
            
        Raises:
            TemplateNotFoundError: 模板不存在
            TemplateRenderError: 渲染错误
        """
        template = await self.get_template(db, template_id)
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")
        
        if not template.is_active:
            raise InvalidTemplateError(f"Template {template_id} is not active")
        
        start_time = time.time()
        
        try:
            result = {}
            variables_used = set()
            
            # 渲染主题
            if template.subject:
                subject_template = self.jinja_env.from_string(template.subject)
                result["subject"] = subject_template.render(**variables)
                variables_used.update(self._extract_variables_from_template(template.subject))
            
            # 渲染内容
            content_template = self.jinja_env.from_string(template.content)
            result["content"] = content_template.render(**variables)
            variables_used.update(self._extract_variables_from_template(template.content))
            
            # 渲染HTML内容
            if template.html_content:
                html_template = self.jinja_env.from_string(template.html_content)
                result["html_content"] = html_template.render(**variables)
                variables_used.update(self._extract_variables_from_template(template.html_content))
            
            # 计算渲染时间
            render_time_ms = (time.time() - start_time) * 1000
            
            # 检查缺失的变量
            expected_variables = set(template.variables or [])
            provided_variables = set(variables.keys())
            missing_variables = expected_variables - provided_variables
            
            # 更新使用次数
            await self._increment_usage_count(db, template_id)
            
            logger.info(f"Rendered template {template_id} in {render_time_ms:.2f}ms")
            
            return {
                "template_id": template_id,
                "rendered_subject": result.get("subject"),
                "rendered_content": result["content"],
                "rendered_html": result.get("html_content"),
                "variables_used": list(variables_used),
                "variables_missing": list(missing_variables),
                "render_time_ms": render_time_ms
            }
            
        except TemplateError as e:
            logger.error(f"Template render error for {template_id}: {str(e)}")
            raise TemplateRenderError(f"Template render error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error rendering template {template_id}: {str(e)}")
            raise TemplateRenderError(f"Unexpected render error: {str(e)}")
    
    async def preview_template(
        self,
        preview_data: TemplatePreview
    ) -> Dict[str, Any]:
        """
        预览模板
        
        Args:
            preview_data: 预览数据
            
        Returns:
            Dict[str, Any]: 预览结果
        """
        try:
            variables = preview_data.variables or {}
            result = {}
            
            # 检测变量
            detected_variables = self._extract_template_variables(
                preview_data.subject,
                preview_data.content,
                preview_data.html_content
            )
            
            # 生成示例数据
            sample_data = self._generate_sample_data(detected_variables, preview_data.type)
            
            # 合并用户提供的变量和示例数据
            render_variables = {**sample_data, **variables}
            
            # 渲染主题
            if preview_data.subject:
                subject_template = self.jinja_env.from_string(preview_data.subject)
                result["rendered_subject"] = subject_template.render(**render_variables)
            
            # 渲染内容
            content_template = self.jinja_env.from_string(preview_data.content)
            result["rendered_content"] = content_template.render(**render_variables)
            
            # 渲染HTML内容
            if preview_data.html_content:
                html_template = self.jinja_env.from_string(preview_data.html_content)
                result["rendered_html"] = html_template.render(**render_variables)
            
            return {
                "rendered_subject": result.get("rendered_subject"),
                "rendered_content": result["rendered_content"],
                "rendered_html": result.get("rendered_html"),
                "detected_variables": detected_variables,
                "sample_data": sample_data
            }
            
        except TemplateError as e:
            raise TemplateRenderError(f"Template preview error: {str(e)}")
        except Exception as e:
            raise TemplateRenderError(f"Unexpected preview error: {str(e)}")
    
    async def validate_template(
        self,
        validation_data: TemplateValidation
    ) -> Dict[str, Any]:
        """
        验证模板
        
        Args:
            validation_data: 验证数据
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        errors = []
        warnings = []
        
        # 语法检查
        syntax_result = await self._validate_template_syntax(
            validation_data.subject,
            validation_data.content,
            validation_data.html_content
        )
        
        errors.extend(syntax_result["errors"])
        warnings.extend(syntax_result["warnings"])
        
        # 检测变量
        detected_variables = self._extract_template_variables(
            validation_data.subject,
            validation_data.content,
            validation_data.html_content
        )
        
        # 变量检查
        expected_variables = set(validation_data.variables or [])
        detected_variables_set = set(detected_variables)
        
        unused_variables = expected_variables - detected_variables_set
        missing_variables = detected_variables_set - expected_variables
        
        if unused_variables:
            warnings.append(f"Unused variables: {', '.join(unused_variables)}")
        
        if missing_variables:
            warnings.append(f"Variables not in expected list: {', '.join(missing_variables)}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "detected_variables": detected_variables,
            "unused_variables": list(unused_variables),
            "missing_variables": list(missing_variables),
            "syntax_check": syntax_result
        }
    
    async def clone_template(
        self,
        db: AsyncSession,
        source_template_id: uuid.UUID,
        new_name: str,
        new_display_name: Optional[str] = None,
        copy_config: bool = True,
        copy_metadata: bool = False,
        created_by: Optional[uuid.UUID] = None
    ) -> NotificationTemplate:
        """
        克隆模板
        
        Args:
            db: 数据库会话
            source_template_id: 源模板ID
            new_name: 新模板名称
            new_display_name: 新模板显示名称
            copy_config: 是否复制配置
            copy_metadata: 是否复制元数据
            created_by: 创建者ID
            
        Returns:
            NotificationTemplate: 克隆的模板
            
        Raises:
            TemplateNotFoundError: 源模板不存在
            InvalidTemplateError: 无效的克隆参数
        """
        source_template = await self.get_template(db, source_template_id)
        if not source_template:
            raise TemplateNotFoundError(f"Source template {source_template_id} not found")
        
        # 检查新名称是否已存在
        existing = await self.get_template_by_name(db, new_name)
        if existing:
            raise InvalidTemplateError(f"Template with name '{new_name}' already exists")
        
        # 创建克隆模板
        cloned_template = NotificationTemplate(
            id=uuid.uuid4(),
            name=new_name,
            display_name=new_display_name or f"{source_template.display_name} (Copy)",
            description=source_template.description,
            type=source_template.type,
            category=source_template.category,
            subject=source_template.subject,
            content=source_template.content,
            html_content=source_template.html_content,
            variables=source_template.variables.copy() if source_template.variables else [],
            config=source_template.config.copy() if copy_config and source_template.config else {},
            is_active=True,
            usage_count=0,
            created_by=created_by,
            metadata=source_template.metadata.copy() if copy_metadata and source_template.metadata else {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 保存到数据库
        db.add(cloned_template)
        await db.commit()
        await db.refresh(cloned_template)
        
        logger.info(f"Cloned template {source_template_id} to {cloned_template.id}")
        return cloned_template
    
    async def get_template_stats(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取模板统计信息
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        conditions = []
        
        if start_date:
            conditions.append(NotificationTemplate.created_at >= start_date)
        
        if end_date:
            conditions.append(NotificationTemplate.created_at <= end_date)
        
        base_query = select(NotificationTemplate)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # 总数统计
        total_query = select(func.count(NotificationTemplate.id))
        if conditions:
            total_query = total_query.where(and_(*conditions))
        
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        # 活跃模板数
        active_query = select(func.count(NotificationTemplate.id)).where(
            NotificationTemplate.is_active == True
        )
        if conditions:
            active_query = active_query.where(and_(*conditions))
        
        active_result = await db.execute(active_query)
        active = active_result.scalar()
        
        # 按类型统计
        type_query = select(
            NotificationTemplate.type,
            func.count(NotificationTemplate.id)
        ).group_by(NotificationTemplate.type)
        if conditions:
            type_query = type_query.where(and_(*conditions))
        
        type_result = await db.execute(type_query)
        type_stats = {template_type.value: count for template_type, count in type_result.fetchall()}
        
        # 按分类统计
        category_query = select(
            NotificationTemplate.category,
            func.count(NotificationTemplate.id)
        ).group_by(NotificationTemplate.category)
        if conditions:
            category_query = category_query.where(and_(*conditions))
        
        category_result = await db.execute(category_query)
        category_stats = {category.value: count for category, count in category_result.fetchall()}
        
        # 最常用模板
        most_used_query = select(NotificationTemplate).order_by(
            NotificationTemplate.usage_count.desc()
        ).limit(5)
        if conditions:
            most_used_query = most_used_query.where(and_(*conditions))
        
        most_used_result = await db.execute(most_used_query)
        most_used = [
            {
                "id": str(template.id),
                "name": template.name,
                "display_name": template.display_name,
                "usage_count": template.usage_count
            }
            for template in most_used_result.scalars().all()
        ]
        
        # 总使用次数
        usage_query = select(func.sum(NotificationTemplate.usage_count))
        if conditions:
            usage_query = usage_query.where(and_(*conditions))
        
        usage_result = await db.execute(usage_query)
        total_usage = usage_result.scalar() or 0
        
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_type": type_stats,
            "by_category": category_stats,
            "most_used": most_used,
            "total_usage": total_usage,
            "average_usage": total_usage / total if total > 0 else 0.0
        }
    
    async def _validate_template_syntax(
        self,
        subject: Optional[str],
        content: str,
        html_content: Optional[str]
    ) -> Dict[str, Any]:
        """
        验证模板语法
        
        Args:
            subject: 主题模板
            content: 内容模板
            html_content: HTML内容模板
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        errors = []
        warnings = []
        
        # 验证主题模板
        if subject:
            try:
                self.jinja_env.from_string(subject)
            except TemplateError as e:
                errors.append(f"Subject template syntax error: {str(e)}")
        
        # 验证内容模板
        try:
            self.jinja_env.from_string(content)
        except TemplateError as e:
            errors.append(f"Content template syntax error: {str(e)}")
        
        # 验证HTML内容模板
        if html_content:
            try:
                self.jinja_env.from_string(html_content)
            except TemplateError as e:
                errors.append(f"HTML content template syntax error: {str(e)}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _extract_template_variables(
        self,
        subject: Optional[str],
        content: str,
        html_content: Optional[str]
    ) -> List[str]:
        """
        提取模板变量
        
        Args:
            subject: 主题模板
            content: 内容模板
            html_content: HTML内容模板
            
        Returns:
            List[str]: 变量列表
        """
        variables = set()
        
        # 从主题提取变量
        if subject:
            variables.update(self._extract_variables_from_template(subject))
        
        # 从内容提取变量
        variables.update(self._extract_variables_from_template(content))
        
        # 从HTML内容提取变量
        if html_content:
            variables.update(self._extract_variables_from_template(html_content))
        
        return sorted(list(variables))
    
    def _extract_variables_from_template(self, template_str: str) -> List[str]:
        """
        从模板字符串中提取变量
        
        Args:
            template_str: 模板字符串
            
        Returns:
            List[str]: 变量列表
        """
        # 使用正则表达式匹配Jinja2变量
        variable_pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*(?:\|[^}]*)?\}\}'
        matches = re.findall(variable_pattern, template_str)
        
        # 提取变量名（去除过滤器）
        variables = []
        for match in matches:
            # 只取变量名的第一部分（去除属性访问）
            var_name = match.split('.')[0]
            if var_name not in variables:
                variables.append(var_name)
        
        return variables
    
    def _generate_sample_data(
        self,
        variables: List[str],
        template_type: TemplateType
    ) -> Dict[str, Any]:
        """
        生成示例数据
        
        Args:
            variables: 变量列表
            template_type: 模板类型
            
        Returns:
            Dict[str, Any]: 示例数据
        """
        sample_data = {}
        
        # 根据模板类型和变量名生成示例数据
        for var in variables:
            var_lower = var.lower()
            
            if 'user' in var_lower or 'name' in var_lower:
                sample_data[var] = "John Doe"
            elif 'email' in var_lower:
                sample_data[var] = "john.doe@example.com"
            elif 'phone' in var_lower:
                sample_data[var] = "+1-555-123-4567"
            elif 'price' in var_lower or 'amount' in var_lower:
                sample_data[var] = 1234.56
            elif 'quantity' in var_lower or 'count' in var_lower:
                sample_data[var] = 10
            elif 'date' in var_lower or 'time' in var_lower:
                sample_data[var] = datetime.utcnow().isoformat()
            elif 'url' in var_lower or 'link' in var_lower:
                sample_data[var] = "https://example.com"
            elif 'percent' in var_lower or 'rate' in var_lower:
                sample_data[var] = 15.5
            elif template_type == TemplateType.TRADING:
                if 'symbol' in var_lower:
                    sample_data[var] = "BTCUSDT"
                elif 'side' in var_lower:
                    sample_data[var] = "BUY"
                elif 'order' in var_lower:
                    sample_data[var] = "ORD123456"
                else:
                    sample_data[var] = f"Sample {var}"
            else:
                sample_data[var] = f"Sample {var}"
        
        return sample_data
    
    async def _increment_usage_count(
        self,
        db: AsyncSession,
        template_id: uuid.UUID
    ):
        """
        增加模板使用次数
        
        Args:
            db: 数据库会话
            template_id: 模板ID
        """
        await db.execute(
            update(NotificationTemplate)
            .where(NotificationTemplate.id == template_id)
            .values(
                usage_count=NotificationTemplate.usage_count + 1,
                last_used_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()