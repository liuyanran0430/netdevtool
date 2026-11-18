"""把厂商配置指导 PDF 转换成按章拆分的 Markdown，供知识库切片使用。

转换引擎：pymupdf4llm（基于 PyMuPDF），直接输出带标题层级、表格与行内代码的 Markdown。

处理内容：
    1. 按页生成 Markdown（page_chunks），保留标题、表格、命令加粗；
    2. 统计跨页重复行，去掉页眉页脚、页码与产品名；
    3. 按 PDF 书签（目录）定位每章起始页，章标题写入 `# 章名`；
    4. 合并 PDF 换行造成的汉字间空格与断词；
    5. 按章输出独立 .md 文件，并写入产品/版本等前置元信息。

用法示例：
    netdevtool-api\\.venv\\Scripts\\python.exe scripts\\pdf_to_markdown.py ^
        "knowledges\\docs\\ZXR10 5960X系列（V6.00.03.94）数据中心交换机 配置指导.pdf" ^
        -o knowledges\\docs\\zxr10_v6000394 --end 120

    # 全量转换，并额外输出合并文件
    ... pdf_to_markdown.py input.pdf -o out --single-file

依赖：pymupdf4llm（会一并安装 PyMuPDF）。
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pymupdf
import pymupdf4llm

CHAPTER_SENTINEL = "\x00CHAPTER\x00"

TOC_LINE_RE = re.compile(r"\.{4,}\s*\d+\s*$")
TOC_ANY_RE = re.compile(r"\.{4,}\s*\d+")
TABLE_SEPARATOR_RE = re.compile(r"^\|[\s\-|:]+\|$")
ROMAN_PAGE_RE = re.compile(r"^[IVX]{1,4}$")
PAGE_NO_RE = re.compile(r"^\s*(?:第\s*)?\d+\s*(?:页)?\s*$")
CHAPTER_RE = re.compile(r"^(\d{1,2})\s+([\u4e00-\u9fa5A-Za-z][^。；：，,;:]{0,23})$")
PRODUCT_RE = re.compile(r"产品版本[：:]\s*(\S+)")
MODEL_RE = re.compile(r"(ZXR10\s+\S+)")
FOOTER_RE = re.compile(
    r"(?:\d*\s*)?SJ-\d{6,}-\d+\s*\|\s*\d{4}-\d{2}-\d{2}（R[\d.]+）\s*\d*\s*$"
)
DOC_NO_RE = re.compile(r"资料编号[∶:].*$")
CJK_SPACE_RE = re.compile(r"(?<=[\u4e00-\u9fff])[ \t]+(?=[\u4e00-\u9fff])")
HYPHEN_SPLIT_RE = re.compile(r"([A-Za-z])-\s+([a-z])")
# 表格换行可能被转换成两个加粗代码片段：`**`interfa-`** **`ce`**`
INLINE_CODE_HYPHEN_SPLIT_RE = re.compile(r"([A-Za-z])-`\*\*\s*\*\*`([a-z])")
MARKUP_RE = re.compile(r"[*_`<>#]+")
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
TAG_RE = re.compile(r"</?(?:u|sup|sub|strong|em|span|font)(?:\s[^>]*)?>", re.IGNORECASE)
SECTION_HEADING_RE = re.compile(r"^(#{1,6})\s+(\d+(?:\.\d+)+)\s+(\S.*)$")
STRUCTURE_WORDS = {
    "配置验证",
    "配置实例",
    "配置步骤",
    "配置说明",
    "配置举例",
    "注意事项",
    "前提条件",
    "背景信息",
}


def log(message: str) -> None:
    print(message)


def strip_markup(text: str) -> str:
    """去掉 Markdown 标记，便于做重复行/页眉判断。"""
    return MARKUP_RE.sub("", TAG_RE.sub("", text)).strip()


def normalize_heading(line: str) -> str:
    """按编号深度重排标题层级：1.1→##，1.1.1→###，1.1.1.1→####。"""
    match = SECTION_HEADING_RE.match(line.strip())
    if not match:
        return line
    number = match.group(2)
    level = min(number.count(".") + 1, 4)
    return f"{'#' * level} {number} {match.group(3)}".rstrip()


