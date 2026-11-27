"""翻译任务服务：任务创建、查询、取消与 Worker 执行流程。"""

import json
import logging
import time
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Device, TranslationTask, TranslationTaskStatus
from app.repositories.device_repository import DeviceRepository
from app.repositories.translation_repository import TranslationRepository
from app.services import review_item_service
from app.schemas import (
    TranslationCreate,
    TranslationEntityInfo,
    TranslationListItem,
    TranslationOut,
    TranslationResult,
    TranslationResultLines,
    TranslationResultSummary,
    TranslationSourceOut,
    TranslationWarning,
)
from app.translate_rule import get_registry, translate_config
from app.translate_rule.parser import ParsedLine

logger = logging.getLogger(__name__)


class TranslationDispatchError(RuntimeError):
    """任务无法投递到消息队列。"""


class TranslationExecutionError(RuntimeError):
    """翻译前置条件不满足，例如设备档案缺失。"""


def create_translation(
    db: Session, payload: TranslationCreate, user_id: int
) -> TranslationTask:
    repository = TranslationRepository(db)
    task = repository.create(
        TranslationTask(
            user_id=user_id,
            request_id=str(uuid4()),
            source_vendor=payload.source_vendor,
            source_model=payload.source_model,
            target_vendor=payload.target_vendor,
            target_model=payload.target_model,
            source_text=payload.source_text,
        )
    )

    try:
        from app.tasks.translation_task import translate_configuration

        async_result = translate_configuration.delay(task.request_id)
    except Exception as exc:
        task.status = TranslationTaskStatus.failed
        task.error_message = "任务队列不可用，请稍后重试"
        task.finished_at = datetime.now()
        repository.update(task)
        raise TranslationDispatchError(task.error_message) from exc

    task.celery_task_id = async_result.id
    return repository.update(task)


def _get_owned_task(db: Session, request_id: str, user_id: int) -> TranslationTask | None:
    """只返回属于当前用户的任务，他人任务与不存在同样处理，避免泄露记录。"""
    task = TranslationRepository(db).get_by_request_id(request_id)
    if task is None or task.user_id != user_id:
        return None
    return task


def get_translation(db: Session, request_id: str, user_id: int) -> TranslationOut | None:
    task = _get_owned_task(db, request_id, user_id)
    if task is None:
        return None

    result = None
    if task.status == TranslationTaskStatus.succeeded and task.result_json:
        result = TranslationResult.model_validate(json.loads(task.result_json))

    return TranslationOut(
        request_id=task.request_id,
        status=task.status,
        result=result,
        error=task.error_message,
    )


def list_translations(
    db: Session, user_id: int, limit: int = 20
) -> list[TranslationListItem]:
    rows = TranslationRepository(db).list_recent(user_id, limit)
    return [TranslationListItem.model_validate(row) for row in rows]


def get_translation_source(
    db: Session, request_id: str, user_id: int
) -> TranslationSourceOut | None:
    task = _get_owned_task(db, request_id, user_id)
    if task is None:
        return None
    return TranslationSourceOut.model_validate(task)


def cancel_translation(db: Session, request_id: str, user_id: int) -> bool:
    repository = TranslationRepository(db)
    task = _get_owned_task(db, request_id, user_id)
    if task is None:
        return False
    if task.status not in {TranslationTaskStatus.pending, TranslationTaskStatus.running}:
        return True

    if task.celery_task_id:
        from app.tasks.celery_app import celery_app

        celery_app.control.revoke(task.celery_task_id, terminate=True)

    task.status = TranslationTaskStatus.failed
    task.error_message = "任务已取消"
    task.finished_at = datetime.now()
    repository.update(task)
    return True


def run_translation_task(request_id: str) -> None:
    """Celery 执行入口：按知识库把源配置翻译为目标厂商配置。"""
    with SessionLocal() as db:
        repository = TranslationRepository(db)
        task = repository.get_by_request_id(request_id)
        if task is None or task.status != TranslationTaskStatus.pending:
            return

        task.status = TranslationTaskStatus.running
        repository.update(task)
        started = time.perf_counter()

        try:
            result, parsed_lines, source_device, target_device = _translate(db, task)
            task = repository.get_by_request_id(request_id)
            if task is None or task.status != TranslationTaskStatus.running:
                return

            result.summary.duration_ms = int((time.perf_counter() - started) * 1000)
            task.result_json = json.dumps(result.model_dump(), ensure_ascii=False)
            task.status = TranslationTaskStatus.succeeded
            task.error_message = None
            task.finished_at = datetime.now()
            repository.update(task)

            # 告警段物化为审核条目；失败只记日志，不影响翻译结果
            try:
                review_item_service.materialize_task_items(
                    db,
                    task,
                    result,
                    parsed_lines,
                    source_device=source_device,
                    target_device=target_device,
                )
            except Exception:
                logger.exception("审核条目物化失败 request_id=%s", request_id)
        except TranslationExecutionError as exc:
            _mark_failed(db, repository, request_id, str(exc))
        except Exception as exc:
            _mark_failed(db, repository, request_id, f"翻译任务执行失败：{exc}")


