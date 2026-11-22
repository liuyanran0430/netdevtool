"""登录认证路由。"""

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import bearer_token, get_current_user
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, LoginResponse, UserOut
from app.services.auth_service import authenticate, issue_token, revoke_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, summary="登录")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = authenticate(db, payload.username, payload.password)
    return LoginResponse(token=issue_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut, summary="获取当前登录用户")
def get_me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/logout", status_code=204, summary="退出登录")
def logout(authorization: str | None = Header(None)) -> None:
    revoke_token(bearer_token(authorization))
