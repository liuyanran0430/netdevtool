"""审核条目物化：翻译成功后把三类告警段写入 review_items。

进入审核条目的三种情况：
1. 源侧未识别（unknown_source）：连续未识别行聚合为一段；
   遇到注释（#）、视图退出/返回（quit/return）或已识别命令即切段
2. 目标侧无实现（missing_target_impl）：对应 renderer 告警 unsupported_entity
3. 源或目标侧未验证（unverified_impl）：实现 verified=false

条目哈希 item_hash = sha1(src_dev_id + dest_dev_id + source_text)，跨任务去重。
"""

from __future__ import annotations

import hashlib
import json
import logging
import math

from sqlalchemy.orm import Session

from app.models import Device, ReviewItem, ReviewItemType, ReviewStatus, TranslationTask
from app.repositories.review_item_repository import ReviewItemRepository
from app.schemas import (
    ReviewItemOut,
    ReviewItemsPageOut,
    ReviewStatsOut,
    ReviewTargetOptionOut,
    TranslationResult,
)
from app.translate_rule.parser import ParsedLine

logger = logging.getLogger(__name__)

# 目标侧告警码 → 审核条目类型
_TYPE_BY_CODE = {
    "unsupported_entity": ReviewItemType.missing_target_impl,
    "unverified_impl": ReviewItemType.unverified_impl,
}


def build_item_hash(
    src_dev_id: int | None, dest_dev_id: int | None, source_text: list[str]
) -> str:
    """条目哈希：设备对 + 源侧段文本，与去重唯一键一致。"""
    raw = json.dumps(
        [src_dev_id, dest_dev_id, *source_text],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def materialize_task_items(
    db: Session,
    task: TranslationTask,
    result: TranslationResult,
    parsed_lines: list[ParsedLine],
    *,
    source_device: Device | None = None,
    target_device: Device | None = None,
) -> int:
    """把一条已成功任务的告警段物化为审核条目，返回写入的段数。

    物化失败由调用方记录日志，不影响翻译主流程。
    """
    if task.user_id is None:
        return 0

    source_lines = [line.rstrip("\r") for line in task.source_text.split("\n")]
    src_dev_id = source_device.id if source_device is not None else None
    dest_dev_id = target_device.id if target_device is not None else None

    # 源行号 → 目标结果行下标：取目标文本与 tone
    source_to_target: dict[int, list[int]] = {}
    for index, src_no in enumerate(result.line_source_nos):
        if src_no is not None:
            source_to_target.setdefault(src_no, []).append(index)

    entity_by_id = {entity.id: entity for entity in result.entities}
    rows: list[dict] = []
    seen: set[str] = set()

    def _add_row(
        item_type: ReviewItemType,
        source_nos: list[int],
        entities_id: list[str] | None,
    ) -> None:
        # 段文本按源配置行号升序排列，保持源侧原始顺序（视图行在前）
        ordered = sorted(set(source_nos))
        texts = [
            source_lines[no - 1].rstrip()
            for no in ordered
            if 0 < no <= len(source_lines)
        ]
        if not texts:
            return
        item_hash = build_item_hash(src_dev_id, dest_dev_id, texts)
        if item_hash in seen:
            return
        seen.add(item_hash)
        indexes = [i for no in ordered for i in source_to_target.get(no, [])]
        original_tone = (
            result.lines[indexes[-1]].tone if indexes else "warn"
        )
        rows.append(
            {
                "user_id": task.user_id,
                "item_hash": item_hash,
                "request_id": task.request_id,
                "src_dev_id": src_dev_id,
                "dest_dev_id": dest_dev_id,
                "source_text": texts,
                "original_tone": original_tone,
                "type": item_type,
                "status": ReviewStatus.pending,
                "entities_id": entities_id,
                "created_at": task.created_at,
            }
        )

    # 1) 源侧未识别：连续 other 行聚段，任何非 other 行（#/quit/return/已识别命令）切段
    run: list[int] = []
    for line in parsed_lines:
        if line.kind == "other":
            run.append(line.no)
        elif run:
            _add_row(ReviewItemType.unknown_source, run, None)
            run = []
    if run:
        _add_row(ReviewItemType.unknown_source, run, None)

    # 2/3) 目标侧无实现 / 未验证：按实体段写入
    for warning in result.warnings:
        item_type = _TYPE_BY_CODE.get(warning.code)
        if item_type is None:
            continue
        entity = entity_by_id.get(warning.entity_id or "")
        if entity is None:
            # 告警无实体 id 时按源行号反查：交集最大者优先，
            # 交集相同取覆盖更完整的实体（视图行归入含命令行的整段）
            warning_nos = set(warning.no)
            candidates = [
                e
                for e in result.entities
                if warning_nos.intersection(e.source_nos)
            ]
            entity = max(
                candidates,
                key=lambda e: (
                    len(warning_nos.intersection(e.source_nos)),
                    len(e.source_nos),
                ),
                default=None,
            )
        if entity is None:
            continue
        _add_row(item_type, list(entity.source_nos), [entity.id])

    if not rows:
        return 0
    ReviewItemRepository(db).upsert_many(rows)
    return len(rows)


def list_items_page(
    db: Session,
    *,
    user_id: int,
    page: int,
    page_size: int,
    target_vendor: str | None = None,
    target_model: str | None = None,
    item_type: str | None = None,
) -> ReviewItemsPageOut:
    """审核页分页读取：待审条目 + 全局统计 + 筛选项（只读，处置未实现）。"""
    repository = ReviewItemRepository(db)
    total = repository.count(
        user_id=user_id,
        dest_vendor=target_vendor,
        dest_model=target_model,
        item_type=item_type,
    )
    total_pages = max(1, math.ceil(total / page_size))
    actual_page = min(page, total_pages)
    rows = repository.list_page(
        user_id=user_id,
        dest_vendor=target_vendor,
        dest_model=target_model,
        item_type=item_type,
        offset=(actual_page - 1) * page_size,
        limit=page_size,
    )

    items = [
        ReviewItemOut(
            item_hash=item.item_hash,
            request_id=item.request_id,
            type=item.type.value,
            status=item.status.value,
            source_text=list(item.source_text or []),
            original_tone=item.original_tone,
            entities_id=list(item.entities_id or []) or None,
            source_vendor=source_vendor,
            source_model=source_model,
            target_vendor=target_vendor,
            target_model=target_model,
            created_at=item.created_at,
        )
        for item, source_vendor, source_model, target_vendor, target_model in rows
    ]

    status_counts = repository.stats(user_id)
    return ReviewItemsPageOut(
        items=items,
        total=total,
        page=actual_page,
        page_size=page_size,
        stats=ReviewStatsOut(
            pending=status_counts.get(ReviewStatus.pending, 0),
            accepted=status_counts.get(ReviewStatus.accepted, 0),
            rejected=status_counts.get(ReviewStatus.rejected, 0),
        ),
        target_options=[
            ReviewTargetOptionOut(vendor=vendor, model=model)
            for vendor, model in repository.list_target_options(user_id)
        ],
        type_options=repository.list_type_options(user_id),
    )
