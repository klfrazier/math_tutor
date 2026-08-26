import uuid
from datetime import datetime, timedelta, timezone

import pytest

from standards.nc_standards import NC_STANDARDS
from tools.problem_generator import generate_problem_impl
from tools.answer_evaluator import evaluate_answer_impl
from tools.standards_catalog import get_nc_standards_impl
from tools.summarizer import generate_session_summary_impl


SAMPLE_CODES = [
    "NC.5.OA.1", "NC.5.NBT.5", "NC.5.NF.1", "NC.5.MD.5", "NC.5.G.1",
    "NC.6.RP.1", "NC.6.NS.1", "NC.6.EE.7", "NC.6.G.1", "NC.6.SP.3",
]


class TestGenerateProblem:
    @pytest.mark.parametrize("code", SAMPLE_CODES)
    def test_valid_standard_returns_payload(self, code):
        payload = generate_problem_impl(code, difficulty=1)
        assert "error" not in payload
        assert payload["standard_code"] == code
        assert payload["problem_text"]
        assert payload["expected_answer"] != ""
        assert payload["difficulty"] == 1

    def test_invalid_standard_returns_safe_error(self):
        payload = generate_problem_impl("NC.9.ZZ.99", difficulty=1)
        assert "error" in payload
        assert "problem_text" not in payload

    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_difficulty_clamped_and_recorded(self, difficulty):
        payload = generate_problem_impl("NC.5.NBT.5", difficulty=difficulty)
        assert payload["difficulty"] == difficulty

    def test_difficulty_out_of_range_is_clamped(self):
        payload = generate_problem_impl("NC.5.NBT.5", difficulty=99)
        assert payload["difficulty"] == 3
        payload_low = generate_problem_impl("NC.5.NBT.5", difficulty=0)
        assert payload_low["difficulty"] == 1

    def test_all_catalog_codes_have_a_generator_or_safe_error(self):
        for code in NC_STANDARDS:
            payload = generate_problem_impl(code, difficulty=1)
            assert "error" in payload or (
                "problem_text" in payload and "expected_answer" in payload
            )


class TestEvaluateAnswer:
    def test_exact_match_correct(self):
        result = evaluate_answer_impl("42", "42")
        assert result["is_correct"] is True

    def test_fraction_forms_are_equivalent(self):
        result = evaluate_answer_impl("1/2", "0.5")
        assert result["is_correct"] is True

    def test_unicode_fraction_is_equivalent(self):
        result = evaluate_answer_impl("½", "1/2")
        assert result["is_correct"] is True

    def test_whitespace_and_case_are_ignored(self):
        result = evaluate_answer_impl("  Fifteen  ", "fifteen")
        assert result["is_correct"] is True

    def test_wrong_answer_gets_hint(self):
        result = evaluate_answer_impl("5", "10")
        assert result["is_correct"] is False
        assert result["hint"]

    def test_rounding_discrepancy_resolves_in_students_favor(self):
        result = evaluate_answer_impl("3.34", "3.333333")
        assert result["is_correct"] is True

    def test_output_schema_fields_present(self):
        result = evaluate_answer_impl("1", "1")
        assert isinstance(result["is_correct"], bool)
        assert "normalized_student_answer" in result
        assert "normalized_expected_answer" in result
        assert "hint" in result


class TestGetNcStandards:
    def test_all_returns_full_catalog_plus_clusters(self):
        results = get_nc_standards_impl("all")
        codes = {r["code"] for r in results}
        assert set(NC_STANDARDS.keys()).issubset(codes)

    def test_grade_filter_5(self):
        results = get_nc_standards_impl("5")
        assert len(results) > 0
        assert all(r["grade"] == "5" for r in results)

    def test_grade_filter_6(self):
        results = get_nc_standards_impl("6")
        assert len(results) > 0
        assert all(r["grade"] == "6" for r in results)

    def test_invalid_filter_falls_back_to_all(self):
        results = get_nc_standards_impl("bogus")
        results_all = get_nc_standards_impl("all")
        assert len(results) == len(results_all)


class TestGenerateSessionSummary:
    def _base_state(self, **overrides):
        state = {
            "student_name": "Alex",
            "session_id": str(uuid.uuid4()),
            "target_problem_count": 10,
            "selected_standard_code": "NC.6.EE.7",
            "selected_standard_name": "Solve real-world problems with one-step equations",
            "problems_attempted": 8,
            "problems_correct": 6,
            "problems_skipped": 2,
            "session_start_time": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        }
        state.update(overrides)
        return state

    def test_required_fields_present(self):
        summary = generate_session_summary_impl(self._base_state())
        required_fields = {
            "student_name", "session_id", "session_date", "standard_code",
            "standard_name", "target_count", "problems_attempted",
            "problems_correct", "problems_skipped", "accuracy_pct",
            "duration_seconds", "encouragement_message", "next_step_recommendation",
        }
        assert required_fields.issubset(summary.keys())

    def test_accuracy_pct_computed_correctly(self):
        summary = generate_session_summary_impl(self._base_state())
        assert summary["accuracy_pct"] == 75.0

    def test_zero_attempted_does_not_divide_by_zero(self):
        summary = generate_session_summary_impl(
            self._base_state(problems_attempted=0, problems_correct=0, problems_skipped=0)
        )
        assert summary["accuracy_pct"] == 0.0

    def test_duration_seconds_is_positive(self):
        summary = generate_session_summary_impl(self._base_state())
        assert summary["duration_seconds"] >= 0

    def test_encouragement_and_recommendation_are_nonempty_strings(self):
        summary = generate_session_summary_impl(self._base_state())
        assert isinstance(summary["encouragement_message"], str) and summary["encouragement_message"]
        assert isinstance(summary["next_step_recommendation"], str) and summary["next_step_recommendation"]
