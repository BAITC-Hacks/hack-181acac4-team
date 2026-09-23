from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .db import get_db
from .schemas import Proposal, ProposalCreate, ProposalDecision
from .services.proposals import decide_proposal, list_task_proposals, submit_proposal


router = APIRouter(tags=["proposals"])

@router.post("/api/tasks/{task_id}/proposals", response_model=Proposal, status_code=status.HTTP_201_CREATED)
def create_proposal(task_id: UUID, payload: ProposalCreate, db: Session = Depends(get_db)) -> Proposal:
    return submit_proposal(db, task_id, payload)


@router.get("/api/tasks/{task_id}/proposals", response_model=list[Proposal])
def get_proposals(task_id: UUID, db: Session = Depends(get_db)) -> list[Proposal]:
    return list_task_proposals(db, task_id)


@router.post("/api/proposals/{proposal_id}/decision", response_model=Proposal)
def make_decision(proposal_id: UUID, payload: ProposalDecision, db: Session = Depends(get_db)) -> Proposal:
    return decide_proposal(db, proposal_id, payload)
