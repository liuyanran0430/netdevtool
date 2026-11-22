from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "ReviewDecision",
    "ReviewDecisionAction",
    "ReviewItem",
]


class ReviewDecisionAction(str, Enum):
    """审核处置动作。"""

    accept = "accept"
    edit = "edit"
    skip = "skip"


class ReviewDecision(Base):
    """审核处置表：审核状态的唯一事实来源。

    以「用户 + 稳定命令标识」为唯一键，跨翻译任务共享同一条处置结果；
    `item_key` 由服务层按源/目标厂商型号与归一化命令生成。
    """

    __tablename__ = "review_decisions"
    __table_args__ = (
        UniqueConstraint("user_id", "item_key", name="uq_review_decisions_user_item"),
        Index("ix_review_decisions_candidate", "candidate_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="users.id")
    item_key: Mapped[str] = mapped_column(
        String(40), nullable=False, comment="稳定命令标识 SHA1"
    )
    action: Mapped[ReviewDecisionAction] = mapped_column(
        SAEnum(
            ReviewDecisionAction,
            name="review_decision_action",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        comment="处置动作：accept=采纳, edit=修改后采纳, skip=拒绝",
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

    以「用户 + 稳定命令标识」为唯一键，同一命令在多次翻译中出现时覆盖为最近一次；
    处置状态存放在 review_decisions，与条目按 (user_id, item_key) 关联。
    """

    __tablename__ = "review_items"
    __table_args__ = (
        UniqueConstraint("user_id", "item_key", name="uq_review_items_user_item"),
        Index(
            "ix_review_items_user_sort",
            "user_id",
            "severity_rank",
            "code_priority",
            "source_no",
        ),
        Index("ix_review_items_target", "user_id", "target_vendor", "target_model"),
        Index("ix_review_items_gap", "gap_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="任务归属 users.id")
    item_key: Mapped[str] = mapped_column(
        String(40), nullable=False, comment="稳定命令标识 SHA1"
    )
    request_id: Mapped[str] = mapped_column(
        String(36), nullable=False, comment="来源翻译任务，仅作溯源"
    )
    line_index: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="结果行序号（从 1 开始），用于检查点回放"
    )
    source_no: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="命中的源配置行号"
    )
    source_vendor: Mapped[str] = mapped_column(String(64), nullable=False)
    source_model: Mapped[str] = mapped_column(String(128), nullable=False)
    target_vendor: Mapped[str] = mapped_column(String(64), nullable=False)
    target_model: Mapped[str] = mapped_column(String(128), nullable=False)
    view: Mapped[str] = mapped_column(String(255), nullable=False, comment="源命令所在视图")
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_text: Mapped[str] = mapped_column(Text, nullable=False)
    original_tone: Mapped[str] = mapped_column(String(16), nullable=False)
    codes: Mapped[list] = mapped_column(JSON, nullable=False, comment="告警码列表")
    code_csv: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", server_default="", comment="告警码逗号串，用于筛选"
    )
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    severity_rank: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, server_default="1"
    )
    code_priority: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=2, server_default="2"
    )
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="告警说明拼接")
    gap_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="关联的知识缺口 id，供生成候选"
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
