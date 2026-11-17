"""CHM 手册转换脚本：解包、GB18030 解码、HTML 转 Markdown。

用法（在项目根目录执行，路径含空格时请加引号）：
    python scripts/convert_chm.py path/to/manual.chm
    python scripts/convert_chm.py "path/to/H3C S6800.chm" -o "knowledges/docs/H3C S6800命令参考.md"
    python scripts/convert_chm.py "path/to/H3C S6800.chm" -o "knowledges/docs/H3C S6800命令参考" --split-chapters
    python scripts/convert_chm.py "path/to/manual.chm" -o knowledges/docs/manual
    python scripts/convert_chm.py path/to/extracted_dir      # 已解包的目录，跳过解包
    python scripts/convert_chm.py manual.chm --keep-html     # 保留解包出来的 HTML
    python scripts/convert_chm.py manual.chm --pandoc        # 用 pandoc 转换（需已安装）
    python scripts/convert_chm.py manual.chm --no-images     # 跳过图片，只保留文字
    python scripts/convert_chm.py manual.chm --include-nav   # 不跳过 toc/index 等导航页

约定：
- 解包优先使用 Windows 自带的 hh.exe，其次 7-Zip；输入为目录时直接转换。
- hh.exe 对中文/超长源路径会静默失败，脚本会自动复制到临时短路径重试。
- 编码优先看 HTML 的 meta charset，其次 UTF-8，最后按 GB18030 解码。
- 默认跳过 toc/index/nav 等导航页和正文过短的页面，可用 --include-nav 关闭。
- -o 指向目录时按原目录结构输出多个 .md；指向 .md 文件时合并为单个文件。
- 输出编码统一为 UTF-8。
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from html.parser import HTMLParser
from pathlib import Path

HTML_SUFFIXES = {".htm", ".html"}
NAV_STEMS = {
    "toc",
    "index",
    "default",
    "nav",
    "header",
    "footer",
    "copyright",
    "blank",
    "main",
}
SKIP_DIRS = {"ss"}  # H3C CHM 中的相关链接索引目录，不属于正文
HEADING_TAGS = {f"h{level}": level for level in range(1, 7)}
SKIP_TAGS = {"script", "style", "head", "noscript", "iframe", "form", "svg", "canvas", "template"}
VOID_TAGS = {"br", "img", "hr", "meta", "link", "base", "input", "area", "col", "embed", "source"}
BLOCK_TAGS = {
    "p",
    "div",
    "section",
    "article",
    "header",
    "footer",
    "main",
    "aside",
    "nav",
    "figure",
    "figcaption",
    "dl",
    "dt",
    "dd",
}
CHARSET_RE = re.compile(rb"""charset\s*=\s*["']?\s*([\w-]+)""", re.IGNORECASE)
MIN_CONTENT_CHARS = 20


# ---------------------------------------------------------------------------
# 解包
# ---------------------------------------------------------------------------


