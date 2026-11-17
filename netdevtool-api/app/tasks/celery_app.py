"""Celery 应用：Redis 仅作 broker，不使用结果后端。"""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "netdevtool",
    broker=settings.REDIS_URL,
    include=[
        "app.tasks.translation_task",
        "app.tasks.knowledge_index_task",
    ],
)
celery_app.conf.update(
    task_ignore_result=True,
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
)

# 支持 celery -A app.tasks.celery_app worker 启动方式。
app = celery_app
