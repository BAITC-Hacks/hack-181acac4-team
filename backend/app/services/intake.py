from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..ai.client import IntakeAI
from .scoring import calculate_score


class IntakeError(Exception):
    def __init__(self, message: str, status: int = 409):
        super().__init__(message)
        self.status = status


def get_draft(db: Session, draft_id: UUID, *, lock: bool = False) -> models.TaskDraft:
    statement = select(models.TaskDraft).where(models.TaskDraft.id == draft_id)
    if lock:
        statement = statement.with_for_update()
    draft = db.scalar(statement)
    if draft is None:
        raise IntakeError("Черновик не найден.", 404)
    return draft


def get_card(db: Session, card_id: UUID, *, lock: bool = False) -> models.TaskCard:
    statement = select(models.TaskCard).where(models.TaskCard.id == card_id)
    if lock:
        statement = statement.with_for_update()
    card = db.scalar(statement)
    if card is None:
        raise IntakeError("Карточка не найдена.", 404)
    return card


def get_draft_card(db: Session, draft_id: UUID) -> models.TaskCard:
    card = db.scalar(select(models.TaskCard).where(models.TaskCard.draft_id == draft_id))
    if card is None:
        raise IntakeError("Карточка ещё не создана.", 404)
    return card


def create_draft(db: Session, request: schemas.TaskDraftCreate, ai: IntakeAI) -> models.TaskDraft:
    description = request.raw_description.strip()
    if not description:
        raise IntakeError("Введите описание задачи.", 422)
    fields, questions = ai.analyze(description)
    draft = models.TaskDraft(
        business_id=request.business_id,
        raw_description=description,
        known_fields=fields.model_dump(),
        questions=[question.model_dump() for question in questions],
        answers=[],
        status="collecting",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def answer_draft(
    db: Session, draft_id: UUID, request: schemas.TaskAnswers, ai: IntakeAI,
) -> models.TaskCard:
    draft = get_draft(db, draft_id, lock=True)
    # Serializes duplicate submits; a retry cannot overwrite a manually edited card.
    if draft.status == "card_created":
        return get_draft_card(db, draft_id)
    expected = {q["id"] for q in draft.questions}
    supplied = [answer.question_id for answer in request.answers]
    if len(supplied) != len(set(supplied)) or set(supplied) != expected:
        raise IntakeError("Ответьте на каждый вопрос один раз.", 422)
    answers = [
        {"question_id": a.question_id, "text": a.text.strip()} for a in request.answers
    ]
    if any(not a["text"] for a in answers):
        raise IntakeError("Заполните ответы. Если сведений нет, напишите «не знаю».", 422)
    fields = ai.assemble(draft.raw_description, draft.questions, answers)
    card = models.TaskCard(
        draft_id=draft.id, business_id=draft.business_id, **fields.model_dump(), status="editing",
    )
    draft.answers = answers
    draft.status = "card_created"
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def update_card(db: Session, card_id: UUID, request: schemas.TaskCardUpdate) -> models.TaskCard:
    card = get_card(db, card_id, lock=True)
    changed = False
    for key, value in request.model_dump(exclude_unset=True).items():
        if value is None:
            raise IntakeError("Пустое поле передавайте пустой строкой.", 422)
        value = value.strip()
        if getattr(card, key) != value:
            setattr(card, key, value)
            changed = True
    if changed:
        # Any content edit invalidates the previous approval and published version.
        card.status = "editing"
        card.score = None
        card.score_total = 0
        card.score_level = "draft"
    db.commit()
    db.refresh(card)
    return card


def confirm_card(db: Session, card_id: UUID) -> models.TaskCard:
    card = get_card(db, card_id, lock=True)
    if card.status == "published":
        return card
    card.status = "confirmed"
    try:
        score = calculate_score(schemas.TaskCard.model_validate(card))
    except NotImplementedError:
        # ANU-7 owns scoring. A missing implementation must never fabricate points.
        score = None
    if score is not None:
        card.score = score.model_dump(mode="json")
        card.score_total = score.total
        card.score_level = score.level
    db.commit()
    db.refresh(card)
    return card


def publish_card(db: Session, card_id: UUID) -> models.TaskCard:
    card = get_card(db, card_id, lock=True)
    if card.status not in {"confirmed", "published"}:
        raise IntakeError("Сначала проверьте и подтвердите карточку.")
    card.status = "published"
    db.commit()
    db.refresh(card)
    return card
