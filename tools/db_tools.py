"""save_session_to_db and get_student_history tools.

Persist session and problem-level results to SQLite using parameterized
queries and transactions, and return per-standard accuracy history.
"""

import sqlite3
import time

from _sdk import function_tool
from db.database import get_connection
from tools.schemas import validate_session_summary, validate_problem_log, ValidationError

_MAX_RETRIES = 2  # initial attempt + 2 retries on transient DB error


def save_session_to_db_impl(session_summary: dict, problem_log: list[dict], db_path: str | None = None) -> dict:
    """Persist a session summary and its problem log to SQLite."""
    try:
        session_summary = validate_session_summary(session_summary)
        problem_log = validate_problem_log(problem_log)
    except ValidationError as e:
        return {
            "success": False,
            "session_id": session_summary.get("session_id", ""),
            "error": f"schema_validation_failed: {e}",
        }
    last_error = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            conn = get_connection(db_path)
            try:
                with conn:
                    conn.execute(
                        "INSERT OR IGNORE INTO students (name) VALUES (:name)",
                        {"name": session_summary["student_name"]},
                    )
                    conn.execute(
                        """INSERT INTO sessions
                           (session_id, student_name, standard_code, standard_name,
                            target_count, problems_attempted, problems_correct,
                            problems_skipped, accuracy_pct, duration_seconds,
                            started_at, completed_at)
                           VALUES (:session_id, :student_name, :standard_code, :standard_name,
                                   :target_count, :problems_attempted, :problems_correct,
                                   :problems_skipped, :accuracy_pct, :duration_seconds,
                                   :started_at, :completed_at)""",
                        {
                            "session_id": session_summary["session_id"],
                            "student_name": session_summary["student_name"],
                            "standard_code": session_summary["standard_code"],
                            "standard_name": session_summary["standard_name"],
                            "target_count": session_summary["target_count"],
                            "problems_attempted": session_summary["problems_attempted"],
                            "problems_correct": session_summary["problems_correct"],
                            "problems_skipped": session_summary["problems_skipped"],
                            "accuracy_pct": session_summary["accuracy_pct"],
                            "duration_seconds": session_summary["duration_seconds"],
                            "started_at": session_summary["session_date"],
                            "completed_at": session_summary["session_date"],
                        },
                    )
                    for p in problem_log:
                        conn.execute(
                            """INSERT INTO problem_results
                               (session_id, standard_code, problem_text, expected_answer,
                                student_answer, is_correct, attempts, skipped, time_taken_seconds)
                               VALUES (:session_id, :standard_code, :problem_text, :expected_answer,
                                       :student_answer, :is_correct, :attempts, :skipped, :time_taken_seconds)""",
                            {
                                "session_id": session_summary["session_id"],
                                "standard_code": p.get("standard_code"),
                                "problem_text": p.get("problem_text"),
                                "expected_answer": p.get("expected_answer"),
                                "student_answer": p.get("student_answer"),
                                "is_correct": 1 if p.get("correct") else 0,
                                "attempts": p.get("attempts", 1),
                                "skipped": 1 if p.get("skipped") else 0,
                                "time_taken_seconds": p.get("time_taken_seconds"),
                            },
                        )
                return {"success": True, "session_id": session_summary["session_id"]}
            finally:
                conn.close()
        except sqlite3.Error as e:
            last_error = e
            time.sleep(0.1)
    return {
        "success": False,
        "session_id": session_summary["session_id"],
        "error": str(last_error),
    }


def get_student_history_impl(student_name: str, db_path: str | None = None) -> dict:
    """Return historical performance for a student (sessions + per-standard accuracy)."""
    conn = get_connection(db_path)
    try:
        sessions = conn.execute(
            "SELECT * FROM sessions WHERE student_name = :name ORDER BY started_at DESC",
            {"name": student_name},
        ).fetchall()
        rows = conn.execute(
            """SELECT pr.standard_code, COUNT(*) AS total_problems, SUM(pr.is_correct) AS correct,
                      ROUND(100.0 * SUM(pr.is_correct) / COUNT(*), 1) AS accuracy_pct
               FROM problem_results pr
               JOIN sessions s USING (session_id)
               WHERE s.student_name = :student_name
               GROUP BY pr.standard_code
               ORDER BY accuracy_pct ASC""",
            {"student_name": student_name},
        ).fetchall()
        return {
            "student_name": student_name,
            "sessions": [dict(r) for r in sessions],
            "topic_breakdown": [dict(r) for r in rows],
        }
    finally:
        conn.close()


@function_tool(strict_mode=False)
def save_session_to_db(session_summary: dict, problem_log: list[dict]) -> dict:
    """Persist a session summary and its problem log to SQLite."""
    return save_session_to_db_impl(session_summary, problem_log)


@function_tool
def get_student_history(student_name: str) -> dict:
    """Return historical performance for a student."""
    return get_student_history_impl(student_name)
