"""Read-only queries for the public catalog of published cards."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models
from ..schemas import ReadinessLevel


def list_published_cards(
    db: Session,
    *,
    topic: str | None = None,
    level: ReadinessLevel | None = None,
    sort: str = "desc",
) -> list[models.TaskCard]:
    statement = select(models.TaskCard).where(models.TaskCard.status == "published")
    if topic and topic.strip():
        statement = statement.where(func.lower(models.TaskCard.topic) == topic.strip().lower())
    if level:
        statement = statement.where(models.TaskCard.score_level == level)

    rating_order = models.TaskCard.score_total.asc() if sort == "asc" else models.TaskCard.score_total.desc()
    statement = statement.order_by(rating_order, models.TaskCard.created_at.desc(), models.TaskCard.id)
    return list(db.scalars(statement).all())


def get_published_card(db: Session, card_id: UUID) -> models.TaskCard | None:
    return db.scalar(
        select(models.TaskCard).where(
            models.TaskCard.id == card_id,
            models.TaskCard.status == "published",
        )
    )
