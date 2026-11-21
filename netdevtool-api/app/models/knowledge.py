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
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "KnowledgeBase",
    "KnowledgeBaseChunkingMode",
    "KnowledgeBaseIndexingMode",
    "KnowledgeBaseRetrievalMode",
    "KnowledgeBaseType",
    "KnowledgeDocument",
    "KnowledgeDocumentFileType",
    "KnowledgeDocumentStage",
    "KnowledgeDocumentStatus",
]


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


class KnowledgeBaseType(str, Enum):
    """知识库类型：决定问答检索时该库服务于哪类意图。"""

    manual = "manual"
    troubleshooting = "troubleshooting"
    architecture = "architecture"


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
    kb_type: Mapped[KnowledgeBaseType] = mapped_column(
        SAEnum(
            KnowledgeBaseType,
            name="knowledge_base_type",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=KnowledgeBaseType.manual,
        server_default=KnowledgeBaseType.manual.value,
        comment="库类型：manual=设备手册, troubleshooting=故障手册, architecture=架构知识",
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
    parent_max_length: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="父块最大长度（tokens）"
    )
    child_delimiter: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="父子分段子块分隔符"
    )
    child_max_length: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="子块最大长度（tokens）"
    )
    heading_split_levels: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="1,2",
        server_default="1,2",
        comment="父块标题硬边界级别，逗号分隔，如 1,2,3,4；空表示不按标题切",
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
