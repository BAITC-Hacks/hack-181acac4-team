from ..schemas import ScoreBreakdown, TaskCard


def calculate_score(card: TaskCard) -> ScoreBreakdown:
    """ANU-7: deterministic score for a confirmed business card."""
    raise NotImplementedError("ANU-7 scoring implementation pending")
