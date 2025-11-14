import os
import json
import asyncio
import aio_pika
from .manager import NotificationManager, NotificationMessage
from .templates import render

async def consume():
    url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    connection = await aio_pika.connect_robust(url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("exchange.notification", aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue("queue.notification_service", durable=True)
        await queue.bind(exchange, routing_key="order.*")
        await queue.bind(exchange, routing_key="risk.*")
        await queue.bind(exchange, routing_key="news.*")
        manager = NotificationManager()
        async with queue.iterator() as q:
            async for message in q:
                async with message.process():
                    try:
                        payload = json.loads(message.body.decode())
                    except Exception:
                        payload = {}
                    title, content = render(message.routing_key, payload)
                    msg = NotificationMessage(title, content, "info", payload)
                    await manager.send(msg)