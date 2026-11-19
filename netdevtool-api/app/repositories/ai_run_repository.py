"""AI 调用记录仓储：ai_runs 表读写唯一入口。"""

from sqlalchemy.orm import Session

from app.models import AiRun


class AiRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, run: AiRun) -> AiRun:
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
