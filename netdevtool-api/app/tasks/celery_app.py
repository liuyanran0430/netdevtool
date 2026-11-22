"""Celery 应用：Redis 仅作 broker，不使用结果后端。"""

from celery import Celery
from celery.schedules import crontab
from celery.signals import after_setup_logger, after_setup_task_logger

from app.config import settings
from app.logging_config import celery_component, configure_logging

celery_app = Celery(
    "netdevtool",
    broker=settings.REDIS_URL,
    include=[
        "app.tasks.translation_task",
        "app.tasks.knowledge_index_task",
        "app.tasks.maintenance_task",
    ],
)
celery_app.conf.update(
    task_ignore_result=True,
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
    timezone="Asia/Shanghai",
    beat_schedule={
        "cleanup-ai-runs-daily": {
            "task": "maintenance.cleanup_ai_runs",
            "schedule": crontab(hour=3, minute=30),
        },
    },
)


@after_setup_logger.connect
def configure_celery_logging(logger, **kwargs) -> None:
    """Worker/Beat 使用统一 root handler，不由 Celery 再次接管。"""
    configure_logging(celery_component())


@after_setup_task_logger.connect
def propagate_task_logging(logger, **kwargs) -> None:
    """任务日志只向 root 传播，避免 Celery 与统一配置各输出一次。"""
    logger.handlers.clear()
    logger.propagate = True


# 支持 celery -A app.tasks.celery_app worker 启动方式。
app = celery_app
