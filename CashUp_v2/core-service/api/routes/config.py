"""
配置管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime

from schemas.config import ConfigCreate, ConfigUpdate, ConfigResponse, ConfigListResponse
from services.config import ConfigService
from database.connection import get_db
from utils.logger import get_logger
from auth.dependencies import get_current_user, get_current_active_user

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)

@router.get("/", response_model=ConfigListResponse)
async def get_configs(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取配置列表"""
    try:
        config_service = ConfigService(db)
        configs, total = await config_service.get_configs(
            skip=skip, 
            limit=limit, 
            category=category, 
            search=search
        )
        
        return ConfigListResponse(
            configs=[ConfigResponse.from_orm(config) for config in configs],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"获取配置列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置列表失败"
        )

@router.get("/{config_id}", response_model=ConfigResponse)
async def get_config(
    config_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取配置详情"""
    try:
        config_service = ConfigService(db)
        config = await config_service.get_config_by_id(config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 检查权限：用户配置只能被创建者查看，系统配置管理员可查看
        if config.user_id and config.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此配置"
            )
        
        return ConfigResponse.from_orm(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置详情失败"
        )

@router.post("/", response_model=ConfigResponse)
async def create_config(
    config_data: ConfigCreate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建配置"""
    try:
        config_service = ConfigService(db)
        
        # 检查配置键是否已存在
        existing_config = await config_service.get_config_by_key(config_data.key)
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="配置键已存在"
            )
        
        # 如果是系统配置，只有管理员可以创建
        if config_data.is_system and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权创建系统配置"
            )
        
        # 创建配置
        config = await config_service.create_config(config_data, current_user.id)
        
        logger.info(f"配置创建成功: {config.key}")
        return ConfigResponse.from_orm(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建配置失败"
        )

@router.put("/{config_id}", response_model=ConfigResponse)
async def update_config(
    config_id: int,
    config_data: ConfigUpdate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新配置"""
    try:
        config_service = ConfigService(db)
        config = await config_service.get_config_by_id(config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 检查权限
        if config.user_id and config.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新此配置"
            )
        
        # 系统配置只有管理员可以更新
        if config.is_system and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新系统配置"
            )
        
        # 更新配置
        updated_config = await config_service.update_config(config_id, config_data)
        
        logger.info(f"配置更新成功: {updated_config.key}")
        return ConfigResponse.from_orm(updated_config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新配置失败"
        )

@router.delete("/{config_id}")
async def delete_config(
    config_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除配置"""
    try:
        config_service = ConfigService(db)
        config = await config_service.get_config_by_id(config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 检查权限
        if config.user_id and config.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此配置"
            )
        
        # 系统配置只有管理员可以删除
        if config.is_system and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除系统配置"
            )
        
        # 删除配置
        await config_service.delete_config(config_id)
        
        logger.info(f"配置删除成功: {config.key}")
        return {"message": "配置删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除配置失败"
        )

@router.get("/by-key/{key}", response_model=ConfigResponse)
async def get_config_by_key(
    key: str,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """根据键获取配置"""
    try:
        config_service = ConfigService(db)
        config = await config_service.get_config_by_key(key)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 检查权限
        if config.user_id and config.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此配置"
            )
        
        return ConfigResponse.from_orm(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置失败"
        )

@router.get("/category/{category}", response_model=ConfigListResponse)
async def get_configs_by_category(
    category: str,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """根据分类获取配置"""
    try:
        config_service = ConfigService(db)
        configs, total = await config_service.get_configs_by_category(
            category, skip=skip, limit=limit
        )
        
        # 过滤用户有权限查看的配置
        accessible_configs = []
        for config in configs:
            if config.user_id is None or config.user_id == current_user.id or current_user.role == "admin":
                accessible_configs.append(config)
        
        return ConfigListResponse(
            configs=[ConfigResponse.from_orm(config) for config in accessible_configs],
            total=len(accessible_configs),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"获取分类配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分类配置失败"
        )

@router.post("/batch")
async def batch_update_configs(
    configs: List[Dict[str, Any]],
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """批量更新配置"""
    try:
        config_service = ConfigService(db)
        updated_configs = []
        
        for config_data in configs:
            config_id = config_data.get('id')
            if not config_id:
                continue
            
            config = await config_service.get_config_by_id(config_id)
            if not config:
                continue
            
            # 检查权限
            if config.user_id and config.user_id != current_user.id and current_user.role != "admin":
                continue
            
            # 系统配置只有管理员可以更新
            if config.is_system and current_user.role != "admin":
                continue
            
            # 更新配置
            update_data = {k: v for k, v in config_data.items() if k != 'id'}
            updated_config = await config_service.update_config(config_id, update_data)
            updated_configs.append(updated_config)
        
        logger.info(f"批量更新配置成功: {len(updated_configs)} 个配置")
        return {
            "message": f"批量更新成功",
            "updated_count": len(updated_configs),
            "configs": [ConfigResponse.from_orm(config) for config in updated_configs]
        }
        
    except Exception as e:
        logger.error(f"批量更新配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量更新配置失败"
        )

@router.get("/my", response_model=ConfigListResponse)
async def get_my_configs(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的配置"""
    try:
        config_service = ConfigService(db)
        configs, total = await config_service.get_user_configs(
            current_user.id, skip=skip, limit=limit, category=category
        )
        
        return ConfigListResponse(
            configs=[ConfigResponse.from_orm(config) for config in configs],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"获取用户配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户配置失败"
        )