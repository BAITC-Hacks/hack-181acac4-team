from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from . import schemas
from .db import get_db
from .services import intake

router = APIRouter(prefix="/api/cards", tags=["cards"])
Database = Annotated[Session, Depends(get_db)]


@router.get("/{card_id}", response_model=schemas.TaskCard)
def read(card_id: UUID, db: Database):
    return intake.get_card(db, card_id)


@router.patch("/{card_id}", response_model=schemas.TaskCard)
def update(card_id: UUID, request: schemas.TaskCardUpdate, db: Database):
    return intake.update_card(db, card_id, request)


@router.post("/{card_id}/confirm", response_model=schemas.TaskCard)
def confirm(card_id: UUID, db: Database):
    return intake.confirm_card(db, card_id)


@router.post("/{card_id}/publish", response_model=schemas.TaskCard)
def publish(card_id: UUID, db: Database):
    return intake.publish_card(db, card_id)
