"""翻译任务仓储：translation_tasks 表读写唯一入口。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TranslationTask, TranslationTaskStatus


class TranslationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, task: TranslationTask) -> TranslationTask:
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_by_request_id(self, request_id: str) -> TranslationTask | None:
        stmt = (
            select(TranslationTask)
            .where(TranslationTask.request_id == request_id)
            .execution_options(populate_existing=True)
        )
        return self.db.scalars(stmt).one_or_none()

    def list_recent(self, user_id: int, limit: int = 20) -> list[dict]:
        """指定用户最近的翻译任务，仅取元数据字段（不加载 source_text/result_json）。"""
        stmt = (
            select(
                TranslationTask.request_id,
                TranslationTask.status,
                TranslationTask.source_vendor,
                TranslationTask.source_model,
                TranslationTask.target_vendor,
                TranslationTask.target_model,
                TranslationTask.created_at,
                TranslationTask.finished_at,
            )
            .where(TranslationTask.user_id == user_id)
            .order_by(TranslationTask.created_at.desc())
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()
        return [row._mapping for row in rows]

    def list_all_succeeded(self) -> list[TranslationTask]:
        """全部已成功、带结果的任务，按创建时间升序，仅用于审核条目一次性回填。"""
        stmt = (
            select(TranslationTask)
            .where(
                TranslationTask.status == TranslationTaskStatus.succeeded,
                TranslationTask.result_json.is_not(None),
            )
            .order_by(TranslationTask.created_at)
        )
        return list(self.db.scalars(stmt))

    def update(self, task: TranslationTask) -> TranslationTask:
        self.db.commit()
        self.db.refresh(task)
        return task
