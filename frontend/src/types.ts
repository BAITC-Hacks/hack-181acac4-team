export type CardStatus = "editing" | "confirmed" | "published";
export type ReadinessLevel = "draft" | "workable" | "ready" | "priority";
export type ProposalStatus = "submitted" | "accepted" | "rejected";

export interface TaskFields {
  topic: string;
  title: string;
  context: string;
  need: string;
  users: string;
  data: string;
  constraints: string;
  expected_result: string;
  success_criteria: string;
  contact: string;
  interaction_format: string;
}

export interface Question {
  id: string;
  text: string;
  field_keys: string[];
}

export interface Answer {
  question_id: string;
  text: string;
}

export interface TaskDraft {
  id: string;
  business_id: string;
  raw_description: string;
  known_fields: TaskFields;
  questions: Question[];
  answers: Answer[];
  status: "collecting" | "card_created";
}

export interface ScoreCriterion {
  earned: number;
  max_points: number;
}

export interface ScoreCriteria {
  context_need: ScoreCriterion;
  data: ScoreCriterion;
  expected_result: ScoreCriterion;
  success_criteria: ScoreCriterion;
  constraints: ScoreCriterion;
  users: ScoreCriterion;
  business_connection: ScoreCriterion;
}

export interface ScoreBreakdown {
  total: number;
  level: ReadinessLevel;
  criteria: ScoreCriteria;
  missing_fields: string[];
}

export interface TaskCard extends TaskFields {
  id: string;
  draft_id: string;
  business_id: string;
  status: CardStatus;
  score: ScoreBreakdown | null;
}

export interface TeamProfile {
  id: string;
  name: string;
  skills: string[];
  interests: string[];
  contact: string;
}

export interface Proposal {
  id: string;
  task_id: string;
  team_id: string;
  idea: string;
  plan: string;
  timeline: string;
  prototype_url: string;
  status: ProposalStatus;
}
