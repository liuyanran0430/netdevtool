"""路由层公共依赖。"""

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services.auth_service import resolve_token


def bearer_token(authorization: str | None) -> str:
    """从 Authorization 头取出 Bearer 令牌，格式不符时返回 401。"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未登录或登录已失效")
    return authorization[7:].strip()


def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """解析 Authorization: Bearer <token>，未登录或令牌失效时返回 401。"""
    return resolve_token(db, bearer_token(authorization))
