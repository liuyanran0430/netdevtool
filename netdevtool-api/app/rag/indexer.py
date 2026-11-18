"""索引编排：解析 → 切块 → 编码 → 写入 Qdrant，不涉及数据库与任务调度。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from openpyxl import load_workbook
from pypdf import PdfReader
from qdrant_client.models import PointStruct

from app.config import settings
from app.rag.chunking import chunk_text
from app.rag.embedding import encode_dense, sparse_encode
from app.rag.qdrant_store import QdrantStore
from app.rag.schema import (
    Chunk,
    ChunkingConfig,
    IndexResult,
    NeedManualError,
    ParsedDocument,
)

ProgressFn = Callable[[str, int, int | None], None]
_BATCH_SIZE = 32


def _decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _parse_excel(path: Path) -> ParsedDocument:
    workbook = load_workbook(filename=path, read_only=True, data_only=True)
    blocks: list[str] = []
    for sheet in workbook.worksheets:
        rows = [
            ["" if cell is None else str(cell).strip() for cell in row]
            for row in sheet.iter_rows(values_only=True)
        ]
        rows = [row for row in rows if any(row)]
        if not rows:
            continue

        header = rows[0]
        question_col = next(
            (
                index
                for index, value in enumerate(header)
                if value.lower() in {"问题", "question", "q"}
            ),
            None,
        )
        answer_col = next(
            (
                index
                for index, value in enumerate(header)
                if value.lower() in {"答案", "answer", "a"}
            ),
            None,
        )

        blocks.append(f"# {sheet.title}")
        if question_col is not None and answer_col is not None:
            for row in rows[1:]:
                question = row[question_col] if question_col < len(row) else ""
                answer = row[answer_col] if answer_col < len(row) else ""
                if question or answer:
                    blocks.append(f"Q: {question}\nA: {answer}")
        else:
            for row in rows:
                blocks.append(" | ".join(value for value in row if value))

    workbook.close()
    return ParsedDocument(text="\n\n".join(blocks))


def _parse_pdf(path: Path) -> ParsedDocument:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(f"## 第 {index} 页\n{text}")
    return ParsedDocument(text="\n\n".join(pages), meta={"pages": len(reader.pages)})


def parse_document(path: Path, file_type: str) -> ParsedDocument:
    """按文件类型抽取纯文本。"""
    if file_type == "markdown":
        return ParsedDocument(text=_decode(path.read_bytes()))
    if file_type == "yaml":
        return ParsedDocument(text=_decode(path.read_bytes()))
    if file_type == "excel":
        return _parse_excel(path)
    if file_type == "pdf":
        return _parse_pdf(path)
    raise NeedManualError(f"暂不支持的文件类型：{file_type}")


def _payload(
    *,
    kb_id: int,
    doc_id: int,
    file_name: str,
    chunk: Chunk,
    metadata: dict[str, object],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "kb_id": kb_id,
        "doc_id": doc_id,
        "file_name": file_name,
        "chunk_type": chunk.kind,
        "chunk_index": chunk.index,
        "text": chunk.text,
    }
    if chunk.parent_index is not None:
        payload["parent_index"] = chunk.parent_index
    if chunk.parent_text:
        payload["parent_text"] = chunk.parent_text
    if metadata:
        payload["metadata"] = metadata
    return payload


def index_document(
    *,
    path: Path,
    file_type: str,
    file_name: str,
    kb_id: int,
    doc_id: int,
    vector_store_name: str,
    config: ChunkingConfig,
    indexing_mode: str,
    metadata: dict[str, object],
    on_progress: ProgressFn,
) -> IndexResult:
    """执行一次完整的文档索引，返回统计信息。"""
    on_progress("parsing", 5, None)
    parsed = parse_document(path, file_type)
    if not parsed.text.strip():
        raise NeedManualError("未从文档中提取到可用文本，请检查文件内容")
    on_progress("parsing", 15, None)

    on_progress("chunking", 20, None)
    chunks = chunk_text(parsed.text, config)
    if not chunks:
        raise NeedManualError("切分结果为空，请检查分隔符与文档内容")
    total = len(chunks)
    on_progress("chunking", 30, 0)

    header_parts = [
        str(metadata.get(key))
        for key in ("vendor", "product", "version")
        if metadata.get(key)
    ]
    header = " | ".join([*header_parts, file_name])

    use_dense = indexing_mode == "high"
    dense_dim = max(settings.EMBEDDING_DIM, 32)
    provider = "sparse-only"
    processed = 0
    written = 0

    with QdrantStore(vector_store_name) as store:
        first_batch = True
        for start in range(0, total, _BATCH_SIZE):
            batch = chunks[start : start + _BATCH_SIZE]
            texts = [f"{header}\n{chunk.text}" for chunk in batch]

            dense_vectors: list[list[float]] = []
            if use_dense:
                dense_vectors, provider = encode_dense(texts)
                dense_dim = len(dense_vectors[0])
                on_progress(
                    "embedding",
                    30 + int(30 * (start + len(batch)) / total),
                    start + len(batch),
                )

            if first_batch:
                store.ensure(dense_dim)
                store.delete_document(doc_id)
                first_batch = False

            points: list[PointStruct] = []
            for offset, chunk in enumerate(batch):
                vectors: dict[str, object] = {"sparse": sparse_encode(texts[offset])}
                if use_dense:
                    vectors["dense"] = dense_vectors[offset]
                points.append(
                    PointStruct(
                        id=str(
                            uuid5(
                                NAMESPACE_URL,
                                f"knowledge-document:{doc_id}:{chunk.index}",
                            )
                        ),
                        vector=vectors,
                        payload=_payload(
                            kb_id=kb_id,
                            doc_id=doc_id,
                            file_name=file_name,
                            chunk=chunk,
                            metadata=metadata,
                        ),
                    )
                )

            store.upsert(points)
            processed += len(batch)
            written += len(points)
            on_progress(
                "indexing",
                60 + int(35 * processed / total),
                processed,
            )

        on_progress("verifying", 95, processed)
        indexed = store.count_document(doc_id)
        if indexed != written:
            raise RuntimeError(f"写入校验失败：期望 {written} 个分块，实际 {indexed} 个")

    return IndexResult(
        chunk_count=written,
        point_count=indexed,
        embedding_provider=provider,
        dense_dim=dense_dim,
    )
