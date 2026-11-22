"""翻译 API：认证、创建响应、异常映射与数据隔离。"""

from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.models import TranslationTaskStatus
from app.services import translation_service

PAYLOAD = {
    "source_text": "ip route-static 10.0.0.0 255.255.255.0 192.168.1.1",
    "source_vendor": "华为",
    "source_model": "S5735",
    "target_vendor": "H3C",
    "target_model": "S6520",
}


def test_create_translation_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/translations", json=PAYLOAD)

    assert response.status_code == 401


def test_create_translation_returns_accepted(
    authenticated_client: TestClient, monkeypatch
) -> None:
    create = Mock(
        return_value=SimpleNamespace(
            request_id="req-api", status=TranslationTaskStatus.pending
        )
    )
    monkeypatch.setattr(translation_service, "create_translation", create)

    response = authenticated_client.post("/api/v1/translations", json=PAYLOAD)

    assert response.status_code == 202
    assert response.json() == {"request_id": "req-api", "status": "pending"}
    assert create.call_args.args[2] == 1


def test_create_translation_maps_dispatch_failure_to_503(
    authenticated_client: TestClient, monkeypatch
) -> None:
    def fail(*args):
        raise translation_service.TranslationDispatchError("任务队列不可用，请稍后重试")

    monkeypatch.setattr(translation_service, "create_translation", fail)

    response = authenticated_client.post("/api/v1/translations", json=PAYLOAD)

    assert response.status_code == 503
    assert response.json()["message"] == "任务队列不可用，请稍后重试"


def test_missing_or_foreign_translation_returns_404(
    authenticated_client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(
        translation_service, "get_translation", lambda db, request_id, user_id: None
    )

    response = authenticated_client.get("/api/v1/translations/foreign-request")

    assert response.status_code == 404
    assert response.json()["message"] == "翻译任务不存在"


def test_create_translation_rejects_blank_source(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/translations", json={**PAYLOAD, "source_text": "  \n"}
    )

    assert response.status_code == 422
    assert response.json()["message"] == "请求参数校验失败"
