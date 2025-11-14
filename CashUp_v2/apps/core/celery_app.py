"""
Celery应用初始化
"""

from celery import Celery
import os

broker_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
result_backend = os.getenv("REDIS_URL", "redis://redis:6379/1")

celery_app = Celery("cashup_core")
celery_app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    task_routes={
        "tasks.rss.*": {"queue": "rss"},
        "tasks.notification.*": {"queue": "notification"},
    },
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    beat_schedule={
        "rss-fetch": {
            "task": "tasks.rss.fetch_feeds",
            "schedule": 300.0,
        },
        "rss-analyze": {
            "task": "tasks.rss.analyze_sentiment",
            "schedule": 600.0,
        },
        "rss-correlation": {
            "task": "tasks.rss.compute_correlation",
            "schedule": 900.0,
        },
        "trading-sync": {
            "task": "tasks.trading.sync",
            "schedule": 60.0,
        },
    },
)