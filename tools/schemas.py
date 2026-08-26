"""Output schema validation for session summaries and problem log entries.

Used before every save_session_to_db write to guarantee the payload
matches the Session Summary Output Contract (agents.md Section 6.3) and
the problem_results schema (Section 7). Validation failures are raised
so the caller can log the error and avoid writing a partial row.
"""

from pydantic import BaseModel, Field, ValidationError


class SessionSummary(BaseModel):
    student_name: str = Field(min_length=1, max_length=50)
    session_id: str
    session_date: str
    standard_code: str
    standard_name: str
    target_count: int = Field(ge=1, le=50)
    problems_attempted: int = Field(ge=0)
    problems_correct: int = Field(ge=0)
    problems_skipped: int = Field(ge=0)
    accuracy_pct: float = Field(ge=0.0, le=100.0)
    duration_seconds: int = Field(ge=0)
    encouragement_message: str
    next_step_recommendation: str
    prompt_version: str | None = None


class ProblemLogEntry(BaseModel):
    standard_code: str
    problem_text: str
    expected_answer: str
    student_answer: str | None = None
    correct: bool = False
    attempts: int = Field(default=1, ge=1)
    skipped: bool = False
    time_taken_seconds: int | None = None


def validate_session_summary(summary: dict) -> dict:
    """Validate a session summary dict; returns it unchanged if valid."""
    return SessionSummary(**summary).model_dump()


def validate_problem_log(problem_log: list[dict]) -> list[dict]:
    """Validate a problem log list; returns it unchanged if valid."""
    return [ProblemLogEntry(**entry).model_dump() for entry in problem_log]


__all__ = [
    "SessionSummary",
    "ProblemLogEntry",
    "validate_session_summary",
    "validate_problem_log",
    "ValidationError",
]
