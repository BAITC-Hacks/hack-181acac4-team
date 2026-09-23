from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from . import schemas
from .ai.client import get_intake_ai, IntakeAI
from .db import get_db
from .services import intake

router = APIRouter(prefix="/api/drafts", tags=["drafts"])
Database = Annotated[Session, Depends(get_db)]
Provider = Annotated[IntakeAI, Depends(get_intake_ai)]


@router.post("", response_model=schemas.TaskDraft, status_code=201)
def create(request: schemas.TaskDraftCreate, db: Database, ai: Provider):
    return intake.create_draft(db, request, ai)


@router.get("/{draft_id}", response_model=schemas.TaskDraft)
def read(draft_id: UUID, db: Database):
    return intake.get_draft(db, draft_id)


@router.get("/{draft_id}/card", response_model=schemas.TaskCard)
def read_card(draft_id: UUID, db: Database):
    return intake.get_draft_card(db, draft_id)


@router.post("/{draft_id}/answers", response_model=schemas.TaskCard)
def answer(draft_id: UUID, request: schemas.TaskAnswers, db: Database, ai: Provider):
    return intake.answer_draft(db, draft_id, request, ai)
