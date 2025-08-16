#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - WebSocket API路由

处理WebSocket连接和实时通信
"""

import uuid
import json
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user_from_token, get_current_user
from ...services.websocket_service import websocket_service, ConnectionManager
from ...schemas.common import BaseResponse

import logging

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="认证令牌"),
    user_id: str = Query(None, description="用户ID"),
    client_id: str = Query(None, description="客户端ID")
):
    """
    WebSocket连接端点
    
    Args:
        websocket: WebSocket连接
        token: 认证令牌
        user_id: 用户ID
        client_id: 客户端ID
    """
    connection_id = None
    
    try:
        # 验证令牌
        try:
            user_info = await get_current_user_from_token(token)
            if not user_info:
                await websocket.close(code=4001, reason="Invalid token")
                return
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # 接受连接
        await websocket.accept()
        
        # 生成连接ID
        if not client_id:
            client_id = str(uuid.uuid4())
        
        # 注册连接
        connection_id = await websocket_service.connect(
            websocket=websocket,
            user_id=user_info["user_id"],
            client_id=client_id
        )
        
        logger.info(f"WebSocket connected: {connection_id}, user: {user_info['user_id']}")
        
        # 发送连接成功消息
        await websocket_service.send_to_connection(
            connection_id,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "user_id": user_info["user_id"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # 监听消息
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理消息
                await _handle_websocket_message(
                    connection_id,
                    user_info["user_id"],
                    message
                )
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON message from {connection_id}")
                await websocket_service.send_to_connection(
                    connection_id,
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Error handling message from {connection_id}: {str(e)}")
                await websocket_service.send_to_connection(
                    connection_id,
                    {
                        "type": "error",
                        "message": "Internal server error",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    
    finally:
        # 断开连接
        if connection_id:
            await websocket_service.disconnect(connection_id)
            logger.info(f"WebSocket connection {connection_id} cleaned up")


async def _handle_websocket_message(
    connection_id: str,
    user_id: str,
    message: Dict[str, Any]
):
    """
    处理WebSocket消息
    
    Args:
        connection_id: 连接ID
        user_id: 用户ID
        message: 消息内容
    """
    message_type = message.get("type")
    
    if message_type == "ping":
        # 处理心跳
        await websocket_service.handle_ping(connection_id)
        await websocket_service.send_to_connection(
            connection_id,
            {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    elif message_type == "subscribe":
        # 订阅频道
        channels = message.get("channels", [])
        for channel in channels:
            await websocket_service.subscribe_channel(connection_id, channel)
        
        await websocket_service.send_to_connection(
            connection_id,
            {
                "type": "subscribed",
                "channels": channels,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    elif message_type == "unsubscribe":
        # 取消订阅频道
        channels = message.get("channels", [])
        for channel in channels:
            await websocket_service.unsubscribe_channel(connection_id, channel)
        
        await websocket_service.send_to_connection(
            connection_id,
            {
                "type": "unsubscribed",
                "channels": channels,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    elif message_type == "get_info":
        # 获取连接信息
        info = await websocket_service.get_connection_info(connection_id)
        await websocket_service.send_to_connection(
            connection_id,
            {
                "type": "connection_info",
                "info": info,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    else:
        # 未知消息类型
        await websocket_service.send_to_connection(
            connection_id,
            {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_websocket_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    获取WebSocket统计信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        Dict[str, Any]: 统计信息
    """
    try:
        stats = await websocket_service.get_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections", response_model=Dict[str, Any])
async def get_websocket_connections(
    user_id: str = Query(None, description="用户ID过滤"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取WebSocket连接列表
    
    Args:
        user_id: 用户ID过滤
        current_user: 当前用户
        
    Returns:
        Dict[str, Any]: 连接列表
    """
    try:
        connections = await websocket_service.get_connections(user_id)
        return {
            "connections": connections,
            "total": len(connections),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket connections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast", response_model=BaseResponse)
async def broadcast_message(
    message: Dict[str, Any],
    channel: str = Query(None, description="频道名称"),
    user_id: str = Query(None, description="用户ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    广播消息
    
    Args:
        message: 消息内容
        channel: 频道名称
        user_id: 用户ID
        current_user: 当前用户
        
    Returns:
        BaseResponse: 广播结果
    """
    try:
        # 添加时间戳
        message["timestamp"] = datetime.utcnow().isoformat()
        message["sender"] = current_user["user_id"]
        
        if channel:
            # 向频道广播
            await websocket_service.send_to_channel(channel, message)
            return BaseResponse(
                success=True,
                message=f"Message broadcasted to channel: {channel}"
            )
        elif user_id:
            # 向特定用户发送
            await websocket_service.send_user_message(user_id, message)
            return BaseResponse(
                success=True,
                message=f"Message sent to user: {user_id}"
            )
        else:
            # 全局广播
            await websocket_service.broadcast(message)
            return BaseResponse(
                success=True,
                message="Message broadcasted to all connections"
            )
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/connections/{connection_id}", response_model=BaseResponse)
async def disconnect_websocket(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    断开WebSocket连接
    
    Args:
        connection_id: 连接ID
        current_user: 当前用户
        
    Returns:
        BaseResponse: 断开结果
    """
    try:
        success = await websocket_service.disconnect(connection_id)
        
        if success:
            return BaseResponse(
                success=True,
                message=f"Connection {connection_id} disconnected"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Connection not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting WebSocket {connection_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}/connections", response_model=BaseResponse)
async def disconnect_user_websockets(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    断开用户的所有WebSocket连接
    
    Args:
        user_id: 用户ID
        current_user: 当前用户
        
    Returns:
        BaseResponse: 断开结果
    """
    try:
        count = await websocket_service.disconnect_user(user_id)
        
        return BaseResponse(
            success=True,
            message=f"Disconnected {count} connections for user {user_id}"
        )
        
    except Exception as e:
        logger.error(f"Error disconnecting user WebSockets {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup", response_model=BaseResponse)
async def cleanup_websocket_connections(
    current_user: dict = Depends(get_current_user)
):
    """
    清理过期的WebSocket连接
    
    Args:
        current_user: 当前用户
        
    Returns:
        BaseResponse: 清理结果
    """
    try:
        count = await websocket_service.cleanup_expired_connections()
        
        return BaseResponse(
            success=True,
            message=f"Cleaned up {count} expired connections"
        )
        
    except Exception as e:
        logger.error(f"Error cleaning up WebSocket connections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, Any])
async def websocket_health_check():
    """
    WebSocket服务健康检查
    
    Returns:
        Dict[str, Any]: 健康状态
    """
    try:
        stats = await websocket_service.get_stats()
        
        return {
            "status": "healthy",
            "service": "websocket",
            "connections": stats.get("total_connections", 0),
            "active_users": stats.get("active_users", 0),
            "channels": stats.get("total_channels", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"WebSocket health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "websocket",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }