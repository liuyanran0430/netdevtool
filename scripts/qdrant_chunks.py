"""读取 Qdrant 中的切片内容（本地调试用）。

用法示例：
    列出集合与别名：
        netdevtool-api\\.venv\\Scripts\\python.exe scripts\\qdrant_chunks.py

    查看某个集合的前 5 条切片：
        ... qdrant_chunks.py --collection troubleshooting_manual --limit 5

    查看某篇文档的切片：
        ... qdrant_chunks.py --collection troubleshooting_manual --doc-id 10 --limit 20

    按关键词过滤（客户端扫描）：
        ... qdrant_chunks.py --collection troubleshooting_manual --keyword VLAN

    输出原始 JSON：
        ... qdrant_chunks.py --collection troubleshooting_manual --json

默认从 netdevtool-api/.env 读取 QDRANT_URL、QDRANT_API_KEY；
也可用 --url / --api-key 覆盖。依赖 qdrant-client（已随后端安装）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / "netdevtool-api" / ".env"


def load_env() -> dict[str, str]:
    """轻量读取 .env，避免额外依赖。"""
    values: dict[str, str] = {}
    if not ENV_FILE.is_file():
        return values
    for raw in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def build_filter(args: argparse.Namespace) -> Filter | None:
    conditions = []
    if args.doc_id is not None:
        conditions.append(
            FieldCondition(key="doc_id", match=MatchValue(value=args.doc_id))
        )
    if args.chunk_type:
        conditions.append(
            FieldCondition(key="chunk_type", match=MatchValue(value=args.chunk_type))
        )
    return Filter(must=conditions) if conditions else None


def list_collections(client: QdrantClient) -> None:
    collections = [item.name for item in client.get_collections().collections]
    aliases = [
        (item.alias_name, item.collection_name)
        for item in client.get_aliases().aliases
    ]
    print(f"collections ({len(collections)}):")
    for name in collections:
        print(f"  - {name}")
    print(f"aliases ({len(aliases)}):")
    for alias, collection in aliases:
        print(f"  - {alias} -> {collection}")


def scroll_records(
    client: QdrantClient,
    collection: str,
    scroll_filter: Filter | None,
    limit: int,
    offset: Any,
    keyword: str | None,
    scan_limit: int,
) -> tuple[list[Any], Any, int]:
    """读取记录；关键词模式下在客户端过滤。"""
    if not keyword:
        records, next_offset = client.scroll(
            collection_name=collection,
            scroll_filter=scroll_filter,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        return records, next_offset, len(records)

    lowered = keyword.lower()
    matched: list[Any] = []
    scanned = 0
    current = offset
    page_size = min(max(limit, 32), 256)
    while scanned < scan_limit and len(matched) < limit:
        records, current = client.scroll(
            collection_name=collection,
            scroll_filter=scroll_filter,
            limit=page_size,
            offset=current,
            with_payload=True,
            with_vectors=False,
        )
        if not records:
            break
        scanned += len(records)
        for record in records:
            text = str((record.payload or {}).get("text", ""))
            if lowered in text.lower():
                matched.append(record)
                if len(matched) >= limit:
                    break
        if current is None:
            break
    return matched, current, scanned


def print_record(index: int, record: Any, max_chars: int) -> None:
    payload = record.payload or {}
    title = " | ".join(
        f"{key}={payload[key]}"
        for key in ("doc_id", "file_name", "chunk_type", "chunk_index")
        if key in payload
    )
    print(f"[{index}] id={record.id} {title}")
    text = str(payload.get("text", "")).replace("\r\n", "\n")
    if max_chars > 0 and len(text) > max_chars:
        text = text[:max_chars] + "..."
    for line in text.splitlines() or [""]:
        print(f"    {line}")
    if "parent_text" in payload:
        parent = str(payload["parent_text"])
        if len(parent) > max_chars:
            parent = parent[:max_chars] + "..."
        print(f"    parent: {parent}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="读取 Qdrant 中的切片内容")
    parser.add_argument("--collection", help="集合名或别名；不填则列出所有集合")
    parser.add_argument("--url", help="Qdrant 地址，默认读取 .env 的 QDRANT_URL")
    parser.add_argument("--api-key", help="Qdrant API Key，默认读取 .env")
    parser.add_argument("--doc-id", type=int, help="只读取指定文档 ID 的切片")
    parser.add_argument(
        "--chunk-type",
        choices=["chunk", "parent", "child"],
        help="只读取指定类型的切片",
    )
    parser.add_argument("--keyword", help="按切片正文做客户端关键词过滤")
    parser.add_argument("--limit", type=int, default=10, help="最多输出条数")
    parser.add_argument("--offset", help="分页游标（上一次输出的 next_offset）")
    parser.add_argument(
        "--scan-limit", type=int, default=1000, help="关键词模式最多扫描条数"
    )
    parser.add_argument("--max-chars", type=int, default=300, help="正文最多字符数，0 表示不截断")
    parser.add_argument("--json", action="store_true", help="输出原始 JSON")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    env = load_env()
    url = args.url or env.get("QDRANT_URL") or "http://127.0.0.1:6333"
    api_key = args.api_key or env.get("QDRANT_API_KEY") or None

    client = QdrantClient(url=url, api_key=api_key, timeout=30)
    try:
        if not args.collection:
            list_collections(client)
            return 0

        scroll_filter = build_filter(args)
        records, next_offset, scanned = scroll_records(
            client,
            args.collection,
            scroll_filter,
            max(args.limit, 1),
            args.offset,
            args.keyword,
            max(args.scan_limit, 1),
        )

        total = client.count(
            collection_name=args.collection,
            count_filter=scroll_filter,
            exact=True,
        ).count
        print(f"collection={args.collection} url={url}")
        print(
            f"total={total} shown={len(records)}"
            + (f" scanned={scanned}" if args.keyword else "")
        )

        if args.json:
            data = [
                {"id": record.id, "payload": record.payload} for record in records
            ]
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for index, record in enumerate(records, start=1):
                print_record(index, record, max(args.max_chars, 0))
            if next_offset is not None and not args.keyword:
                print(f"next_offset={next_offset}")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
