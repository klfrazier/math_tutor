import asyncio
import os
import random
import time
from pathlib import Path

import httpx

from _sdk import Agent, Runner

from tools.problem_generator import generate_problem
from tools.answer_evaluator import evaluate_answer
from tools.standards_catalog import get_nc_standards
from tools.summarizer import generate_session_summary
from tools.db_tools import save_session_to_db, get_student_history
from tools.problem_generator import generate_problem_impl
from tools.answer_evaluator import evaluate_answer_impl
from tools.standards_catalog import get_nc_standards_impl
from tools.summarizer import generate_session_summary_impl
from tools.db_tools import save_session_to_db_impl, get_student_history_impl
from tools.moderation import check_moderation
from standards.nc_standards import NC_STANDARDS, TOPIC_CLUSTERS
from agents.session_state import SessionState

MAX_MODERATION_ATTEMPTS = 2
API_TIMEOUT_RETRY_DELAY = 3.0


def run_agent_turn(message: str, history: list, state: SessionState) -> str:
    """Run a live agent turn via the SDK Runner, retrying once on API timeout.

    Returns the agent's text response. On a persistent timeout, returns a
    friendly message instead of surfacing the raw error.
    """
    input_messages = history + [{"role": "user", "content": message}]
    try:
        result = asyncio.run(Runner.run(math_tutor_agent, input=input_messages))
        return result.final_output
    except httpx.TimeoutException:
        time.sleep(API_TIMEOUT_RETRY_DELAY)
        try:
            result = asyncio.run(Runner.run(math_tutor_agent, input=input_messages))
            return result.final_output
        except httpx.TimeoutException:
            return "Oops, my math brain glitched! Give me a moment and try again. 😊"

SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
SYSTEM_PROMPT_TEMPLATE = SYSTEM_PROMPT_PATH.read_text()

math_tutor_agent = Agent(
    name="math-tutor",
    instructions=SYSTEM_PROMPT_TEMPLATE,
    model=os.environ.get("MODEL", "gpt-4o"),
    tools=[
        generate_problem,
        evaluate_answer,
        get_nc_standards,
        generate_session_summary,
        save_session_to_db,
        get_student_history,
    ],
)

_INJECTION_MARKERS = [
    "ignore your", "ignore all previous", "ignore previous", "ignore all",
    "system prompt", "you are now", "act as", "disregard", "override your",
    "forget your instructions", "new instructions", "pretend you are",
    "you are a different",
]
_OFFTOPIC_MARKERS = [
    "capital of", "who is", "what is the meaning of life", "weather",
    "sports", "movie", "game", "song", "recipe", "animal", "planet",
    "president", "country", "favorite color", "hobby", "friend", "family",
]


def _is_injection(message: str) -> bool:
    m = message.lower()
    return any(marker in m for marker in _INJECTION_MARKERS)


def _is_offtopic(message: str) -> bool:
    m = message.lower()
    return any(marker in m for marker in _OFFTOPIC_MARKERS)


def _handle_offtopic(state: SessionState) -> tuple[str, SessionState]:
    """Redirect off-topic/abuse messages once, then ignore after 3+ repeats."""
    state.offtopic_count += 1
    if state.offtopic_count > 3:
        return "Let's get back to the math! 🔢", state
    return "I'm just a math tutor — let's get back to the numbers! 🔢", state


def _classify_command(message: str) -> str | None:
    m = message.strip().lower()
    if m in ("reset", "start over", "restart", "new session"):
        return "reset"
    if m in ("skip", "pass", "i don't know", "i dont know", "next", "skip it"):
        return "skip"
    if m in ("quit", "stop", "i'm done", "im done", "done", "end session", "exit", "i am done"):
        return "quit"
    if m in ("show my history", "how am i doing", "history", "show history",
             "my progress", "progress", "how am i doing overall"):
        return "history"
    if m in ("what can i practice", "show standards", "standards",
             "what can i do", "show me the standards", "what topics"):
        return "standards"
    return None


def _setup_complete(state: SessionState) -> bool:
    return bool(state.student_name and state.target_problem_count and state.selected_standard_code)


def _parse_count(message: str) -> int | None:
    try:
        count = int(message.strip())
    except ValueError:
        return None
    if 1 <= count <= 50:
        return count
    return None


