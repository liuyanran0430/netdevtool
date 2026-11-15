"""ORM 模型：表结构、约束、索引。

新增模型时继承 Base，并在 app/repositories 中提供对应仓储。
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "Base",
    "Device",
    "DeviceType",
    "KnowledgeGap",
    "KnowledgeGapKind",
    "KnowledgeGapStatus",
    "LlmRun",
    "LlmRunStatus",
    "ReviewDecision",
    "ReviewDecisionAction",
    "ReviewItem",
    "SupplementCandidate",
    "SupplementCandidateStatus",
    "TranslationTask",
    "TranslationTaskStatus",
    "User",
    "UserStatus",
]


class DeviceType(str, Enum):
    """设备类型。"""

    switch = "switch"
    firewall = "firewall"


class Device(Base):
    """设备表。"""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="设备厂商")
    vendor_en: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="设备厂商英文名（key，用于查找配置文件）"
    )
    model: Mapped[str] = mapped_column(String(128), nullable=False, comment="设备型号")
    device_type: Mapped[DeviceType] = mapped_column(
        SAEnum(DeviceType, name="device_type", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        index=True,
        comment="设备类型：switch=交换机, firewall=防火墙",
    )


class TranslationTaskStatus(str, Enum):
    """翻译任务状态。"""

    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class TranslationTask(Base):
    """翻译任务表，任务状态的唯一事实来源。"""

    __tablename__ = "translation_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True, comment="创建人 users.id，存量任务为空"
    )
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[TranslationTaskStatus] = mapped_column(
        SAEnum(
            TranslationTaskStatus,
            name="translation_task_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=TranslationTaskStatus.pending,
        server_default=TranslationTaskStatus.pending.value,
        index=True,
    )
    source_vendor: Mapped[str] = mapped_column(String(64), nullable=False)
    source_model: Mapped[str] = mapped_column(String(128), nullable=False)
    target_vendor: Mapped[str] = mapped_column(String(64), nullable=False)
    target_model: Mapped[str] = mapped_column(String(128), nullable=False)
    # 大字段延迟加载：前端每秒轮询状态时无需传输源配置与结果 JSON
    source_text: Mapped[str] = mapped_column(MEDIUMTEXT, nullable=False, deferred=True)
    result_json: Mapped[str | None] = mapped_column(MEDIUMTEXT, nullable=True, deferred=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class UserStatus(str, Enum):
    """用户账号状态。"""

    enabled = "enabled"
    disabled = "disabled"


class User(Base):
    """用户表。

    仅存储登录所需的账号信息；密码只保存 bcrypt 哈希，不落明文。
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, comment="登录用户名"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="bcrypt 密码哈希，不存明文"
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(
            UserStatus,
            name="user_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=UserStatus.enabled,
        server_default=UserStatus.enabled.value,
        index=True,
        comment="账号状态：enabled=启用, disabled=禁用",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )


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
    llm_model: Mapped[str] = mapped_column(String(128), nullable=False, comment="调用的大模型标识")
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False, comment="提示词版本")
    request_json: Mapped[str | None] = mapped_column(
        MEDIUMTEXT, nullable=True, comment="组装后的请求体，便于回放"
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


class LlmRunStatus(str, Enum):
    """大模型调用状态。"""

    success = "success"
    failed = "failed"


class LlmRun(Base):
    """大模型调用记录表：每次调用留痕，用于计费与成本核算。"""

    __tablename__ = "llm_runs"
    __table_args__ = (
        Index("ix_llm_runs_biz", "biz_type", "biz_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False, comment="调用的模型标识")
    method: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="调用方法或用途，如 chat_json"
    )
    prompt_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0", comment="输入消耗 token 数"
    )
    completion_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0", comment="输出消耗 token 数"
    )
    total_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0", comment="合计消耗 token 数"
    )
    latency_ms: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0", comment="调用耗时（毫秒）"
    )
    status: Mapped[LlmRunStatus] = mapped_column(
        SAEnum(
            LlmRunStatus,
            name="llm_run_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        index=True,
        comment="调用结果：success=成功, failed=失败",
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, comment="失败原因"
    )
    request_id: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, comment="本次 LLM 调用 ID（UUID）"
    )
    biz_type: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="关联对象类型：knowledge_gap",
    )
    biz_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="关联对象主键，与 biz_type 组合使用"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


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
