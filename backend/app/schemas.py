from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


CardStatus = Literal["editing", "confirmed", "published"]
ReadinessLevel = Literal["draft", "workable", "ready", "priority"]
ProposalStatus = Literal["submitted", "accepted", "rejected"]


class TaskFields(BaseModel):
    topic: str = ""
    title: str = ""
    context: str = ""
    need: str = ""
    users: str = ""
    data: str = ""
    constraints: str = ""
    expected_result: str = ""
    success_criteria: str = ""
    contact: str = ""
    interaction_format: str = ""


class Question(BaseModel):
    id: str
    text: str
    field_keys: list[str] = Field(default_factory=list)


class Answer(BaseModel):
    question_id: str
    text: str


class TaskDraft(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: str
    raw_description: str
    known_fields: TaskFields = Field(default_factory=TaskFields)
    questions: list[Question] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)
    status: Literal["collecting", "card_created"] = "collecting"


class TaskDraftCreate(BaseModel):
    business_id: str = "demo-business"
    raw_description: str = Field(min_length=1)


class TaskAnswers(BaseModel):
    answers: list[Answer] = Field(min_length=1)


class ScoreCriterion(BaseModel):
    earned: int = Field(ge=0)
    max_points: int = Field(gt=0)


class ScoreCriteria(BaseModel):
    context_need: ScoreCriterion
    data: ScoreCriterion
    expected_result: ScoreCriterion
    success_criteria: ScoreCriterion
    constraints: ScoreCriterion
    users: ScoreCriterion
    business_connection: ScoreCriterion


class ScoreBreakdown(BaseModel):
    total: int = Field(ge=0, le=100)
    level: ReadinessLevel
    criteria: ScoreCriteria
    missing_fields: list[str] = Field(default_factory=list)


class TaskCard(TaskFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    draft_id: UUID
    business_id: str
    status: CardStatus = "editing"
    score: ScoreBreakdown | None = None


class TaskCardUpdate(BaseModel):
    topic: str | None = None
    title: str | None = None
    context: str | None = None
    need: str | None = None
    users: str | None = None
    data: str | None = None
    constraints: str | None = None
    expected_result: str | None = None
    success_criteria: str | None = None
    contact: str | None = None
    interaction_format: str | None = None


class TeamProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    contact: str = ""


class Proposal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    team_id: UUID
    idea: str
    plan: str
    timeline: str = ""
    prototype_url: str = ""
    status: ProposalStatus = "submitted"


class ProposalCreate(BaseModel):
    team_id: UUID
    idea: str = Field(min_length=1)
    plan: str = Field(min_length=1)
    timeline: str = ""
    prototype_url: str = ""


class ProposalDecision(BaseModel):
    decision: Literal["accepted", "rejected"]
