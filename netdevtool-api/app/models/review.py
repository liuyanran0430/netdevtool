from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "ReviewDecision",
    "ReviewItem",
    "ReviewItemType",
    "ReviewStatus",
]


class ReviewStatus(str, Enum):
    """审核处置状态。pending未处理、accepted已接受、rejected已拒绝。"""

    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class ReviewItemType(str, Enum):
    """审核条目类型。unknown_source源侧未识别、missing_target_impl目标侧无实现、unverified_impl源或目标侧未验证。"""

    unknown_source = "unknown_source"
    missing_target_impl = "missing_target_impl"
    unverified_impl = "unverified_impl"


class ReviewDecision(Base):
    """审核处置表：审核状态的唯一事实来源。

    以「用户 + 稳定段标识」为唯一键，跨翻译任务共享同一条处置结果；
    `item_hash` 由服务层按 src_dev_id + dest_dev_id + source_text 生成，
    与 review_items.item_hash 同值关联。
    """

    __tablename__ = "review_decisions"
    __table_args__ = (
        UniqueConstraint("user_id", "item_hash", name="uq_review_decisions_user_hash"),
        Index("ix_review_decisions_candidate", "candidate_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="users.id")
    item_hash: Mapped[str] = mapped_column(
        String(40), nullable=False, comment="稳定段标识（src_dev_id+dest_dev_id+source_text 哈希）"
    )
    action: Mapped[ReviewStatus] = mapped_column(
        SAEnum(
            ReviewStatus,
            name="review_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        comment="处置状态：pending=未处理, accepted=已接受, rejected=已拒绝",
    )
    decided_text: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="修改后采纳的命令文本"
    )
    candidate_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="采纳时沉淀的 AI 候选 id"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ReviewItem(Base):
    """审核条目表：翻译成功时物化，审核页直接分页读取。

    以「用户 + 稳定段标识」为唯一键实现跨任务去重，同一命令段在多次翻译中
    出现时覆盖为最近一次；处置状态存放在 review_decisions，与条目按
    (user_id, item_hash) 关联。`item_hash` 由服务层按
    src_dev_id + dest_dev_id + source_text（多行拼接）哈希生成。
    """

    __tablename__ = "review_items"
    __table_args__ = (
        UniqueConstraint("user_id", "item_hash", name="uq_review_items_user_hash"),
        Index(
            "ix_review_items_user_sort",
            "user_id",
        ),
        Index("ix_review_items_target", "user_id", "dest_dev_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="任务归属 users.id")
    item_hash: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        comment="稳定段标识（src_dev_id+dest_dev_id+source_text 哈希，去重键）",
    )
    request_id: Mapped[str] = mapped_column(
        String(36), nullable=False, comment="来源翻译任务，仅作溯源"
    )
    src_dev_id: Mapped[int | None] = mapped_column(
        # devices.id 为 BIGINT UNSIGNED，外键要求两侧类型与符号一致
        BIGINT(unsigned=True),
        ForeignKey("devices.id"),
        nullable=True,
        comment="源设备档案 devices.id；设备档案缺失时为空",
    )
    dest_dev_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("devices.id"),
        nullable=True,
        comment="目标设备档案 devices.id；设备档案缺失时为空",
    )
    source_text: Mapped[list] = mapped_column(
        JSON, nullable=False, comment="命中的源配置行文本列表"
    )
    original_tone: Mapped[str] = mapped_column(String(16), nullable=False)
    type: Mapped[ReviewItemType] = mapped_column(
        SAEnum(
            ReviewItemType,
            name="review_item_type",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        comment="条目类型：unknown_source=源侧未识别, missing_target_impl=目标侧无实现, unverified_impl=源或目标侧未验证",
    )
    status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(
            ReviewStatus,
            name="review_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=ReviewStatus.pending,
        server_default=ReviewStatus.pending.value,
        index=True,
        comment="处置状态：pending=未处理, accepted=已接受, rejected=已拒绝",
    )
    entities_id: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="命中的源厂商实体 id 列表（源侧 yaml 实体段）；未识别命令段为空",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="来源翻译任务创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
