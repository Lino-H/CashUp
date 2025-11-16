import os
import json
import asyncio
import aio_pika

async def publish_event(routing_key: str, data: dict):
    url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    connection = await aio_pika.connect_robust(url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("exchange.notification", aio_pika.ExchangeType.TOPIC, durable=True)
        body = json.dumps(data).encode()
        message = aio_pika.Message(body)
        await exchange.publish(message, routing_key=routing_key)
    return True