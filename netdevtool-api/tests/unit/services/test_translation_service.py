"""翻译服务：任务生命周期、所有权隔离与 Worker 状态竞争。"""

import json
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from app.models import (
    Device,
    DeviceType,
    TranslationTaskStatus,
)
from app.repositories.device_repository import DeviceRepository
from app.schemas import TranslationCreate
from app.services import translation_service
from app.translate_rule import (
    EntityTarget,
    ParsedLine,
    RenderedLines,
    RenderWarning,
    TranslationOutput,
)


def payload() -> TranslationCreate:
    return TranslationCreate(
        source_text="ip route-static 10.0.0.0 255.255.255.0 192.168.1.1",
        source_vendor="华为",
        source_model="S5735",
        target_vendor="H3C",
        target_model="S6520",
    )


def device(vendor: str, vendor_en: str, model: str) -> Device:
    return Device(
        id=1 if vendor_en == "huawei" else 2,
        vendor=vendor,
        vendor_en=vendor_en,
        model=model,
        device_type=DeviceType.switch,
    )


def translation_output() -> TranslationOutput:
    return TranslationOutput(
        lines=[
            RenderedLines(
                text="ip route-static 10.0.0.0 255.255.255.0 192.168.1.1",
                tone="success",
            )
        ],
        entity_targets={
            "static_route": EntityTarget(
                entity_id="static_route",
                source_nos=(1,),
                target_line_indices=(0,),
            )
        },
        warnings=[
            RenderWarning(no=(1,), message="请复核", code="low_confidence")
        ],
        summary={"total": 1, "duration_ms": 0},
        parsed_lines=[ParsedLine(no=1, text="ip route-static ...", kind="command")],
    )


def use_worker_session(monkeypatch: pytest.MonkeyPatch, db: MagicMock) -> None:
    @contextmanager
    def session_scope():
        yield db

    monkeypatch.setattr(translation_service, "SessionLocal", session_scope)


def use_devices(monkeypatch: pytest.MonkeyPatch) -> tuple[Device, Device]:
    source = device("华为", "huawei", "S5735")
    target = device("H3C", "h3c", "S6520")

    def find_by_vendor_and_model(self, vendor: str, model: str):
        if (vendor, model) == ("华为", "S5735"):
            return source
        if (vendor, model) == ("H3C", "S6520"):
            return target
        return None

    monkeypatch.setattr(
        DeviceRepository, "find_by_vendor_and_model", find_by_vendor_and_model
    )
    return source, target


