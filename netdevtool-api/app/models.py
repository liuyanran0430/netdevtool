"""ORM 模型：表结构、约束、索引。

新增模型时继承 Base，并在 app/repositories 中提供对应仓储。
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.mysql import BIGINT, MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "AiRun",
    "AiRunKind",
    "AiRunStatus",
    "Base",
    "ChatMessage",
    "ChatMessageCitation",
    "ChatMessageFeedback",
    "ChatMessageRole",
    "ChatMessageStatus",
    "ChatQuestionMode",
    "ChatSession",
    "Device",
    "DeviceType",
    "KnowledgeBase",
    "KnowledgeDocument",
    "KnowledgeDocumentFileType",
    "KnowledgeDocumentStatus",
    "KnowledgeDocumentStage",
    "KnowledgeGap",
    "KnowledgeGapKind",
    "KnowledgeGapStatus",
    "KnowledgeBaseChunkingMode",
    "KnowledgeBaseIndexingMode",
    "KnowledgeBaseRetrievalMode",
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
    manual_path: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="设备手册相对路径，相对项目 knowledges 目录"
    )
    device_type: Mapped[DeviceType] = mapped_column(
        SAEnum(DeviceType, name="device_type", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        index=True,
        comment="设备类型：switch=交换机, firewall=防火墙",
    )


class KnowledgeBaseChunkingMode(str, Enum):
    """知识库分段模式。"""

    general = "general"
    parent_child = "parent-child"
    qa = "qa"


class KnowledgeBaseIndexingMode(str, Enum):
    """知识库索引模式。"""

    high = "high"
    economical = "economical"


class KnowledgeBaseRetrievalMode(str, Enum):
    """知识库检索模式。"""

    embedding = "embedding"
    bm25 = "bm25"
    hybrid = "hybrid"


class KnowledgeBase(Base):
    """知识库表：知识库与向量库的映射及向量检索配置。"""

    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, comment="知识库名称"
    )
    vector_store_name: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, comment="对应向量库名称"
    )
    chunking_mode: Mapped[KnowledgeBaseChunkingMode] = mapped_column(
        SAEnum(
            KnowledgeBaseChunkingMode,
            name="knowledge_base_chunking_mode",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=KnowledgeBaseChunkingMode.general,
        server_default=KnowledgeBaseChunkingMode.general.value,
        comment="分段模式：general=通用, parent-child=父子, qa=问答",
    )
    general_delimiter: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="通用分段分隔符"
    )
    general_max_length: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="通用分段最大长度（tokens）"
    )
    general_overlap: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="通用分段重叠长度（tokens）"
    )
    parent_delimiter: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="父子分段父块分隔符"
    )
    parent_max_length: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="父块最大长度（tokens）"
    )
    child_delimiter: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="父子分段子块分隔符"
    )
    child_max_length: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="子块最大长度（tokens）"
    )
    indexing_mode: Mapped[KnowledgeBaseIndexingMode] = mapped_column(
        SAEnum(
            KnowledgeBaseIndexingMode,
            name="knowledge_base_indexing_mode",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=KnowledgeBaseIndexingMode.high,
        server_default=KnowledgeBaseIndexingMode.high.value,
        comment="索引质量：high=高质量, economical=经济",
    )
    retrieval_mode: Mapped[KnowledgeBaseRetrievalMode] = mapped_column(
        SAEnum(
            KnowledgeBaseRetrievalMode,
            name="knowledge_base_retrieval_mode",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=KnowledgeBaseRetrievalMode.hybrid,
        server_default=KnowledgeBaseRetrievalMode.hybrid.value,
        comment="检索方式：embedding=向量, bm25=关键词, hybrid=混合",
    )
    hybrid_semantic_weight: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=50,
        server_default="50",
        comment="混合检索语义权重（0-100）",
    )
    hybrid_top_k: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, server_default="3", comment="检索返回条数"
    )
    hybrid_score_threshold: Mapped[Decimal] = mapped_column(
        Numeric(4, 3),
        nullable=False,
        default=Decimal("0.600"),
        server_default="0.600",
        comment="相似度阈值（0-1）",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )


class KnowledgeDocumentFileType(str, Enum):
    """知识库文档文件类型。"""

    pdf = "pdf"
    yaml = "yaml"
    excel = "excel"
    markdown = "markdown"


class KnowledgeDocumentStatus(str, Enum):
    """知识库文档处理状态。"""

    pending = "pending"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"
    configured = "configured"
    needmanual = "needmanual"


class KnowledgeDocumentStage(str, Enum):
    """知识库文档处理阶段，仅 processing 时有值。"""

    parsing = "parsing"
    chunking = "chunking"
    embedding = "embedding"
    indexing = "indexing"
    verifying = "verifying"
    done = "done"


class KnowledgeDocument(Base):
    """知识库文档表：记录文档来源、切分结果与索引状态。

    文档按知识库隔离，同一知识库内文件名唯一；`file_hash` 用于重复文件识别，
    `metadata_json` 存放切块时附着到每个块的扩展元数据。
    """

    __tablename__ = "knowledge_documents"
    __table_args__ = (
        UniqueConstraint("kb_id", "file_name", name="uq_knowledge_documents_kb_file"),
        Index("ix_knowledge_documents_kb_status", "kb_id", "status"),
        Index("ix_knowledge_documents_hash", "file_hash"),
    )

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), primary_key=True, autoincrement=True
    )
    kb_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("knowledge_bases.id"),
        nullable=False,
        comment="所属知识库 knowledge_bases.id",
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    file_path: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="文件相对路径，相对项目 knowledges 目录"
    )
    file_type: Mapped[KnowledgeDocumentFileType] = mapped_column(
        SAEnum(
            KnowledgeDocumentFileType,
            name="knowledge_document_file_type",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        comment="文件类型：pdf=PDF, yaml=YAML, excel=Excel, markdown=Markdown",
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0", comment="文件大小（字节）"
    )
    file_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="文件内容 SHA256，用于去重与增量更新"
    )
    status: Mapped[KnowledgeDocumentStatus] = mapped_column(
        SAEnum(
            KnowledgeDocumentStatus,
            name="knowledge_document_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=KnowledgeDocumentStatus.pending,
        server_default=KnowledgeDocumentStatus.pending.value,
        comment=(
            "处理状态：pending=待处理, processing=处理中, indexed=已索引, "
            "failed=失败"
        ),
    )
    chunk_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="切分后的分块数量，未切分时为空"
    )
    stage: Mapped[KnowledgeDocumentStage | None] = mapped_column(
        SAEnum(
            KnowledgeDocumentStage,
            name="knowledge_document_stage",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=True,
        comment="处理阶段：parsing/chunking/embedding/indexing/verifying/done",
    )
    progress: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default="0",
        comment="处理进度（0-100）",
    )
    total_chunks: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="切块完成后的总块数"
    )
    processed_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="已编码/已写入的块数",
    )
    metadata_json: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="扩展元数据：厂商、版本、状态等",
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, comment="处理失败原因"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
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


class AiRunKind(str, Enum):
    """AI 调用类型。"""

    llm = "llm"
    embedding = "embedding"
    rerank = "rerank"


class AiRunStatus(str, Enum):
    """AI 调用状态。"""

    success = "success"
    failed = "failed"


class AiRun(Base):
    """AI 调用记录表：LLM / 向量编码 / 重排的用量与耗时留痕，用于计费与成本核算。"""

    __tablename__ = "ai_runs"
    __table_args__ = (
        Index("ix_ai_runs_kind_created", "kind", "created_at"),
        Index("ix_ai_runs_trace", "trace_id"),
        Index("ix_ai_runs_biz", "biz_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kind: Mapped[AiRunKind] = mapped_column(
        SAEnum(
            AiRunKind,
            name="ai_run_kind",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        comment="调用类型：llm=大模型, embedding=向量编码, rerank=重排",
    )
    provider: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="服务提供方，如 openai / local-hash / rerank",
    )
    model: Mapped[str] = mapped_column(String(128), nullable=False, comment="调用的模型标识")
    trace_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        comment="业务追踪 ID：knowledge_gap 为缺口主键，knowledge_document 为文档主键，chat_messages 为消息主键",
    )
    biz_type: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="关联对象类型：knowledge_document / knowledge_gap / chat_messages",
    )
    input_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="输入条数：embedding 文本条数 / rerank 文档数",
    )
    input_chars: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default="0",
        comment="输入字符数：query 与文档正文合计",
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
    top_n: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="rerank 返回条数"
    )
    latency_ms: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0", comment="调用耗时（毫秒）"
    )
    status: Mapped[AiRunStatus] = mapped_column(
        SAEnum(
            AiRunStatus,
            name="ai_run_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        index=True,
        comment="调用结果：success=成功, failed=失败",
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, comment="失败原因"
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


class ChatMessageRole(str, Enum):
    """会话消息角色。"""

    user = "user"
    assistant = "assistant"


class ChatMessageStatus(str, Enum):
    """消息生成状态。"""

    streaming = "streaming"
    completed = "completed"
    clarifying = "clarifying"
    failed = "failed"


class ChatQuestionMode(str, Enum):
    """问答模式，与前端输入框的模式选项一致。"""

    command = "command"
    troubleshoot = "troubleshoot"
    knowledge = "knowledge"
    unknown = "unknown"
    out_of_scope = "out_of_scope"


class ChatSession(Base):
    """智能问答会话表：按用户隔离，列表按最后消息时间排序。"""

    __tablename__ = "chat_sessions"
    __table_args__ = (
        Index("ix_chat_sessions_user_recent", "user_id", "deleted_at", "last_message_at"),
        Index("ix_chat_sessions_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="归属 users.id"
    )
    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="新对话",
        server_default="新对话",
        comment="会话标题，默认取首条提问摘要",
    )
    vendor: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="会话级厂商上下文"
    )
    message_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0", comment="消息条数冗余"
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最后一条消息时间，用于列表排序"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="软删除时间，空表示未删除"
    )
    pending_clarify: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="待补充信息：{slots, mode, origin_question, round}，补齐后清空",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ChatMessage(Base):
    """会话消息表：用户提问与助手回答，流式生成时先落 streaming 行。"""

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id", "id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chat_sessions.id"),
        nullable=False,
        comment="归属会话 chat_sessions.id",
    )
    role: Mapped[ChatMessageRole] = mapped_column(
        SAEnum(
            ChatMessageRole,
            name="chat_message_role",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        comment="消息角色：user=用户提问, assistant=助手回答",
    )
    content: Mapped[str] = mapped_column(
        MEDIUMTEXT, nullable=False, comment="消息正文"
    )
    status: Mapped[ChatMessageStatus] = mapped_column(
        SAEnum(
            ChatMessageStatus,
            name="chat_message_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=ChatMessageStatus.completed,
        server_default=ChatMessageStatus.completed.value,
        comment="生成状态：streaming/completed/failed",
    )
    mode: Mapped[ChatQuestionMode] = mapped_column(
        SAEnum(
            ChatQuestionMode,
            name="chat_question_mode",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=ChatQuestionMode.command,
        server_default=ChatQuestionMode.command.value,
        comment="问答模式：command=命令检索, troubleshoot=故障排查, knowledge=知识提问",
    )
    model: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="实际调用的模型"
    )
    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="输入 token 数"
    )
    completion_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="输出 token 数"
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="响应耗时（毫秒）"
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, comment="生成失败时的错误信息"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ChatMessageCitation(Base):
    """回答引用表：记录回答命中的知识库切片，便于溯源展示。"""

    __tablename__ = "chat_message_citations"
    __table_args__ = (
        Index("ix_chat_message_citations_message", "message_id"),
        Index("ix_chat_message_citations_kb", "kb_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chat_messages.id"),
        nullable=False,
        comment="归属消息 chat_messages.id",
    )
    kb_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="来源知识库 id，一次回答可跨多个知识库"
    )
    doc_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="knowledge_documents.id"
    )
    file_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="引用文档文件名，冗余便于展示"
    )
    point_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="Qdrant point id，便于回溯切片"
    )
    score: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True, comment="检索相似度分数"
    )
    snippet: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="命中切片摘要"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class ChatMessageFeedback(Base):
    """回答点赞/点踩表：每个用户对同一条回答仅保留一条反馈。"""

    __tablename__ = "chat_message_feedbacks"
    __table_args__ = (
        UniqueConstraint(
            "message_id", "user_id", name="uq_chat_feedback_message_user"
        ),
        Index("ix_chat_feedback_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chat_messages.id"),
        nullable=False,
        comment="归属消息 chat_messages.id",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="归属 users.id"
    )
    rating: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, comment="1=赞, -1=踩"
    )
    reason: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="点踩原因"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
