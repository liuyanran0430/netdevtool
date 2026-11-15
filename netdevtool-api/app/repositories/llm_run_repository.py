"""大模型调用记录仓储：llm_runs 表读写唯一入口。"""

from sqlalchemy.orm import Session

from app.models import LlmRun


class LlmRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, run: LlmRun) -> LlmRun:
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