def test_create_translation_dispatches_and_saves_celery_id(
    db: MagicMock, translation_repository, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.tasks.translation_task import translate_configuration

    delay = Mock(return_value=SimpleNamespace(id="celery-new"))
    monkeypatch.setattr(translate_configuration, "delay", delay)

    task = translation_service.create_translation(db, payload(), user_id=1)

    assert task.status == TranslationTaskStatus.pending
    assert task.celery_task_id == "celery-new"
    assert task.user_id == 1
    delay.assert_called_once_with(task.request_id)


def test_create_translation_marks_task_failed_when_dispatch_fails(
    db: MagicMock, translation_repository, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.tasks.translation_task import translate_configuration

    monkeypatch.setattr(
        translate_configuration, "delay", Mock(side_effect=RuntimeError("redis down"))
    )

    with pytest.raises(translation_service.TranslationDispatchError):
        translation_service.create_translation(db, payload(), user_id=1)

    task = next(iter(translation_repository.tasks.values()))
    assert task.status == TranslationTaskStatus.failed
    assert task.error_message == "任务队列不可用，请稍后重试"
    assert task.finished_at is not None
    assert task.celery_task_id is None


def test_translation_queries_enforce_user_ownership(
    db: MagicMock,
    translation_repository,
    translation_task_factory,
) -> None:
    own = translation_repository.create(translation_task_factory("own", user_id=1))
    foreign = translation_repository.create(
        translation_task_factory("foreign", id=2, user_id=2)
    )

    assert translation_service.get_translation(db, "foreign", user_id=1) is None
    assert translation_service.get_translation_source(db, "foreign", user_id=1) is None
    assert translation_service.cancel_translation(db, "foreign", user_id=1) is False
    assert foreign.status == TranslationTaskStatus.pending
    assert [item.request_id for item in translation_service.list_translations(db, 1)] == [
        own.request_id
    ]


def test_get_translation_only_exposes_result_after_success(
    db: MagicMock, translation_repository, translation_task_factory
) -> None:
    result = {
        "lines": [{"no": [1], "text": "return", "tone": "muted"}],
        "warnings": [],
        "entities": [],
        "summary": {"total": 1, "duration_ms": 3},
    }
    task = translation_repository.create(
        translation_task_factory(
            status=TranslationTaskStatus.succeeded, result_json=json.dumps(result)
        )
    )

    response = translation_service.get_translation(db, task.request_id, user_id=1)

    assert response.status == TranslationTaskStatus.succeeded
    assert response.result.lines[0].text == "return"
    task.status = TranslationTaskStatus.running
    running = translation_service.get_translation(db, task.request_id, user_id=1)
    assert running.result is None


@pytest.mark.parametrize(
    "initial_status",
    [TranslationTaskStatus.pending, TranslationTaskStatus.running],
)
def test_cancel_translation_revokes_worker_and_marks_failed(
    db: MagicMock,
    translation_repository,
    translation_task_factory,
    monkeypatch: pytest.MonkeyPatch,
    initial_status: TranslationTaskStatus,
) -> None:
    from app.tasks.celery_app import celery_app

    task = translation_repository.create(
        translation_task_factory(status=initial_status)
    )
    revoke = Mock()
    monkeypatch.setattr(celery_app.control, "revoke", revoke)

    assert translation_service.cancel_translation(db, task.request_id, user_id=1)

    revoke.assert_called_once_with("celery-1", terminate=True)
    assert task.status == TranslationTaskStatus.failed
    assert task.error_message == "任务已取消"
    assert task.finished_at is not None


def test_cancel_finished_translation_is_idempotent_without_revoke(
    db: MagicMock,
    translation_repository,
    translation_task_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.tasks.celery_app import celery_app

    task = translation_repository.create(
        translation_task_factory(status=TranslationTaskStatus.succeeded)
    )
    revoke = Mock()
    monkeypatch.setattr(celery_app.control, "revoke", revoke)

    assert translation_service.cancel_translation(db, task.request_id, user_id=1)

    revoke.assert_not_called()
    assert task.status == TranslationTaskStatus.succeeded


def test_worker_saves_result(
    db: MagicMock,
    translation_repository,
    translation_task_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = translation_repository.create(translation_task_factory())
    use_worker_session(monkeypatch, db)
    _, target = use_devices(monkeypatch)
    output = translation_output()
    registry = MagicMock()
    registry.get_entity.return_value = SimpleNamespace(description="配置 IPv4 静态路由")
    monkeypatch.setattr(translation_service, "get_registry", lambda: registry)
    monkeypatch.setattr(
        translation_service, "translate_config", Mock(return_value=output)
    )
    collect_gaps = Mock(return_value=1)
    materialize = Mock(return_value=1)

    translation_service.run_translation_task(task.request_id)

    assert task.status == TranslationTaskStatus.succeeded
    assert task.error_message is None
    assert task.finished_at is not None
    saved = json.loads(task.result_json)
    assert saved["lines"][0]["text"] == "ip route-static 10.0.0.0 255.255.255.0 192.168.1.1"
    assert saved["entities"] == [
        {
            "id": "static_route",
            "source_nos": [1],
            "command_nos": [],
            "target_line_indices": [0],
            "description": "配置 IPv4 静态路由",
        }
    ]
    assert saved["summary"]["total"] == 1
    assert target.vendor_en == "h3c"


def test_worker_does_not_overwrite_cancellation_during_translation(
    db: MagicMock,
    translation_repository,
    translation_task_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = translation_repository.create(translation_task_factory())
    use_worker_session(monkeypatch, db)
    use_devices(monkeypatch)
    monkeypatch.setattr(translation_service, "get_registry", MagicMock)

    def cancel_while_translating(*args, **kwargs):
        task.status = TranslationTaskStatus.failed
        task.error_message = "任务已取消"
        return translation_output()

    monkeypatch.setattr(
        translation_service, "translate_config", cancel_while_translating
    )

    translation_service.run_translation_task(task.request_id)

    assert task.status == TranslationTaskStatus.failed
    assert task.error_message == "任务已取消"
    assert task.result_json is None


def test_worker_marks_missing_device_as_failed(
    db: MagicMock,
    translation_repository,
    translation_task_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = translation_repository.create(translation_task_factory())
    use_worker_session(monkeypatch, db)
    monkeypatch.setattr(
        DeviceRepository, "find_by_vendor_and_model", lambda self, vendor, model: None
    )

    translation_service.run_translation_task(task.request_id)

    assert task.status == TranslationTaskStatus.failed
    assert "未找到源设备档案" in task.error_message
    assert task.finished_at is not None
    db.rollback.assert_called_once()

