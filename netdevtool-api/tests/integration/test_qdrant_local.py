"""嵌入式 Qdrant 集成：使用测试临时目录，不连接外部服务。"""

import os
from pathlib import Path

import pytest
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    SparseVector,
)

from app.config import settings
from app.rag.qdrant_store import QdrantStore

ENABLED = os.getenv("NETDEVTOOL_TEST_QDRANT_LOCAL") == "1"
pytestmark = [
    pytest.mark.integration,
    pytest.mark.qdrant_local,
    pytest.mark.skipif(
        not ENABLED,
        reason="设置 NETDEVTOOL_TEST_QDRANT_LOCAL=1 后启用嵌入式 Qdrant 测试",
    ),
]


def use_local_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "QDRANT_URL", "")
    monkeypatch.setattr(settings, "QDRANT_API_KEY", "")
    monkeypatch.setattr(settings, "QDRANT_LOCAL_PATH", str(tmp_path / "qdrant"))


def make_point(point_id: int = 1) -> PointStruct:
    return PointStruct(
        id=point_id,
        vector={
            "dense": [1.0, 0.0],
            "sparse": SparseVector(indices=[0], values=[1.0]),
        },
        payload={
            "kb_id": 1,
            "doc_id": 7,
            "chunk_type": "chunk",
            "text": "interface GigabitEthernet0/0/1",
            "metadata": {"vendor": "huawei"},
        },
    )


def test_local_store_round_trip_search_metadata_and_delete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_local_path(monkeypatch, tmp_path)

    with QdrantStore("pytest_round_trip") as store:
        assert store.ensure(2) == "pytest_round_trip"
        store.upsert([make_point()])
        assert store.count_document(7) == 1

        query_filter = Filter(
            must=[FieldCondition(key="kb_id", match=MatchValue(value=1))]
        )
        dense = store.search_dense(vector=[1.0, 0.0], query_filter=query_filter, limit=5)
        sparse = store.search_sparse(
            vector=SparseVector(indices=[0], values=[1.0]),
            query_filter=query_filter,
            limit=5,
        )
        assert [item.id for item in dense] == [1]
        assert [item.id for item in sparse] == [1]

        store.set_document_metadata(7, {"vendor": "h3c", "status": "current"})
        stored = store.client.retrieve(store.name, ids=[1], with_payload=True)
        assert stored[0].payload["metadata"] == {
            "vendor": "h3c",
            "status": "current",
        }

        store.delete_document(7)
        assert store.count_document(7) == 0


def test_local_store_rejects_dense_dimension_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_local_path(monkeypatch, tmp_path)

    with QdrantStore("pytest_dimension") as store:
        store.ensure(2)
        with pytest.raises(RuntimeError, match="向量维度不一致"):
            store.ensure(3)