def find_seven_zip() -> str | None:
    """查找 7z 可执行文件，优先 PATH，其次常见安装目录。"""
    found = shutil.which("7z") or shutil.which("7za")
    if found:
        return found
    candidates = [
        Path(r"C:\Program Files\7-Zip\7z.exe"),
        Path(r"C:\Program Files (x86)\7-Zip\7z.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def unpack_chm(chm: Path, dest: Path) -> None:
    """把 CHM 解包到 dest，优先 hh.exe，其次 7-Zip。"""
    dest.mkdir(parents=True, exist_ok=True)

    if os.name == "nt":
        hh = Path(os.environ.get("WINDIR", r"C:\Windows")) / "hh.exe"
        if hh.is_file():
            run([str(hh), "-decompile", str(dest), str(chm)], "hh.exe 解包失败")
            return

    seven = find_seven_zip()
    if seven:
        run([seven, "x", f"-o{dest}", "-y", str(chm)], "7-Zip 解包失败")
        return

    raise RuntimeError("未找到 hh.exe 或 7-Zip，无法解包 CHM")


def run(command: list[str], message: str) -> None:
    result = subprocess.run(command, capture_output=True, text=True, errors="replace")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"{message}：{detail or '退出码 ' + str(result.returncode)}")


def has_html_files(root: Path) -> bool:
    return any(path.suffix.lower() in HTML_SUFFIXES for path in root.rglob("*"))


def wait_for_unpack(dest: Path, timeout: float = 300.0) -> bool:
    """等待 hh.exe 异步解包结束。

    hh.exe 会立即返回，实际由后台进程写文件，因此轮询文件数量和总大小，
    连续多次不再变化才认为解包完成；目录持续为空则判定为解包失败。
    """
    deadline = time.monotonic() + timeout
    last_stats: tuple[int, int] | None = None
    stable_rounds = 0
    empty_rounds = 0

    while time.monotonic() < deadline:
        files = [path for path in dest.rglob("*") if path.is_file()]
        stats = (len(files), sum(path.stat().st_size for path in files))
        if stats[0] == 0:
            empty_rounds += 1
            if empty_rounds >= 8:  # 约 4 秒仍无文件，判定失败
                return False
        elif stats == last_stats:
            stable_rounds += 1
            if stable_rounds >= 4:  # 约 2 秒无变化，判定完成
                return True
        else:
            stable_rounds = 0
            empty_rounds = 0
        last_stats = stats
        time.sleep(0.5)

    return bool(last_stats and last_stats[0] > 0)


# ---------------------------------------------------------------------------
# 解码
# ---------------------------------------------------------------------------


def decode_html(data: bytes, fallback: str) -> str:
    """按 BOM → meta charset → UTF-8 → 兜底编码的顺序解码。"""
    for bom, encoding in (
        (b"\xef\xbb\xbf", "utf-8-sig"),
        (b"\xff\xfe", "utf-16"),
        (b"\xfe\xff", "utf-16"),
    ):
        if data.startswith(bom):
            return data.decode(encoding, errors="replace")

    declared = _declared_charset(data)
    if declared:
        normalized = _normalize_charset(declared)
        text = _try_decode(data, normalized)
        if text is not None:
            return text

    text = _try_decode(data, "utf-8")
    if text is not None:
        return text
    return data.decode(fallback, errors="replace")


def _declared_charset(data: bytes) -> str | None:
    matched = CHARSET_RE.search(data[:4096])
    if matched is None:
        return None
    return matched.group(1).decode("ascii", errors="ignore") or None


def _normalize_charset(charset: str) -> str:
    charset = charset.strip().lower()
    if charset in {"gb2312", "gbk", "gb18030", "gb_2312-80", "x-gbk"}:
        return "gb18030"
    if charset in {"utf8", "utf-8"}:
        return "utf-8"
    return charset


def _try_decode(data: bytes, encoding: str) -> str | None:
    try:
        return data.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        return None


# ---------------------------------------------------------------------------
# HTML → Markdown
# ---------------------------------------------------------------------------


class MarkdownConverter(HTMLParser):
    """轻量 HTML 转 Markdown，覆盖手册常见的标题、段落、列表、表格和代码块。"""

    def __init__(self, include_images: bool = True) -> None:
        super().__init__(convert_charrefs=True)
        self.include_images = include_images
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self.in_title = False
        self.skip_depth = 0
        self.pre_parts: list[str] | None = None
        self.list_stack: list[tuple[str, int]] = []
        self.link_stack: list[tuple[int, str | None]] = []
        self.table_rows: list[list[str]] | None = None
        self.table_row: list[str] | None = None
        self.cell_parts: list[str] | None = None
        self.heading_level: int | None = None

    # -- 对外入口 ---------------------------------------------------------
    def convert(self, text: str) -> str:
        self.feed(text)
        self.close()
        markdown = "".join(self.parts)
        markdown = self._cleanup(markdown)
        title = "".join(self.title_parts).strip()
        if title and not re.match(r"^\s*#\s", markdown):
            markdown = f"# {title}\n\n{markdown}"
        return markdown

    # -- HTMLParser 回调 --------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attributes = dict(attrs)

        if tag in {"meta", "link", "base"}:
            return
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = True
            return
        if tag in VOID_TAGS:
            self._handle_void(tag, attributes)
            return

        if tag in HEADING_TAGS:
            self.heading_level = HEADING_TAGS[tag]
            self.parts.append("\n\n" + "#" * self.heading_level + " ")
            return
        if tag in {"p", "section", "article", "header", "footer", "main", "aside", "figure"}:
            self.parts.append("\n\n")
            return
        if tag in {"div", "nav", "dl", "dt", "dd", "figcaption"}:
            self.parts.append("\n")
            return
        if tag == "blockquote":
            self.parts.append("\n> ")
            return
        if tag == "pre":
            self.pre_parts = []
            return
        if tag == "code":
            if self.pre_parts is None:
                self._append_inline("`")
            return
        if tag in {"strong", "b"}:
            self._append_inline("**")
            return
        if tag in {"em", "i"}:
            self._append_inline("*")
            return
        if tag == "a":
            target = self._inline_target()
            target.append("[")
            self.link_stack.append((len(target), attributes.get("href")))
            return
        if tag == "ul" or tag == "ol":
            self.parts.append("\n")
            self.list_stack.append((tag, 0))
            return
        if tag == "li":
            self._start_list_item()
            return
        if tag == "table":
            self.table_rows = []
            return
        if tag == "tr":
            self.table_row = []
            return
        if tag in {"td", "th"}:
            self.cell_parts = []
            return

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"meta", "link", "base"}:
            return
        if tag in SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = False
            return

        if tag in HEADING_TAGS:
            self.heading_level = None
            self.parts.append("\n\n")
            return
        if tag in {"p", "section", "article", "header", "footer", "main", "aside", "figure"}:
            self.parts.append("\n\n")
            return
        if tag in {"div", "nav", "dl", "dt", "dd", "figcaption"}:
            self.parts.append("\n")
            return
        if tag == "blockquote":
            self.parts.append("\n")
            return
        if tag == "pre":
            self._flush_pre()
            return
        if tag == "code":
            if self.pre_parts is None:
                self._append_inline("`")
            return
        if tag in {"strong", "b"}:
            self._append_inline("**")
            return
        if tag in {"em", "i"}:
            self._append_inline("*")
            return
        if tag == "a":
            self._flush_link()
            return
        if tag in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
            self.parts.append("\n")
            return
        if tag == "li":
            return
        if tag in {"td", "th"}:
            self._flush_cell()
            return
        if tag == "tr":
            self._flush_row()
            return
        if tag == "table":
            self._flush_table()
            return

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
            return
        if self.skip_depth:
            return
        if self.pre_parts is not None:
            self.pre_parts.append(data)
            return
        if self.cell_parts is not None:
            self.cell_parts.append(data)
            return
        text = re.sub(r"[ \t\r\n\u00a0]+", " ", data)
        if not text:
            return
        if self.heading_level is None:
            # 命令行提示符或正文里的行首 # 需要转义，避免被当成标题
            text = re.sub(r"(?m)^(\s*)#", r"\1\\#", text)
        self.parts.append(text)

    # -- 内部工具 ---------------------------------------------------------
    def _inline_target(self) -> list[str]:
        return self.cell_parts if self.cell_parts is not None else self.parts

    def _append_inline(self, text: str) -> None:
        if self.pre_parts is not None:
            self.pre_parts.append(text)
        else:
            self._inline_target().append(text)

    def _flush_link(self) -> None:
        if not self.link_stack:
            return
        start, href = self.link_stack.pop()
        target = self._inline_target()
        inner = "".join(target[start:])
        if not inner.strip():
            del target[start - 1 :]
            return
        if href:
            target.append(f"]({href})")
        else:
            # 没有链接地址时去掉方括号，只保留内容
            target[start - 1] = ""

    def _handle_void(self, tag: str, attributes: dict[str, str | None]) -> None:
        if tag == "br":
            self.parts.append("\n")
        elif tag == "hr":
            self.parts.append("\n\n---\n\n")
        elif tag == "img":
            if not self.include_images:
                return
            alt = attributes.get("alt") or ""
            src = attributes.get("src") or ""
            if src:
                self._append_inline(f"![{alt}]({src})")

    def _start_list_item(self) -> None:
        depth = max(0, len(self.list_stack) - 1)
        indent = "  " * depth
        if self.list_stack:
            kind, index = self.list_stack[-1]
            self.list_stack[-1] = (kind, index + 1)
            marker = f"{index + 1}. " if kind == "ol" else "- "
        else:
            marker = "- "
        self.parts.append("\n" + indent + marker)

    def _flush_pre(self) -> None:
        content = "".join(self.pre_parts or []).strip("\n")
        self.pre_parts = None
        if not content.strip():
            return
        fence = "````" if "```" in content else "```"
        self.parts.append(f"\n\n{fence}text\n{content}\n{fence}\n\n")

    def _flush_cell(self) -> None:
        if self.cell_parts is None:
            return
        text = _clean_cell("".join(self.cell_parts))
        self.cell_parts = None
        if self.table_row is not None:
            self.table_row.append(text)

    def _flush_row(self) -> None:
        if self.table_row:
            if self.table_rows is None:
                self.table_rows = []
            self.table_rows.append(self.table_row)
        self.table_row = None

    def _flush_table(self) -> None:
        if self.table_row:
            self._flush_row()
        rows = [row for row in (self.table_rows or []) if row]
        self.table_rows = None
        if not rows:
            return
        width = max(len(row) for row in rows)
        rows = [row + [""] * (width - len(row)) for row in rows]
        lines = [
            "| " + " | ".join(rows[0]) + " |",
            "| " + " | ".join("---" for _ in range(width)) + " |",
        ]
        for row in rows[1:]:
            lines.append("| " + " | ".join(row) + " |")
        self.parts.append("\n\n" + "\n".join(lines) + "\n\n")

    @staticmethod
    def _cleanup(markdown: str) -> str:
        markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")
        markdown = re.sub(r"[ \t]+\n", "\n", markdown)
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)
        markdown = re.sub(r" {2,}", " ", markdown)
        markdown = re.sub(r" +([,.;:!?，。；：！？、）】》])", r"\1", markdown)
        markdown = re.sub(r"([（【《]) +", r"\1", markdown)
        return markdown.strip() + "\n"


