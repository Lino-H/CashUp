"""
Celery应用初始化
函数集注释：
- celery_app: Celery 应用实例，按单节点/分布式自动选择 Broker/Backend
"""

from celery import Celery
import os
from config.settings import settings

def _resolve_broker_and_backend():
    # 优先使用显式设置
    broker = settings.CELERY_BROKER_URL
    backend = settings.CELERY_RESULT_BACKEND
    if broker is None:
        if settings.SINGLE_NODE:
            broker = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        else:
            broker = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")
    if backend is None:
        # 单节点默认使用 Redis 作为结果后端
        backend = os.getenv("REDIS_URL", "redis://localhost:6379/1")
    return broker, backend

broker_url, result_backend = _resolve_broker_and_backend()

celery_app = Celery("cashup_core")
celery_app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_default_retry_delay=30,
    broker_transport_options={"visibility_timeout": 3600},
    task_routes={
        "tasks.rss.*": {"queue": "rss"},
        "tasks.notification.*": {"queue": "notification"},
        "tasks.market.*": {"queue": "market"},
    },
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    beat_schedule={
        "scheduler-heartbeat": {
            "task": "tasks.scheduler.heartbeat",
            "schedule": 30.0,
        },
    },
    include=[
        "tasks.scheduler",
        "tasks.market_collector",
        "tasks.rss",
    ],
)