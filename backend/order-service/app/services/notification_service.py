#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知服务

处理订单相关的通知发送
"""

import uuid
import logging
from typing import Dict, Any, Optional
import httpx
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationService:
    """
    通知服务类
    
    负责发送订单相关的通知
    """
    
    def __init__(self):
        self.notification_service_url = settings.NOTIFICATION_SERVICE_URL
        self.timeout = 10.0
    
    async def send_order_notification(
        self,
        user_id: uuid.UUID,
        order_id: uuid.UUID,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        发送订单通知
        
        Args:
            user_id: 用户ID
            order_id: 订单ID
            event_type: 事件类型
            message: 通知消息
            metadata: 额外元数据
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 使用notification服务的标准格式
            notification_data = {
                "title": self._get_notification_title(event_type),
                "content": message,
                "category": "trading",
                "priority": self._get_notification_priority(event_type),
                "channels": self._get_notification_channels(event_type),
                "recipients": {
                    "wxpusher": [],
                    "pushplus": [],
                    "qanotify": []
                },
                "user_id": str(user_id),
                "metadata": {
                    "order_id": str(order_id),
                    "service": "order-service",
                    "event_type": event_type,
                    **(metadata or {})
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.notification_service_url}/api/v1/notifications",
                    json=notification_data
                )
                response.raise_for_status()
                
            logger.info(f"Notification sent for order {order_id}: {event_type}")
            return True
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending notification: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    async def send_order_alert(
        self,
        user_id: uuid.UUID,
        order_id: uuid.UUID,
        alert_type: str,
        message: str,
        severity: str = "warning"
    ) -> bool:
        """
        发送订单警报
        
        Args:
            user_id: 用户ID
            order_id: 订单ID
            alert_type: 警报类型
            message: 警报消息
            severity: 严重程度
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 使用notification服务的标准格式
            alert_data = {
                "title": f"Order Alert: {alert_type.title()}",
                "content": message,
                "category": "alert",
                "priority": "high" if severity in ["error", "critical"] else "normal",
                "channels": ["wxpusher", "pushplus", "qanotify"] if severity in ["error", "critical"] else ["wxpusher", "pushplus"],
                "recipients": {
                    "wxpusher": [],
                    "pushplus": [],
                    "qanotify": []
                },
                "user_id": str(user_id),
                "metadata": {
                    "order_id": str(order_id),
                    "service": "order-service",
                    "alert_type": alert_type,
                    "severity": severity,
                    "alert_category": "order"
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.notification_service_url}/api/v1/notifications",
                    json=alert_data
                )
                response.raise_for_status()
                
            logger.info(f"Alert sent for order {order_id}: {alert_type} ({severity})")
            return True
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending alert: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
            return False
    
    async def send_batch_notification(
        self,
        notifications: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量发送通知
        
        Args:
            notifications: 通知列表
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        try:
            batch_data = {
                "notifications": notifications
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.notification_service_url}/api/v1/notifications/batch",
                    json=batch_data
                )
                response.raise_for_status()
                result = response.json()
                
            logger.info(f"Batch notification sent: {len(notifications)} notifications")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending batch notification: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error sending batch notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_notification_title(self, event_type: str) -> str:
        """
        获取通知标题
        
        Args:
            event_type: 事件类型
            
        Returns:
            str: 通知标题
        """
        titles = {
            "order_created": "Order Created",
            "order_submitted": "Order Submitted",
            "order_filled": "Order Filled",
            "order_partial_filled": "Order Partially Filled",
            "order_cancelled": "Order Cancelled",
            "order_rejected": "Order Rejected",
            "order_failed": "Order Failed",
            "order_expired": "Order Expired",
            "order_updated": "Order Updated"
        }
        return titles.get(event_type, "Order Notification")
    
    def _get_notification_priority(self, event_type: str) -> str:
        """
        获取通知优先级
        
        Args:
            event_type: 事件类型
            
        Returns:
            str: 优先级
        """
        high_priority_events = [
            "order_filled", "order_rejected", "order_failed", "order_expired"
        ]
        normal_priority_events = [
            "order_partial_filled", "order_cancelled"
        ]
        
        if event_type in high_priority_events:
            return "high"
        elif event_type in normal_priority_events:
            return "normal"
        else:
            return "low"
    
    def _get_notification_channels(self, event_type: str) -> list[str]:
        """
        获取通知渠道
        
        Args:
            event_type: 事件类型
            
        Returns:
            list[str]: 通知渠道列表
        """
        # 重要事件使用多渠道通知
        important_events = [
            "order_filled", "order_rejected", "order_failed"
        ]
        
        if event_type in important_events:
            return ["wxpusher", "pushplus", "qanotify"]
        else:
            return ["wxpusher", "pushplus"]
    
    async def health_check(self) -> Dict[str, Any]:
        """
        检查通知服务健康状态
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.notification_service_url}/health")
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Notification service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }