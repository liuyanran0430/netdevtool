"""审核处置：候选采纳、失败补偿与共享候选删除保护。"""

from unittest.mock import MagicMock, Mock

import pytest

from app.models import (
    ReviewDecision,
    ReviewDecisionAction,
    SupplementCandidate,
    SupplementCandidateStatus,
    User,
)
from app.repositories.review_decision_repository import ReviewDecisionRepository
from app.repositories.supplement_candidate_repository import (
    SupplementCandidateRepository,
)
from app.schemas import ReviewDecisionCreate
from app.services import review_service, supplement_service


def candidate(status: SupplementCandidateStatus) -> SupplementCandidate:
    return SupplementCandidate(id=5, gap_id=3, status=status)


def decision_payload() -> ReviewDecisionCreate:
    return ReviewDecisionCreate(
        source_vendor="华为",
        source_model="S5735",
        target_vendor="H3C",
        target_model="S6520",
        source_text="unknown action 10",
        action=ReviewDecisionAction.accept,
        candidate_id=5,
    )


def test_record_decision_accepts_candidate_before_upsert(
    db: MagicMock, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    item = candidate(SupplementCandidateStatus.passed)
    monkeypatch.setattr(SupplementCandidateRepository, "get", lambda self, candidate_id: item)
    accept = Mock(side_effect=lambda db, candidate_id, user: setattr(item, "status", SupplementCandidateStatus.accepted))
    monkeypatch.setattr(supplement_service, "accept_candidate", accept)
    saved = ReviewDecision(
        user_id=user.id,
        item_key="key",
        action=ReviewDecisionAction.accept,
        candidate_id=item.id,
    )
    upsert = Mock(return_value=saved)
    monkeypatch.setattr(ReviewDecisionRepository, "upsert", upsert)

    result = review_service.record_decision(db, user, decision_payload())

    accept.assert_called_once_with(db, item.id, user)
    assert result.candidate_id == item.id
    assert upsert.call_args.kwargs["candidate_id"] == item.id


def test_record_decision_rolls_back_candidate_when_upsert_fails(
    db: MagicMock, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    item = candidate(SupplementCandidateStatus.passed)
    monkeypatch.setattr(SupplementCandidateRepository, "get", lambda self, candidate_id: item)
    monkeypatch.setattr(supplement_service, "accept_candidate", Mock())
    revoke = Mock()
    monkeypatch.setattr(supplement_service, "revoke_candidate", revoke)
    monkeypatch.setattr(
        ReviewDecisionRepository, "upsert", Mock(side_effect=RuntimeError("write failed"))
    )

    with pytest.raises(RuntimeError, match="write failed"):
        review_service.record_decision(db, user, decision_payload())

    revoke.assert_called_once_with(db, item.id, user)


def test_record_decision_does_not_reaccept_already_accepted_candidate(
    db: MagicMock, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    item = candidate(SupplementCandidateStatus.accepted)
    monkeypatch.setattr(SupplementCandidateRepository, "get", lambda self, candidate_id: item)
    accept = Mock()
    monkeypatch.setattr(supplement_service, "accept_candidate", accept)
    monkeypatch.setattr(
        ReviewDecisionRepository,
        "upsert",
        Mock(
            return_value=ReviewDecision(
                user_id=user.id,
                item_key="key",
                action=ReviewDecisionAction.accept,
                candidate_id=item.id,
            )
        ),
    )

    review_service.record_decision(db, user, decision_payload())

    accept.assert_not_called()


def test_delete_decision_revokes_candidate_only_for_last_reference(
    db: MagicMock, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    item = ReviewDecision(
        id=1,
        user_id=user.id,
        item_key="key",
        action=ReviewDecisionAction.accept,
        candidate_id=5,
    )
    monkeypatch.setattr(ReviewDecisionRepository, "get_by_key", lambda self, user_id, key: item)
    monkeypatch.setattr(ReviewDecisionRepository, "count_by_candidate", lambda self, candidate_id: 1)
    revoke = Mock()
    delete = Mock()
    monkeypatch.setattr(supplement_service, "revoke_candidate", revoke)
    monkeypatch.setattr(ReviewDecisionRepository, "delete", delete)

    review_service.delete_decision(db, user, "key")

    revoke.assert_called_once_with(db, 5, user)
    delete.assert_called_once()


def test_delete_decision_keeps_candidate_referenced_by_another_user(
    db: MagicMock, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    item = ReviewDecision(
        id=1,
        user_id=user.id,
        item_key="key",
        action=ReviewDecisionAction.accept,
        candidate_id=5,
    )
    monkeypatch.setattr(ReviewDecisionRepository, "get_by_key", lambda self, user_id, key: item)
    monkeypatch.setattr(ReviewDecisionRepository, "count_by_candidate", lambda self, candidate_id: 2)
    revoke = Mock()
    monkeypatch.setattr(supplement_service, "revoke_candidate", revoke)
    monkeypatch.setattr(ReviewDecisionRepository, "delete", Mock())

    review_service.delete_decision(db, user, "key")

    revoke.assert_not_called()
