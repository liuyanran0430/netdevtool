"""文档切块：general / parent-child / qa 三种策略。

分隔符允许使用 `\\n`、`\\t` 这类转义写法；分块长度按字符数计算。
"""

from __future__ import annotations

import re

from app.rag.schema import Chunk, ChunkingConfig, NeedManualError

_ESCAPES = {"\\n": "\n", "\\r": "\r", "\\t": "\t"}

# 标题行：`#### 1.1.1.1 xxx`，用于识别父块的标题路径
_HEADING_LINE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

# 分隔线作为父块的硬边界
_RULE_LINE = re.compile(r"(?m)^(?:-{3,}|\*{3,}|_{3,})\s*$")

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


def heading_break_pattern(levels_text: str) -> re.Pattern[str] | None:
    """按标题级别生成父块硬边界正则；级别为空时返回 None（不切）。"""
    levels = {
        int(part)
        for part in (levels_text or "").split(",")
        if part.strip().isdigit() and 1 <= int(part) <= 6
    }
    if not levels:
        return None
    marks = "|".join("#" * level for level in sorted(levels, reverse=True))
    # 行首前瞻，保留标题行本身，且 H6 不会被 H4 规则误伤
    return re.compile(rf"(?m)^(?=(?:{marks})\s)")


def _split_sections(text: str, levels_text: str) -> list[str]:
    """按配置的标题级别与分隔线预切小节，保证父块不跨越标题。"""
    pattern = heading_break_pattern(levels_text)
    raw_parts = pattern.split(text) if pattern else [text]
    sections: list[str] = []
    for part in raw_parts:
        # 分隔线单独成行时再切一刀，丢弃只剩分隔线的空片段
        for section in re.split(r"(?m)^(?=(?:-{3,}|\*{3,}|_{3,})\s*$)", part):
            cleaned = section.strip()
            if not cleaned or not _RULE_LINE.sub("", cleaned).strip():
                continue
            sections.append(cleaned)
    return sections


def _parent_child_chunks(text: str, config: ChunkingConfig) -> list[Chunk]:
    # 父块边界由标题级别决定，段落拼装固定按空行
    parent_delimiter = "\n\n"
    child_delimiter = normalize_delimiter(config.child_delimiter, "\n")
    parent_max = max(config.parent_max_length, 50)
    child_max = max(config.child_max_length, 20)

    chunks: list[Chunk] = []
    parent_index = 0
    # 标题栈：记录当前所处的标题路径，供父块补上下文
    stack: list[tuple[int, str]] = []

    for section in _split_sections(text, config.heading_split_levels):
        heading = _HEADING_LINE.match(section.split("\n", 1)[0])
        own_level: int | None = None
        if heading:
            own_level = len(heading.group(1))
            while stack and stack[-1][0] >= own_level:
                stack.pop()
            stack.append((own_level, heading.group(2)))
            # 只有标题、没有正文的小节（如仅作为目录层级）不单独成块
            body = _RULE_LINE.sub("", _HEADING_LINE.sub("", section)).strip()
            if not body:
                continue

        for position, parent in enumerate(
            _split_by(section, parent_delimiter, parent_max)
        ):
            titles = [title for _, title in stack]
            # 首个父块已含自身标题，只补祖先路径；续块补完整路径
            if position == 0 and own_level is not None:
                titles = titles[:-1]
            prefix = " > ".join(titles)
            parent_text = f"{prefix}\n\n{parent}" if prefix else parent

            for child in _split_by(parent, child_delimiter, child_max):
                chunks.append(
                    Chunk(
                        text=child,
                        kind="child",
                        index=len(chunks),
                        parent_index=parent_index,
                        parent_text=parent_text,
                    )
                )
            parent_index += 1
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
