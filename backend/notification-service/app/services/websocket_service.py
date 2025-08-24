#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - WebSocket服务业务逻辑

处理实时通知推送和WebSocket连接管理
"""

import uuid
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.notification import Notification, NotificationStatus
from ..schemas.common import WebSocketMessage
from ..core.config import get_config

import logging

logger = logging.getLogger(__name__)
config = get_config()


class ConnectionManager:
    """
    WebSocket连接管理器
    
    管理所有活跃的WebSocket连接
    """
    
    def __init__(self):
        # 存储活跃连接 {connection_id: {websocket, user_id, channels, last_ping}}
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        
        # 用户连接映射 {user_id: [connection_ids]}
        self.user_connections: Dict[str, List[str]] = {}
        
        # 频道订阅映射 {channel: [connection_ids]}
        self.channel_subscriptions: Dict[str, List[str]] = {}
        
        # 连接锁
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        connection_id: Optional[str] = None
    ) -> str:
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket对象
            user_id: 用户ID
            connection_id: 连接ID（可选）
            
        Returns:
            str: 连接ID
        """
        if not connection_id:
            connection_id = str(uuid.uuid4())
        
        await websocket.accept()
        
        async with self._lock:
            # 存储连接信息
            self.active_connections[connection_id] = {
                "websocket": websocket,
                "user_id": user_id,
                "channels": set(),
                "last_ping": datetime.utcnow(),
                "connected_at": datetime.utcnow()
            }
            
            # 更新用户连接映射
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = []
                self.user_connections[user_id].append(connection_id)
        
        logger.info(f"WebSocket connection established: {connection_id} for user {user_id}")
        
        # 发送连接确认消息
        await self.send_to_connection(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        断开WebSocket连接
        
        Args:
            connection_id: 连接ID
        """
        async with self._lock:
            if connection_id not in self.active_connections:
                return
            
            connection_info = self.active_connections[connection_id]
            user_id = connection_info.get("user_id")
            channels = connection_info.get("channels", set())
            
            # 从频道订阅中移除
            for channel in channels:
                if channel in self.channel_subscriptions:
                    if connection_id in self.channel_subscriptions[channel]:
                        self.channel_subscriptions[channel].remove(connection_id)
                    if not self.channel_subscriptions[channel]:
                        del self.channel_subscriptions[channel]
            
            # 从用户连接映射中移除
            if user_id and user_id in self.user_connections:
                if connection_id in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # 移除连接
            del self.active_connections[connection_id]
        
        logger.info(f"WebSocket connection disconnected: {connection_id}")
    
    async def subscribe_channel(self, connection_id: str, channel: str) -> bool:
        """
        订阅频道
        
        Args:
            connection_id: 连接ID
            channel: 频道名称
            
        Returns:
            bool: 是否订阅成功
        """
        async with self._lock:
            if connection_id not in self.active_connections:
                return False
            
            # 添加到连接的频道列表
            self.active_connections[connection_id]["channels"].add(channel)
            
            # 添加到频道订阅映射
            if channel not in self.channel_subscriptions:
                self.channel_subscriptions[channel] = []
            if connection_id not in self.channel_subscriptions[channel]:
                self.channel_subscriptions[channel].append(connection_id)
        
        logger.info(f"Connection {connection_id} subscribed to channel {channel}")
        return True
    
    async def unsubscribe_channel(self, connection_id: str, channel: str) -> bool:
        """
        取消订阅频道
        
        Args:
            connection_id: 连接ID
            channel: 频道名称
            
        Returns:
            bool: 是否取消订阅成功
        """
        async with self._lock:
            if connection_id not in self.active_connections:
                return False
            
            # 从连接的频道列表中移除
            self.active_connections[connection_id]["channels"].discard(channel)
            
            # 从频道订阅映射中移除
            if channel in self.channel_subscriptions:
                if connection_id in self.channel_subscriptions[channel]:
                    self.channel_subscriptions[channel].remove(connection_id)
                if not self.channel_subscriptions[channel]:
                    del self.channel_subscriptions[channel]
        
        logger.info(f"Connection {connection_id} unsubscribed from channel {channel}")
        return True
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        向指定连接发送消息
        
        Args:
            connection_id: 连接ID
            message: 消息内容
            
        Returns:
            bool: 是否发送成功
        """
        if connection_id not in self.active_connections:
            return False
        
        websocket = self.active_connections[connection_id]["websocket"]
        
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"Failed to send message to connection {connection_id}: {str(e)}")
            # 连接可能已断开，移除它
            await self.disconnect(connection_id)
            return False
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """
        向指定用户的所有连接发送消息
        
        Args:
            user_id: 用户ID
            message: 消息内容
            
        Returns:
            int: 成功发送的连接数
        """
        if user_id not in self.user_connections:
            return 0
        
        connection_ids = self.user_connections[user_id].copy()
        success_count = 0
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                success_count += 1
        
        return success_count
    
    async def send_to_channel(self, channel: str, message: Dict[str, Any]) -> int:
        """
        向指定频道的所有订阅者发送消息
        
        Args:
            channel: 频道名称
            message: 消息内容
            
        Returns:
            int: 成功发送的连接数
        """
        if channel not in self.channel_subscriptions:
            return 0
        
        connection_ids = self.channel_subscriptions[channel].copy()
        success_count = 0
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                success_count += 1
        
        return success_count
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """
        向所有连接广播消息
        
        Args:
            message: 消息内容
            
        Returns:
            int: 成功发送的连接数
        """
        connection_ids = list(self.active_connections.keys())
        success_count = 0
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                success_count += 1
        
        return success_count
    
    async def update_ping(self, connection_id: str):
        """
        更新连接的ping时间
        
        Args:
            connection_id: 连接ID
        """
        if connection_id in self.active_connections:
            self.active_connections[connection_id]["last_ping"] = datetime.utcnow()
    
    async def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        获取连接信息
        
        Args:
            connection_id: 连接ID
            
        Returns:
            Optional[Dict[str, Any]]: 连接信息
        """
        if connection_id not in self.active_connections:
            return None
        
        info = self.active_connections[connection_id].copy()
        # 移除WebSocket对象，避免序列化问题
        info.pop("websocket", None)
        info["channels"] = list(info.get("channels", set()))
        info["last_ping"] = info["last_ping"].isoformat()
        info["connected_at"] = info["connected_at"].isoformat()
        
        return info
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取连接统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "total_connections": len(self.active_connections),
            "total_users": len(self.user_connections),
            "total_channels": len(self.channel_subscriptions),
            "connections_per_user": {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            },
            "subscriptions_per_channel": {
                channel: len(connections) 
                for channel, connections in self.channel_subscriptions.items()
            }
        }
    
    async def cleanup_stale_connections(self, timeout_minutes: int = 30):
        """
        清理过期连接
        
        Args:
            timeout_minutes: 超时时间（分钟）
        """
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        stale_connections = []
        
        for connection_id, info in self.active_connections.items():
            if info["last_ping"] < cutoff_time:
                stale_connections.append(connection_id)
        
        for connection_id in stale_connections:
            await self.disconnect(connection_id)
        
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")


class WebSocketService:
    """
    WebSocket服务业务逻辑类
    
    处理实时通知推送和WebSocket连接管理
    """
    
    def __init__(self):
        """
        初始化WebSocket服务
        """
        self.connection_manager = ConnectionManager()
        self._cleanup_task = None
        
    async def start(self):
        """启动WebSocket服务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
    async def stop(self):
        """停止WebSocket服务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None
    ) -> str:
        """
        处理WebSocket连接
        
        Args:
            websocket: WebSocket对象
            user_id: 用户ID
            
        Returns:
            str: 连接ID
        """
        connection_id = await self.connection_manager.connect(websocket, user_id)
        
        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                await self._handle_message(connection_id, data)
                
        except WebSocketDisconnect:
            await self.connection_manager.disconnect(connection_id)
        except Exception as e:
            logger.error(f"WebSocket error for connection {connection_id}: {str(e)}")
            await self.connection_manager.disconnect(connection_id)
        
        return connection_id
    
    async def send_notification(
        self,
        notification: Notification,
        target_type: str = "user",
        target_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送实时通知
        
        Args:
            notification: 通知对象
            target_type: 目标类型 (user, channel, broadcast)
            target_value: 目标值
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        message = {
            "type": "notification",
            "data": {
                "id": str(notification.id),
                "title": notification.title,
                "content": notification.content,
                "category": notification.category.value if notification.category else None,
                "priority": notification.priority.value if notification.priority else None,
                "status": notification.status.value if notification.status else None,
                "created_at": notification.created_at.isoformat(),
                "metadata": notification.metadata
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        success_count = 0
        
        if target_type == "user" and target_value:
            success_count = await self.connection_manager.send_to_user(target_value, message)
        elif target_type == "channel" and target_value:
            success_count = await self.connection_manager.send_to_channel(target_value, message)
        elif target_type == "broadcast":
            success_count = await self.connection_manager.broadcast(message)
        
        logger.info(
            f"Sent notification {notification.id} to {success_count} connections "
            f"via {target_type}:{target_value or 'all'}"
        )
        
        return {
            "notification_id": str(notification.id),
            "target_type": target_type,
            "target_value": target_value,
            "success_count": success_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def send_notification_update(
        self,
        notification: Notification,
        update_type: str = "status_update",
        target_type: str = "user",
        target_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送通知状态更新
        
        Args:
            notification: 通知对象
            update_type: 更新类型
            target_type: 目标类型 (user, channel, broadcast)
            target_value: 目标值
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        message = {
            "type": "notification_update",
            "update_type": update_type,
            "data": {
                "id": str(notification.id),
                "title": notification.title,
                "content": notification.content,
                "category": notification.category.value if notification.category else None,
                "priority": notification.priority.value if notification.priority else None,
                "status": notification.status.value if notification.status else None,
                "created_at": notification.created_at.isoformat(),
                "updated_at": notification.updated_at.isoformat() if notification.updated_at else None,
                "metadata": notification.metadata
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        success_count = 0
        
        if target_type == "user" and target_value:
            success_count = await self.connection_manager.send_to_user(target_value, message)
        elif target_type == "channel" and target_value:
            success_count = await self.connection_manager.send_to_channel(target_value, message)
        elif target_type == "broadcast":
            success_count = await self.connection_manager.broadcast(message)
        
        logger.info(
            f"Sent notification update {notification.id} to {success_count} connections "
            f"via {target_type}:{target_value or 'all'}"
        )
        
        return {
            "notification_id": str(notification.id),
            "update_type": update_type,
            "target_type": target_type,
            "target_value": target_value,
            "success_count": success_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def send_system_message(
        self,
        message_type: str,
        content: Dict[str, Any],
        target_type: str = "broadcast",
        target_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送系统消息
        
        Args:
            message_type: 消息类型
            content: 消息内容
            target_type: 目标类型
            target_value: 目标值
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        message = {
            "type": "system",
            "message_type": message_type,
            "data": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        success_count = 0
        
        if target_type == "user" and target_value:
            success_count = await self.connection_manager.send_to_user(target_value, message)
        elif target_type == "channel" and target_value:
            success_count = await self.connection_manager.send_to_channel(target_value, message)
        elif target_type == "broadcast":
            success_count = await self.connection_manager.broadcast(message)
        
        return {
            "message_type": message_type,
            "target_type": target_type,
            "target_value": target_value,
            "success_count": success_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """
        获取连接统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return await self.connection_manager.get_stats()
    
    async def get_user_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有连接信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Dict[str, Any]]: 连接信息列表
        """
        if user_id not in self.connection_manager.user_connections:
            return []
        
        connection_ids = self.connection_manager.user_connections[user_id]
        connections = []
        
        for connection_id in connection_ids:
            info = await self.connection_manager.get_connection_info(connection_id)
            if info:
                connections.append(info)
        
        return connections
    
    async def disconnect_user(self, user_id: str) -> int:
        """
        断开用户的所有连接
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 断开的连接数
        """
        if user_id not in self.connection_manager.user_connections:
            return 0
        
        connection_ids = self.connection_manager.user_connections[user_id].copy()
        
        for connection_id in connection_ids:
            await self.connection_manager.disconnect(connection_id)
        
        return len(connection_ids)
    
    async def _handle_message(self, connection_id: str, data: str):
        """
        处理WebSocket消息
        
        Args:
            connection_id: 连接ID
            data: 消息数据
        """
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type == "ping":
                await self._handle_ping(connection_id)
            elif message_type == "subscribe":
                await self._handle_subscribe(connection_id, message)
            elif message_type == "unsubscribe":
                await self._handle_unsubscribe(connection_id, message)
            elif message_type == "get_info":
                await self._handle_get_info(connection_id)
            else:
                logger.warning(f"Unknown message type: {message_type} from connection {connection_id}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from connection {connection_id}: {data}")
        except Exception as e:
            logger.error(f"Error handling message from connection {connection_id}: {str(e)}")
    
    async def _handle_ping(self, connection_id: str):
        """处理ping消息"""
        await self.connection_manager.update_ping(connection_id)
        await self.connection_manager.send_to_connection(connection_id, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_subscribe(self, connection_id: str, message: Dict[str, Any]):
        """处理订阅消息"""
        channel = message.get("channel")
        if not channel:
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": "Channel name is required for subscription",
                "timestamp": datetime.utcnow().isoformat()
            })
            return
        
        success = await self.connection_manager.subscribe_channel(connection_id, channel)
        
        await self.connection_manager.send_to_connection(connection_id, {
            "type": "subscribe_response",
            "channel": channel,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_unsubscribe(self, connection_id: str, message: Dict[str, Any]):
        """处理取消订阅消息"""
        channel = message.get("channel")
        if not channel:
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": "Channel name is required for unsubscription",
                "timestamp": datetime.utcnow().isoformat()
            })
            return
        
        success = await self.connection_manager.unsubscribe_channel(connection_id, channel)
        
        await self.connection_manager.send_to_connection(connection_id, {
            "type": "unsubscribe_response",
            "channel": channel,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_get_info(self, connection_id: str):
        """处理获取信息消息"""
        info = await self.connection_manager.get_connection_info(connection_id)
        
        await self.connection_manager.send_to_connection(connection_id, {
            "type": "info_response",
            "data": info,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _periodic_cleanup(self):
        """定期清理过期连接"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                await self.connection_manager.cleanup_stale_connections()
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {str(e)}")


# 全局WebSocket服务实例
websocket_service = None

def get_websocket_service() -> WebSocketService:
    """获取WebSocket服务实例"""
    global websocket_service
    if websocket_service is None:
        websocket_service = WebSocketService()
    return websocket_service