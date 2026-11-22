"""维护任务：按保留期清理 AI 调用记录并提交事务。"""

from datetime import datetime as RealDateTime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.tasks import maintenance_task


class FrozenDateTime(RealDateTime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 1, 31, 12, 0, 0)


def test_cleanup_ai_runs_uses_retention_cutoff_and_returns_deleted_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = MagicMock()
    db.execute.return_value = SimpleNamespace(rowcount=4)
    session = MagicMock()
    session.__enter__.return_value = db
    monkeypatch.setattr(maintenance_task, "SessionLocal", lambda: session)
    monkeypatch.setattr(maintenance_task, "datetime", FrozenDateTime)

    deleted = maintenance_task.cleanup_ai_runs(days=7)

    assert deleted == 4
    statement = db.execute.call_args.args[0]
    assert RealDateTime(2026, 1, 24, 12, 0, 0) in statement.compile().params.values()
    db.commit.assert_called_once()
    session.__exit__.assert_called_once()
