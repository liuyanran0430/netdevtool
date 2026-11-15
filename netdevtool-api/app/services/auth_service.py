"""登录认证：密码校验与令牌管理。

令牌保存在进程内存中，服务重启后自动失效；如需多实例共享，后续可换为 Redis。
"""

import secrets
import threading
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import User, UserStatus
from app.repositories.user_repository import UserRepository

TOKEN_TTL = timedelta(hours=12)

_tokens: dict[str, tuple[int, datetime]] = {}
_lock = threading.Lock()


def authenticate(db: Session, username: str, password: str) -> User:
    """校验用户名与密码，失败统一提示，避免暴露账号是否存在。"""
    user = UserRepository(db).find_by_username(username)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    try:
        matched = bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))
    except ValueError:
        matched = False
    if not matched:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if user.status != UserStatus.enabled:
        raise HTTPException(status_code=403, detail="账号已被禁用，请联系管理员")
    return user


def issue_token(user: User) -> str:
    """签发登录令牌，同一账号可同时持有多个令牌。"""
    token = secrets.token_urlsafe(32)
    with _lock:
        _tokens[token] = (user.id, datetime.now(timezone.utc) + TOKEN_TTL)
    return token


def resolve_token(db: Session, token: str) -> User:
    """按令牌取回当前用户，过期或失效时返回 401。"""
    with _lock:
        entry = _tokens.get(token)
        if entry is None:
            raise HTTPException(status_code=401, detail="未登录或登录已失效")
        user_id, expires_at = entry
        if expires_at <= datetime.now(timezone.utc):
            _tokens.pop(token, None)
            raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    user = UserRepository(db).find_by_id(user_id)
    if user is None or user.status != UserStatus.enabled:
        revoke_token(token)
        raise HTTPException(status_code=401, detail="账号不存在或已被禁用")
    return user


def revoke_token(token: str) -> None:
    """退出登录时销毁令牌。"""
    with _lock:
        _tokens.pop(token, None)
