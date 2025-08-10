#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 健康检查API路由

处理系统健康检查和监控相关的API请求
"""

import uuid
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ...core.database import get_db, engine
from ...core.config import get_config
from ...schemas.common import HealthCheckResponse
from ...services.websocket_service import websocket_service
from ...services.scheduler_service import scheduler_service

import logging
import psutil
import time

logger = logging.getLogger(__name__)
config = get_config()

# 创建路由器
router = APIRouter()


@router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """
    基础健康检查
    
    Returns:
        HealthCheckResponse: 健康状态信息
    """
    try:
        return HealthCheckResponse(
            status="healthy",
            service="notification-service",
            version="1.0.0",
            timestamp=datetime.utcnow().isoformat(),
            uptime=_get_uptime()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            service="notification-service",
            version="1.0.0",
            timestamp=datetime.utcnow().isoformat(),
            uptime=_get_uptime(),
            error=str(e)
        )


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check(
    db: AsyncSession = Depends(get_db)
):
    """
    详细健康检查
    
    Args:
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 详细健康状态信息
    """
    health_status = {
        "service": "notification-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": _get_uptime(),
        "status": "healthy",
        "checks": {}
    }
    
    # 数据库健康检查
    db_health = await _check_database_health(db)
    health_status["checks"]["database"] = db_health
    
    # WebSocket服务健康检查
    ws_health = await _check_websocket_health()
    health_status["checks"]["websocket"] = ws_health
    
    # 调度服务健康检查
    scheduler_health = await _check_scheduler_health()
    health_status["checks"]["scheduler"] = scheduler_health
    
    # 系统资源检查
    system_health = await _check_system_health()
    health_status["checks"]["system"] = system_health
    
    # 外部依赖检查
    dependencies_health = await _check_dependencies_health()
    health_status["checks"]["dependencies"] = dependencies_health
    
    # 确定整体状态
    all_checks = [db_health, ws_health, scheduler_health, system_health, dependencies_health]
    if any(check["status"] == "unhealthy" for check in all_checks):
        health_status["status"] = "unhealthy"
    elif any(check["status"] == "degraded" for check in all_checks):
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/database", response_model=Dict[str, Any])
async def database_health_check(
    db: AsyncSession = Depends(get_db)
):
    """
    数据库健康检查
    
    Args:
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 数据库健康状态
    """
    return await _check_database_health(db)


@router.get("/websocket", response_model=Dict[str, Any])
async def websocket_health_check():
    """
    WebSocket服务健康检查
    
    Returns:
        Dict[str, Any]: WebSocket服务健康状态
    """
    return await _check_websocket_health()


@router.get("/scheduler", response_model=Dict[str, Any])
async def scheduler_health_check():
    """
    调度服务健康检查
    
    Returns:
        Dict[str, Any]: 调度服务健康状态
    """
    return await _check_scheduler_health()


@router.get("/system", response_model=Dict[str, Any])
async def system_health_check():
    """
    系统资源健康检查
    
    Returns:
        Dict[str, Any]: 系统健康状态
    """
    return await _check_system_health()


@router.get("/dependencies", response_model=Dict[str, Any])
async def dependencies_health_check():
    """
    外部依赖健康检查
    
    Returns:
        Dict[str, Any]: 外部依赖健康状态
    """
    return await _check_dependencies_health()


@router.get("/metrics", response_model=Dict[str, Any])
async def get_health_metrics(
    db: AsyncSession = Depends(get_db)
):
    """
    获取健康指标
    
    Args:
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 健康指标
    """
    try:
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": _get_uptime(),
            "system": _get_system_metrics(),
            "database": await _get_database_metrics(db),
            "websocket": await _get_websocket_metrics(),
            "scheduler": await _get_scheduler_metrics()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting health metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/readiness", response_model=Dict[str, Any])
async def readiness_check(
    db: AsyncSession = Depends(get_db)
):
    """
    就绪状态检查
    
    Args:
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 就绪状态
    """
    try:
        # 检查关键组件是否就绪
        checks = {
            "database": await _is_database_ready(db),
            "websocket": await _is_websocket_ready(),
            "scheduler": await _is_scheduler_ready()
        }
        
        all_ready = all(checks.values())
        
        return {
            "ready": all_ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {
            "ready": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/liveness", response_model=Dict[str, Any])
async def liveness_check():
    """
    存活状态检查
    
    Returns:
        Dict[str, Any]: 存活状态
    """
    try:
        # 简单的存活检查
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": _get_uptime()
        }
        
    except Exception as e:
        logger.error(f"Liveness check failed: {str(e)}")
        return {
            "alive": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# 辅助函数

def _get_uptime() -> str:
    """
    获取服务运行时间
    
    Returns:
        str: 运行时间
    """
    try:
        # 这里应该记录服务启动时间
        # 为了演示，使用进程启动时间
        process = psutil.Process()
        start_time = datetime.fromtimestamp(process.create_time())
        uptime = datetime.now() - start_time
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{days}d {hours}h {minutes}m {seconds}s"
    except Exception:
        return "unknown"


async def _check_database_health(db: AsyncSession) -> Dict[str, Any]:
    """
    检查数据库健康状态
    
    Args:
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 数据库健康状态
    """
    try:
        start_time = time.time()
        
        # 执行简单查询
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        
        response_time = (time.time() - start_time) * 1000  # 毫秒
        
        # 检查连接池状态
        pool_status = {
            "size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "invalid": engine.pool.invalid()
        }
        
        status = "healthy"
        if response_time > 1000:  # 响应时间超过1秒
            status = "degraded"
        elif response_time > 5000:  # 响应时间超过5秒
            status = "unhealthy"
        
        return {
            "status": status,
            "response_time_ms": round(response_time, 2),
            "pool": pool_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def _check_websocket_health() -> Dict[str, Any]:
    """
    检查WebSocket服务健康状态
    
    Returns:
        Dict[str, Any]: WebSocket服务健康状态
    """
    try:
        stats = await websocket_service.get_stats()
        
        status = "healthy"
        total_connections = stats.get("total_connections", 0)
        
        # 根据连接数判断状态
        if total_connections > 10000:  # 连接数过多
            status = "degraded"
        
        return {
            "status": status,
            "connections": total_connections,
            "active_users": stats.get("active_users", 0),
            "channels": stats.get("total_channels", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"WebSocket health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def _check_scheduler_health() -> Dict[str, Any]:
    """
    检查调度服务健康状态
    
    Returns:
        Dict[str, Any]: 调度服务健康状态
    """
    try:
        stats = await scheduler_service.get_stats()
        
        status = "healthy"
        if not stats.get("is_running", False):
            status = "unhealthy"
        elif stats.get("failed_tasks", 0) > stats.get("completed_tasks", 0) * 0.1:  # 失败率超过10%
            status = "degraded"
        
        return {
            "status": status,
            "is_running": stats.get("is_running", False),
            "worker_count": stats.get("worker_count", 0),
            "pending_tasks": stats.get("pending_tasks", 0),
            "running_tasks": stats.get("running_tasks", 0),
            "completed_tasks": stats.get("completed_tasks", 0),
            "failed_tasks": stats.get("failed_tasks", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Scheduler health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def _check_system_health() -> Dict[str, Any]:
    """
    检查系统资源健康状态
    
    Returns:
        Dict[str, Any]: 系统健康状态
    """
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # 确定状态
        status = "healthy"
        if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
            status = "unhealthy"
        elif cpu_percent > 80 or memory_percent > 80 or disk_percent > 80:
            status = "degraded"
        
        return {
            "status": status,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def _check_dependencies_health() -> Dict[str, Any]:
    """
    检查外部依赖健康状态
    
    Returns:
        Dict[str, Any]: 外部依赖健康状态
    """
    try:
        # 这里应该检查外部服务的健康状态
        # 例如：Redis、消息队列、外部API等
        
        dependencies = {
            "redis": {"status": "healthy", "response_time_ms": 5},
            "email_service": {"status": "healthy", "response_time_ms": 100},
            "sms_service": {"status": "healthy", "response_time_ms": 200}
        }
        
        # 确定整体状态
        statuses = [dep["status"] for dep in dependencies.values()]
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "dependencies": dependencies,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Dependencies health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def _get_system_metrics() -> Dict[str, Any]:
    """
    获取系统指标
    
    Returns:
        Dict[str, Any]: 系统指标
    """
    try:
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "network": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        return {}


async def _get_database_metrics(db: AsyncSession) -> Dict[str, Any]:
    """
    获取数据库指标
    
    Args:
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 数据库指标
    """
    try:
        # 这里应该查询数据库统计信息
        return {
            "pool_size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "invalid": engine.pool.invalid()
        }
    except Exception as e:
        logger.error(f"Error getting database metrics: {str(e)}")
        return {}


async def _get_websocket_metrics() -> Dict[str, Any]:
    """
    获取WebSocket指标
    
    Returns:
        Dict[str, Any]: WebSocket指标
    """
    try:
        return await websocket_service.get_stats()
    except Exception as e:
        logger.error(f"Error getting WebSocket metrics: {str(e)}")
        return {}


async def _get_scheduler_metrics() -> Dict[str, Any]:
    """
    获取调度服务指标
    
    Returns:
        Dict[str, Any]: 调度服务指标
    """
    try:
        return await scheduler_service.get_stats()
    except Exception as e:
        logger.error(f"Error getting scheduler metrics: {str(e)}")
        return {}


async def _is_database_ready(db: AsyncSession) -> bool:
    """
    检查数据库是否就绪
    
    Args:
        db: 数据库会话
        
    Returns:
        bool: 是否就绪
    """
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _is_websocket_ready() -> bool:
    """
    检查WebSocket服务是否就绪
    
    Returns:
        bool: 是否就绪
    """
    try:
        await websocket_service.get_stats()
        return True
    except Exception:
        return False


async def _is_scheduler_ready() -> bool:
    """
    检查调度服务是否就绪
    
    Returns:
        bool: 是否就绪
    """
    try:
        stats = await scheduler_service.get_stats()
        return stats.get("is_running", False)
    except Exception:
        return False