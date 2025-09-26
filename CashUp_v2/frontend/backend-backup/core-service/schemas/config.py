"""
配置数据模型定义
"""

from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ConfigType(str, Enum):
    """配置类型枚举"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY = "array"

class ConfigBase(BaseModel):
    """配置基础模型"""
    key: str
    value: Any
    description: Optional[str] = None
    category: Optional[str] = "general"
    config_type: ConfigType = ConfigType.STRING
    is_system: bool = False
    is_sensitive: bool = False
    
    @validator('key')
    def validate_key(cls, v):
        if not v or not v.strip():
            raise ValueError('配置键不能为空')
        if len(v) > 100:
            raise ValueError('配置键长度不能超过100个字符')
        return v.strip()

class ConfigCreate(ConfigBase):
    """创建配置模型"""
    pass

class ConfigUpdate(BaseModel):
    """更新配置模型"""
    value: Any
    description: Optional[str] = None
    category: Optional[str] = None
    
    @validator('value')
    def validate_value(cls, v):
        if v is None:
            raise ValueError('配置值不能为空')
        return v

class ConfigResponse(ConfigBase):
    """配置响应模型"""
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ConfigListResponse(BaseModel):
    """配置列表响应模型"""
    configs: List[ConfigResponse]
    total: int
    skip: int
    limit: int

class BatchConfigUpdate(BaseModel):
    """批量配置更新模型"""
    configs: List[Dict[str, Any]]
    
    @validator('configs')
    def validate_configs(cls, v):
        if not v:
            raise ValueError('配置列表不能为空')
        if len(v) > 100:
            raise ValueError('批量更新最多支持100个配置')
        return v