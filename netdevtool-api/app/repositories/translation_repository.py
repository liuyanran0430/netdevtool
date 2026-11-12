"""翻译任务仓储：translation_tasks 表读写唯一入口。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TranslationTask


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

    def update(self, task: TranslationTask) -> TranslationTask:
        self.db.commit()
        self.db.refresh(task)
        return task
