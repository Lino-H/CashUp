#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 订单服务API路由主文件

整合所有API路由
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from .orders import router as orders_router
from ...core.database import check_database_health
from ...services.exchange_client import ExchangeClient
from ...services.notification_service import NotificationService

api_router = APIRouter(prefix="/api/v1")

# 包含订单路由
api_router.include_router(orders_router)


@api_router.get("/")
async def root():
    """
    API根路径
    
    Returns:
        dict: 服务信息
    """
    return {
        "service": "CashUp Order Service",
        "version": "1.0.0",
        "description": "订单管理服务",
        "docs": "/docs",
        "health": "/health"
    }


@api_router.get("/health")
async def health_check():
    """
    健康检查接口
    
    Returns:
        JSONResponse: 健康状态信息
    """
    try:
        # 检查数据库连接
        db_healthy = await check_database_health()
        
        # 检查外部服务
        exchange_client = ExchangeClient()
        notification_service = NotificationService()
        
        exchange_health = await exchange_client.health_check()
        notification_health = await notification_service.health_check()
        
        # 汇总健康状态
        overall_status = "healthy"
        if (
            db_healthy.get("status") != "healthy" or
            exchange_health.get("status") != "healthy" or
            notification_health.get("status") != "healthy"
        ):
            overall_status = "unhealthy"
        
        health_data = {
            "status": overall_status,
            "timestamp": db_healthy.get("timestamp"),
            "service": "order-service",
            "version": "1.0.0",
            "dependencies": {
                "database": db_healthy,
                "exchange_service": exchange_health,
                "notification_service": notification_health
            }
        }
        
        status_code = 200 if overall_status == "healthy" else 503
        return JSONResponse(content=health_data, status_code=status_code)
        
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "service": "order-service",
                "version": "1.0.0"
            },
            status_code=503
        )