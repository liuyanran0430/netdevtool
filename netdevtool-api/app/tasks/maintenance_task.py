"""维护任务：清理超过保留期的 AI 调用记录。"""

from datetime import datetime, timedelta

from sqlalchemy import delete

from app.config import settings
from app.database import SessionLocal
from app.models import AiRun
from app.tasks.celery_app import celery_app


def cleanup_ai_runs(days: int | None = None) -> int:
    """删除 created_at 早于保留期的 AiRun 记录，返回删除条数。"""
    retention = max(1, int(days or settings.AI_RUN_RETENTION_DAYS))
    cutoff = datetime.now() - timedelta(days=retention)
    with SessionLocal() as db:
        result = db.execute(delete(AiRun).where(AiRun.created_at < cutoff))
        db.commit()
        return int(result.rowcount or 0)


@celery_app.task(name="maintenance.cleanup_ai_runs")
def cleanup_ai_runs_task() -> int:
    deleted = cleanup_ai_runs()
    print(f"[maintenance] ai_runs cleaned: {deleted}")
    return deleted