def _resolve_standard(message: str) -> tuple[str | None, str | None]:
    msg = message.strip()
    if msg in NC_STANDARDS:
        return msg, NC_STANDARDS[msg]["description"]
    for code in NC_STANDARDS:
        if code.lower() == msg.lower():
            return code, NC_STANDARDS[code]["description"]
    for cluster, codes in TOPIC_CLUSTERS.items():
        if msg.lower() == cluster.lower():
            code = random.choice(codes)
            return code, NC_STANDARDS[code]["description"]
    return None, None


def _current_difficulty(state: SessionState) -> int:
    if state.problems_attempted == 0:
        return 1
    accuracy = state.problems_correct / state.problems_attempted
    if accuracy >= 0.8:
        return 3
    if accuracy >= 0.5:
        return 2
    return 1


def _record_problem(state: SessionState, student_answer: str, correct: bool, skipped: bool) -> None:
    state.problem_log.append({
        "standard_code": state.selected_standard_code,
        "problem_text": state.current_problem,
        "expected_answer": state.current_expected_answer,
        "student_answer": student_answer,
        "correct": correct,
        "attempts": max(1, state.current_attempt),
        "skipped": skipped,
        "time_taken_seconds": None,
    })


def _state_to_dict(state: SessionState) -> dict:
    return {
        "student_name": state.student_name,
        "session_id": state.session_id,
        "target_problem_count": state.target_problem_count,
        "selected_standard_code": state.selected_standard_code,
        "selected_standard_name": state.selected_standard_name,
        "problems_attempted": state.problems_attempted,
        "problems_correct": state.problems_correct,
        "problems_skipped": state.problems_skipped,
        "session_start_time": state.session_start_time,
    }


def _start_problem(state: SessionState) -> tuple[str, SessionState]:
    for _ in range(MAX_MODERATION_ATTEMPTS + 1):
        payload = generate_problem_impl(state.selected_standard_code, difficulty=_current_difficulty(state))
        if "error" in payload:
            return "Oops, my math brain glitched! Let me try a different topic.", state
        if not check_moderation(payload["problem_text"]):
            state.current_problem = payload["problem_text"]
            state.current_expected_answer = payload["expected_answer"]
            state.current_attempt = 0
            return (
                f"Here's your problem #{state.problems_attempted + 1}:\n\n"
                f"**{payload['problem_text']}**\n\nTake your time! 😊",
                state,
            )
    return "Hmm, I couldn't find a good problem for that topic just now. Let's try a different one!", state


def _handle_answer(message: str, state: SessionState) -> tuple[str, SessionState]:
    result = evaluate_answer_impl(message, state.current_expected_answer, state.current_problem)
    state.current_attempt += 1
    if result["is_correct"]:
        state.problems_correct += 1
        state.problems_attempted += 1
        _record_problem(state, student_answer=message, correct=True, skipped=False)
        state.current_problem = ""
        state.current_expected_answer = ""
        state.current_attempt = 0
        if state.problems_attempted >= state.target_problem_count:
            return _end_session(state)
        return (
            f"Woohoo! That's correct! 🎉\n\n"
            f"That's problem {state.problems_attempted} of {state.target_problem_count}. "
            f"Ready for the next one?",
            state,
        )
    if state.current_attempt >= 2:
        answer = state.current_expected_answer
        state.problems_attempted += 1
        _record_problem(state, student_answer=message, correct=False, skipped=False)
        state.current_problem = ""
        state.current_expected_answer = ""
        state.current_attempt = 0
        reveal = f"No worries — the answer was **{answer}**. Now you know!"
        if state.problems_attempted >= state.target_problem_count:
            return _end_session(state, prefix=reveal)
        return reveal + " Ready for the next one? 🚀", state
    return (
        f"Not quite, but you're thinking in the right direction! "
        f"Here's a hint: {result['hint']} Give it another try! 💪",
        state,
    )


def _handle_skip(state: SessionState) -> tuple[str, SessionState]:
    answer = state.current_expected_answer
    state.problems_skipped += 1
    state.problems_attempted += 1
    _record_problem(state, student_answer="", correct=False, skipped=True)
    state.current_problem = ""
    state.current_expected_answer = ""
    state.current_attempt = 0
    reveal = f"No worries — the answer was **{answer}**. Now you know!"
    if state.problems_attempted >= state.target_problem_count:
        return _end_session(state, prefix=reveal)
    return reveal + " Ready for the next? 🚀", state


