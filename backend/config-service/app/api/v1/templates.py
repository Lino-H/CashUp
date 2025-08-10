#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 配置模板API路由

提供配置模板的REST API接口
"""

import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_database_session
from ...core.exceptions import (
    ConfigNotFoundError,
    ConfigValidationError,
    ConfigPermissionError
)
from ...services.template_service import TemplateService
from ...schemas.config import (
    ConfigTemplateCreate,
    ConfigTemplateUpdate,
    ConfigTemplateResponse,
    ConfigTemplateListResponse
)
from ...models.config import ConfigType

router = APIRouter(prefix="/templates", tags=["配置模板"])


# 依赖注入
async def get_template_service() -> TemplateService:
    """
    获取模板服务实例
    """
    return TemplateService()


async def get_current_user_id() -> Optional[uuid.UUID]:
    """
    获取当前用户ID（这里简化处理，实际应该从JWT token中获取）
    """
    # TODO: 实现真正的用户认证
    return None


@router.post("/", response_model=ConfigTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: ConfigTemplateCreate,
    db: AsyncSession = Depends(get_database_session),
    template_service: TemplateService = Depends(get_template_service),
    current_user_id: Optional[uuid.UUID] = Depends(get_current_user_id)
):
    """
    创建配置模板
    """
    try:
        template = await template_service.create_template(db, template_data, current_user_id)
        return ConfigTemplateResponse.from_orm(template)
    except ConfigValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=ConfigTemplateListResponse)
async def list_templates(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    type: Optional[ConfigType] = Query(None, description="模板类型"),
    category: Optional[str] = Query(None, description="模板分类"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_database_session),
    template_service: TemplateService = Depends(get_template_service)
):
    """
    获取配置模板列表
    """
    try:
        templates, total = await template_service.list_templates(
            db, type, category, is_active, search, page, size
        )
        
        pages = (total + size - 1) // size
        
        return ConfigTemplateListResponse(
            items=[ConfigTemplateResponse.from_orm(template) for template in templates],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{template_id}", response_model=ConfigTemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    template_service: TemplateService = Depends(get_template_service)
):
    """
    获取配置模板详情
    """
    try:
        template = await template_service.get_template_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")
        return ConfigTemplateResponse.from_orm(template)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{template_id}", response_model=ConfigTemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    template_data: ConfigTemplateUpdate,
    db: AsyncSession = Depends(get_database_session),
    template_service: TemplateService = Depends(get_template_service),
    current_user_id: Optional[uuid.UUID] = Depends(get_current_user_id)
):
    """
    更新配置模板
    """
    try:
        template = await template_service.update_template(db, template_id, template_data, current_user_id)
        return ConfigTemplateResponse.from_orm(template)
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConfigValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    template_service: TemplateService = Depends(get_template_service),
    current_user_id: Optional[uuid.UUID] = Depends(get_current_user_id)
):
    """
    删除配置模板
    """
    try:
        await template_service.delete_template(db, template_id, current_user_id)
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConfigPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/type/{template_type}/default", response_model=ConfigTemplateResponse)
async def get_default_template(
    template_type: ConfigType,
    db: AsyncSession = Depends(get_database_session),
    template_service: TemplateService = Depends(get_template_service)
):
    """
    获取指定类型的默认模板
    """
    try:
        template = await template_service.get_default_template(db, template_type)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="默认模板不存在")
        return ConfigTemplateResponse.from_orm(template)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{template_id}/apply")
async def apply_template(
    template_id: uuid.UUID,
    user_values: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_database_session),
    template_service: TemplateService = Depends(get_template_service)
):
    """
    应用模板生成配置值
    """
    try:
        result = await template_service.apply_template(db, template_id, user_values)
        return {"config_value": result}
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConfigValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{template_id}/clone", response_model=ConfigTemplateResponse)
async def clone_template(
    template_id: uuid.UUID,
    new_name: str = Query(..., description="新模板名称"),
    db: AsyncSession = Depends(get_database_session),
    template_service: TemplateService = Depends(get_template_service),
    current_user_id: Optional[uuid.UUID] = Depends(get_current_user_id)
):
    """
    克隆配置模板
    """
    try:
        template = await template_service.clone_template(db, template_id, new_name, current_user_id)
        return ConfigTemplateResponse.from_orm(template)
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConfigValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{template_id}/usage")
async def get_template_usage(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    template_service: TemplateService = Depends(get_template_service)
):
    """
    获取模板使用情况
    """
    try:
        usage = await template_service.get_template_usage(db, template_id)
        return usage
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/validate")
async def validate_template(
    template_content: Dict[str, Any],
    schema: Optional[Dict[str, Any]] = None,
    template_service: TemplateService = Depends(get_template_service)
):
    """
    验证模板内容
    """
    try:
        result = await template_service.validate_template(template_content, schema)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/builtin/list")
async def get_builtin_templates(
    template_service: TemplateService = Depends(get_template_service)
):
    """
    获取内置模板列表
    """
    try:
        builtin_templates = template_service.get_builtin_templates()
        return builtin_templates
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/builtin/install")
async def install_builtin_templates(
    template_types: Optional[list[ConfigType]] = None,
    db: AsyncSession = Depends(get_database_session),
    template_service: TemplateService = Depends(get_template_service),
    current_user_id: Optional[uuid.UUID] = Depends(get_current_user_id)
):
    """
    安装内置模板
    """
    try:
        builtin_templates = template_service.get_builtin_templates()
        installed_count = 0
        failed_count = 0
        details = []
        
        # 如果没有指定类型，安装所有类型的模板
        if not template_types:
            template_types = list(builtin_templates.keys())
        
        for template_type in template_types:
            if template_type not in builtin_templates:
                continue
            
            for template_data in builtin_templates[template_type]:
                try:
                    # 检查是否已存在
                    existing = await template_service.get_template_by_name(
                        db, template_data["name"], template_type
                    )
                    
                    if existing:
                        details.append({
                            "name": template_data["name"],
                            "type": template_type.value,
                            "status": "skipped",
                            "reason": "已存在"
                        })
                        continue
                    
                    # 创建模板
                    create_data = ConfigTemplateCreate(
                        name=template_data["name"],
                        description=template_data["description"],
                        template=template_data["template"],
                        schema=template_data.get("schema"),
                        type=template_type,
                        is_active=True,
                        is_default=False
                    )
                    
                    await template_service.create_template(db, create_data, current_user_id)
                    installed_count += 1
                    
                    details.append({
                        "name": template_data["name"],
                        "type": template_type.value,
                        "status": "installed"
                    })
                    
                except Exception as e:
                    failed_count += 1
                    details.append({
                        "name": template_data["name"],
                        "type": template_type.value,
                        "status": "failed",
                        "error": str(e)
                    })
        
        return {
            "installed_count": installed_count,
            "failed_count": failed_count,
            "details": details
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))