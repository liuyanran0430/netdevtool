"""RAG 数据结构：切块结果、Qdrant payload、检索命中与 collection 配置。"""

from __future__ import annotations

from dataclasses import dataclass, field


class NeedManualError(RuntimeError):
    """文档需要人工补充配置或元数据后才能继续处理。"""


@dataclass(frozen=True)
class ChunkingConfig:
    """知识库切分配置快照。"""

    mode: str = "general"
    general_delimiter: str = "\\n\\n"
    general_max_length: int = 500
    general_overlap: int = 50
    parent_delimiter: str = "\\n\\n"
    parent_max_length: int = 1000
    child_delimiter: str = "\\n"
    child_max_length: int = 200


@dataclass
class ParsedDocument:
    """解析后的纯文本与解析阶段附加信息。"""

    text: str
    meta: dict[str, object] = field(default_factory=dict)


@dataclass
class Chunk:
    """待写入向量库的文本块。"""

    text: str
    kind: str
    index: int
    parent_index: int | None = None
    parent_text: str | None = None


@dataclass
class IndexResult:
    """索引完成后的统计信息。"""

    chunk_count: int
    point_count: int
    embedding_provider: str
    dense_dim: int
