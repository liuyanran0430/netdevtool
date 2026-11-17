"""文档切块：general / parent-child / qa 三种策略。

分隔符允许使用 `\\n`、`\\t` 这类转义写法；分块长度按字符数计算。
"""

from __future__ import annotations

import re

from app.rag.schema import Chunk, ChunkingConfig, NeedManualError

_ESCAPES = {"\\n": "\n", "\\r": "\r", "\\t": "\t"}

_QA_QUESTION = re.compile(r"^\s*(?:Q|问|问题)\s*[:：]\s*", re.IGNORECASE)
_QA_ANSWER = re.compile(r"^\s*(?:A|答|答案)\s*[:：]\s*", re.IGNORECASE)


def normalize_delimiter(value: str, fallback: str) -> str:
    """把界面上的转义分隔符还原为真实字符。"""
    raw = (value or "").strip()
    if not raw:
        return fallback
    for escaped, real in _ESCAPES.items():
        raw = raw.replace(escaped, real)
    return raw or fallback


def _split_long(text: str, max_length: int) -> list[str]:
    """对超长片段做硬切，优先在句号/换行处断开。"""
    if len(text) <= max_length:
        return [text]

    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_length, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind("\n"), window.rfind("。"), window.rfind("；"))
            if cut > max_length // 2:
                end = start + cut + 1
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        start = end
    return pieces


def _split_by(text: str, delimiter: str, max_length: int) -> list[str]:
    parts = [part.strip() for part in text.split(delimiter) if part.strip()]
    if len(parts) <= 1:
        parts = [part.strip() for part in text.split("\n\n") if part.strip()]

    merged: list[str] = []
    buffer = ""
    for part in parts:
        if not buffer:
            buffer = part
            continue
        if len(buffer) + len(delimiter) + len(part) <= max_length:
            buffer = f"{buffer}{delimiter}{part}"
        else:
            merged.extend(_split_long(buffer, max_length))
            buffer = part
    if buffer:
        merged.extend(_split_long(buffer, max_length))
    return merged


def _general_chunks(text: str, config: ChunkingConfig) -> list[Chunk]:
    delimiter = normalize_delimiter(config.general_delimiter, "\n\n")
    max_length = max(config.general_max_length, 20)
    overlap = min(max(config.general_overlap, 0), max_length // 2)

    chunks: list[Chunk] = []
    tail = ""
    for piece in _split_by(text, delimiter, max_length):
        content = f"{tail}{piece}" if tail else piece
        for part in _split_long(content, max_length):
            chunks.append(Chunk(text=part, kind="chunk", index=len(chunks)))
            if overlap:
                tail = part[-overlap:]
            else:
                tail = ""
    return chunks


def _parent_child_chunks(text: str, config: ChunkingConfig) -> list[Chunk]:
    parent_delimiter = normalize_delimiter(config.parent_delimiter, "\n\n")
    child_delimiter = normalize_delimiter(config.child_delimiter, "\n")
    parent_max = max(config.parent_max_length, 50)
    child_max = max(config.child_max_length, 20)

    chunks: list[Chunk] = []
    for parent_index, parent in enumerate(
        _split_by(text, parent_delimiter, parent_max)
    ):
        children = _split_by(parent, child_delimiter, child_max)
        for child in children:
            chunks.append(
                Chunk(
                    text=child,
                    kind="child",
                    index=len(chunks),
                    parent_index=parent_index,
                    parent_text=parent,
                )
            )
    return chunks


def _qa_chunks(text: str, config: ChunkingConfig) -> list[Chunk]:
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if _QA_QUESTION.match(line):
            if current:
                blocks.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current:
        blocks.append(current)

    if not blocks:
        raise NeedManualError("未识别到 Q&A 结构，请检查文档格式或在元数据中手动配置")

    max_length = max(config.general_max_length, 50)
    chunks: list[Chunk] = []
    for block in blocks:
        content = "\n".join(block).strip()
        if not content:
            continue
        for part in _split_long(content, max_length):
            chunks.append(Chunk(text=part, kind="chunk", index=len(chunks)))
    return chunks


def chunk_text(text: str, config: ChunkingConfig) -> list[Chunk]:
    """按知识库配置切分文本，返回待索引的块。"""
    if config.mode == "parent-child":
        return _parent_child_chunks(text, config)
    if config.mode == "qa":
        return _qa_chunks(text, config)
    return _general_chunks(text, config)
