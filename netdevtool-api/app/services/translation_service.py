"""翻译任务服务：任务创建、查询、取消与 Worker 执行流程。"""

import json
import time
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Device, TranslationTask, TranslationTaskStatus
from app.repositories.device_repository import DeviceRepository
from app.repositories.translation_repository import TranslationRepository
from app.schemas import (
    TranslationCreate,
    TranslationEntityInfo,
    TranslationOut,
    TranslationResult,
    TranslationResultLine,
    TranslationResultSummary,
    TranslationWarning,
)
from app.translate_rule import get_registry, translate_config


class TranslationDispatchError(RuntimeError):
    """任务无法投递到消息队列。"""


class TranslationExecutionError(RuntimeError):
    """翻译前置条件不满足，例如设备档案缺失。"""


def create_translation(db: Session, payload: TranslationCreate) -> TranslationTask:
    repository = TranslationRepository(db)
    task = repository.create(
        TranslationTask(
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


def get_translation(db: Session, request_id: str) -> TranslationOut | None:
    task = TranslationRepository(db).get_by_request_id(request_id)
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


def cancel_translation(db: Session, request_id: str) -> bool:
    repository = TranslationRepository(db)
    task = repository.get_by_request_id(request_id)
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
            result = _translate(db, task)
            task = repository.get_by_request_id(request_id)
            if task is None or task.status != TranslationTaskStatus.running:
                return

            result.summary.duration_ms = int((time.perf_counter() - started) * 1000)
            task.result_json = json.dumps(result.model_dump(), ensure_ascii=False)
            task.status = TranslationTaskStatus.succeeded
            task.error_message = None
            task.finished_at = datetime.now()
            repository.update(task)
        except TranslationExecutionError as exc:
            _mark_failed(db, repository, request_id, str(exc))
        except Exception as exc:
            _mark_failed(db, repository, request_id, f"翻译任务执行失败：{exc}")


def _translate(db: Session, task: TranslationTask) -> TranslationResult:
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

    entity_ids: list[str] = []
    for line in output.lines:
        if line.entity_id and line.entity_id not in entity_ids:
            entity_ids.append(line.entity_id)

    entities: list[TranslationEntityInfo] = []
    for entity_id in entity_ids:
        spec = registry.get_entity(entity_id)
        entities.append(
            TranslationEntityInfo(
                id=entity_id,
                description=spec.description if spec else None,
            )
        )

    return TranslationResult(
        lines=[
            TranslationResultLine(
                no=line.no,
                text=line.text,
                tone=line.tone,
                source_no=line.source_no,
                entity_id=line.entity_id,
            )
            for line in output.lines
        ],
        warnings=[
            TranslationWarning(
                no=warning.no,
                message=warning.message,
                code=warning.code,
                severity=warning.severity,
            )
            for warning in output.warnings
        ],
        entities=entities,
        summary=TranslationResultSummary(
            total=output.summary["total"],
            duration_ms=output.summary["duration_ms"],
        ),
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
