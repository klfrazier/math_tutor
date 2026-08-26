from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass
class SessionState:
    student_name: str = ""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_problem_count: int = 0
    selected_standard_code: str = ""
    selected_standard_name: str = ""
    problems_attempted: int = 0
    problems_correct: int = 0
    problems_skipped: int = 0
    current_problem: str = ""
    current_expected_answer: str = ""
    current_attempt: int = 0
    session_start_time: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    problem_log: list[dict] = field(default_factory=list)
    session_complete: bool = False
