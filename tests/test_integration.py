"""Finalized end-to-end integration test (Phase 5 gate).

Simulates a full 10-problem session through the app's chat handler,
verifying: setup, problem loop, session summary, SQLite persistence,
history query, and the "Start Over" reset.
"""

import os
import tempfile

import pytest

import app
from agents.session_state import SessionState
from db.database import init_db
from tools.db_tools import get_student_history_impl


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    db_path = tmp_path / "integration_tutor.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    init_db()
    return db_path


def _run_full_session():
    """Drive a 10-problem session through app.chat_fn. Returns (history, state)."""
    state = SessionState()
    history = []

    def turn(msg):
        nonlocal state, history
        history, state, _cleared = app.chat_fn(msg, history, state)
        return history[-1]["content"]

    # Setup
    turn("Sam")
    turn("10")
    turn("NC.5.NBT.5")

    # Problem loop: alternate correct / wrong-then-correct / skip
    for i in range(10):
        if state.session_complete:
            break
        if not state.current_problem:
            turn("next")
        if not state.current_problem:
            break
        expected = state.current_expected_answer
        if i % 3 == 0:
            turn(expected)  # correct
        elif i % 3 == 1:
            turn(str(int(expected) + 1))  # wrong
            if state.current_problem:
                turn(expected)  # correct on retry
        else:
            turn("skip")  # skip
        if state.current_problem:
            turn("next")

    return history, state


class TestFullSession:
    def test_ten_problem_session(self, fresh_db):
        history, state = _run_full_session()
        assert state.session_complete
        assert state.problems_attempted == 10
        assert state.problems_correct + state.problems_skipped == 10
        # Summary was displayed
        assert any("Session Complete" in m["content"] for m in history)

    def test_sqlite_data_persisted(self, fresh_db):
        _run_full_session()
        record = get_student_history_impl("Sam")
        assert len(record["sessions"]) == 1
        s = record["sessions"][0]
        assert s["problems_attempted"] == 10
        assert s["standard_code"] == "NC.5.NBT.5"
        assert s["prompt_version"]  # prompt_version tracked
        assert 0 <= s["accuracy_pct"] <= 100

    def test_history_query(self, fresh_db):
        _run_full_session()
        record = get_student_history_impl("Sam")
        assert record["student_name"] == "Sam"
        assert len(record["topic_breakdown"]) >= 1
        assert record["topic_breakdown"][0]["standard_code"] == "NC.5.NBT.5"

    def test_start_over_reset(self, fresh_db):
        state = SessionState()
        history = []
        history, state, _ = app.chat_fn("Sam", history, state)
        history, state, _ = app.chat_fn("3", history, state)
        history, state, _ = app.chat_fn("Fractions", history, state)
        assert state.current_problem
        # Start Over resets to a fresh session
        history, state, _ = app.chat_fn("start over", history, state)
        assert state.student_name == ""
        assert state.target_problem_count == 0
        assert state.current_problem == ""
        assert state.session_complete is False

    def test_input_length_cap(self, fresh_db):
        state = SessionState()
        history = []
        long_msg = "x" * 600
        history, state, cleared = app.chat_fn(long_msg, history, state)
        assert len(history[0]["content"]) == 500
        assert "500 characters" in history[1]["content"]
        assert cleared == ""  # input box is cleared after submission