def read_pages(
    pdf_path: Path, start: int, end: int | None
) -> tuple[list[dict[str, object]], int]:
    """一次性把 PDF 转成按页的 Markdown。"""
    with pymupdf.open(str(pdf_path)) as doc:
        total = doc.page_count
        first = max(start, 1)
        last = total if end is None else min(end, total)
        numbers = list(range(first, last + 1))

    # pymupdf4llm 会向 stdout 打印解析信息，此处静默
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        chunks = pymupdf4llm.to_markdown(
            str(pdf_path),
            pages=[number - 1 for number in numbers],
            page_chunks=True,
        )

    pages: list[dict[str, object]] = []
    for index, chunk in enumerate(chunks):
        text = chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
        page_no = numbers[index] if index < len(numbers) else first + index
        pages.append({"page": page_no, "text": text.replace("\r\n", "\n")})
    return pages, total


def outline_chapters(pdf_path: Path) -> dict[int, str]:
    """读取 PDF 书签的一级标题，返回 {页码: 标题}。"""
    chapters: dict[int, str] = {}
    with pymupdf.open(str(pdf_path)) as doc:
        for level, title, page in doc.get_toc(simple=True):
            if level != 1:
                continue
            cleaned = title.strip()
            if not CHAPTER_RE.match(cleaned):
                continue
            chapters.setdefault(page, cleaned)
    return chapters


def detect_repeated_lines(pages: list[dict[str, object]]) -> set[str]:
    """跨页高频出现的短行视为页眉/页脚。"""
    from collections import Counter

    counter: Counter[str] = Counter()
    for page in pages:
        seen = set()
        for raw in str(page["text"]).splitlines():
            stripped = strip_markup(raw)
            if not stripped or len(stripped) > 44:
                continue
            # 表格行（含表头/分隔行）跨页重复是正常的，不参与页眉判定
            if raw.strip().startswith("|"):
                continue
            if any(char in stripped for char in "。，；：、！？"):
                continue
            if stripped in STRUCTURE_WORDS or ROMAN_PAGE_RE.match(stripped):
                continue
            seen.add(stripped)
        counter.update(seen)
    threshold = max(10, int(len(pages) * 0.3))
    return {line for line, count in counter.items() if count >= threshold}


def clean_line(line: str, in_code: bool) -> str:
    if in_code:
        return line.rstrip()
    cleaned = FOOTER_RE.sub("", line)
    cleaned = DOC_NO_RE.sub("", cleaned).rstrip()
    cleaned = BR_RE.sub(" ", cleaned)
    cleaned = TAG_RE.sub("", cleaned)
    cleaned = CJK_SPACE_RE.sub("", cleaned)
    cleaned = INLINE_CODE_HYPHEN_SPLIT_RE.sub(r"\1\2", cleaned)
    cleaned = HYPHEN_SPLIT_RE.sub(r"\1\2", cleaned)
    return cleaned


def clean_page(
    text: str,
    repeated: set[str],
    drop_chapter_heads: bool,
) -> list[str]:
    """清洗单页 Markdown：去页眉页脚、页码、目录行与章标题页眉。"""
    lines: list[str] = []
    in_code = False
    in_toc = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            lines.append(clean_line(raw, False))
            continue

        line = clean_line(raw, in_code)
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if in_code:
            lines.append(line)
            continue

        plain = strip_markup(stripped)
        if TOC_ANY_RE.search(plain):
            in_toc = True
            continue
        if in_toc and TABLE_SEPARATOR_RE.match(stripped):
            continue
        in_toc = False
        if TOC_LINE_RE.search(plain) or PAGE_NO_RE.match(plain) or ROMAN_PAGE_RE.match(plain):
            continue
        if "配置指导" in plain and "ZXR10" in plain and len(plain) <= 50:
            continue
        if plain in repeated:
            continue
        if drop_chapter_heads and stripped.startswith("# ") and CHAPTER_RE.match(plain):
            continue
        if stripped.startswith("#"):
            lines.append(normalize_heading(line))
            continue
        lines.append(line)

    # 去掉页码残留导致的连续空行
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def build_lines(
    pages: list[dict[str, object]],
    chapters: dict[int, str],
    repeated: set[str],
) -> list[str]:
    drop_heads = bool(chapters)
    all_lines: list[str] = []
    for page in pages:
        page_no = int(page["page"])  # type: ignore[arg-type]
        if page_no in chapters:
            all_lines.append(CHAPTER_SENTINEL + chapters[page_no])
            all_lines.append("")
        all_lines.extend(
            clean_page(str(page["text"]), repeated, drop_heads)
        )
        all_lines.append("")
    return all_lines


