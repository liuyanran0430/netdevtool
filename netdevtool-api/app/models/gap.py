from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.device import DeviceType

__all__ = [
    "KnowledgeGap",
    "KnowledgeGapKind",
    "KnowledgeGapStatus",
    "SupplementCandidate",
    "SupplementCandidateStatus",
]


class KnowledgeGapKind(str, Enum):
    """知识缺口类型。"""

    unknown_source = "unknown_source"
    missing_target_impl = "missing_target_impl"


class KnowledgeGapStatus(str, Enum):
    """知识缺口处理状态。"""

    open = "open"
    candidate_generated = "candidate_generated"
    resolved = "resolved"
    ignored = "ignored"


class KnowledgeGap(Base):
    """知识缺口表：翻译未命中命令按设备与模板聚合，作为 AI 兜底的输入。"""

    __tablename__ = "knowledge_gaps"
    __table_args__ = (
        UniqueConstraint(
            "vendor",
            "device_type",
            "product",
            "os",
            "target_vendor",
            "target_device_type",
            "command_template",
            "kind",
            name="uq_knowledge_gaps_scope",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor: Mapped[str] = mapped_column(String(64), nullable=False, comment="设备厂商英文名")
    device_type: Mapped[DeviceType] = mapped_column(
        SAEnum(DeviceType, name="device_type", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        comment="设备类型：switch=交换机, firewall=防火墙",
    )
    product: Mapped[str] = mapped_column(String(128), nullable=False, comment="设备型号")
    os: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="设备版本，未知时为空")
    target_vendor: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="",
        server_default="",
        comment="目标厂商英文名；源侧未识别时为空",
    )
    target_device_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="",
        server_default="",
        comment="目标设备类型；源侧未识别时为空",
    )
    view: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="命令所在配置视图")
    command_template: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="参数归一化后的命令模板"
    )
    raw_sample: Mapped[str | None] = mapped_column(
        MEDIUMTEXT, nullable=True, comment="首次出现时的原始命令行样例"
    )
    occurrences: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=1, server_default="1", comment="累计出现次数"
    )
    kind: Mapped[KnowledgeGapKind] = mapped_column(
        SAEnum(
            KnowledgeGapKind,
            name="knowledge_gap_kind",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        comment="缺口类型：unknown_source=源侧未识别, missing_target_impl=目标侧无实现",
    )
    status: Mapped[KnowledgeGapStatus] = mapped_column(
        SAEnum(
            KnowledgeGapStatus,
            name="knowledge_gap_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=KnowledgeGapStatus.open,
        server_default=KnowledgeGapStatus.open.value,
        index=True,
        comment="处理状态：open=待处理, candidate_generated=已生成候选, resolved=已沉淀, ignored=已忽略",
    )
    request_ids: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, comment="出现该缺口的翻译任务 request_id 列表"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="最近一次出现时间",
    )


class SupplementCandidateStatus(str, Enum):
    """补充知识库候选状态。"""

    pending = "pending"
    passed = "passed"
    failed = "failed"
    accepted = "accepted"
    rejected = "rejected"


class SupplementCandidate(Base):
    """补充知识库候选表：LLM 调用与校验留痕，可审计可回放。"""

    __tablename__ = "supplement_candidates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    gap_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("knowledge_gaps.id"), nullable=False, index=True, comment="knowledge_gaps.id"
    )
    request_json: Mapped[str | None] = mapped_column(
        MEDIUMTEXT, nullable=True, comment="user 提示词与检索上下文，便于回放"
    )
    response_json: Mapped[str | None] = mapped_column(
        MEDIUMTEXT, nullable=True, comment="模型原始返回内容"
    )
    validation_json: Mapped[str | None] = mapped_column(
        MEDIUMTEXT, nullable=True, comment="自动校验结果（模板回放 / 参数 / 渲染 / 视图）"
    )
    status: Mapped[SupplementCandidateStatus] = mapped_column(
        SAEnum(
            SupplementCandidateStatus,
            name="supplement_candidate_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=SupplementCandidateStatus.pending,
        server_default=SupplementCandidateStatus.pending.value,
        index=True,
        comment="状态：pending=待确认, passed=校验通过, failed=校验失败, accepted=已采纳, rejected=已拒绝",
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="确认人 users.id"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="确认时间")
