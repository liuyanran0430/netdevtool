"""认证服务：密码校验、账号状态与令牌生命周期。"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models import User, UserStatus
from app.repositories.user_repository import UserRepository
from app.services import auth_service


def test_authenticate_returns_enabled_user(
    db: MagicMock, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        UserRepository, "find_by_username", lambda self, username: user
    )

    assert auth_service.authenticate(db, "alice", "secret") is user


@pytest.mark.parametrize("user_exists", [False, True], ids=["unknown-user", "bad-password"])
def test_authenticate_uses_same_error_for_unknown_user_and_bad_password(
    db: MagicMock,
    user: User,
    user_exists: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        UserRepository,
        "find_by_username",
        lambda self, username: user if user_exists else None,
    )

    with pytest.raises(HTTPException) as exc_info:
        auth_service.authenticate(db, "alice", "wrong")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "用户名或密码错误"


def test_authenticate_rejects_disabled_user(
    db: MagicMock, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    user.status = UserStatus.disabled
    monkeypatch.setattr(
        UserRepository, "find_by_username", lambda self, username: user
    )

    with pytest.raises(HTTPException) as exc_info:
        auth_service.authenticate(db, "alice", "secret")

    assert exc_info.value.status_code == 403


def test_token_can_be_resolved_and_revoked(
    db: MagicMock, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(UserRepository, "find_by_id", lambda self, user_id: user)
    token = auth_service.issue_token(user)

    assert auth_service.resolve_token(db, token) is user

    auth_service.revoke_token(token)
    with pytest.raises(HTTPException) as exc_info:
        auth_service.resolve_token(db, token)
    assert exc_info.value.status_code == 401


def test_expired_token_is_rejected_and_removed(
    db: MagicMock, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = auth_service.issue_token(user)
    clock = MagicMock(wraps=datetime)
    clock.now.return_value = datetime.now(UTC) + auth_service.TOKEN_TTL + timedelta(seconds=1)
    monkeypatch.setattr(auth_service, "datetime", clock)

    with pytest.raises(HTTPException) as exc_info:
        auth_service.resolve_token(db, token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "登录已过期，请重新登录"
    assert token not in auth_service._tokens


def test_disabled_user_token_is_revoked(
    db: MagicMock, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = auth_service.issue_token(user)
    user.status = UserStatus.disabled
    monkeypatch.setattr(UserRepository, "find_by_id", lambda self, user_id: user)

    with pytest.raises(HTTPException) as exc_info:
        auth_service.resolve_token(db, token)

    assert exc_info.value.status_code == 401
    assert token not in auth_service._tokens
