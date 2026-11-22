"""Golden Case：健康检查与接口契约冒烟测试。"""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    resp = client.get("/api/v1/health")

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_openapi_available(client: TestClient) -> None:
    resp = client.get("/openapi.json")

    assert resp.status_code == 200
    assert "/api/v1/health" in resp.json()["paths"]
