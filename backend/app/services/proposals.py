"""Submission and independent manual decisions for task proposals."""

from uuid import UUID
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..schemas import ProposalCreate, ProposalDecision


def _require_published_task(db: Session, task_id: UUID) -> None:
    exists = db.scalar(
        select(models.TaskCard.id).where(
            models.TaskCard.id == task_id,
            models.TaskCard.status == "published",
        )
    )
    if exists is None:
        raise HTTPException(status_code=404, detail="Published task not found")


def list_task_proposals(db: Session, task_id: UUID) -> list[models.Proposal]:
    _require_published_task(db, task_id)
    return list(db.scalars(
        select(models.Proposal)
        .where(models.Proposal.task_id == task_id)
        .order_by(models.Proposal.created_at.desc(), models.Proposal.id)
    ).all())


def submit_proposal(db: Session, task_id: UUID, data: ProposalCreate) -> models.Proposal:
    _require_published_task(db, task_id)
    if db.get(models.TeamProfile, data.team_id) is None:
        raise HTTPException(status_code=404, detail="Team profile not found")
    if not data.idea.strip() or not data.plan.strip():
        raise HTTPException(status_code=422, detail="Idea and plan cannot be blank")
    if data.prototype_url.strip():
        try:
            parsed_url = urlsplit(data.prototype_url.strip())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Prototype URL must be an HTTP(S) link") from exc
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise HTTPException(status_code=422, detail="Prototype URL must be an HTTP(S) link")

    proposal = models.Proposal(
        task_id=task_id,
        team_id=data.team_id,
        idea=data.idea.strip(),
        plan=data.plan.strip(),
        timeline=data.timeline.strip(),
        prototype_url=data.prototype_url.strip(),
        status="submitted",
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def decide_proposal(db: Session, proposal_id: UUID, data: ProposalDecision) -> models.Proposal:
    proposal = db.get(models.Proposal, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    # A decision applies to this proposal only. Other teams remain unchanged.
    proposal.status = data.decision
    db.commit()
    db.refresh(proposal)
    return proposal
