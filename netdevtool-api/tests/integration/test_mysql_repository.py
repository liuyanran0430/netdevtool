"""真实 MySQL 集成：仅使用显式指定的独立 *_test 数据库。"""

import os
from collections.abc import Iterator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.models import (
    KnowledgeBase,
    KnowledgeDocument,
    KnowledgeDocumentFileType,
    KnowledgeDocumentStatus,
)
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository

MYSQL_URL = os.getenv("NETDEVTOOL_TEST_MYSQL_URL", "")
pytestmark = [
    pytest.mark.integration,
    pytest.mark.mysql,
    pytest.mark.skipif(
        not MYSQL_URL,
        reason="设置 NETDEVTOOL_TEST_MYSQL_URL 为独立 *_test 数据库后启用",
    ),
]


@pytest.fixture(scope="module")
def mysql_engine() -> Iterator[Engine]:
    database = make_url(MYSQL_URL).database or ""
    if not database.endswith("_test"):
        pytest.fail("集成测试数据库名必须以 _test 结尾，拒绝连接开发或生产库")
    engine = create_engine(MYSQL_URL, pool_pre_ping=True, future=True)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def knowledge_base(mysql_engine: Engine) -> Iterator[int]:
    unique = uuid4().hex
    with Session(mysql_engine, expire_on_commit=False) as session:
        base = KnowledgeBase(
            name=f"pytest-{unique}",
            vector_store_name=f"pytest_{unique}",
        )
        session.add(base)
        session.commit()
        base_id = base.id
    try:
        yield base_id
    finally:
        with Session(mysql_engine) as session:
            session.execute(
                delete(KnowledgeDocument).where(KnowledgeDocument.kb_id == base_id)
            )
            session.execute(delete(KnowledgeBase).where(KnowledgeBase.id == base_id))
            session.commit()


def document(base_id: int, suffix: str, *, file_hash: str) -> KnowledgeDocument:
    return KnowledgeDocument(
        kb_id=base_id,
        file_name=f"guide-{suffix}.md",
        file_path=f"pytest/{suffix}.md",
        file_type=KnowledgeDocumentFileType.markdown,
        file_size=10,
        file_hash=file_hash,
        status=KnowledgeDocumentStatus.pending,
    )


def test_document_name_and_hash_unique_constraints(
    mysql_engine: Engine, knowledge_base: int
) -> None:
    suffix = uuid4().hex
    file_hash = suffix + suffix[::-1]
    with Session(mysql_engine) as session:
        session.add(document(knowledge_base, suffix, file_hash=file_hash))
        session.commit()

        duplicate_name = document(knowledge_base, suffix, file_hash=uuid4().hex * 2)
        session.add(duplicate_name)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        duplicate_hash = document(knowledge_base, uuid4().hex, file_hash=file_hash)
        session.add(duplicate_hash)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_claim_for_index_allows_only_one_of_two_sessions(
    mysql_engine: Engine, knowledge_base: int
) -> None:
    suffix = uuid4().hex
    with Session(mysql_engine, expire_on_commit=False) as first:
        item = document(knowledge_base, suffix, file_hash=suffix * 2)
        first.add(item)
        first.commit()
        doc_id = item.id

        with Session(mysql_engine, expire_on_commit=False) as second:
            assert KnowledgeDocumentRepository(first).claim_for_index(doc_id) is True
            assert KnowledgeDocumentRepository(second).claim_for_index(doc_id) is False
            second.expire_all()
            claimed = second.get(KnowledgeDocument, doc_id)
            assert claimed is not None
            assert claimed.status == KnowledgeDocumentStatus.processing
