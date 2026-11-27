"""审核条目仓储：review_items 表读写唯一入口。

写入按 (user_id, item_hash) 覆盖；status 不在覆盖列中，
已处置条目的状态以 review_decisions 为唯一事实来源。
"""

from sqlalchemy import case, func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session, aliased

from app.models import Device, ReviewItem, ReviewItemType, ReviewStatus

UPSERT_COLUMNS = (
    "request_id",
    "src_dev_id",
    "dest_dev_id",
    "source_text",
    "original_tone",
    "type",
    "entities_id",
    "created_at",
)

# error 优先于 warn 展示
_TONE_ORDER = case(
    (ReviewItem.original_tone == "error", 0),
    (ReviewItem.original_tone == "warn", 1),
    else_=2,
)


class ReviewItemRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_many(self, rows: list[dict]) -> None:
        """按 (user_id, item_hash) 批量覆盖写入，单条 SQL 完成。"""
        if not rows:
            return
        stmt = insert(ReviewItem).values(rows)
        stmt = stmt.on_duplicate_key_update(
            **{column: stmt.inserted[column] for column in UPSERT_COLUMNS}
        )
        self.db.execute(stmt)
        self.db.commit()

    # ---------------------------- 审核页查询 ----------------------------

    def _conditions(
        self,
        *,
        user_id: int,
        dest_vendor: str | None,
        dest_model: str | None,
        item_type: str | None,
    ) -> list:
        source_device = aliased(Device)
        target_device = aliased(Device)
        conditions = [
            ReviewItem.user_id == user_id,
            ReviewItem.status == ReviewStatus.pending,
        ]
        if dest_vendor:
            conditions.append(ReviewItem.dest_dev_id == target_device.id)
            conditions.append(target_device.vendor == dest_vendor)
        if dest_model:
            conditions.append(ReviewItem.dest_dev_id == target_device.id)
            conditions.append(target_device.model == dest_model)
        if item_type:
            conditions.append(ReviewItem.type == ReviewItemType(item_type))
        return conditions

    def count(
        self,
        *,
        user_id: int,
        dest_vendor: str | None = None,
        dest_model: str | None = None,
        item_type: str | None = None,
    ) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(ReviewItem)
                .where(*self._conditions(
                    user_id=user_id,
                    dest_vendor=dest_vendor,
                    dest_model=dest_model,
                    item_type=item_type,
                ))
            )
            or 0
        )

    def list_page(
        self,
        *,
        user_id: int,
        dest_vendor: str | None,
        dest_model: str | None,
        item_type: str | None,
        offset: int,
        limit: int,
    ) -> list[tuple[ReviewItem, str, str, str, str]]:
        """分页读取待审条目，附带源/目标设备厂商与型号。"""
        source_device = aliased(Device)
        target_device = aliased(Device)
        stmt = (
            select(
                ReviewItem,
                func.coalesce(source_device.vendor, ""),
                func.coalesce(source_device.model, ""),
                func.coalesce(target_device.vendor, ""),
                func.coalesce(target_device.model, ""),
            )
            .outerjoin(source_device, ReviewItem.src_dev_id == source_device.id)
            .outerjoin(target_device, ReviewItem.dest_dev_id == target_device.id)
            .where(*self._conditions(
                user_id=user_id,
                dest_vendor=dest_vendor,
                dest_model=dest_model,
                item_type=item_type,
            ))
            .order_by(_TONE_ORDER, ReviewItem.type, ReviewItem.id)
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.execute(stmt).all())

    def stats(self, user_id: int) -> dict[ReviewStatus, int]:
        """按处置状态统计全部条目。"""
        stmt = (
            select(ReviewItem.status, func.count())
            .where(ReviewItem.user_id == user_id)
            .group_by(ReviewItem.status)
        )
        return {status: int(count) for status, count in self.db.execute(stmt).all()}

    def list_target_options(self, user_id: int) -> list[tuple[str, str]]:
        """目的设备筛选项（待审条目涉及的目标设备）。"""
        target_device = aliased(Device)
        stmt = (
            select(target_device.vendor, target_device.model)
            .select_from(ReviewItem)
            .outerjoin(target_device, ReviewItem.dest_dev_id == target_device.id)
            .where(
                ReviewItem.user_id == user_id,
                ReviewItem.status == ReviewStatus.pending,
                target_device.id.is_not(None),
            )
            .distinct()
            .order_by(target_device.vendor, target_device.model)
        )
        return [(row[0], row[1]) for row in self.db.execute(stmt).all()]

    def list_type_options(self, user_id: int) -> list[str]:
        stmt = (
            select(ReviewItem.type)
            .where(
                ReviewItem.user_id == user_id,
                ReviewItem.status == ReviewStatus.pending,
            )
            .distinct()
            .order_by(ReviewItem.type)
        )
        return [row[0].value for row in self.db.execute(stmt).all()]
