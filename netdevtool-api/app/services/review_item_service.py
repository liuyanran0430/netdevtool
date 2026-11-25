"""审核条目服务：翻译成功时物化条目，审核页按页读取。

物化后审核页不再解析 `translation_tasks.result_json`，读路径固定为
「分页 + 统计 + 筛选项 + 候选」几条批量查询，与任务数量无关。
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re

from sqlalchemy.orm import Session

from app.models import (
    Device,
    KnowledgeGapKind,
    ReviewDecision,
    ReviewItem,
    SupplementCandidate,
    TranslationTask,
)
from app.repositories.device_repository import DeviceRepository
from app.repositories.knowledge_gap_repository import KnowledgeGapRepository
from app.repositories.review_item_repository import ReviewItemRepository
from app.repositories.supplement_candidate_repository import SupplementCandidateRepository
from app.repositories.translation_repository import TranslationRepository
from app.schemas import (
    ReviewCandidateOut,
    ReviewDecisionOut,
    ReviewDecisionSnapshotOut,
    ReviewHistoryItemOut,
    ReviewHistoryPageOut,
    ReviewItemOut,
    ReviewItemsPageOut,
    ReviewStatsOut,
    ReviewTargetOptionOut,
    TranslationResult,
)
from app.translate_rule.candidate import normalize_command_template

logger = logging.getLogger(__name__)

# 接口名映射、参数校验失败与显示命令转换不进入审核池，仅在翻译页审计面板处理
EXCLUDED_CODES = frozenset(
    {"intf_translated", "intf_unmapped", "invalid_param", "display_command"}
)

QUIT_RE = re.compile(r"^quit$", re.IGNORECASE)
VIEW_FLUSH_RE = re.compile(r"^[#!]$")

# 会进入配置视图的源命令行 → 视图名称
VIEW_ENTER_RULES = (
    (re.compile(r"^interface\s+\S+", re.IGNORECASE), "interface"),
    (re.compile(r"^ospf\s+", re.IGNORECASE), "ospf"),
    (re.compile(r"^bgp\s+", re.IGNORECASE), "bgp"),
    (re.compile(r"^vlan\s+\d+", re.IGNORECASE), "vlan"),
    (re.compile(r"^user-interface\s+", re.IGNORECASE), "user-interface"),
    (re.compile(r"^acl\s+", re.IGNORECASE), "acl"),
    (re.compile(r"^aaa\s*$", re.IGNORECASE), "aaa"),
)

SEVERITY_RANK = {"error": 0, "warn": 1}
CODE_PRIORITY = {"unknown_command": 0, "unsupported_entity": 1}


def build_item_key(
    *,
    source_vendor: str,
    source_model: str,
    target_vendor: str,
    target_model: str,
    source_text: str,
) -> str:
    """稳定命令标识：由源/目标设备与归一化命令生成，供审核处置跨任务复用。"""
    raw = json.dumps(
        [
            source_vendor,
            source_model,
            target_vendor,
            target_model,
            normalize_command_template(source_text),
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def materialize_task_items(
    db: Session,
    task: TranslationTask,
    result: TranslationResult | None = None,
    source_device: Device | None = None,
) -> int:
    """把一条已成功任务的告警行物化为审核条目。

    `result` 为空时从 `task.result_json` 解析并做契约校验。返回写入的条目数
    （同一任务内按命令去重）。物化失败由调用方记录日志，不影响主流程。
    """
    if task.user_id is None:
        return 0

    if result is None:
        if not task.result_json:
            return 0
        try:
            result = TranslationResult.model_validate_json(task.result_json)
        except Exception:
            logger.exception("审核条目物化失败：结果解析异常 request_id=%s", task.request_id)
            return 0

    source_lines = [line.rstrip("\r") for line in task.source_text.split("\n")]
    views = _views_of_lines(source_lines)

    if source_device is None:
        source_device = DeviceRepository(db).find_by_vendor_and_model(
            task.source_vendor, task.source_model
        )
    gap_map = _gap_map(db, source_device)

    rows: list[dict] = []
    seen: set[str] = set()
    # 直接从 warnings 出发构建审核条目：每条 warning 自带 no（源行号）和 entity_id
    for warning in result.warnings:
        if warning.code in EXCLUDED_CODES:
            continue
        for source_no in warning.no:
            source_text = _source_line(source_lines, source_no)
            if source_text is None:
                continue
            item_key = build_item_key(
                source_vendor=task.source_vendor,
                source_model=task.source_model,
                target_vendor=task.target_vendor,
                target_model=task.target_model,
                source_text=source_text,
            )
            if item_key in seen:
                continue
            seen.add(item_key)

            code = warning.code or "unknown"
            severity = warning.severity or "warn"
            template = normalize_command_template(source_text) if source_text else ""
            rows.append(
                {
                    "user_id": task.user_id,
                    "item_key": item_key,
                    "request_id": task.request_id,
                    "line_index": source_no,  # 简化：用源行号代替目标行索引
                    "source_no": source_no,
                    "source_vendor": task.source_vendor,
                    "source_model": task.source_model,
                    "target_vendor": task.target_vendor,
                    "target_model": task.target_model,
                    "view": _view_at(views, source_no),
                    "source_text": source_text,
                    "codes": [code],
                    "code_csv": code,
                    "severity": severity,
                    "severity_rank": SEVERITY_RANK.get(severity, 1),
                    "code_priority": _code_priority([code]),
                    "message": warning.message,
                    "gap_id": gap_map.get(template) if template else None,
                    "created_at": task.created_at,
                }
            )

    if not rows:
        return 0
    ReviewItemRepository(db).upsert_many(rows)
    return len(rows)


def rebuild_all_review_items(db: Session) -> int:
    """清空并按全部已成功任务重建物化条目，仅用于升级后的一次性回填。"""
    ReviewItemRepository(db).delete_all()
    total = 0
    for task in TranslationRepository(db).list_all_succeeded():
        total += materialize_task_items(db, task)
    return total


def list_items_page(
    db: Session,
    *,
    user_id: int,
    page: int,
    page_size: int,
    target_vendor: str | None,
    target_model: str | None,
    code: str | None,
) -> ReviewItemsPageOut:
    """只返回待审核条目：命令处置后即从列表消失，撤销后重新出现。"""
    repository = ReviewItemRepository(db)
    total = repository.count(
        user_id=user_id,
        target_vendor=target_vendor,
        target_model=target_model,
        code=code,
    )
    total_pages = max(1, math.ceil(total / page_size))
    actual_page = min(page, total_pages)
    items = repository.list_page(
        user_id=user_id,
        target_vendor=target_vendor,
        target_model=target_model,
        code=code,
        offset=(actual_page - 1) * page_size,
        limit=page_size,
    )

    gap_ids = sorted({item.gap_id for item in items if item.gap_id is not None})
    candidates = SupplementCandidateRepository(db).latest_by_gaps(gap_ids)
    candidate_map = {gap_id: candidate_out(candidate) for gap_id, candidate in candidates.items()}

    item_outs = [
        _item_out(item, candidate_map.get(item.gap_id) if item.gap_id is not None else None)
        for item in items
    ]

    actions = repository.stats(user_id)
    stats = ReviewStatsOut(
        pending=repository.count(user_id=user_id),
        accepted=actions.get("accept", 0),
        edited=actions.get("edit", 0),
        skipped=actions.get("skip", 0),
    )
    target_options = [
        ReviewTargetOptionOut(vendor=vendor, model=model)
        for vendor, model in repository.list_target_options(user_id)
    ]
    return ReviewItemsPageOut(
        items=item_outs,
        total=total,
        page=actual_page,
        page_size=page_size,
        stats=stats,
        target_options=target_options,
        code_options=repository.list_code_options(user_id),
    )


def list_history_page(
    db: Session,
    *,
    user_id: int,
    page: int,
    page_size: int,
    action: str,
    keyword: str | None,
) -> ReviewHistoryPageOut:
    """分页读取处置记录，按处置时间倒序；不修改审核状态。"""
    repository = ReviewItemRepository(db)
    total = repository.count_history(user_id=user_id, action=action, keyword=keyword)
    total_pages = max(1, math.ceil(total / page_size))
    actual_page = min(page, total_pages)
    rows = repository.list_history_page(
        user_id=user_id,
        action=action,
        keyword=keyword,
        offset=(actual_page - 1) * page_size,
        limit=page_size,
    )
    items = [
        ReviewHistoryItemOut(
            item_key=decision.item_key,
            action=decision.action,
            decided_text=decision.decided_text,
            request_id=item.request_id,
            source_vendor=item.source_vendor,
            source_model=item.source_model,
            target_vendor=item.target_vendor,
            target_model=item.target_model,
            view=item.view,
            source_text=item.source_text,
            target_text=item.target_text,
            codes=list(item.codes or []),
            severity=item.severity,
            candidate=candidate_out(candidate) if candidate is not None else None,
            created_at=decision.created_at,
            updated_at=decision.updated_at,
        )
        for decision, item, candidate in rows
    ]
    return ReviewHistoryPageOut(
        items=items,
        total=total,
        page=actual_page,
        page_size=page_size,
    )


def list_decision_snapshots(db: Session, user_id: int) -> list[ReviewDecisionSnapshotOut]:
    """当前用户全部处置及来源行信息，供审核页生成检查点。"""
    return [
        ReviewDecisionSnapshotOut(
            request_id=item.request_id,
            line_index=item.line_index,
            action=decision.action,
            decided_text=decision.decided_text,
            original_tone=item.original_tone,
        )
        for decision, item in ReviewItemRepository(db).list_decisions_with_items(user_id)
    ]


def decision_out(decision: ReviewDecision) -> ReviewDecisionOut:
    return ReviewDecisionOut(
        item_key=decision.item_key,
        action=decision.action,
        decided_text=decision.decided_text,
        candidate_id=decision.candidate_id,
    )


def candidate_out(candidate: SupplementCandidate) -> ReviewCandidateOut:
    response = _json_dict(candidate.response_json)
    validation = _json_dict(candidate.validation_json)
    views = response.get("target_view_path")
    return ReviewCandidateOut(
        id=candidate.id,
        status=candidate.status,
        command=response.get("target_command"),
        views=[view for view in views if isinstance(view, str)] if isinstance(views, list) else [],
        reasoning=response.get("reasoning"),
        passed=bool(validation.get("passed")),
        created_at=candidate.created_at,
    )


def _item_out(item: ReviewItem, candidate: ReviewCandidateOut | None) -> ReviewItemOut:
    return ReviewItemOut(
        request_id=item.request_id,
        line_index=item.line_index,
        item_key=item.item_key,
        source_no=item.source_no,
        codes=list(item.codes or []),
        severity=item.severity,
        source_vendor=item.source_vendor,
        source_model=item.source_model,
        target_vendor=item.target_vendor,
        target_model=item.target_model,
        gap_id=item.gap_id,
        candidate=candidate,
        view=item.view,
        source_text=item.source_text,
        target_text=item.target_text,
        message=item.message,
        created_at=item.created_at,
    )


def _gap_map(db: Session, device: Device | None) -> dict[str, int]:
    """命令模板 → 缺口 id，仅关联源侧未识别缺口（补充库只能覆盖核心层缺失的实现）。"""
    if device is None or not device.vendor_en:
        return {}
    gaps = KnowledgeGapRepository(db).list_by_scope(
        vendor=device.vendor_en.strip().lower(), product=device.model
    )
    return {
        gap.command_template: gap.id
        for gap in gaps
        if gap.kind == KnowledgeGapKind.unknown_source and not gap.target_vendor
    }


def _source_line(source_lines: list[str], source_no: int | None) -> str:
    if source_no is None or not (0 < source_no <= len(source_lines)):
        return ""
    return source_lines[source_no - 1]


def _views_of_lines(source_lines: list[str]) -> list[str]:
    """一次线性扫描得到每行处理完后的视图，避免逐条从头重放视图栈。"""
    stack: list[str] = []
    views: list[str] = []
    for raw in source_lines:
        text = raw.strip()
        if not text or VIEW_FLUSH_RE.match(text):
            stack.clear()
        elif QUIT_RE.match(text):
            if stack:
                stack.pop()
        else:
            for pattern, name in VIEW_ENTER_RULES:
                if pattern.match(text):
                    stack.append(name)
                    break
        views.append(stack[-1] if stack else "system-view")
    return views


def _view_at(views: list[str], source_no: int | None) -> str:
    """命令所在视图：取该行之前已处理完的视图状态。"""
    if source_no is None or source_no <= 1:
        return "system-view"
    index = source_no - 2
    if index >= len(views):
        index = len(views) - 1
    return views[index] if index >= 0 else "system-view"


def _code_priority(codes: list[str]) -> int:
    priorities = [CODE_PRIORITY[code] for code in codes if code in CODE_PRIORITY]
    return min(priorities) if priorities else len(CODE_PRIORITY)


def _json_dict(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}
