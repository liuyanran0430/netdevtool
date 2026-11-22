"""知识库元数据：类型兼容规则与依赖连接状态汇总。"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.models import KnowledgeBaseType
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services import knowledge_base_service


@pytest.mark.parametrize(
    ("base", "expected"),
    [
        (
            SimpleNamespace(kb_type=KnowledgeBaseType.architecture),
            KnowledgeBaseType.architecture,
        ),
        (
            SimpleNamespace(kb_type=None, vector_store_name="vendor_command_huawei", name=""),
            KnowledgeBaseType.manual,
        ),
        (
            SimpleNamespace(kb_type=None, vector_store_name="custom", name="网络故障手册"),
            KnowledgeBaseType.troubleshooting,
        ),
        (
            SimpleNamespace(kb_type=None, vector_store_name="custom", name="未分类"),
            KnowledgeBaseType.manual,
        ),
    ],
)
def test_resolve_kb_type_prefers_field_then_legacy_rules(base, expected) -> None:
    assert knowledge_base_service.resolve_kb_type(base) == expected


def test_connection_status_reports_qdrant_failure(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(KnowledgeBaseRepository, "list_all", lambda self: [object()])
    monkeypatch.setattr(knowledge_base_service, "ping_qdrant", lambda: False)

    status = knowledge_base_service.get_connection_status(db)

    assert status == {
        "connected": False,
        "database": True,
        "qdrant": False,
        "knowledge_bases": 1,
        "detail": "Qdrant 向量库不可用",
    }


def test_connection_status_contains_database_failure_without_raising(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        KnowledgeBaseRepository,
        "list_all",
        MagicMock(side_effect=RuntimeError("database down")),
    )
    monkeypatch.setattr(knowledge_base_service, "ping_qdrant", lambda: True)

    status = knowledge_base_service.get_connection_status(db)

    assert status["connected"] is False
    assert status["database"] is False
    assert status["qdrant"] is True
    assert status["knowledge_bases"] == 0
    assert status["detail"] == "数据库不可用"