def _translate(
    db: Session, task: TranslationTask
) -> tuple[TranslationResult, list[ParsedLine], Device, Device]:
    """查询设备档案并调用知识库完成翻译。"""
    device_repository = DeviceRepository(db)
    source_device = device_repository.find_by_vendor_and_model(task.source_vendor, task.source_model)
    if source_device is None:
        raise TranslationExecutionError(
            f"未找到源设备档案：{task.source_vendor} {task.source_model}"
        )
    target_device = device_repository.find_by_vendor_and_model(task.target_vendor, task.target_model)
    if target_device is None:
        raise TranslationExecutionError(
            f"未找到目标设备档案：{task.target_vendor} {task.target_model}"
        )

    registry = get_registry()
    output = translate_config(
        task.source_text,
        source_vendor=_vendor_key(source_device),
        source_device_type=source_device.device_type.value,
        target_vendor=_vendor_key(target_device),
        target_device_type=target_device.device_type.value,
        registry=registry,
    )

    # 按 entity_targets 构建：每个实体的联动元数据（source_nos + target_line_indices）
    entity_list: list[TranslationEntityInfo] = []
    for entity_id, target in output.entity_targets.items():
        spec = registry.get_entity(entity_id)
        entity_list.append(
            TranslationEntityInfo(
                id=entity_id,
                source_nos=list(target.source_nos),
                command_nos=list(target.command_nos),
                target_line_indices=list(target.target_line_indices),
                description=spec.description if spec else None,
            )
        )

    # 告警关联 entity_id：warning.no 与 entity.source_nos 做交集匹配
    entity_source_nos_map = {
        entity_id: set(target.source_nos)
        for entity_id, target in output.entity_targets.items()
    }
    warnings_out: list[TranslationWarning] = []
    for warning in output.warnings:
        # 找出 source_nos 与 warning.no 交集最大的 entity；
        # 交集相同时取覆盖更完整（source_nos 更多）的实体，视图行告警归入含命令行的整段
        warning_nos = set(warning.no)
        matched_entity_id: str | None = None
        best_overlap = 0
        best_size = 0
        for eid, source_nos in entity_source_nos_map.items():
            overlap = len(warning_nos & source_nos)
            if overlap > best_overlap or (overlap == best_overlap and len(source_nos) > best_size):
                best_overlap = overlap
                best_size = len(source_nos)
                matched_entity_id = eid
        warnings_out.append(
            TranslationWarning(
                entity_id=matched_entity_id,
                no=list(warning.no),
                message=warning.message,
                code=warning.code,
                severity=warning.severity,
            )
        )

    return (
        TranslationResult(
            lines=[
                TranslationResultLines(text=line.text, tone=line.tone)
                for line in output.lines
            ],
            line_source_nos=list(output.line_source_nos),
            entities=entity_list,
            warnings=warnings_out,
            summary=TranslationResultSummary(
                total=output.summary["total"],
                duration_ms=output.summary["duration_ms"],
            ),
        ),
        output.parsed_lines,
        source_device,
        target_device,
    )


def _vendor_key(device: Device) -> str:
    if not device.vendor_en:
        raise TranslationExecutionError(
            f"设备档案缺少厂商英文名：{device.vendor} {device.model}"
        )
    return device.vendor_en.strip().lower()


def _mark_failed(
    db: Session,
    repository: TranslationRepository,
    request_id: str,
    message: str,
) -> None:
    db.rollback()
    task = repository.get_by_request_id(request_id)
    if task is None or task.status == TranslationTaskStatus.failed:
        return
    task.status = TranslationTaskStatus.failed
    task.error_message = message[:1024]
    task.finished_at = datetime.now()
    repository.update(task)
