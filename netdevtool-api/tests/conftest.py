"""共享测试设施：默认隔离数据库、消息队列、向量库与模型服务。"""

from collections.abc import Callable, Iterator
from datetime import datetime
from unittest.mock import MagicMock

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.logging_config import configure_logging
from app.main import app
from app.models import TranslationTask, TranslationTaskStatus, User, UserStatus
from app.services import auth_service, translation_service


@pytest.fixture(scope="session", autouse=True)
def isolate_test_logs(tmp_path_factory) -> None:
    configure_logging("backend", tmp_path_factory.mktemp("logs"))


@pytest.fixture(autouse=True)
def clear_auth_tokens() -> Iterator[None]:
    with auth_service._lock:
        auth_service._tokens.clear()
    yield
    with auth_service._lock:
        auth_service._tokens.clear()


@pytest.fixture
def db() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture
def user() -> User:
    return User(
        id=1,
        username="alice",
        password_hash=bcrypt.hashpw(b"secret", bcrypt.gensalt(rounds=4)).decode(),
        name="Alice",
        status=UserStatus.enabled,
    )


@pytest.fixture
def other_user() -> User:
    return User(
        id=2,
        username="bob",
        password_hash="not-used",
        name="Bob",
        status=UserStatus.enabled,
    )


@pytest.fixture
def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_service.issue_token(user)}"}


@pytest.fixture
def client(db: MagicMock) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[MagicMock]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client: TestClient, user: User) -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: user
    return client


@pytest.fixture
def knowledge_root(tmp_path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "knowledges"
    root.mkdir()
    monkeypatch.setattr(settings, "KNOWLEDGE_BASE_DIR", str(root))
    return root


class FakeTranslationRepository:
    """翻译仓储的进程内实现，不模拟 SQL 或数据库约束。"""

    def __init__(self) -> None:
        self.tasks: dict[str, TranslationTask] = {}

    def create(self, task: TranslationTask) -> TranslationTask:
        task.id = task.id or len(self.tasks) + 1
        task.status = task.status or TranslationTaskStatus.pending
        task.created_at = task.created_at or datetime.now()
        self.tasks[task.request_id] = task
        return task

    def get_by_request_id(self, request_id: str) -> TranslationTask | None:
        return self.tasks.get(request_id)

    def update(self, task: TranslationTask) -> TranslationTask:
        self.tasks[task.request_id] = task
        return task

    def list_recent(self, user_id: int, limit: int = 20) -> list[dict[str, object]]:
        tasks = [task for task in self.tasks.values() if task.user_id == user_id]
        tasks.sort(key=lambda task: task.created_at, reverse=True)
        return [
            {
                "request_id": task.request_id,
                "status": task.status,
                "source_vendor": task.source_vendor,
                "source_model": task.source_model,
                "target_vendor": task.target_vendor,
                "target_model": task.target_model,
                "created_at": task.created_at,
                "finished_at": task.finished_at,
            }
            for task in tasks[:limit]
        ]


@pytest.fixture
def translation_repository(monkeypatch: pytest.MonkeyPatch) -> FakeTranslationRepository:
    repository = FakeTranslationRepository()
    monkeypatch.setattr(
        translation_service, "TranslationRepository", lambda db: repository
    )
    return repository


@pytest.fixture
def translation_task_factory() -> Callable[..., TranslationTask]:
    def build(request_id: str = "req-1", **overrides) -> TranslationTask:
        values = {
            "id": 1,
            "user_id": 1,
            "request_id": request_id,
            "celery_task_id": "celery-1",
            "status": TranslationTaskStatus.pending,
            "source_vendor": "华为",
            "source_model": "S5735",
            "target_vendor": "H3C",
            "target_model": "S6520",
            "source_text": "interface GigabitEthernet0/0/1",
            "result_json": None,
            "error_message": None,
            "created_at": datetime.now(),
            "finished_at": None,
        }
        values.update(overrides)
        return TranslationTask(**values)

    return build
