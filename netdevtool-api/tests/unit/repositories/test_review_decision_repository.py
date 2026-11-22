"""审核处置仓储：唯一键冲突后的幂等更新。"""

from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError

from app.models import ReviewDecision, ReviewDecisionAction
from app.repositories.review_decision_repository import ReviewDecisionRepository


def test_upsert_recovers_from_concurrent_insert_conflict(db: MagicMock) -> None:
    existing = ReviewDecision(
        id=1,
        user_id=1,
        item_key="key",
        action=ReviewDecisionAction.skip,
    )
    db.scalars.return_value.first.side_effect = [None, existing]
    db.commit.side_effect = [
        IntegrityError("INSERT", {}, Exception("duplicate")),
        None,
    ]
    repository = ReviewDecisionRepository(db)

    result = repository.upsert(
        user_id=1,
        item_key="key",
        action=ReviewDecisionAction.accept,
        decided_text=None,
        candidate_id=5,
    )

    assert result is existing
    assert existing.action == ReviewDecisionAction.accept
    assert existing.candidate_id == 5
    db.rollback.assert_called_once()
    assert db.commit.call_count == 2
