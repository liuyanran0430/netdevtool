"""Qdrant 底层操作：collection/alias 管理、upsert、delete、count、retrieve、search。"""

from __future__ import annotations

from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    CreateAlias,
    CreateAliasOperation,
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    SparseVectorParams,
    VectorParams,
)

from app.config import settings

_PAYLOAD_INDEXES: dict[str, PayloadSchemaType] = {
    "kb_id": PayloadSchemaType.INTEGER,
    "doc_id": PayloadSchemaType.INTEGER,
    "chunk_type": PayloadSchemaType.KEYWORD,
    "metadata.vendor": PayloadSchemaType.KEYWORD,
    "metadata.version": PayloadSchemaType.KEYWORD,
    "metadata.status": PayloadSchemaType.KEYWORD,
}


def ping_qdrant() -> bool:
    """探测 Qdrant 是否可用（不依赖具体知识库）。"""
    try:
        if settings.QDRANT_URL:
            client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY or None,
                timeout=5,
            )
        else:
            path = (
                Path(settings.QDRANT_LOCAL_PATH).expanduser()
                if settings.QDRANT_LOCAL_PATH
                else Path(".qdrant")
            )
            if not path.is_absolute():
                path = Path(__file__).resolve().parents[2] / path
            client = QdrantClient(path=str(path))
        try:
            client.get_collections()
        finally:
            client.close()
        return True
    except Exception:  # noqa: BLE001 连接失败按不可用处理
        return False


class QdrantStore:
    """按知识库隔离的 Qdrant 封装；服务端模式使用 `_current` 别名。"""

    def __init__(self, vector_store_name: str) -> None:
        self.name = vector_store_name
        self.alias = f"{vector_store_name}_current"
        self._is_server = bool(settings.QDRANT_URL)
        self.collection = vector_store_name
        if self._is_server:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY or None,
                timeout=30,
            )
        else:
            path = (
                Path(settings.QDRANT_LOCAL_PATH).expanduser()
                if settings.QDRANT_LOCAL_PATH
                else Path(".qdrant")
            )
            if not path.is_absolute():
                path = Path(__file__).resolve().parents[2] / path
            path.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(path))

    def __enter__(self) -> "QdrantStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.client.close()

    def _resolve_collection(self, dense_dim: int) -> str:
        """确保 collection 存在，并解析别名指向的集合。"""
        if self._is_server:
            for alias in self.client.get_aliases().aliases:
                if alias.alias_name == self.alias:
                    self.collection = alias.collection_name
                    return self.collection

        if not self.client.collection_exists(self.name):
            self.client.create_collection(
                collection_name=self.name,
                vectors_config={
                    "dense": VectorParams(size=dense_dim, distance=Distance.COSINE)
                },
                sparse_vectors_config={"sparse": SparseVectorParams()},
            )
            self._create_payload_indexes()
        else:
            self._validate_dimension(dense_dim)
            self._create_payload_indexes()

        if self._is_server:
            self.client.update_collection_aliases(
                change_aliases_operations=[
                    CreateAliasOperation(
                        create_alias=CreateAlias(
                            collection_name=self.name, alias_name=self.alias
                        )
                    )
                ]
            )
        self.collection = self.name
        return self.collection

    def _validate_dimension(self, dense_dim: int) -> None:
        info = self.client.get_collection(self.name)
        vectors = info.config.params.vectors
        current = vectors.get("dense") if isinstance(vectors, dict) else None
        size = getattr(current, "size", None)
        if size and size != dense_dim:
            raise RuntimeError(
                f"向量维度不一致：知识库为 {size}，当前模型输出 {dense_dim}，"
                "请先重建该知识库索引"
            )

    def _create_payload_indexes(self) -> None:
        for field_name, schema in _PAYLOAD_INDEXES.items():
            try:
                self.client.create_payload_index(
                    collection_name=self.name,
                    field_name=field_name,
                    field_schema=schema,
                )
            except Exception:  # noqa: BLE001  索引已存在或本地模式不支持时忽略
                continue

    def ensure(self, dense_dim: int) -> str:
        """确保 collection 与别名就绪，供后续写入复用。"""
        return self._resolve_collection(dense_dim)

    def delete_document(self, doc_id: int) -> None:
        """删除文档已写入的全部 point。"""
        if not self.client.collection_exists(self.collection):
            return
        self.client.delete(
            collection_name=self.collection,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                )
            ),
            wait=True,
        )

    def set_document_metadata(
        self,
        doc_id: int,
        metadata: dict[str, object],
    ) -> None:
        """只更新已有 point 的元数据 payload，不重新向量化。"""
        collection = self.alias if self._is_server else self.name
        if not self._is_server and not self.client.collection_exists(collection):
            return
        self._create_payload_indexes()
        self.client.set_payload(
            collection_name=collection,
            payload={"metadata": metadata},
            points=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            ),
            wait=True,
        )

    def upsert(self, points: list[PointStruct]) -> None:
        if points:
            self.client.upsert(
                collection_name=self.collection, points=points, wait=True
            )

    def count_document(self, doc_id: int) -> int:
        result = self.client.count(
            collection_name=self.collection,
            count_filter=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            ),
            exact=True,
        )
        return int(result.count)
