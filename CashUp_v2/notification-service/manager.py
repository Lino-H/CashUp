import os
import json
import aiohttp
import smtplib
from email.mime.text import MIMEText

class NotificationMessage:
    def __init__(self, title: str, content: str, level: str = "info", metadata: dict | None = None):
        self.title = title
        self.content = content
        self.level = level
        self.metadata = metadata or {}

class TelegramChannel:
    async def send(self, message: NotificationMessage) -> bool:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            return False
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        text = f"{message.title}\n\n{message.content}"
        payload = {"chat_id": chat_id, "text": text}
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=payload) as r:
                return r.status == 200

class WebhookChannel:
    async def send(self, message: NotificationMessage) -> bool:
        url = os.getenv("WEBHOOK_URL", "")
        if not url:
            return False
        payload = {"title": message.title, "content": message.content, "level": message.level, "metadata": message.metadata}
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=payload) as r:
                return r.status in (200, 201)

class EmailChannel:
    async def send(self, message: NotificationMessage) -> bool:
        host = os.getenv("SMTP_HOST", "")
        port = int(os.getenv("SMTP_PORT", "587"))
        user = os.getenv("SMTP_USERNAME", "")
        pwd = os.getenv("SMTP_PASSWORD", "")
        from_addr = os.getenv("SMTP_FROM", "")
        to_addr = os.getenv("SMTP_TO", "")
        if not host or not user or not pwd or not from_addr or not to_addr:
            return False
        msg = MIMEText(message.content, "plain", "utf-8")
        msg["Subject"] = message.title
        msg["From"] = from_addr
        msg["To"] = to_addr
        try:
            srv = smtplib.SMTP(host, port)
            srv.starttls()
            srv.login(user, pwd)
            srv.send_message(msg)
            srv.quit()
            return True
        except Exception:
            return False

class NotificationManager:
    def __init__(self):
        self.channels = {
            "telegram": TelegramChannel(),
            "webhook": WebhookChannel(),
            "email": EmailChannel(),
        }

    async def send(self, message: NotificationMessage, channels: list[str] | None = None) -> dict:
        used = channels or list(self.channels.keys())
        results = {}
        for name in used:
            ch = self.channels.get(name)
            if not ch:
                continue
            ok = await ch.send(message)
            results[name] = ok
        return results