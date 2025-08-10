#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 配置服务核心业务逻辑

提供配置的CRUD操作、版本管理、缓存、验证等功能
"""

import uuid
import json
import yaml
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.config import get_settings
from ..core.cache import ConfigCache
from ..core.exceptions import (
    ConfigNotFoundError,
    ConfigValidationError,
    ConfigPermissionError,
    ConfigVersionError,
    ConfigCacheError
)
from ..models.config import (
    Config,
    ConfigTemplate,
    ConfigVersion,
    ConfigAuditLog,
    ConfigType,
    ConfigScope,
    ConfigStatus,
    ConfigFormat
)
from ..schemas.config import (
    ConfigCreate,
    ConfigUpdate,
    ConfigFilter,
    ConfigValidationRequest,
    ConfigValidationResponse,
    ConfigBatchOperation,
    ConfigSyncRequest,
    ConfigSyncResponse,
    ConfigStatistics,
    ConfigExportRequest,
    ConfigImportRequest,
    ConfigImportResponse
)


class ConfigService:
    """
    配置服务核心业务逻辑
    """
    
    def __init__(self, cache: ConfigCache):
        self.cache = cache
        self.settings = get_settings()
    
    async def create_config(
        self,
        db: AsyncSession,
        config_data: ConfigCreate,
        user_id: Optional[uuid.UUID] = None
    ) -> Config:
        """
        创建配置
        """
        # 检查配置键是否已存在
        existing = await self.get_config_by_key(
            db, config_data.key, config_data.scope, 
            config_data.user_id, config_data.strategy_id
        )
        if existing:
            raise ConfigValidationError(f"配置键 '{config_data.key}' 已存在")
        
        # 验证配置值
        validation_result = await self.validate_config_value(
            config_data.value,
            config_data.schema,
            config_data.validation_rules
        )
        if not validation_result.is_valid:
            raise ConfigValidationError(f"配置值验证失败: {', '.join(validation_result.errors)}")
        
        # 处理模板继承
        if config_data.template_id:
            template = await self.get_template_by_id(db, config_data.template_id)
            if template:
                config_data.value = self._merge_template_values(template.template, config_data.value)
        
        # 加密敏感配置
        if config_data.is_encrypted:
            config_data.value = await self._encrypt_config_value(config_data.value)
        
        # 创建配置
        config = Config(
            **config_data.dict(),
            version=1,
            created_by=user_id,
            updated_by=user_id
        )
        
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
        # 创建初始版本
        await self._create_config_version(
            db, config.id, config.value, "初始创建", user_id
        )
        
        # 记录审计日志
        await self._create_audit_log(
            db, config.id, "CREATE", None, config.value, user_id
        )
        
        # 更新缓存
        await self._update_config_cache(config)
        
        # 发送配置变更通知
        await self._notify_config_change(config, "CREATE")
        
        return config
    
    async def get_config_by_id(
        self,
        db: AsyncSession,
        config_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> Optional[Config]:
        """
        根据ID获取配置
        """
        # 先从缓存获取
        cached_config = await self.cache.get_config(str(config_id))
        if cached_config:
            config_dict = json.loads(cached_config)
            # 检查权限
            if not await self._check_config_permission(config_dict, user_id, "READ"):
                raise ConfigPermissionError("无权限访问此配置")
            return Config(**config_dict)
        
        # 从数据库获取
        stmt = select(Config).where(Config.id == config_id)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            return None
        
        # 检查权限
        if not await self._check_config_permission(config, user_id, "READ"):
            raise ConfigPermissionError("无权限访问此配置")
        
        # 解密敏感配置
        if config.is_encrypted:
            config.value = await self._decrypt_config_value(config.value)
        
        # 更新缓存
        await self._update_config_cache(config)
        
        return config
    
    async def get_config_by_key(
        self,
        db: AsyncSession,
        key: str,
        scope: ConfigScope = ConfigScope.GLOBAL,
        user_id: Optional[uuid.UUID] = None,
        strategy_id: Optional[uuid.UUID] = None
    ) -> Optional[Config]:
        """
        根据键获取配置
        """
        # 构建缓存键
        cache_key = f"config:key:{key}:{scope.value}"
        if user_id:
            cache_key += f":user:{user_id}"
        if strategy_id:
            cache_key += f":strategy:{strategy_id}"
        
        # 先从缓存获取
        cached_config = await self.cache.get_config(cache_key)
        if cached_config:
            config_dict = json.loads(cached_config)
            return Config(**config_dict)
        
        # 从数据库获取
        conditions = [Config.key == key, Config.scope == scope]
        if user_id:
            conditions.append(Config.user_id == user_id)
        if strategy_id:
            conditions.append(Config.strategy_id == strategy_id)
        
        stmt = select(Config).where(and_(*conditions))
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if config:
            # 解密敏感配置
            if config.is_encrypted:
                config.value = await self._decrypt_config_value(config.value)
            
            # 更新缓存
            await self.cache.set_config(cache_key, json.dumps(config.dict()), ttl=3600)
        
        return config
    
    async def update_config(
        self,
        db: AsyncSession,
        config_id: uuid.UUID,
        config_data: ConfigUpdate,
        user_id: Optional[uuid.UUID] = None
    ) -> Config:
        """
        更新配置
        """
        # 获取现有配置
        config = await self.get_config_by_id(db, config_id, user_id)
        if not config:
            raise ConfigNotFoundError(f"配置 {config_id} 不存在")
        
        # 检查权限
        if not await self._check_config_permission(config, user_id, "UPDATE"):
            raise ConfigPermissionError("无权限更新此配置")
        
        # 检查只读配置
        if config.is_readonly:
            raise ConfigPermissionError("配置为只读，无法更新")
        
        # 保存旧值
        old_value = config.value.copy()
        
        # 更新字段
        update_data = config_data.dict(exclude_unset=True)
        
        # 验证新的配置值
        if 'value' in update_data:
            validation_result = await self.validate_config_value(
                update_data['value'],
                config.schema,
                config.validation_rules
            )
            if not validation_result.is_valid:
                raise ConfigValidationError(f"配置值验证失败: {', '.join(validation_result.errors)}")
            
            # 加密敏感配置
            if config.is_encrypted:
                update_data['value'] = await self._encrypt_config_value(update_data['value'])
        
        # 更新配置
        for field, value in update_data.items():
            setattr(config, field, value)
        
        config.version += 1
        config.updated_at = datetime.utcnow()
        config.updated_by = user_id
        
        await db.commit()
        await db.refresh(config)
        
        # 创建版本记录
        if 'value' in update_data:
            await self._create_config_version(
                db, config.id, config.value, "配置更新", user_id
            )
        
        # 记录审计日志
        await self._create_audit_log(
            db, config.id, "UPDATE", old_value, config.value, user_id
        )
        
        # 更新缓存
        await self._update_config_cache(config)
        
        # 发送配置变更通知
        await self._notify_config_change(config, "UPDATE")
        
        return config
    
    async def delete_config(
        self,
        db: AsyncSession,
        config_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> bool:
        """
        删除配置
        """
        # 获取配置
        config = await self.get_config_by_id(db, config_id, user_id)
        if not config:
            raise ConfigNotFoundError(f"配置 {config_id} 不存在")
        
        # 检查权限
        if not await self._check_config_permission(config, user_id, "DELETE"):
            raise ConfigPermissionError("无权限删除此配置")
        
        # 检查是否为必需配置
        if config.is_required:
            raise ConfigPermissionError("必需配置无法删除")
        
        # 记录审计日志
        await self._create_audit_log(
            db, config.id, "DELETE", config.value, None, user_id
        )
        
        # 删除配置
        await db.delete(config)
        await db.commit()
        
        # 清除缓存
        await self._clear_config_cache(config)
        
        # 发送配置变更通知
        await self._notify_config_change(config, "DELETE")
        
        return True
    
    async def list_configs(
        self,
        db: AsyncSession,
        filter_params: ConfigFilter,
        page: int = 1,
        size: int = 20,
        user_id: Optional[uuid.UUID] = None
    ) -> Tuple[List[Config], int]:
        """
        获取配置列表
        """
        # 构建查询条件
        conditions = []
        
        if filter_params.key:
            conditions.append(Config.key.ilike(f"%{filter_params.key}%"))
        if filter_params.name:
            conditions.append(Config.name.ilike(f"%{filter_params.name}%"))
        if filter_params.type:
            conditions.append(Config.type == filter_params.type)
        if filter_params.scope:
            conditions.append(Config.scope == filter_params.scope)
        if filter_params.category:
            conditions.append(Config.category == filter_params.category)
        if filter_params.status:
            conditions.append(Config.status == filter_params.status)
        if filter_params.user_id:
            conditions.append(Config.user_id == filter_params.user_id)
        if filter_params.strategy_id:
            conditions.append(Config.strategy_id == filter_params.strategy_id)
        if filter_params.parent_id:
            conditions.append(Config.parent_id == filter_params.parent_id)
        if filter_params.template_id:
            conditions.append(Config.template_id == filter_params.template_id)
        if filter_params.is_encrypted is not None:
            conditions.append(Config.is_encrypted == filter_params.is_encrypted)
        if filter_params.is_readonly is not None:
            conditions.append(Config.is_readonly == filter_params.is_readonly)
        if filter_params.is_required is not None:
            conditions.append(Config.is_required == filter_params.is_required)
        if filter_params.created_after:
            conditions.append(Config.created_at >= filter_params.created_after)
        if filter_params.created_before:
            conditions.append(Config.created_at <= filter_params.created_before)
        if filter_params.updated_after:
            conditions.append(Config.updated_at >= filter_params.updated_after)
        if filter_params.updated_before:
            conditions.append(Config.updated_at <= filter_params.updated_before)
        
        # 搜索关键词
        if filter_params.search:
            search_conditions = [
                Config.key.ilike(f"%{filter_params.search}%"),
                Config.name.ilike(f"%{filter_params.search}%"),
                Config.description.ilike(f"%{filter_params.search}%")
            ]
            conditions.append(or_(*search_conditions))
        
        # 权限过滤
        if user_id:
            permission_conditions = [
                Config.scope == ConfigScope.GLOBAL,
                Config.user_id == user_id
            ]
            conditions.append(or_(*permission_conditions))
        
        # 查询总数
        count_stmt = select(func.count(Config.id)).where(and_(*conditions))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # 查询数据
        offset = (page - 1) * size
        stmt = (
            select(Config)
            .where(and_(*conditions))
            .order_by(Config.updated_at.desc())
            .offset(offset)
            .limit(size)
        )
        
        result = await db.execute(stmt)
        configs = result.scalars().all()
        
        # 解密敏感配置
        for config in configs:
            if config.is_encrypted:
                config.value = await self._decrypt_config_value(config.value)
        
        return list(configs), total
    
    async def validate_config_value(
        self,
        value: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> ConfigValidationResponse:
        """
        验证配置值
        """
        errors = []
        warnings = []
        
        try:
            # JSON Schema验证
            if schema:
                import jsonschema
                try:
                    jsonschema.validate(value, schema)
                except jsonschema.ValidationError as e:
                    errors.append(f"Schema验证失败: {e.message}")
            
            # 自定义验证规则
            if validation_rules:
                for rule_name, rule_config in validation_rules.items():
                    try:
                        await self._apply_validation_rule(value, rule_name, rule_config)
                    except Exception as e:
                        errors.append(f"验证规则 '{rule_name}' 失败: {str(e)}")
            
            # 基础验证
            if not isinstance(value, dict):
                errors.append("配置值必须是字典类型")
            
            if not value:
                warnings.append("配置值为空")
            
        except Exception as e:
            errors.append(f"验证过程出错: {str(e)}")
        
        return ConfigValidationResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def get_config_versions(
        self,
        db: AsyncSession,
        config_id: uuid.UUID,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[ConfigVersion], int]:
        """
        获取配置版本历史
        """
        # 查询总数
        count_stmt = select(func.count(ConfigVersion.id)).where(
            ConfigVersion.config_id == config_id
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # 查询数据
        offset = (page - 1) * size
        stmt = (
            select(ConfigVersion)
            .where(ConfigVersion.config_id == config_id)
            .order_by(ConfigVersion.version.desc())
            .offset(offset)
            .limit(size)
        )
        
        result = await db.execute(stmt)
        versions = result.scalars().all()
        
        return list(versions), total
    
    async def rollback_config(
        self,
        db: AsyncSession,
        config_id: uuid.UUID,
        target_version: int,
        user_id: Optional[uuid.UUID] = None
    ) -> Config:
        """
        回滚配置到指定版本
        """
        # 获取配置
        config = await self.get_config_by_id(db, config_id, user_id)
        if not config:
            raise ConfigNotFoundError(f"配置 {config_id} 不存在")
        
        # 检查权限
        if not await self._check_config_permission(config, user_id, "UPDATE"):
            raise ConfigPermissionError("无权限回滚此配置")
        
        # 获取目标版本
        stmt = select(ConfigVersion).where(
            and_(
                ConfigVersion.config_id == config_id,
                ConfigVersion.version == target_version
            )
        )
        result = await db.execute(stmt)
        target_version_obj = result.scalar_one_or_none()
        
        if not target_version_obj:
            raise ConfigVersionError(f"版本 {target_version} 不存在")
        
        # 保存当前值
        old_value = config.value.copy()
        
        # 回滚配置
        config.value = target_version_obj.value
        config.version += 1
        config.updated_at = datetime.utcnow()
        config.updated_by = user_id
        
        await db.commit()
        await db.refresh(config)
        
        # 创建新版本记录
        await self._create_config_version(
            db, config.id, config.value, 
            f"回滚到版本 {target_version}", user_id
        )
        
        # 记录审计日志
        await self._create_audit_log(
            db, config.id, "ROLLBACK", old_value, config.value, user_id
        )
        
        # 更新缓存
        await self._update_config_cache(config)
        
        # 发送配置变更通知
        await self._notify_config_change(config, "ROLLBACK")
        
        return config
    
    async def batch_operation(
        self,
        db: AsyncSession,
        operation: ConfigBatchOperation,
        user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        批量操作配置
        """
        results = {
            "success_count": 0,
            "failed_count": 0,
            "details": []
        }
        
        for config_id in operation.config_ids:
            try:
                if operation.operation == "delete":
                    await self.delete_config(db, config_id, user_id)
                elif operation.operation == "activate":
                    await self.update_config(
                        db, config_id, 
                        ConfigUpdate(status=ConfigStatus.ACTIVE),
                        user_id
                    )
                elif operation.operation == "deactivate":
                    await self.update_config(
                        db, config_id,
                        ConfigUpdate(status=ConfigStatus.INACTIVE),
                        user_id
                    )
                elif operation.operation == "update" and operation.data:
                    await self.update_config(
                        db, config_id,
                        ConfigUpdate(**operation.data),
                        user_id
                    )
                
                results["success_count"] += 1
                results["details"].append({
                    "config_id": str(config_id),
                    "status": "success"
                })
                
            except Exception as e:
                results["failed_count"] += 1
                results["details"].append({
                    "config_id": str(config_id),
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    async def get_statistics(self, db: AsyncSession) -> ConfigStatistics:
        """
        获取配置统计信息
        """
        # 总配置数
        total_stmt = select(func.count(Config.id))
        total_result = await db.execute(total_stmt)
        total_configs = total_result.scalar()
        
        # 按状态统计
        status_stmt = (
            select(Config.status, func.count(Config.id))
            .group_by(Config.status)
        )
        status_result = await db.execute(status_stmt)
        by_status = {status.value: count for status, count in status_result.fetchall()}
        
        # 按类型统计
        type_stmt = (
            select(Config.type, func.count(Config.id))
            .group_by(Config.type)
        )
        type_result = await db.execute(type_stmt)
        by_type = {type_.value: count for type_, count in type_result.fetchall()}
        
        # 按作用域统计
        scope_stmt = (
            select(Config.scope, func.count(Config.id))
            .group_by(Config.scope)
        )
        scope_result = await db.execute(scope_stmt)
        by_scope = {scope.value: count for scope, count in scope_result.fetchall()}
        
        # 过期配置数
        expired_stmt = select(func.count(Config.id)).where(
            and_(
                Config.expires_at.isnot(None),
                Config.expires_at < datetime.utcnow()
            )
        )
        expired_result = await db.execute(expired_stmt)
        expired_configs = expired_result.scalar()
        
        # 最近变更数（24小时内）
        recent_stmt = select(func.count(Config.id)).where(
            Config.updated_at >= datetime.utcnow() - timedelta(hours=24)
        )
        recent_result = await db.execute(recent_stmt)
        recent_changes = recent_result.scalar()
        
        return ConfigStatistics(
            total_configs=total_configs,
            active_configs=by_status.get(ConfigStatus.ACTIVE.value, 0),
            inactive_configs=by_status.get(ConfigStatus.INACTIVE.value, 0),
            expired_configs=expired_configs,
            by_type=by_type,
            by_scope=by_scope,
            by_status=by_status,
            recent_changes=recent_changes
        )
    
    # 私有方法
    async def _create_config_version(
        self,
        db: AsyncSession,
        config_id: uuid.UUID,
        value: Dict[str, Any],
        change_summary: str,
        user_id: Optional[uuid.UUID] = None
    ) -> ConfigVersion:
        """
        创建配置版本记录
        """
        # 获取当前最大版本号
        stmt = select(func.max(ConfigVersion.version)).where(
            ConfigVersion.config_id == config_id
        )
        result = await db.execute(stmt)
        max_version = result.scalar() or 0
        
        version = ConfigVersion(
            config_id=config_id,
            version=max_version + 1,
            value=value,
            change_summary=change_summary,
            created_by=user_id
        )
        
        db.add(version)
        await db.commit()
        
        # 清理旧版本（保留最近N个版本）
        await self._cleanup_old_versions(db, config_id)
        
        return version
    
    async def _create_audit_log(
        self,
        db: AsyncSession,
        config_id: uuid.UUID,
        action: str,
        old_value: Optional[Dict[str, Any]],
        new_value: Optional[Dict[str, Any]],
        user_id: Optional[uuid.UUID] = None
    ) -> ConfigAuditLog:
        """
        创建审计日志
        """
        audit_log = ConfigAuditLog(
            config_id=config_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            user_id=user_id
        )
        
        db.add(audit_log)
        await db.commit()
        
        return audit_log
    
    async def _update_config_cache(self, config: Config) -> None:
        """
        更新配置缓存
        """
        try:
            # 主键缓存
            await self.cache.set_config(
                str(config.id),
                json.dumps(config.dict()),
                ttl=self.settings.CONFIG_CACHE_TTL
            )
            
            # 键缓存
            cache_key = f"config:key:{config.key}:{config.scope.value}"
            if config.user_id:
                cache_key += f":user:{config.user_id}"
            if config.strategy_id:
                cache_key += f":strategy:{config.strategy_id}"
            
            await self.cache.set_config(
                cache_key,
                json.dumps(config.dict()),
                ttl=self.settings.CONFIG_CACHE_TTL
            )
            
        except Exception as e:
            # 缓存失败不影响主流程
            print(f"更新配置缓存失败: {e}")
    
    async def _clear_config_cache(self, config: Config) -> None:
        """
        清除配置缓存
        """
        try:
            # 清除主键缓存
            await self.cache.delete_config(str(config.id))
            
            # 清除键缓存
            cache_key = f"config:key:{config.key}:{config.scope.value}"
            if config.user_id:
                cache_key += f":user:{config.user_id}"
            if config.strategy_id:
                cache_key += f":strategy:{config.strategy_id}"
            
            await self.cache.delete_config(cache_key)
            
        except Exception as e:
            print(f"清除配置缓存失败: {e}")
    
    async def _check_config_permission(
        self,
        config: Config,
        user_id: Optional[uuid.UUID],
        action: str
    ) -> bool:
        """
        检查配置权限
        """
        # 全局配置所有人可读
        if config.scope == ConfigScope.GLOBAL and action == "READ":
            return True
        
        # 用户配置只有所有者可访问
        if config.scope == ConfigScope.USER:
            return config.user_id == user_id
        
        # 策略配置需要检查策略权限（这里简化处理）
        if config.scope == ConfigScope.STRATEGY:
            return config.user_id == user_id
        
        return True
    
    async def _encrypt_config_value(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        加密配置值
        """
        # 这里应该实现真正的加密逻辑
        # 为了演示，这里只是简单标记
        return {"encrypted": True, "data": value}
    
    async def _decrypt_config_value(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        解密配置值
        """
        # 这里应该实现真正的解密逻辑
        # 为了演示，这里只是简单提取
        if isinstance(value, dict) and value.get("encrypted"):
            return value.get("data", {})
        return value
    
    def _merge_template_values(
        self,
        template: Dict[str, Any],
        user_value: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        合并模板值和用户值
        """
        result = template.copy()
        result.update(user_value)
        return result
    
    async def _apply_validation_rule(
        self,
        value: Dict[str, Any],
        rule_name: str,
        rule_config: Dict[str, Any]
    ) -> None:
        """
        应用验证规则
        """
        # 这里可以实现各种自定义验证规则
        if rule_name == "required_fields":
            required_fields = rule_config.get("fields", [])
            for field in required_fields:
                if field not in value:
                    raise ValueError(f"必需字段 '{field}' 缺失")
        
        elif rule_name == "value_range":
            field = rule_config.get("field")
            min_val = rule_config.get("min")
            max_val = rule_config.get("max")
            
            if field in value:
                val = value[field]
                if min_val is not None and val < min_val:
                    raise ValueError(f"字段 '{field}' 值 {val} 小于最小值 {min_val}")
                if max_val is not None and val > max_val:
                    raise ValueError(f"字段 '{field}' 值 {val} 大于最大值 {max_val}")
    
    async def _cleanup_old_versions(
        self,
        db: AsyncSession,
        config_id: uuid.UUID
    ) -> None:
        """
        清理旧版本
        """
        # 保留最近的版本数量
        keep_versions = self.settings.CONFIG_VERSION_KEEP_COUNT
        
        # 获取需要删除的版本
        stmt = (
            select(ConfigVersion.id)
            .where(ConfigVersion.config_id == config_id)
            .order_by(ConfigVersion.version.desc())
            .offset(keep_versions)
        )
        
        result = await db.execute(stmt)
        old_version_ids = [row[0] for row in result.fetchall()]
        
        if old_version_ids:
            delete_stmt = delete(ConfigVersion).where(
                ConfigVersion.id.in_(old_version_ids)
            )
            await db.execute(delete_stmt)
            await db.commit()
    
    async def _notify_config_change(
        self,
        config: Config,
        action: str
    ) -> None:
        """
        发送配置变更通知
        """
        # 这里可以实现配置变更通知逻辑
        # 比如发送到消息队列、WebSocket等
        pass
    
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