def _clean_cell(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("|", r"\|")


def html_to_markdown(
    text: str, *, use_pandoc: bool = False, include_images: bool = True
) -> str:
    """把 HTML 文本转成 Markdown；use_pandoc 时调用外部 pandoc。"""
    if use_pandoc:
        markdown = _html_to_markdown_pandoc(text)
    else:
        markdown = MarkdownConverter(include_images=include_images).convert(text)
    if not include_images:
        markdown = re.sub(r"!\[[^\]\n]*\]\([^)\n]*\)", "", markdown)
    return clean_markdown(markdown)


def clean_markdown(markdown: str) -> str:
    """删除手册导航内容，并去掉指向 HTML 页面的失效链接。"""
    # 「相关链接」索引块：从标题一直删到下一个标题
    markdown = re.sub(
        r"(?ms)^#{1,6}[ \t]*相关链接[ \t]*\n.*?(?=^#{1,6}[ \t]|\Z)",
        "",
        markdown,
    )
    # 父主题导航行
    markdown = re.sub(r"(?m)^\*\*父主题：\*\*.*\n?", "", markdown)
    # 整行只有链接的导航条目
    markdown = re.sub(
        r"(?m)^[ \t]*[-*][ \t]+\*\*\[[^\]\n]+\]\([^)]*\.html?\)\*\*[ \t]*\n?",
        "",
        markdown,
    )
    # 兼容 mk:@MSITStore 链接中带括号和空格的旧路径
    markdown = re.sub(
        r"\[([^\]\n]+)\]\(mk:@MSITStore:[^\n]*?\.html?\)",
        r"\1",
        markdown,
    )
    # 行内 HTML 链接保留文字，去掉失效地址
    markdown = re.sub(
        r"\[([^\]\n]+)\]\([^)\n]*\.html?[^)\n]*\)",
        r"\1",
        markdown,
    )
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip() + "\n"


def _html_to_markdown_pandoc(text: str) -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("未找到 pandoc，请先安装或去掉 --pandoc")
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "in.html"
        target = Path(tmp) / "out.md"
        source.write_text(text, encoding="utf-8")
        run(
            [pandoc, "-f", "html", "-t", "gfm", "--wrap=none", str(source), "-o", str(target)],
            "pandoc 转换失败",
        )
        return target.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 批量转换
# ---------------------------------------------------------------------------


def convert_tree(
    source: Path,
    output: Path,
    *,
    fallback: str,
    use_pandoc: bool,
    include_nav: bool,
    include_images: bool = True,
    merge_file: Path | None = None,
    split_chapters: bool = False,
    title: str = "",
) -> tuple[int, int]:
    """转换目录下所有 HTML，返回（成功数，跳过数）。

    指定 merge_file 时合并成一个 Markdown；指定 split_chapters 时按
    CHM 一级目录输出多个 Markdown；否则按原目录结构逐页输出。
    """
    converted = 0
    skipped = 0
    merged: list[str] = []
    chapter_pages: dict[str, list[str]] = {}
    pages = sorted(
        path for path in source.rglob("*") if path.suffix.lower() in HTML_SUFFIXES
    )
    for page in pages:
        relative = page.relative_to(source)
        if relative.parts[0].lower() in SKIP_DIRS:
            skipped += 1
            continue
        if not include_nav and relative.stem.lower() in NAV_STEMS:
            skipped += 1
            continue
        try:
            text = decode_html(page.read_bytes(), fallback)
            markdown = html_to_markdown(
                text, use_pandoc=use_pandoc, include_images=include_images
            )
        except Exception as exc:  # noqa: BLE001 单页失败不阻断整本手册
            print(f"[跳过] {relative}: {exc}", file=sys.stderr)
            skipped += 1
            continue
        if len(re.sub(r"\s", "", markdown)) < MIN_CONTENT_CHARS:
            skipped += 1
            continue
        if merge_file is not None:
            merged.append(f"<!-- {relative.as_posix()} -->\n\n{markdown}")
        elif split_chapters:
            chapter = relative.parts[0] if len(relative.parts) > 1 else "未分类"
            chapter_pages.setdefault(chapter, []).append(
                f"<!-- {relative.as_posix()} -->\n\n{markdown}"
            )
        else:
            target = output / relative.with_suffix(".md")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(markdown, encoding="utf-8")
        converted += 1

    if merge_file is not None and merged:
        merge_file.parent.mkdir(parents=True, exist_ok=True)
        body = "\n\n---\n\n".join(merged)
        heading = f"# {title}\n\n" if title else ""
        merge_file.write_text(heading + body.rstrip() + "\n", encoding="utf-8")

    if split_chapters and chapter_pages:
        output.mkdir(parents=True, exist_ok=True)
        for chapter, pages_markdown in chapter_pages.items():
            filename = re.sub(r'[<>:"/\\|?*]', "_", chapter).strip() or "未分类"
            body = "\n\n---\n\n".join(pages_markdown)
            target = output / f"{filename}.md"
            target.write_text(f"# {chapter}\n\n{body.rstrip()}\n", encoding="utf-8")
    return converted, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="把 CHM 手册解包并转换为 Markdown")
    parser.add_argument("input", type=Path, help="CHM 文件或已解包的 HTML 目录")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="输出目录；以 .md 结尾时合并为单个文件。默认生成 <名称>_md 目录",
    )
    parser.add_argument(
        "--encoding",
        default="gb18030",
        help="无法识别编码时的兜底编码，默认 gb18030",
    )
    parser.add_argument("--pandoc", action="store_true", help="使用 pandoc 转换（需已安装）")
    parser.add_argument(
        "--split-chapters",
        action="store_true",
        help="按 CHM 一级目录分章输出多个 Markdown（输出必须是目录）",
    )
    parser.add_argument("--keep-html", action="store_true", help="保留解包出来的 HTML")
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="跳过图片，只保留文字（适合用于知识库）",
    )
    parser.add_argument("--include-nav", action="store_true", help="不跳过 toc/index 等导航页")
    args = parser.parse_args()

    source = args.input.expanduser().resolve()
    if not source.exists():
        print(f"输入不存在：{source}", file=sys.stderr)
        return 1

    temp_dirs: list[Path] = []
    if source.is_dir():
        html_dir = source
        default_output = source.with_name(f"{source.name}_md")
    elif source.suffix.lower() == ".chm":
        default_output = source.with_name(f"{source.stem}_md")
        html_dir = source.with_name(f"_{source.stem}_html")
        if html_dir.exists():
            shutil.rmtree(html_dir)
        print(f"[解包] {source.name} -> {html_dir}")
        try:
            unpack_chm(source, html_dir)
            if not wait_for_unpack(html_dir) or not has_html_files(html_dir):
                print("[重试] 直接解包失败，复制到临时短路径重试", file=sys.stderr)
                shutil.rmtree(html_dir, ignore_errors=True)
                retry_root = Path(tempfile.mkdtemp(prefix="chm_unpack_"))
                shutil.copy2(source, retry_root / "manual.chm")
                retry_out = retry_root / "out"
                unpack_chm(retry_root / "manual.chm", retry_out)
                if not wait_for_unpack(retry_out) or not has_html_files(retry_out):
                    shutil.rmtree(retry_root, ignore_errors=True)
                    raise RuntimeError("解包后没有找到 HTML 文件，请确认 CHM 文件是否完整")
                html_dir = retry_out
                temp_dirs.append(retry_root)
                print(f"[解包] 已改用临时目录：{retry_root}")
            elif not args.keep_html:
                temp_dirs.append(html_dir)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            for path in temp_dirs:
                shutil.rmtree(path, ignore_errors=True)
            return 1
    else:
        print(f"不支持的输入类型：{source.suffix or '目录'}", file=sys.stderr)
        return 1

    output = (args.output or default_output).expanduser().resolve()
    merge_file: Path | None = None
    if output.suffix.lower() == ".md":
        if args.split_chapters:
            print("--split-chapters 需要输出目录，-o 不能是 .md 文件", file=sys.stderr)
            return 1
        merge_file = output
        output = output.parent
        print(f"[转换] HTML 目录：{html_dir}")
        print(f"[输出] 合并为单文件：{merge_file}")
    else:
        print(f"[转换] HTML 目录：{html_dir}")
        mode = "按章节拆分" if args.split_chapters else "逐页输出"
        print(f"[输出] {output}（{mode}）")
    converted, skipped = convert_tree(
        html_dir,
        output,
        fallback=args.encoding,
        use_pandoc=args.pandoc,
        include_nav=args.include_nav,
        include_images=not args.no_images,
        merge_file=merge_file,
        split_chapters=args.split_chapters,
        title=source.stem if source.suffix.lower() == ".chm" else "",
    )

    for path in temp_dirs:
        shutil.rmtree(path, ignore_errors=True)

    print(f"[完成] 转换 {converted} 页，跳过 {skipped} 页")
    return 0 if converted else 1


if __name__ == "__main__":
    raise SystemExit(main())
