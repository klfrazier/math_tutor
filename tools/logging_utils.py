"""Structured JSON-line logging per agents.md Section 13.

Events are emitted as single-line JSON to stdout:
    {"ts": "...", "session_id": "...", "event": "...", "data": {...}}

Wrong answers are only logged at DEBUG level (omitted from INFO logs) to
avoid storing student answers in the default log stream.
"""

import json
import logging
import sys
from datetime import datetime, timezone

logger = logging.getLogger("math_tutor")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(event: str, session_id: str = "", data: dict | None = None, level: int = logging.INFO) -> None:
    """Emit a structured JSON log line."""
    record = {
        "ts": _ts(),
        "session_id": session_id,
        "event": event,
        "data": data or {},
    }
    logger.log(level, json.dumps(record, default=str))


def log_session_start(session_id: str, student_name: str = "") -> None:
    log_event("session_start", session_id, {"student_name": student_name})


def log_setup_complete(session_id: str, data: dict) -> None:
    log_event("setup_complete", session_id, data)


def log_problem_generated(session_id: str, data: dict) -> None:
    log_event("problem_generated", session_id, data)


def log_answer_evaluated(session_id: str, data: dict, wrong_answer: str = "") -> None:
    # Wrong answers are redacted from INFO logs; only logged at DEBUG.
    if data.get("is_correct") is False and wrong_answer:
        log_event("answer_evaluated", session_id, {**data, "student_answer": wrong_answer}, level=logging.DEBUG)
    else:
        log_event("answer_evaluated", session_id, data)


def log_summary_generated(session_id: str, data: dict) -> None:
    log_event("summary_generated", session_id, data)


def log_db_write(session_id: str, success: bool, error: str = "") -> None:
    log_event("db_write", session_id, {"success": success, "error": error})


def log_error(session_id: str, message: str, data: dict | None = None) -> None:
    log_event("error", session_id, {"message": message, **(data or {})}, level=logging.ERROR)
