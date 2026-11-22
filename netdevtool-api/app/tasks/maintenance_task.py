"""维护任务：清理超过保留期的 AI 调用记录。"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import delete

from app.config import settings
from app.database import SessionLocal
from app.logging_config import logging_context
from app.models import AiRun
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def cleanup_ai_runs(days: int | None = None) -> int:
    """删除 created_at 早于保留期的 AiRun 记录，返回删除条数。"""
    retention = max(1, int(days or settings.AI_RUN_RETENTION_DAYS))
    cutoff = datetime.now() - timedelta(days=retention)
    with SessionLocal() as db:
        result = db.execute(delete(AiRun).where(AiRun.created_at < cutoff))
        db.commit()
        return int(result.rowcount or 0)


@celery_app.task(bind=True, name="maintenance.cleanup_ai_runs")
def cleanup_ai_runs_task(self) -> int:
    with logging_context(task_id=self.request.id):
        deleted = cleanup_ai_runs()
        logger.info(
            "event=ai_runs_cleanup_completed deleted=%d retention_days=%d",
            deleted,
            settings.AI_RUN_RETENTION_DAYS,
        )
        return deleted
