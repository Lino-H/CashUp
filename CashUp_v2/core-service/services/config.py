"""
配置服务层
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import json

from ..models.models import Config
from ..schemas.config import ConfigCreate, ConfigUpdate
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ConfigService:
    """配置服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_config_by_id(self, config_id: int) -> Optional[Config]:
        """根据ID获取配置"""
        query = select(Config).where(Config.id == config_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_config_by_key(self, key: str) -> Optional[Config]:
        """根据键获取配置"""
        query = select(Config).where(Config.key == key)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_configs(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        category: Optional[str] = None, 
        search: Optional[str] = None
    ) -> Tuple[List[Config], int]:
        """获取配置列表"""
        query = select(Config)
        
        conditions = []
        if category:
            conditions.append(Config.category == category)
        
        if search:
            conditions.append(
                or_(
                    Config.key.ilike(f"%{search}%"),
                    Config.description.ilike(f"%{search}%")
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 获取总数
        count_query = select(Config.__table__)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.db.execute(count_query)
        total = len(count_result.fetchall())
        
        # 分页查询
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        configs = result.scalars().all()
        
        return list(configs), total
    
    async def get_configs_by_category(
        self, 
        category: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Config], int]:
        """根据分类获取配置"""
        query = select(Config).where(Config.category == category)
        
        # 获取总数
        count_query = select(Config.__table__).where(Config.category == category)
        count_result = await self.db.execute(count_query)
        total = len(count_result.fetchall())
        
        # 分页查询
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        configs = result.scalars().all()
        
        return list(configs), total
    
    async def get_user_configs(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100, 
        category: Optional[str] = None
    ) -> Tuple[List[Config], int]:
        """获取用户配置"""
        query = select(Config).where(Config.user_id == user_id)
        
        if category:
            query = query.where(Config.category == category)
        
        # 获取总数
        count_query = select(Config.__table__).where(Config.user_id == user_id)
        if category:
            count_query = count_query.where(Config.category == category)
        
        count_result = await self.db.execute(count_query)
        total = len(count_result.fetchall())
        
        # 分页查询
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        configs = result.scalars().all()
        
        return list(configs), total
    
    async def create_config(self, config_data: ConfigCreate, user_id: Optional[int] = None) -> Config:
        """创建配置"""
        # 序列化复杂类型的值
        value = self._serialize_value(config_data.value, config_data.config_type)
        
        config = Config(
            key=config_data.key,
            value=value,
            description=config_data.description,
            category=config_data.category,
            config_type=config_data.config_type,
            is_system=config_data.is_system,
            is_sensitive=config_data.is_sensitive,
            user_id=user_id
        )
        
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        
        return config
    
    async def update_config(self, config_id: int, update_data: dict) -> Config:
        """更新配置"""
        # 如果更新值，需要序列化
        if 'value' in update_data:
            config = await self.get_config_by_id(config_id)
            if config:
                update_data['value'] = self._serialize_value(update_data['value'], config.config_type)
        
        query = update(Config).where(Config.id == config_id).values(**update_data)
        await self.db.execute(query)
        await self.db.commit()
        
        updated_config = await self.get_config_by_id(config_id)
        return updated_config
    
    async def delete_config(self, config_id: int) -> bool:
        """删除配置"""
        query = delete(Config).where(Config.id == config_id)
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def get_system_configs(self) -> Dict[str, Any]:
        """获取所有系统配置"""
        query = select(Config).where(Config.is_system == True)
        result = await self.db.execute(query)
        configs = result.scalars().all()
        
        return {config.key: self._deserialize_value(config.value, config.config_type) for config in configs}
    
    def _serialize_value(self, value: Any, config_type: str) -> str:
        """序列化配置值"""
        if config_type in ['json', 'array']:
            return json.dumps(value, ensure_ascii=False)
        return str(value)
    
    def _deserialize_value(self, value: str, config_type: str) -> Any:
        """反序列化配置值"""
        if config_type in ['json', 'array']:
            return json.loads(value)
        elif config_type == 'number':
            return float(value)
        elif config_type == 'boolean':
            return value.lower() in ['true', '1', 'yes']
        else:
            return value