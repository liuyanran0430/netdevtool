"""知识缺口服务：翻译成功后采集未识别命令并聚合。"""

import logging

from sqlalchemy.orm import Session

from app.models import DeviceType, KnowledgeGap, KnowledgeGapKind
from app.repositories.knowledge_gap_repository import KnowledgeGapRepository
from app.schemas import TranslationResult
from app.translate_rule.candidate import is_sensitive, normalize_command_template
from app.translate_rule.parser import ParsedLine

logger = logging.getLogger(__name__)

# 目标侧实现质量问题：命令已识别，但目标实现缺失、未验证或置信度偏低
TARGET_WARNING_CODES = frozenset({"unsupported_entity", "unverified_impl", "low_confidence"})


def collect_gaps(
    db: Session,
    *,
    request_id: str,
    source_vendor: str,
    source_device_type: str,
    product: str,
    os: str | None,
    parsed_lines: list[ParsedLine],
    result: TranslationResult | None = None,
    target_vendor: str = "",
    target_device_type: str = "",
) -> int:
    """把翻译过程中的知识质量问题归一化后聚合到 knowledge_gaps。

    - 源侧未识别命令：`unknown_source`，目标维度为空，可供任意目标设备生成补充规则
    - 目标侧实现问题（不支持 / 未验证 / 低置信度）：`missing_target_impl`，
      按目标厂商与目标设备类型区分，避免不同目标互相覆盖

    同一次翻译内重复出现的命令在落库前按模板去重，每个模板只累加一次；
    敏感命令（密码、密钥、团体名）不落库，由审核页标记为需人工处理。
    """
    repository = KnowledgeGapRepository(db)
    device_type = DeviceType(source_device_type)
    seen: set[str] = set()
    collected = 0
    for line in parsed_lines:
        if line.kind != "other":
            continue
        text = line.text.strip()
        if not text or text.startswith(("#", "!")):
            continue
        if is_sensitive(text):
            continue
        command_template = normalize_command_template(text)
        if command_template in seen:
            continue
        seen.add(command_template)
        repository.upsert(
            vendor=source_vendor,
            device_type=device_type,
            product=product,
            os=os,
            view=line.view,
            command_template=command_template,
            raw_sample=text,
            request_id=request_id,
            kind=KnowledgeGapKind.unknown_source,
        )
        collected += 1

    if result is not None and target_vendor:
        collected += _collect_target_gaps(
            repository,
            request_id=request_id,
            source_vendor=source_vendor,
            device_type=device_type,
            product=product,
            os=os,
            parsed_lines=parsed_lines,
            result=result,
            target_vendor=target_vendor,
            target_device_type=target_device_type,
        )
    return collected


def _collect_target_gaps(
    repository: KnowledgeGapRepository,
    *,
    request_id: str,
    source_vendor: str,
    device_type: DeviceType,
    product: str,
    os: str | None,
    parsed_lines: list[ParsedLine],
    result: TranslationResult,
    target_vendor: str,
    target_device_type: str,
) -> int:
    """从结果告警反查源行，采集目标侧实现缺口。"""
    parsed_by_no = {line.no: line for line in parsed_lines}
    entity_line_by_source: dict[int, str] = {}
    for line in result.lines:
        if line.source_no is not None and line.entity_id:
            entity_line_by_source.setdefault(line.source_no, line.entity_id)

    seen: set[tuple[str, str]] = set()
    collected = 0
    for warning in result.warnings:
        if warning.code not in TARGET_WARNING_CODES:
            continue
        if warning.no not in entity_line_by_source:
            continue
        parsed = parsed_by_no.get(warning.no)
        if parsed is None:
            continue
        text = parsed.text.strip()
        if not text or is_sensitive(text):
            continue
        command_template = normalize_command_template(text)
        key = (target_vendor, command_template)
        if key in seen:
            continue
        seen.add(key)
        repository.upsert(
            vendor=source_vendor,
            device_type=device_type,
            product=product,
            os=os,
            view=parsed.view,
            command_template=command_template,
            raw_sample=text,
            request_id=request_id,
            kind=KnowledgeGapKind.missing_target_impl,
            target_vendor=target_vendor,
            target_device_type=target_device_type,
        )
        collected += 1
    return collected


def list_gaps(
    db: Session,
    *,
    limit: int = 20,
    kind: str | None = None,
    status: str | None = None,
    vendor: str | None = None,
) -> list[KnowledgeGap]:
    kind_value = KnowledgeGapKind(kind) if kind else None
    return KnowledgeGapRepository(db).list(
        limit=limit, kind=kind_value, status=status, vendor=vendor
    )


def get_gap(db: Session, gap_id: int) -> KnowledgeGap | None:
    return KnowledgeGapRepository(db).get(gap_id)
