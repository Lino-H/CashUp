#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 发送服务业务逻辑

处理通知的实际发送逻辑，支持多种渠道
"""

import uuid
import json
import asyncio
import aiohttp
import smtplib
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.notification import Notification, NotificationStatus
from ..models.channel import NotificationChannel, ChannelType, ChannelStatus
from ..models.template import NotificationTemplate
from ..core.exceptions import (
    ChannelNotFoundError, ChannelNotAvailableError, 
    NotificationSendError, TemplateRenderError
)
from ..core.config import get_config
from .template_service import TemplateService

import logging

logger = logging.getLogger(__name__)
config = get_config()


class SenderService:
    """
    发送服务业务逻辑类
    
    负责处理通知的实际发送逻辑，支持多种渠道
    """
    
    def __init__(self):
        self.template_service = TemplateService()
        
        # 渠道发送器映射
        self.channel_senders = {
            ChannelType.EMAIL: self._send_email,
            ChannelType.SMS: self._send_sms,
            ChannelType.WECHAT: self._send_wechat,
            ChannelType.TELEGRAM: self._send_telegram,
            ChannelType.SLACK: self._send_slack,
            ChannelType.DISCORD: self._send_discord,
            ChannelType.WEBHOOK: self._send_webhook,
            ChannelType.PUSH: self._send_push,
        }
        
        # HTTP会话
        self._http_session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._http_session:
            await self._http_session.close()
    
    async def send_notification(
        self,
        db: AsyncSession,
        notification: Notification,
        channel: NotificationChannel,
        template: Optional[NotificationTemplate] = None
    ) -> Dict[str, Any]:
        """
        发送通知
        
        Args:
            db: 数据库会话
            notification: 通知对象
            channel: 发送渠道
            template: 通知模板（可选）
            
        Returns:
            Dict[str, Any]: 发送结果
            
        Raises:
            ChannelNotAvailableError: 渠道不可用
            NotificationSendError: 发送失败
        """
        # 检查渠道状态
        if not channel.is_available():
            raise ChannelNotAvailableError(f"Channel {channel.id} is not available")
        
        # 检查渠道限制
        if not await self._check_channel_limits(channel):
            raise ChannelNotAvailableError(f"Channel {channel.id} has reached its limits")
        
        start_time = datetime.utcnow()
        
        try:
            # 准备发送内容
            send_content = await self._prepare_send_content(
                db, notification, template
            )
            
            # 获取对应的发送器
            sender = self.channel_senders.get(channel.type)
            if not sender:
                raise NotificationSendError(f"No sender available for channel type {channel.type}")
            
            # 执行发送
            send_result = await sender(channel, notification, send_content)
            
            # 计算发送时间
            send_duration = (datetime.utcnow() - start_time).total_seconds()
            
            # 更新渠道统计
            await self._update_channel_stats(db, channel.id, success=True)
            
            logger.info(
                f"Notification {notification.id} sent successfully via {channel.type.value} "
                f"in {send_duration:.2f}s"
            )
            
            return {
                "success": True,
                "channel_id": channel.id,
                "channel_type": channel.type.value,
                "send_duration": send_duration,
                "timestamp": start_time.isoformat(),
                "message_id": send_result.get("message_id"),
                "details": send_result.get("details", {})
            }
            
        except Exception as e:
            # 更新渠道统计
            await self._update_channel_stats(
                db, channel.id, success=False, error_message=str(e)
            )
            
            logger.error(
                f"Failed to send notification {notification.id} via {channel.type.value}: {str(e)}"
            )
            
            return {
                "success": False,
                "channel_id": channel.id,
                "channel_type": channel.type.value,
                "error": str(e),
                "timestamp": start_time.isoformat()
            }
    
    async def send_batch_notifications(
        self,
        db: AsyncSession,
        notifications: List[Notification],
        channel: NotificationChannel,
        template: Optional[NotificationTemplate] = None,
        max_concurrent: int = 10
    ) -> List[Dict[str, Any]]:
        """
        批量发送通知
        
        Args:
            db: 数据库会话
            notifications: 通知列表
            channel: 发送渠道
            template: 通知模板（可选）
            max_concurrent: 最大并发数
            
        Returns:
            List[Dict[str, Any]]: 发送结果列表
        """
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def send_single(notification):
            async with semaphore:
                return await self.send_notification(db, notification, channel, template)
        
        # 并发发送
        tasks = [send_single(notification) for notification in notifications]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "notification_id": notifications[i].id,
                    "error": str(result),
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                result["notification_id"] = notifications[i].id
                processed_results.append(result)
        
        return processed_results
    
    async def _prepare_send_content(
        self,
        db: AsyncSession,
        notification: Notification,
        template: Optional[NotificationTemplate] = None
    ) -> Dict[str, Any]:
        """
        准备发送内容
        
        Args:
            db: 数据库会话
            notification: 通知对象
            template: 通知模板
            
        Returns:
            Dict[str, Any]: 发送内容
        """
        content = {
            "subject": notification.title,
            "content": notification.content,
            "html_content": notification.html_content,
            "recipient": notification.recipient,
            "sender": notification.sender,
            "metadata": notification.metadata or {}
        }
        
        # 如果有模板，进行渲染
        if template and notification.template_variables:
            try:
                render_result = await self.template_service.render_template(
                    db, template.id, notification.template_variables
                )
                
                content["subject"] = render_result.get("rendered_subject") or content["subject"]
                content["content"] = render_result["rendered_content"]
                content["html_content"] = render_result.get("rendered_html") or content["html_content"]
                
            except Exception as e:
                logger.warning(f"Template render failed for notification {notification.id}: {str(e)}")
                # 继续使用原始内容
        
        return content
    
    async def _check_channel_limits(self, channel: NotificationChannel) -> bool:
        """
        检查渠道限制
        
        Args:
            channel: 渠道对象
            
        Returns:
            bool: 是否在限制范围内
        """
        # 检查日发送限制
        if channel.daily_limit:
            today_sent = channel.get_today_sent_count()
            if today_sent >= channel.daily_limit:
                return False
        
        # 检查速率限制
        if channel.rate_limit:
            # 这里可以实现更复杂的速率限制逻辑
            # 目前简化处理
            pass
        
        return True
    
    async def _send_email(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送邮件
        
        Args:
            channel: 邮件渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        config = channel.config
        
        try:
            # 创建邮件消息
            msg = MIMEMultipart('alternative')
            msg['Subject'] = content['subject']
            msg['From'] = content.get('sender') or config.get('from_email')
            msg['To'] = content['recipient']
            
            # 添加文本内容
            text_part = MIMEText(content['content'], 'plain', 'utf-8')
            msg.attach(text_part)
            
            # 添加HTML内容（如果有）
            if content.get('html_content'):
                html_part = MIMEText(content['html_content'], 'html', 'utf-8')
                msg.attach(html_part)
            
            # 连接SMTP服务器并发送
            smtp_host = config['smtp_host']
            smtp_port = int(config['smtp_port'])
            username = config['username']
            password = config['password']
            use_tls = config.get('use_tls', True)
            
            if use_tls:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            
            server.login(username, password)
            text = msg.as_string()
            server.sendmail(msg['From'], [msg['To']], text)
            server.quit()
            
            return {
                "message_id": f"email_{uuid.uuid4().hex[:8]}",
                "details": {
                    "smtp_host": smtp_host,
                    "recipient": content['recipient']
                }
            }
            
        except Exception as e:
            raise NotificationSendError(f"Email send failed: {str(e)}")
    
    async def _send_sms(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送短信
        
        Args:
            channel: 短信渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        config = channel.config
        provider = config['provider']
        
        try:
            if provider == 'twilio':
                return await self._send_twilio_sms(config, content)
            elif provider == 'aliyun':
                return await self._send_aliyun_sms(config, content)
            elif provider == 'tencent':
                return await self._send_tencent_sms(config, content)
            else:
                raise NotificationSendError(f"Unsupported SMS provider: {provider}")
                
        except Exception as e:
            raise NotificationSendError(f"SMS send failed: {str(e)}")
    
    async def _send_wechat(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送微信消息
        
        Args:
            channel: 微信渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        config = channel.config
        
        try:
            # 获取access_token
            access_token = await self._get_wechat_access_token(config)
            
            # 发送消息
            url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}"
            
            payload = {
                "touser": content['recipient'],
                "msgtype": "text",
                "text": {
                    "content": content['content']
                }
            }
            
            async with self._http_session.post(url, json=payload) as response:
                result = await response.json()
                
                if result.get('errcode') == 0:
                    return {
                        "message_id": f"wechat_{uuid.uuid4().hex[:8]}",
                        "details": {
                            "recipient": content['recipient']
                        }
                    }
                else:
                    raise NotificationSendError(f"WeChat API error: {result.get('errmsg')}")
                    
        except Exception as e:
            raise NotificationSendError(f"WeChat send failed: {str(e)}")
    
    async def _send_telegram(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送Telegram消息
        
        Args:
            channel: Telegram渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        config = channel.config
        bot_token = config['bot_token']
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": content['recipient'],
                "text": content['content'],
                "parse_mode": "HTML" if content.get('html_content') else None
            }
            
            async with self._http_session.post(url, json=payload) as response:
                result = await response.json()
                
                if result.get('ok'):
                    return {
                        "message_id": str(result['result']['message_id']),
                        "details": {
                            "chat_id": content['recipient']
                        }
                    }
                else:
                    raise NotificationSendError(f"Telegram API error: {result.get('description')}")
                    
        except Exception as e:
            raise NotificationSendError(f"Telegram send failed: {str(e)}")
    
    async def _send_slack(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送Slack消息
        
        Args:
            channel: Slack渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        config = channel.config
        webhook_url = config['webhook_url']
        
        try:
            payload = {
                "text": content['subject'],
                "attachments": [
                    {
                        "color": "good",
                        "text": content['content'],
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            async with self._http_session.post(webhook_url, json=payload) as response:
                if response.status == 200:
                    return {
                        "message_id": f"slack_{uuid.uuid4().hex[:8]}",
                        "details": {
                            "webhook_url": webhook_url[:50] + "..."
                        }
                    }
                else:
                    raise NotificationSendError(f"Slack webhook error: {response.status}")
                    
        except Exception as e:
            raise NotificationSendError(f"Slack send failed: {str(e)}")
    
    async def _send_discord(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送Discord消息
        
        Args:
            channel: Discord渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        config = channel.config
        webhook_url = config['webhook_url']
        
        try:
            payload = {
                "content": f"**{content['subject']}**\n{content['content']}",
                "embeds": [
                    {
                        "title": content['subject'],
                        "description": content['content'],
                        "color": 0x00ff00,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ]
            }
            
            async with self._http_session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    return {
                        "message_id": f"discord_{uuid.uuid4().hex[:8]}",
                        "details": {
                            "webhook_url": webhook_url[:50] + "..."
                        }
                    }
                else:
                    raise NotificationSendError(f"Discord webhook error: {response.status}")
                    
        except Exception as e:
            raise NotificationSendError(f"Discord send failed: {str(e)}")
    
    async def _send_webhook(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送Webhook消息
        
        Args:
            channel: Webhook渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        config = channel.config
        url = config['url']
        method = config.get('method', 'POST')
        headers = config.get('headers', {})
        
        try:
            payload = {
                "notification_id": str(notification.id),
                "subject": content['subject'],
                "content": content['content'],
                "recipient": content['recipient'],
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": content['metadata']
            }
            
            # 合并自定义头部
            request_headers = {
                "Content-Type": "application/json",
                **headers
            }
            
            async with self._http_session.request(
                method, url, json=payload, headers=request_headers
            ) as response:
                if 200 <= response.status < 300:
                    return {
                        "message_id": f"webhook_{uuid.uuid4().hex[:8]}",
                        "details": {
                            "url": url[:50] + "...",
                            "method": method,
                            "status": response.status
                        }
                    }
                else:
                    raise NotificationSendError(f"Webhook error: {response.status}")
                    
        except Exception as e:
            raise NotificationSendError(f"Webhook send failed: {str(e)}")
    
    async def _send_push(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送推送消息
        
        Args:
            channel: 推送渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        config = channel.config
        provider = config['provider']
        
        try:
            if provider == 'firebase':
                return await self._send_firebase_push(config, content)
            elif provider == 'apns':
                return await self._send_apns_push(config, content)
            elif provider == 'jpush':
                return await self._send_jpush_push(config, content)
            else:
                raise NotificationSendError(f"Unsupported push provider: {provider}")
                
        except Exception as e:
            raise NotificationSendError(f"Push send failed: {str(e)}")
    
    async def _send_twilio_sms(self, config: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
        """发送Twilio短信"""
        # 这里应该实现实际的Twilio API调用
        # 为了演示，这里只是模拟
        await asyncio.sleep(0.1)
        
        return {
            "message_id": f"twilio_{uuid.uuid4().hex[:8]}",
            "details": {
                "provider": "twilio",
                "recipient": content['recipient']
            }
        }
    
    async def _send_aliyun_sms(self, config: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
        """发送阿里云短信"""
        await asyncio.sleep(0.1)
        
        return {
            "message_id": f"aliyun_{uuid.uuid4().hex[:8]}",
            "details": {
                "provider": "aliyun",
                "recipient": content['recipient']
            }
        }
    
    async def _send_tencent_sms(self, config: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
        """发送腾讯云短信"""
        await asyncio.sleep(0.1)
        
        return {
            "message_id": f"tencent_{uuid.uuid4().hex[:8]}",
            "details": {
                "provider": "tencent",
                "recipient": content['recipient']
            }
        }
    
    async def _get_wechat_access_token(self, config: Dict[str, Any]) -> str:
        """获取微信access_token"""
        # 这里应该实现实际的微信API调用
        # 为了演示，这里只是模拟
        return f"mock_access_token_{uuid.uuid4().hex[:8]}"
    
    async def _send_firebase_push(self, config: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
        """发送Firebase推送"""
        await asyncio.sleep(0.1)
        
        return {
            "message_id": f"firebase_{uuid.uuid4().hex[:8]}",
            "details": {
                "provider": "firebase",
                "recipient": content['recipient']
            }
        }
    
    async def _send_apns_push(self, config: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
        """发送APNS推送"""
        await asyncio.sleep(0.1)
        
        return {
            "message_id": f"apns_{uuid.uuid4().hex[:8]}",
            "details": {
                "provider": "apns",
                "recipient": content['recipient']
            }
        }
    
    async def _send_jpush_push(self, config: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
        """发送极光推送"""
        await asyncio.sleep(0.1)
        
        return {
            "message_id": f"jpush_{uuid.uuid4().hex[:8]}",
            "details": {
                "provider": "jpush",
                "recipient": content['recipient']
            }
        }
    
    async def _update_channel_stats(
        self,
        db: AsyncSession,
        channel_id: uuid.UUID,
        success: bool,
        error_message: Optional[str] = None
    ):
        """
        更新渠道统计信息
        
        Args:
            db: 数据库会话
            channel_id: 渠道ID
            success: 是否成功
            error_message: 错误消息
        """
        from sqlalchemy import update
        from ..models.channel import NotificationChannel
        
        update_data = {
            "updated_at": datetime.utcnow()
        }
        
        if success:
            update_data["sent_count"] = NotificationChannel.sent_count + 1
            update_data["last_sent_at"] = datetime.utcnow()
        else:
            update_data["failed_count"] = NotificationChannel.failed_count + 1
            if error_message:
                update_data["last_error_message"] = error_message
                update_data["last_error_at"] = datetime.utcnow()
        
        await db.execute(
            update(NotificationChannel)
            .where(NotificationChannel.id == channel_id)
            .values(**update_data)
        )
        await db.commit()