def split_chapters(lines: list[str]) -> list[tuple[str, list[str]]]:
    chapters: list[tuple[str, list[str]]] = [("前言", [])]
    current = chapters[0][1]
    last_number = 0
    for line in lines:
        if line.startswith(CHAPTER_SENTINEL):
            title = line[len(CHAPTER_SENTINEL) :].strip()
            match = CHAPTER_RE.match(title)
            number = int(match.group(1)) if match else last_number + 1
            if number > last_number:
                last_number = number
                current = []
                chapters.append((title, current))
                continue
        current.append(line)
    if not chapters[0][1]:
        chapters.pop(0)
    return chapters


def render(lines: list[str]) -> str:
    """压缩多余空行，保证 Markdown 块之间只有一个空行。"""
    output: list[str] = []
    for line in lines:
        if not line.strip():
            if output and output[-1] != "":
                output.append("")
            continue
        output.append(line.rstrip())
    while output and output[-1] == "":
        output.pop()
    return "\n".join(output) + "\n"


def sanitize(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\s]+', "-", name).strip("-")
    return cleaned[:60] or "untitled"


def chapter_filename(index: int, title: str) -> str:
    return f"{index:02d}-{sanitize(title)}.md"


def detect_product(pages: list[dict[str, object]]) -> tuple[str, str]:
    head = "\n".join(str(page["text"]) for page in pages[:6])
    version = ""
    match = PRODUCT_RE.search(head)
    if match:
        version = match.group(1)
    model = ""
    match = MODEL_RE.search(head)
    if match:
        model = match.group(1)
    return model, version


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF 转 Markdown（pymupdf4llm 引擎）")
    parser.add_argument("pdf", help="PDF 文件路径")
    parser.add_argument("-o", "--output", required=True, help="输出目录")
    parser.add_argument("--start", type=int, default=1, help="起始页（从 1 开始）")
    parser.add_argument("--end", type=int, help="结束页（含）")
    parser.add_argument("--single-file", action="store_true", help="额外输出合并后的单文件")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.is_file():
        log(f"PDF 不存在：{pdf_path}")
        return 2

    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    pages, total = read_pages(pdf_path, args.start, args.end)
    log(f"读取 {len(pages)} 页（文档共 {total} 页）")

    chapters = outline_chapters(pdf_path)
    if chapters:
        log(f"读取书签章节 {len(chapters)} 个，按书签定位章起点")
    else:
        log("未找到书签，按页眉中的章标题分章")

    repeated = detect_repeated_lines(pages)
    log(f"识别重复页眉/页脚 {len(repeated)} 条：{sorted(repeated)[:6]}")

    lines = build_lines(pages, chapters, repeated)
    chapter_items = split_chapters(lines)
    log(f"识别章节 {len(chapter_items)} 个")

    product, version = detect_product(pages)
    header = ["---"]
    header.append(f"source: {pdf_path.name}")
    if product:
        header.append(f"product: {product}")
    if version:
        header.append(f"version: {version}")
    header.append("---\n")

    chapter_index = 0
    total_chars = 0
    written: list[Path] = []
    for title, content in chapter_items:
        body = render(content)
        if len(body.strip()) < 40:
            continue
        target = output_dir / chapter_filename(chapter_index, title)
        target.write_text(
            "\n".join(header) + f"\n# {title}\n\n" + body,
            encoding="utf-8",
        )
        written.append(target)
        total_chars += len(body)
        log(f"  输出 {target.name}（{len(body)} 字符）")
        chapter_index += 1

    if args.single_file:
        combined = output_dir / "_full.md"
        combined.write_text(
            "\n".join(header)
            + "\n"
            + "\n\n".join(
                f"# {title}\n\n{render(content)}" for title, content in chapter_items
            ),
            encoding="utf-8",
        )
        written.append(combined)
        log(f"  输出 {combined.name}")

    log(f"完成：{len(written)} 个文件，正文约 {total_chars} 字符，目录 {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
