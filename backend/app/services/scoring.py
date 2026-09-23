from collections.abc import Callable
from typing import Final

from ..schemas import ScoreBreakdown, ScoreCriteria, ScoreCriterion, TaskCard


CONFIRMED_STATUSES: Final = {"confirmed", "published"}


def _has_text(value: str) -> bool:
    return bool(value.strip())


def _criterion(points: int, *checks: tuple[str, Callable[[], bool], int]) -> tuple[ScoreCriterion, list[str]]:
    missing: list[str] = []
    earned = 0

    for field_name, check, value in checks:
        if check():
            earned += value
        else:
            missing.append(field_name)

    return ScoreCriterion(earned=earned, max_points=points), missing


def _level(total: int) -> str:
    if total >= 90:
        return "priority"
    if total >= 70:
        return "ready"
    if total >= 40:
        return "workable"
    return "draft"


def calculate_score(card: TaskCard) -> ScoreBreakdown:
    """Return a deterministic, side-effect-free score for a business card.

    Editing cards never earn points: only information explicitly confirmed by
    the business may contribute to the official readiness score.  Composite
    criteria split their weight evenly, so a missing field remains visible and
    the score can grow after a confirmed edit.
    """
    confirmed = card.status in CONFIRMED_STATUSES
    present = lambda value: confirmed and _has_text(value)

    context_need, context_missing = _criterion(
        20,
        ("context", lambda: present(card.context), 10),
        ("need", lambda: present(card.need), 10),
    )
    data, data_missing = _criterion(
        20,
        ("data", lambda: present(card.data), 20),
    )
    expected_result, result_missing = _criterion(
        15,
        ("expected_result", lambda: present(card.expected_result), 15),
    )
    success_criteria, success_missing = _criterion(
        15,
        ("success_criteria", lambda: present(card.success_criteria), 15),
    )
    constraints, constraints_missing = _criterion(
        10,
        ("constraints", lambda: present(card.constraints), 10),
    )
    users, users_missing = _criterion(
        10,
        ("users", lambda: present(card.users), 10),
    )
    business_connection, connection_missing = _criterion(
        10,
        ("contact", lambda: present(card.contact), 5),
        ("interaction_format", lambda: present(card.interaction_format), 5),
    )

    criteria = ScoreCriteria(
        context_need=context_need,
        data=data,
        expected_result=expected_result,
        success_criteria=success_criteria,
        constraints=constraints,
        users=users,
        business_connection=business_connection,
    )
    total = sum(
        criterion.earned
        for criterion in (
            criteria.context_need,
            criteria.data,
            criteria.expected_result,
            criteria.success_criteria,
            criteria.constraints,
            criteria.users,
            criteria.business_connection,
        )
    )

    # The order is intentional: the first item is the highest-value next step.
    missing_fields = [
        *data_missing,
        *result_missing,
        *success_missing,
        *context_missing,
        *constraints_missing,
        *users_missing,
        *connection_missing,
    ]

    return ScoreBreakdown(
        total=total,
        level=_level(total),
        criteria=criteria,
        missing_fields=missing_fields,
    )
