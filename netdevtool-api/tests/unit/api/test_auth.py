"""认证 API：登录响应、Bearer 校验与退出登录。"""

from fastapi.testclient import TestClient

from app.models import User
from app.repositories.user_repository import UserRepository


def test_login_then_read_current_user_and_logout(
    client: TestClient, user: User, monkeypatch
) -> None:
    monkeypatch.setattr(
        UserRepository, "find_by_username", lambda self, username: user
    )
    monkeypatch.setattr(UserRepository, "find_by_id", lambda self, user_id: user)

    login = client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "secret"}
    )

    assert login.status_code == 200
    body = login.json()
    assert body["user"] == {
        "id": 1,
        "username": "alice",
        "name": "Alice",
        "status": "enabled",
    }
    assert "password" not in body["user"]
    headers = {"Authorization": f"Bearer {body['token']}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_login_failure_uses_unified_error_response(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(
        UserRepository, "find_by_username", lambda self, username: None
    )

    response = client.post(
        "/api/v1/auth/login", json={"username": "nobody", "password": "bad"}
    )

    assert response.status_code == 401
    assert response.json() == {"code": 401, "message": "用户名或密码错误", "detail": None}


def test_me_rejects_missing_or_malformed_bearer_token(client: TestClient) -> None:
    missing = client.get("/api/v1/auth/me")
    malformed = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Token abc"}
    )

    assert missing.status_code == 401
    assert malformed.status_code == 401
    assert malformed.json()["message"] == "未登录或登录已失效"
