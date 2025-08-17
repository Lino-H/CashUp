#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 健康检查服务

系统健康状态监控和检查的业务逻辑
"""

import asyncio
import logging
import json
import aiohttp
import psutil
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from app.core.database import get_db
from app.core.cache import CacheManager
from app.core.exceptions import HealthCheckError, ServiceUnavailableError
from app.models.health import HealthCheck, ServiceStatus, HealthCheckResult
from app.schemas.health import HealthStatusEnum, ServiceTypeEnum, CheckTypeEnum
from app.schemas.health import (
    HealthCheckCreate, HealthCheckUpdate, ServiceStatusCreate, ServiceStatusUpdate,
    HealthCheckExecuteRequest, HealthCheckBatchExecuteRequest
)

logger = logging.getLogger(__name__)


class HealthService:
    """健康检查服务类"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.check_tasks = {}
        self.service_registry = {}
        
    async def create_health_check(self, db: Session, check_data: HealthCheckCreate) -> HealthCheck:
        """创建健康检查配置"""
        try:
            # 检查名称是否已存在
            existing = db.query(HealthCheck).filter(HealthCheck.name == check_data.name).first()
            if existing:
                raise ValueError(f"Health check '{check_data.name}' already exists")
            
            # 创建健康检查配置
            health_check = HealthCheck(
                name=check_data.name,
                description=check_data.description,
                service_name=check_data.service_name,
                service_type=check_data.service_type,
                check_type=check_data.check_type,
                endpoint=check_data.endpoint,
                method=check_data.method,
                headers=check_data.headers or {},
                body=check_data.body,
                expected_status=check_data.expected_status,
                expected_response=check_data.expected_response,
                timeout=check_data.timeout,
                interval=check_data.interval,
                retries=check_data.retries,
                retry_interval=check_data.retry_interval,
                enabled=check_data.enabled,
                tags=check_data.tags or [],
                metadata=check_data.metadata or {}
            )
            
            db.add(health_check)
            db.commit()
            db.refresh(health_check)
            
            # 如果启用，立即执行一次检查
            if health_check.enabled:
                await self._execute_health_check(db, health_check)
            
            # 清除相关缓存
            await self.cache.clear_pattern("health:*")
            
            logger.info(f"Created health check: {health_check.name} (ID: {health_check.id})")
            return health_check
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create health check: {e}")
            raise HealthCheckError(f"Failed to create health check: {e}")
    
    async def get_health_check(self, db: Session, check_id: int) -> Optional[HealthCheck]:
        """获取健康检查配置详情"""
        cache_key = f"health:check:{check_id}"
        
        # 尝试从缓存获取
        cached_check = await self.cache.get(cache_key)
        if cached_check:
            return cached_check
        
        # 从数据库获取
        health_check = db.query(HealthCheck).filter(HealthCheck.id == check_id).first()
        
        if health_check:
            # 缓存结果
            await self.cache.set(cache_key, health_check, ttl=300)
        
        return health_check
    
    async def get_health_checks(self, db: Session, 
                               service_name: Optional[str] = None,
                               service_type: Optional[ServiceTypeEnum] = None,
                               check_type: Optional[CheckTypeEnum] = None,
                               enabled: Optional[bool] = None,
                               limit: int = 100,
                               offset: int = 0) -> Tuple[List[HealthCheck], int]:
        """获取健康检查配置列表"""
        try:
            # 构建查询
            query = db.query(HealthCheck)
            
            # 应用过滤条件
            if service_name:
                query = query.filter(HealthCheck.service_name.ilike(f"%{service_name}%"))
            
            if service_type:
                query = query.filter(HealthCheck.service_type == service_type)
            
            if check_type:
                query = query.filter(HealthCheck.check_type == check_type)
            
            if enabled is not None:
                query = query.filter(HealthCheck.enabled == enabled)
            
            # 获取总数
            total = query.count()
            
            # 应用排序和分页
            checks = query.order_by(desc(HealthCheck.created_at)).offset(offset).limit(limit).all()
            
            return checks, total
            
        except Exception as e:
            logger.error(f"Failed to get health checks: {e}")
            raise HealthCheckError(f"Failed to get health checks: {e}")
    
    async def update_health_check(self, db: Session, check_id: int, check_data: HealthCheckUpdate) -> Optional[HealthCheck]:
        """更新健康检查配置"""
        try:
            health_check = db.query(HealthCheck).filter(HealthCheck.id == check_id).first()
            if not health_check:
                return None
            
            # 更新字段
            update_data = check_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(health_check, field, value)
            
            health_check.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(health_check)
            
            # 清除相关缓存
            await self.cache.delete(f"health:check:{check_id}")
            await self.cache.clear_pattern("health:*")
            
            logger.info(f"Updated health check: {health_check.name} (ID: {health_check.id})")
            return health_check
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update health check: {e}")
            raise HealthCheckError(f"Failed to update health check: {e}")
    
    async def delete_health_check(self, db: Session, check_id: int) -> bool:
        """删除健康检查配置"""
        try:
            health_check = db.query(HealthCheck).filter(HealthCheck.id == check_id).first()
            if not health_check:
                return False
            
            # 停止相关的检查任务
            if check_id in self.check_tasks:
                self.check_tasks[check_id].cancel()
                del self.check_tasks[check_id]
            
            # 删除相关的检查结果
            db.query(HealthCheckResult).filter(HealthCheckResult.health_check_id == check_id).delete()
            
            # 删除健康检查配置
            db.delete(health_check)
            db.commit()
            
            # 清除相关缓存
            await self.cache.delete(f"health:check:{check_id}")
            await self.cache.clear_pattern("health:*")
            
            logger.info(f"Deleted health check: {health_check.name} (ID: {check_id})")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete health check: {e}")
            raise HealthCheckError(f"Failed to delete health check: {e}")
    
    async def execute_health_check(self, db: Session, check_id: int, request: HealthCheckExecuteRequest) -> HealthCheckResult:
        """手动执行健康检查"""
        try:
            health_check = db.query(HealthCheck).filter(HealthCheck.id == check_id).first()
            if not health_check:
                raise ValueError(f"Health check with ID {check_id} not found")
            
            # 执行检查
            result = await self._execute_health_check(db, health_check, request.timeout)
            
            logger.info(f"Manually executed health check: {health_check.name} (ID: {check_id})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute health check: {e}")
            raise HealthCheckError(f"Failed to execute health check: {e}")
    
    async def batch_execute_health_checks(self, db: Session, request: HealthCheckBatchExecuteRequest) -> Dict[str, Any]:
        """批量执行健康检查"""
        try:
            results = {"success": [], "failed": []}
            
            # 获取要执行的健康检查
            if request.check_ids:
                checks = db.query(HealthCheck).filter(HealthCheck.id.in_(request.check_ids)).all()
            elif request.service_names:
                checks = db.query(HealthCheck).filter(HealthCheck.service_name.in_(request.service_names)).all()
            elif request.tags:
                checks = db.query(HealthCheck).filter(
                    HealthCheck.tags.op('@>')([tag for tag in request.tags])
                ).all()
            else:
                checks = db.query(HealthCheck).filter(HealthCheck.enabled == True).all()
            
            # 并发执行检查
            tasks = []
            for check in checks:
                task = asyncio.create_task(self._execute_health_check(db, check, request.timeout))
                tasks.append((check.id, task))
            
            # 等待所有任务完成
            for check_id, task in tasks:
                try:
                    result = await task
                    results["success"].append({
                        "check_id": check_id,
                        "status": result.status.value,
                        "response_time": result.response_time
                    })
                except Exception as e:
                    results["failed"].append({
                        "check_id": check_id,
                        "error": str(e)
                    })
            
            logger.info(f"Batch executed {len(results['success'])} health checks")
            return results
            
        except Exception as e:
            logger.error(f"Failed to batch execute health checks: {e}")
            raise HealthCheckError(f"Failed to batch execute health checks: {e}")
    
    async def get_service_status(self, db: Session, service_name: str) -> Optional[ServiceStatus]:
        """获取服务状态"""
        cache_key = f"health:service:{service_name}"
        
        # 尝试从缓存获取
        cached_status = await self.cache.get(cache_key)
        if cached_status:
            return cached_status
        
        # 从数据库获取
        service_status = db.query(ServiceStatus).filter(ServiceStatus.service_name == service_name).first()
        
        if service_status:
            # 缓存结果
            await self.cache.set(cache_key, service_status, ttl=60)
        
        return service_status
    
    async def update_service_status(self, db: Session, service_name: str, status_data: ServiceStatusUpdate) -> ServiceStatus:
        """更新服务状态"""
        try:
            # 查找或创建服务状态
            service_status = db.query(ServiceStatus).filter(ServiceStatus.service_name == service_name).first()
            
            if not service_status:
                service_status = ServiceStatus(
                    service_name=service_name,
                    service_type=status_data.service_type,
                    status=status_data.status,
                    last_check_at=datetime.utcnow(),
                    metadata=status_data.metadata or {}
                )
                db.add(service_status)
            else:
                # 更新现有状态
                if status_data.service_type:
                    service_status.service_type = status_data.service_type
                if status_data.status:
                    service_status.status = status_data.status
                if status_data.metadata:
                    service_status.metadata = status_data.metadata
                
                service_status.last_check_at = datetime.utcnow()
                service_status.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(service_status)
            
            # 清除相关缓存
            await self.cache.delete(f"health:service:{service_name}")
            await self.cache.clear_pattern("health:*")
            
            logger.info(f"Updated service status: {service_name} -> {status_data.status}")
            return service_status
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update service status: {e}")
            raise HealthCheckError(f"Failed to update service status: {e}")
    
    async def refresh_service_status(self, db: Session, service_name: str) -> ServiceStatus:
        """刷新服务状态"""
        try:
            # 获取该服务的所有健康检查
            checks = db.query(HealthCheck).filter(
                and_(
                    HealthCheck.service_name == service_name,
                    HealthCheck.enabled == True
                )
            ).all()
            
            if not checks:
                raise ValueError(f"No enabled health checks found for service: {service_name}")
            
            # 执行所有检查
            results = []
            for check in checks:
                try:
                    result = await self._execute_health_check(db, check)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to execute health check {check.id}: {e}")
            
            # 计算整体状态
            if not results:
                overall_status = HealthStatusEnum.UNKNOWN
            elif all(r.status == HealthStatusEnum.HEALTHY for r in results):
                overall_status = HealthStatusEnum.HEALTHY
            elif any(r.status == HealthStatusEnum.UNHEALTHY for r in results):
                overall_status = HealthStatusEnum.UNHEALTHY
            else:
                overall_status = HealthStatusEnum.DEGRADED
            
            # 更新服务状态
            service_status = await self.update_service_status(
                db, service_name, 
                ServiceStatusUpdate(
                    status=overall_status,
                    metadata={
                        "last_refresh": datetime.utcnow().isoformat(),
                        "check_count": len(results),
                        "healthy_checks": sum(1 for r in results if r.status == HealthStatusEnum.HEALTHY)
                    }
                )
            )
            
            logger.info(f"Refreshed service status: {service_name} -> {overall_status}")
            return service_status
            
        except Exception as e:
            logger.error(f"Failed to refresh service status: {e}")
            raise HealthCheckError(f"Failed to refresh service status: {e}")
    
    async def get_system_health(self, db: Session) -> Dict[str, Any]:
        """获取系统整体健康状态"""
        try:
            cache_key = "health:system"
            
            # 尝试从缓存获取
            cached_health = await self.cache.get(cache_key)
            if cached_health:
                return cached_health
            
            # 获取所有服务状态
            services = db.query(ServiceStatus).all()
            
            # 获取最近的健康检查结果
            recent_results = db.query(HealthCheckResult).filter(
                HealthCheckResult.created_at >= datetime.utcnow() - timedelta(minutes=30)
            ).all()
            
            # 计算系统状态
            if not services:
                system_status = HealthStatusEnum.UNKNOWN
            elif all(s.status == HealthStatusEnum.HEALTHY for s in services):
                system_status = HealthStatusEnum.HEALTHY
            elif any(s.status == HealthStatusEnum.UNHEALTHY for s in services):
                system_status = HealthStatusEnum.UNHEALTHY
            else:
                system_status = HealthStatusEnum.DEGRADED
            
            # 统计信息
            total_services = len(services)
            healthy_services = sum(1 for s in services if s.status == HealthStatusEnum.HEALTHY)
            unhealthy_services = sum(1 for s in services if s.status == HealthStatusEnum.UNHEALTHY)
            degraded_services = sum(1 for s in services if s.status == HealthStatusEnum.DEGRADED)
            
            # 检查统计
            total_checks = len(recent_results)
            successful_checks = sum(1 for r in recent_results if r.status == HealthStatusEnum.HEALTHY)
            failed_checks = sum(1 for r in recent_results if r.status == HealthStatusEnum.UNHEALTHY)
            
            # 平均响应时间
            avg_response_time = 0
            if recent_results:
                avg_response_time = sum(r.response_time for r in recent_results) / len(recent_results)
            
            # 系统资源信息
            system_resources = await self._get_system_resources()
            
            health_data = {
                "status": system_status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "total": total_services,
                    "healthy": healthy_services,
                    "unhealthy": unhealthy_services,
                    "degraded": degraded_services
                },
                "checks": {
                    "total": total_checks,
                    "successful": successful_checks,
                    "failed": failed_checks,
                    "success_rate": (successful_checks / total_checks * 100) if total_checks > 0 else 0,
                    "avg_response_time": avg_response_time
                },
                "system_resources": system_resources,
                "service_details": [
                    {
                        "name": s.service_name,
                        "type": s.service_type.value if s.service_type else "unknown",
                        "status": s.status.value,
                        "last_check": s.last_check_at.isoformat() if s.last_check_at else None
                    }
                    for s in services
                ]
            }
            
            # 缓存结果
            await self.cache.set(cache_key, health_data, ttl=60)
            
            return health_data
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            raise HealthCheckError(f"Failed to get system health: {e}")
    
    async def get_health_check_history(self, db: Session, 
                                      check_id: Optional[int] = None,
                                      service_name: Optional[str] = None,
                                      status: Optional[HealthStatusEnum] = None,
                                      start_time: Optional[datetime] = None,
                                      end_time: Optional[datetime] = None,
                                      limit: int = 100,
                                      offset: int = 0) -> Tuple[List[HealthCheckResult], int]:
        """获取健康检查历史记录"""
        try:
            # 构建查询
            query = db.query(HealthCheckResult)
            
            # 应用过滤条件
            if check_id:
                query = query.filter(HealthCheckResult.health_check_id == check_id)
            
            if service_name:
                query = query.join(HealthCheck).filter(HealthCheck.service_name == service_name)
            
            if status:
                query = query.filter(HealthCheckResult.status == status)
            
            if start_time:
                query = query.filter(HealthCheckResult.created_at >= start_time)
            
            if end_time:
                query = query.filter(HealthCheckResult.created_at <= end_time)
            
            # 获取总数
            total = query.count()
            
            # 应用排序和分页
            results = query.order_by(desc(HealthCheckResult.created_at)).offset(offset).limit(limit).all()
            
            return results, total
            
        except Exception as e:
            logger.error(f"Failed to get health check history: {e}")
            raise HealthCheckError(f"Failed to get health check history: {e}")
    
    async def get_health_statistics(self, db: Session) -> Dict[str, Any]:
        """获取健康检查统计信息"""
        try:
            cache_key = "health:statistics"
            
            # 尝试从缓存获取
            cached_stats = await self.cache.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # 基础统计
            total_checks = db.query(HealthCheck).count()
            enabled_checks = db.query(HealthCheck).filter(HealthCheck.enabled == True).count()
            total_services = db.query(ServiceStatus).count()
            
            # 最近24小时的检查结果
            recent_time = datetime.utcnow() - timedelta(hours=24)
            recent_results = db.query(HealthCheckResult).filter(
                HealthCheckResult.created_at >= recent_time
            ).all()
            
            # 成功率统计
            total_recent = len(recent_results)
            successful_recent = sum(1 for r in recent_results if r.status == HealthStatusEnum.HEALTHY)
            success_rate = (successful_recent / total_recent * 100) if total_recent > 0 else 0
            
            # 平均响应时间
            avg_response_time = 0
            if recent_results:
                avg_response_time = sum(r.response_time for r in recent_results) / len(recent_results)
            
            # 按服务类型统计
            service_type_stats = db.query(
                ServiceStatus.service_type,
                func.count(ServiceStatus.id)
            ).group_by(ServiceStatus.service_type).all()
            
            # 按状态统计
            status_stats = db.query(
                ServiceStatus.status,
                func.count(ServiceStatus.id)
            ).group_by(ServiceStatus.status).all()
            
            # 按检查类型统计
            check_type_stats = db.query(
                HealthCheck.check_type,
                func.count(HealthCheck.id)
            ).group_by(HealthCheck.check_type).all()
            
            stats = {
                "total_health_checks": total_checks,
                "enabled_health_checks": enabled_checks,
                "total_services": total_services,
                "success_rate_24h": success_rate,
                "avg_response_time_24h": avg_response_time,
                "total_checks_24h": total_recent,
                "successful_checks_24h": successful_recent,
                "failed_checks_24h": total_recent - successful_recent,
                "service_type_distribution": dict(service_type_stats),
                "status_distribution": dict(status_stats),
                "check_type_distribution": dict(check_type_stats)
            }
            
            # 缓存结果
            await self.cache.set(cache_key, stats, ttl=300)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get health statistics: {e}")
            raise HealthCheckError(f"Failed to get health statistics: {e}")
    
    async def _execute_health_check(self, db: Session, health_check: HealthCheck, timeout: Optional[int] = None) -> HealthCheckResult:
        """执行单个健康检查"""
        start_time = datetime.utcnow()
        check_timeout = timeout or health_check.timeout
        
        try:
            # 根据检查类型执行不同的检查逻辑
            if health_check.check_type == CheckTypeEnum.HTTP:
                result = await self._execute_http_check(health_check, check_timeout)
            elif health_check.check_type == CheckTypeEnum.TCP:
                result = await self._execute_tcp_check(health_check, check_timeout)
            elif health_check.check_type == CheckTypeEnum.DATABASE:
                result = await self._execute_database_check(health_check, check_timeout)
            elif health_check.check_type == CheckTypeEnum.CUSTOM:
                result = await self._execute_custom_check(health_check, check_timeout)
            else:
                raise ValueError(f"Unsupported check type: {health_check.check_type}")
            
            # 计算响应时间
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # 创建检查结果
            check_result = HealthCheckResult(
                health_check_id=health_check.id,
                status=result["status"],
                response_time=response_time,
                response_data=result.get("response_data"),
                error_message=result.get("error_message"),
                metadata=result.get("metadata", {})
            )
            
            db.add(check_result)
            
            # 更新健康检查的最后执行时间
            health_check.last_check_at = datetime.utcnow()
            health_check.last_status = result["status"]
            
            db.commit()
            db.refresh(check_result)
            
            return check_result
            
        except Exception as e:
            # 记录失败结果
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            check_result = HealthCheckResult(
                health_check_id=health_check.id,
                status=HealthStatusEnum.UNHEALTHY,
                response_time=response_time,
                error_message=str(e),
                metadata={"exception_type": type(e).__name__}
            )
            
            db.add(check_result)
            
            health_check.last_check_at = datetime.utcnow()
            health_check.last_status = HealthStatusEnum.UNHEALTHY
            
            db.commit()
            db.refresh(check_result)
            
            logger.error(f"Health check failed for {health_check.name}: {e}")
            return check_result
    
    async def _execute_http_check(self, health_check: HealthCheck, timeout: int) -> Dict[str, Any]:
        """执行HTTP健康检查"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.request(
                    method=health_check.method or "GET",
                    url=health_check.endpoint,
                    headers=health_check.headers,
                    data=health_check.body
                ) as response:
                    response_text = await response.text()
                    
                    # 检查状态码
                    expected_status = health_check.expected_status or 200
                    if response.status != expected_status:
                        return {
                            "status": HealthStatusEnum.UNHEALTHY,
                            "error_message": f"Expected status {expected_status}, got {response.status}",
                            "response_data": response_text[:1000]  # 限制响应数据长度
                        }
                    
                    # 检查响应内容
                    if health_check.expected_response:
                        if health_check.expected_response not in response_text:
                            return {
                                "status": HealthStatusEnum.UNHEALTHY,
                                "error_message": f"Expected response content not found",
                                "response_data": response_text[:1000]
                            }
                    
                    return {
                        "status": HealthStatusEnum.HEALTHY,
                        "response_data": response_text[:1000],
                        "metadata": {
                            "status_code": response.status,
                            "content_length": len(response_text)
                        }
                    }
                    
        except asyncio.TimeoutError:
            return {
                "status": HealthStatusEnum.UNHEALTHY,
                "error_message": f"Request timeout after {timeout}s"
            }
        except Exception as e:
            return {
                "status": HealthStatusEnum.UNHEALTHY,
                "error_message": str(e)
            }
    
    async def _execute_tcp_check(self, health_check: HealthCheck, timeout: int) -> Dict[str, Any]:
        """执行TCP健康检查"""
        try:
            # 解析主机和端口
            if "://" in health_check.endpoint:
                # 如果是URL格式，提取主机和端口
                from urllib.parse import urlparse
                parsed = urlparse(health_check.endpoint)
                host = parsed.hostname
                port = parsed.port
            else:
                # 如果是host:port格式
                parts = health_check.endpoint.split(":")
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else 80
            
            # 尝试连接
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            
            # 关闭连接
            writer.close()
            await writer.wait_closed()
            
            return {
                "status": HealthStatusEnum.HEALTHY,
                "metadata": {
                    "host": host,
                    "port": port
                }
            }
            
        except asyncio.TimeoutError:
            return {
                "status": HealthStatusEnum.UNHEALTHY,
                "error_message": f"Connection timeout after {timeout}s"
            }
        except Exception as e:
            return {
                "status": HealthStatusEnum.UNHEALTHY,
                "error_message": str(e)
            }
    
    async def _execute_database_check(self, health_check: HealthCheck, timeout: int) -> Dict[str, Any]:
        """执行数据库健康检查"""
        try:
            # 这里应该根据数据库类型实现具体的检查逻辑
            # 示例实现
            return {
                "status": HealthStatusEnum.HEALTHY,
                "metadata": {
                    "check_type": "database",
                    "endpoint": health_check.endpoint
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatusEnum.UNHEALTHY,
                "error_message": str(e)
            }
    
    async def _execute_custom_check(self, health_check: HealthCheck, timeout: int) -> Dict[str, Any]:
        """执行自定义健康检查"""
        try:
            # 这里应该实现自定义检查逻辑
            # 可以执行脚本、调用API等
            return {
                "status": HealthStatusEnum.HEALTHY,
                "metadata": {
                    "check_type": "custom",
                    "endpoint": health_check.endpoint
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatusEnum.UNHEALTHY,
                "error_message": str(e)
            }
    
    async def _get_system_resources(self) -> Dict[str, Any]:
        """获取系统资源信息"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络统计
            network = psutil.net_io_counters()
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage_percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system resources: {e}")
            return {}
    
    async def start_periodic_checks(self, db: Session):
        """启动定期健康检查"""
        try:
            # 获取所有启用的健康检查
            enabled_checks = db.query(HealthCheck).filter(HealthCheck.enabled == True).all()
            
            for check in enabled_checks:
                if check.id not in self.check_tasks:
                    # 创建定期检查任务
                    task = asyncio.create_task(self._periodic_check_task(db, check))
                    self.check_tasks[check.id] = task
            
            logger.info(f"Started {len(enabled_checks)} periodic health check tasks")
            
        except Exception as e:
            logger.error(f"Failed to start periodic checks: {e}")
    
    async def _periodic_check_task(self, db: Session, health_check: HealthCheck):
        """定期检查任务"""
        while True:
            try:
                await self._execute_health_check(db, health_check)
                await asyncio.sleep(health_check.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic check task for {health_check.name}: {e}")
                await asyncio.sleep(health_check.interval)
    
    async def stop_periodic_checks(self):
        """停止所有定期健康检查"""
        for task in self.check_tasks.values():
            task.cancel()
        
        # 等待所有任务完成
        if self.check_tasks:
            await asyncio.gather(*self.check_tasks.values(), return_exceptions=True)
        
        self.check_tasks.clear()
        logger.info("Stopped all periodic health check tasks")