def _format_summary(summary: dict) -> str:
    return (
        f"---\n### 🎉 Session Complete, {summary['student_name']}!\n\n"
        f"**Topic:** {summary['standard_code']} — {summary['standard_name']}\n"
        f"**Problems:** {summary['problems_attempted']} attempted, "
        f"{summary['problems_correct']} correct, {summary['problems_skipped']} skipped\n"
        f"**Accuracy:** {summary['accuracy_pct']}%\n"
        f"**Time:** {summary['duration_seconds']} seconds\n\n"
        f"{summary['encouragement_message']}\n\n"
        f"**Next step:** {summary['next_step_recommendation']}\n\n"
        f"Type **\"start over\"** to begin a new session!\n---"
    )


def _end_session(state: SessionState, prefix: str = "") -> tuple[str, SessionState]:
    summary = generate_session_summary_impl(_state_to_dict(state))
    save_result = save_session_to_db_impl(summary, state.problem_log)
    state.session_complete = True
    body = _format_summary(summary)
    if prefix:
        body = prefix + "\n\n" + body
    if not save_result.get("success"):
        return (
            body
            + "\n\n*(I had trouble saving your session to history — but great work today!)*",
            state,
        )
    return body, state


def _format_standards(standards: list[dict]) -> str:
    lines = ["Here are the topics you can practice! 📋\n"]
    for s in standards:
        if s["code"] == "clusters":
            lines.append(f"**Topic shortcuts:** {s['description']}")
        else:
            lines.append(f"- **{s['code']}** ({s['grade']}th grade): {s['description']}")
    return "\n".join(lines)


def _format_history(record: dict) -> str:
    if not record["sessions"]:
        return f"I don't have any history for {record['student_name']} yet. Let's start a session!"
    lines = [f"Here's how you're doing, {record['student_name']}! 📊\n"]
    lines.append("**By topic:**")
    for t in record["topic_breakdown"]:
        lines.append(
            f"- {t['standard_code']}: {t['accuracy_pct']}% "
            f"({t['correct']}/{t['total_problems']} correct)"
        )
    lines.append(f"\n**Sessions completed:** {len(record['sessions'])}")
    return "\n".join(lines)


def _handle_setup(message: str, state: SessionState) -> tuple[str, SessionState]:
    if not state.student_name:
        name = message.strip()[:50]
        state.student_name = name
        return (
            f"Nice to meet you, {name}! How many problems would you like to do today? (1 to 50)",
            state,
        )
    if state.target_problem_count == 0:
        count = _parse_count(message)
        if count is None:
            return "That doesn't look like a number between 1 and 50. How many problems would you like to do?", state
        state.target_problem_count = count
        return (
            "Great! Which topic or standard would you like to practice? "
            "(e.g. 'Fractions', 'NC.6.EE.7', or 'Mix It Up')",
            state,
        )
    if not state.selected_standard_code:
        code, name = _resolve_standard(message)
        if code is None:
            return (
                "Hmm, I don't recognize that standard. Want to pick a topic from the list? "
                "Try 'Fractions', 'Decimals', 'Ratios', 'Algebra', 'Geometry', "
                "'Statistics', 'Base Ten', or 'Mix It Up'.",
                state,
            )
        state.selected_standard_code = code
        state.selected_standard_name = name
        return _start_problem(state)
    return _start_problem(state)


def _new_session_from(state: SessionState) -> SessionState:
    new_state = SessionState()
    new_state.student_name = state.student_name
    return new_state


def run_tutor_turn(message: str, history: list, state: SessionState) -> tuple[str, SessionState]:
    """Main turn handler. Classifies the message, updates SessionState, returns (response, state)."""
    message = (message or "").strip()
    if not message:
        return "Hmm, I didn't quite catch that — can you try again? 😊", state

    if _is_injection(message):
        return "I'm just a math tutor — let's get back to the numbers! 🔢", state

    cmd = _classify_command(message)

    if cmd == "reset":
        state = SessionState()
        return "Okay, let's start over! What's your name? 😊", state
    if cmd == "history":
        if not state.student_name:
            return "I need your name first to look up your history. What's your name?", state
        return _format_history(get_student_history_impl(state.student_name)), state
    if cmd == "standards":
        return _format_standards(get_nc_standards_impl("all")), state
    if cmd == "quit":
        if not _setup_complete(state) or state.session_complete:
            return "We haven't started a session yet. Want to begin? What's your name?", state
        return _end_session(state)

    if state.session_complete:
        state = _new_session_from(state)

    if not _setup_complete(state):
        if _is_offtopic(message):
            return _handle_offtopic(state)
        return _handle_setup(message, state)

    if state.current_problem:
        if cmd == "skip":
            return _handle_skip(state)
        if _is_offtopic(message):
            return _handle_offtopic(state)
        return _handle_answer(message, state)

    return _start_problem(state)
