from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .db import get_db
from .schemas import ReadinessLevel, TaskCard
from .services.catalog import get_published_card, list_published_cards


router = APIRouter(prefix="/api/tasks", tags=["catalog"])

@router.get("", response_model=list[TaskCard])
def list_tasks(
    topic: str | None = Query(default=None),
    level: ReadinessLevel | None = Query(default=None),
    sort: Literal["asc", "desc"] = Query(default="desc"),
    db: Session = Depends(get_db),
) -> list[TaskCard]:
    return list_published_cards(db, topic=topic, level=level, sort=sort)


@router.get("/{task_id}", response_model=TaskCard)
def get_task(task_id: UUID, db: Session = Depends(get_db)) -> TaskCard:
    card = get_published_card(db, task_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Published task not found")
    return card
