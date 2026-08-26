"""generate_session_summary tool.

Produces the end-of-session summary payload per the Session Summary
Output Contract (agents.md Section 6.3).
"""

from datetime import datetime, timezone

from _sdk import function_tool


def generate_session_summary_impl(session_state: dict) -> dict:
    """Plain callable used by the tool wrapper below and directly in tests."""
    problems_attempted = session_state.get("problems_attempted", 0)
    problems_correct = session_state.get("problems_correct", 0)
    problems_skipped = session_state.get("problems_skipped", 0)

    accuracy_pct = round(
        (problems_correct / problems_attempted) * 100, 1
    ) if problems_attempted else 0.0

    start_raw = session_state.get("session_start_time")
    if isinstance(start_raw, datetime):
        start_time = start_raw
    elif isinstance(start_raw, str) and start_raw:
        start_time = datetime.fromisoformat(start_raw)
    else:
        start_time = datetime.now(timezone.utc)
    now = datetime.now(timezone.utc)
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    duration_seconds = max(0, int((now - start_time).total_seconds()))

    if accuracy_pct >= 90:
        encouragement_message = "Fantastic work — you really know your stuff! 🌟"
    elif accuracy_pct >= 70:
        encouragement_message = "Great effort today — you're making solid progress! 💪"
    elif accuracy_pct >= 50:
        encouragement_message = "Nice work sticking with it — every problem is practice! 🙂"
    else:
        encouragement_message = "You worked hard today — that's what counts! Let's keep practicing. 🚀"

    if problems_skipped > problems_attempted / 2 if problems_attempted else False:
        next_step_recommendation = (
            "Let's revisit this topic together next time before moving on."
        )
    elif accuracy_pct >= 90:
        next_step_recommendation = "You're ready to try a harder topic or a new standard next time!"
    else:
        next_step_recommendation = "A little more practice on this topic will help it click even more."

    return {
        "student_name": session_state.get("student_name", ""),
        "session_id": session_state.get("session_id", ""),
        "session_date": now.isoformat(),
        "standard_code": session_state.get("selected_standard_code", ""),
        "standard_name": session_state.get("selected_standard_name", ""),
        "target_count": session_state.get("target_problem_count", 0),
        "problems_attempted": problems_attempted,
        "problems_correct": problems_correct,
        "problems_skipped": problems_skipped,
        "accuracy_pct": accuracy_pct,
        "duration_seconds": duration_seconds,
        "encouragement_message": encouragement_message,
        "next_step_recommendation": next_step_recommendation,
    }


@function_tool(strict_mode=False)
def generate_session_summary(session_state: dict) -> dict:
    """Produce the end-of-session summary payload from the current session state."""
    return generate_session_summary_impl(session_state)
