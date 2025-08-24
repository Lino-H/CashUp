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

# QANotify消息推送
try:
    from qanotify import run_order_notify, run_price_notify, run_strategy_notify
except ImportError:
    run_order_notify = None
    run_price_notify = None
    run_strategy_notify = None

import logging

logger = logging.getLogger(__name__)
config = get_config()


class SenderService:
    """
    发送服务业务逻辑类
    
    负责处理通知的实际发送逻辑，支持多种渠道
    """
    
    def __init__(self, websocket_service=None):
        self.template_service = TemplateService()
        self.websocket_service = websocket_service
        
        # 渠道发送器映射
        self.channel_senders = {
            ChannelType.EMAIL: self._send_email,
            ChannelType.SMS: self._send_sms,
            ChannelType.WXPUSHER: self._send_wxpusher,
            ChannelType.QANOTIFY: self._send_qanotify,
            ChannelType.PUSHPLUS: self._send_pushplus,
            ChannelType.TELEGRAM: self._send_telegram,
            ChannelType.WEBSOCKET: self._send_websocket,
            ChannelType.WEBHOOK: self._send_webhook,
            ChannelType.SYSTEM: self._send_system,
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
        if channel.status != ChannelStatus.ACTIVE:
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
            
            channel_type_str = channel.type.value if channel.type else "unknown"
            logger.error(
                f"Failed to send notification {notification.id} via {channel_type_str}: {str(e)}"
            )
            
            return {
                "success": False,
                "channel_id": channel.id,
                "channel_type": channel_type_str,
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
            "html_content": None,  # 从模板渲染或保持为None
            "recipient": notification.recipient_email or notification.recipient_phone or "default",
            "sender": "CashUp System",  # 默认发送者
            "metadata": notification.meta_data or {}
        }
        
        # 如果有模板，进行渲染
        if template and notification.template_data:
            try:
                render_result = await self.template_service.render_template(
                    db, template.id, notification.template_data
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
    
    async def _send_wxpusher(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送WxPusher消息
        
        Args:
            channel: WxPusher渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        config = channel.config
        app_token = config.get('app_token') or config.get('token')
        api_url = config.get('api_url', 'http://wxpusher.zjiecode.com/api/send/message')
        uid = config.get('uid') or config.get('uids', [])
        
        if not app_token:
            raise NotificationSendError("WxPusher app_token not configured")
        
        if not uid:
            raise NotificationSendError("WxPusher uid not configured")
        
        try:
            # 准备发送数据
            title = content.get('subject', notification.title)
            message = content.get('content', notification.content)
            
            # 构建请求数据
            data = {
                "appToken": app_token,
                "content": message,
                "summary": title,
                "contentType": 1,  # 1-文本，2-html，3-markdown
                "uids": [uid] if isinstance(uid, str) else uid
            }
            
            # 发送请求
            if not self._http_session:
                self._http_session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                )
            
            async with self._http_session.post(
                api_url,
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("success"):
                    # 安全地获取messageId
                    data = result.get('data', {})
                    message_id = uuid.uuid4().hex[:8]  # 默认值
                    if isinstance(data, dict):
                        message_id = data.get('messageId', message_id)
                    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                        message_id = data[0].get('messageId', message_id)
                    
                    return {
                        "message_id": f"wxpusher_{message_id}",
                        "details": {
                            "provider": "wxpusher",
                            "recipient": uid,
                            "response_code": result.get("code"),
                            "response_msg": result.get("msg")
                        }
                    }
                else:
                    raise NotificationSendError(
                        f"WxPusher API error: {result.get('msg', 'Unknown error')}"
                    )
                    
        except Exception as e:
            raise NotificationSendError(f"WxPusher send failed: {str(e)}")
    
    async def _send_qanotify(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送QANotify消息
        
        Args:
            channel: QANotify渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        config = channel.config
        token = config.get('token') or config.get('key')
        
        if not token:
            raise NotificationSendError("QANotify token not configured")
        
        # 检查qanotify包是否可用
        if run_order_notify is None or run_price_notify is None or run_strategy_notify is None:
            raise NotificationSendError("QANotify package not available. Please install qanotify package.")
        
        try:
            # 根据通知类别选择合适的发送方法
            logger.info(f"Debug: notification.category = {notification.category}, type = {type(notification.category)}")
            category = notification.category.value if notification.category else 'general'
            title = content.get('subject', notification.title)
            message = content.get('content', notification.content)
            
            if category == 'order' or 'order' in title.lower():
                # 订单通知
                template_vars = notification.template_data or {}
                strategy_name = template_vars.get('strategy_name', 'CashUp')
                account_name = template_vars.get('account_name', 'Default')
                contract = template_vars.get('contract', 'Unknown')
                order_direction = template_vars.get('order_direction', 'BUY')
                order_offset = template_vars.get('order_offset', 'OPEN')
                price = template_vars.get('price', 0)
                volume = template_vars.get('volume', 0)
                order_time = notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
                
                # 使用run_order_notify发送订单通知
                run_order_notify(
                    token, strategy_name, account_name, contract,
                    order_direction, order_offset, price, volume, order_time
                )
                
            elif category == 'price' or 'price' in title.lower() or '价格' in title:
                # 价格预警通知
                template_vars = notification.template_data or {}
                contract = template_vars.get('contract', 'Unknown')
                cur_price = template_vars.get('current_price', '0')
                limit_price = template_vars.get('limit_price', 0)
                order_id = template_vars.get('order_id', str(notification.id))
                
                # 使用run_price_notify发送价格预警
                run_price_notify(
                    token, title, contract, str(cur_price), limit_price, order_id
                )
                
            else:
                # 策略通知或其他通知
                template_vars = notification.template_data or {}
                strategy_name = template_vars.get('strategy_name', 'CashUp')
                frequency = template_vars.get('frequency', 'once')
                
                # 使用run_strategy_notify发送策略通知
                run_strategy_notify(
                    token, strategy_name, title, message, frequency
                )
            
            return {
                "message_id": f"qanotify_{uuid.uuid4().hex[:8]}",
                "details": {
                    "provider": "qanotify",
                    "category": category,
                    "recipient": content.get('recipient', 'default'),
                    "method": self._get_qanotify_method_name(category)
                }
            }
                    
        except Exception as e:
            raise NotificationSendError(f"QANotify send failed: {str(e)}")
    
    def _get_qanotify_method_name(self, category: str) -> str:
        """
        根据通知类别获取QANotify方法名称
        
        Args:
            category: 通知类别
            
        Returns:
            str: 方法名称
        """
        if category == 'order' or 'order' in category.lower():
            return 'run_order_notify'
        elif category == 'price' or 'price' in category.lower():
            return 'run_price_notify'
        else:
            return 'run_strategy_notify'
    
    async def _send_pushplus(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送PushPlus消息
        
        Args:
            channel: PushPlus渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        config = channel.config
        token = config.get('token') or config.get('key')
        
        if not token:
            raise NotificationSendError("PushPlus token not configured")
        
        try:
            # 准备发送数据
            title = content.get('subject', notification.title)
            message = content.get('content', notification.content)
            
            # 根据通知类型选择模板
            template = "html"  # 默认使用HTML模板
            
            # 如果内容包含Markdown标记，使用markdown模板
            if any(marker in message for marker in ['#', '**', '*', '`', '>', '-', '1.']):
                template = "markdown"
            
            # 构建请求数据
            data = {
                "token": token,
                "title": title,
                "content": message,
                "template": template
            }
            
            # 添加群组编码（如果配置了）
            topic = config.get('topic')
            if topic:
                data["topic"] = topic
            
            # 发送请求
            if not self._http_session:
                self._http_session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                )
            
            async with self._http_session.post(
                "http://www.pushplus.plus/send",
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("code") == 200:
                    return {
                        "message_id": f"pushplus_{result.get('data', uuid.uuid4().hex[:8])}",
                        "details": {
                            "provider": "pushplus",
                            "template": template,
                            "topic": topic,
                            "recipient": content.get('recipient', 'default'),
                            "response_code": result.get("code"),
                            "response_msg": result.get("msg")
                        }
                    }
                else:
                    raise NotificationSendError(
                        f"PushPlus API error: {result.get('msg', 'Unknown error')}"
                    )
                    
        except Exception as e:
            raise NotificationSendError(f"PushPlus send failed: {str(e)}")
    
    async def _send_websocket(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送WebSocket消息
        
        Args:
            channel: WebSocket渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        try:
            # 通过WebSocket服务发送消息
            if self.websocket_service:
                result = await self.websocket_service.send_notification(
                    notification,
                    target_type="user",
                    target_value=content.get('recipient')
                )
                
                return {
                    "message_id": f"websocket_{uuid.uuid4().hex[:8]}",
                    "details": {
                        "provider": "websocket",
                        "recipient": content.get('recipient'),
                        "success_count": result.get('success_count', 0)
                    }
                }
            else:
                raise NotificationSendError("WebSocket service not available")
                    
        except Exception as e:
            raise NotificationSendError(f"WebSocket send failed: {str(e)}")
    
    async def _send_system(
        self,
        channel: NotificationChannel,
        notification: Notification,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送系统消息
        
        Args:
            channel: 系统渠道
            notification: 通知对象
            content: 发送内容
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        try:
            # 系统消息通常只是记录到数据库或日志
            logger.info(f"System notification sent: {content['subject']} to {content['recipient']}")
            
            return {
                "message_id": f"system_{uuid.uuid4().hex[:8]}",
                "details": {
                    "provider": "system",
                    "recipient": content['recipient']
                }
            }
                    
        except Exception as e:
            raise NotificationSendError(f"System send failed: {str(e)}")
    
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
            update_data["total_sent"] = NotificationChannel.total_sent + 1
            update_data["last_sent_at"] = datetime.utcnow()
        else:
            update_data["total_failed"] = NotificationChannel.total_failed + 1
            if error_message:
                update_data["last_error_message"] = error_message
                update_data["last_error_at"] = datetime.utcnow()
        
        await db.execute(
            update(NotificationChannel)
            .where(NotificationChannel.id == channel_id)
            .values(**update_data)
        )
        await db.commit()