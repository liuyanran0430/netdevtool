"""审核条目仓储：review_items 表读写唯一入口。"""

from sqlalchemy import and_, delete, func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from app.models import ReviewDecision, ReviewDecisionAction, ReviewItem

# 条目与处置按「用户 + 稳定命令标识」关联
DECISION_JOIN = and_(
    ReviewDecision.user_id == ReviewItem.user_id,
    ReviewDecision.item_key == ReviewItem.item_key,
)

# 物化覆盖时同步刷新的字段；user_id / item_key 为唯一键不更新
UPSERT_COLUMNS = (
    "request_id",
    "line_index",
    "source_no",
    "source_vendor",
    "source_model",
    "target_vendor",
    "target_model",
    "view",
    "source_text",
    "target_text",
    "original_tone",
    "codes",
    "code_csv",
    "severity",
    "severity_rank",
    "code_priority",
    "message",
    "gap_id",
    "created_at",
)


class ReviewItemRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_many(self, rows: list[dict]) -> None:
        """按 (user_id, item_key) 批量覆盖写入，单条 SQL 完成。"""
        if not rows:
            return
        stmt = insert(ReviewItem).values(rows)
        stmt = stmt.on_duplicate_key_update(
            **{column: stmt.inserted[column] for column in UPSERT_COLUMNS}
        )
        self.db.execute(stmt)
        self.db.commit()

    def delete_all(self) -> None:
        """重建物化条目时清空（仅用于一次性回填）。"""
        self.db.execute(delete(ReviewItem))
        self.db.commit()

    def count(
        self,
        *,
        user_id: int,
        status: str = "all",
        target_vendor: str | None = None,
        target_model: str | None = None,
        code: str | None = None,
    ) -> int:
        conditions = self._conditions(
            user_id=user_id,
            status=status,
            target_vendor=target_vendor,
            target_model=target_model,
            code=code,
        )
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(ReviewItem)
                .outerjoin(ReviewDecision, DECISION_JOIN)
                .where(*conditions)
            )
            or 0
        )

    def list_page(
        self,
        *,
        user_id: int,
        status: str,
        target_vendor: str | None,
        target_model: str | None,
        code: str | None,
        offset: int,
        limit: int,
    ) -> list[tuple[ReviewItem, ReviewDecision | None]]:
        conditions = self._conditions(
            user_id=user_id,
            status=status,
            target_vendor=target_vendor,
            target_model=target_model,
            code=code,
        )
        stmt = (
            select(ReviewItem, ReviewDecision)
            .outerjoin(ReviewDecision, DECISION_JOIN)
            .where(*conditions)
            .order_by(
                ReviewItem.severity_rank,
                ReviewItem.code_priority,
                func.coalesce(ReviewItem.source_no, 0),
                ReviewItem.id,
            )
            .offset(offset)
            .limit(limit)
        )
        return [(row[0], row[1]) for row in self.db.execute(stmt).all()]

    def stats(self, user_id: int) -> dict[ReviewDecisionAction, int]:
        """按处置动作统计全部条目，未处置的条目不在结果中。"""
        stmt = (
            select(ReviewDecision.action, func.count())
            .select_from(ReviewItem)
            .outerjoin(ReviewDecision, DECISION_JOIN)
            .where(ReviewItem.user_id == user_id)
            .group_by(ReviewDecision.action)
        )
        result: dict[ReviewDecisionAction, int] = {}
        for action, count in self.db.execute(stmt).all():
            if action is not None:
                result[action] = int(count)
        return result

    def list_target_options(self, user_id: int) -> list[tuple[str, str]]:
        stmt = (
            select(ReviewItem.target_vendor, ReviewItem.target_model)
            .where(ReviewItem.user_id == user_id)
            .distinct()
            .order_by(ReviewItem.target_vendor, ReviewItem.target_model)
        )
        return [(row[0], row[1]) for row in self.db.execute(stmt).all()]

    def list_code_options(self, user_id: int) -> list[str]:
        stmt = select(ReviewItem.code_csv).where(ReviewItem.user_id == user_id).distinct()
        codes: set[str] = set()
        for (code_csv,) in self.db.execute(stmt).all():
            codes.update(part for part in (code_csv or "").split(",") if part)
        return sorted(codes)

    def list_decisions_with_items(
        self, user_id: int
    ) -> list[tuple[ReviewDecision, ReviewItem]]:
        """当前用户的全部处置及其来源条目，用于生成检查点快照。"""
        stmt = (
            select(ReviewDecision, ReviewItem)
            .join(ReviewItem, DECISION_JOIN)
            .where(ReviewDecision.user_id == user_id)
            .order_by(ReviewItem.request_id, ReviewItem.line_index)
        )
        return [(row[0], row[1]) for row in self.db.execute(stmt).all()]

    def _conditions(
        self,
        *,
        user_id: int,
        status: str,
        target_vendor: str | None,
        target_model: str | None,
        code: str | None,
    ) -> list:
        conditions = [ReviewItem.user_id == user_id]
        if status == "pending":
            conditions.append(ReviewDecision.id.is_(None))
        elif status == "accepted":
            conditions.append(
                ReviewDecision.action.in_(
                    [ReviewDecisionAction.accept, ReviewDecisionAction.edit]
                )
            )
        elif status == "skipped":
            conditions.append(ReviewDecision.action == ReviewDecisionAction.skip)
        if target_vendor:
            conditions.append(ReviewItem.target_vendor == target_vendor)
        if target_model:
            conditions.append(ReviewItem.target_model == target_model)
        if code:
            conditions.append(func.find_in_set(code, ReviewItem.code_csv) > 0)
        return conditions
