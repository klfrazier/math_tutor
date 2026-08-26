"""evaluate_answer tool.

Normalizes and compares a student's free-text answer against the expected
answer, accepting equivalent forms (e.g. "1/2", "0.5", "½").
"""

import re
import unicodedata
from fractions import Fraction

from _sdk import function_tool

_UNICODE_FRACTIONS = {
    "½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4",
    "⅕": "1/5", "⅖": "2/5", "⅗": "3/5", "⅘": "4/5", "⅙": "1/6",
    "⅚": "5/6", "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8",
}

_TOLERANCE = 0.01


def _clean(text: str) -> str:
    text = text or ""
    for uni, ascii_frac in _UNICODE_FRACTIONS.items():
        text = text.replace(uni, ascii_frac)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u2044", "/")
    text = text.strip().lower()
    text = text.replace("$", "").replace("%", "").replace(" ", "")
    return text


def _to_number(text: str) -> float | None:
    if re.fullmatch(r"-?\d+/\d+", text):
        try:
            return float(Fraction(text))
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(text)
    except ValueError:
        return None


def evaluate_answer_impl(student_answer: str, expected_answer: str, problem_text: str = "") -> dict:
    """Plain callable used by the tool wrapper below and directly in tests."""
    normalized_student = _clean(student_answer)
    normalized_expected = _clean(expected_answer)

    student_num = _to_number(normalized_student)
    expected_num = _to_number(normalized_expected)

    if student_num is not None and expected_num is not None:
        is_correct = abs(student_num - expected_num) <= _TOLERANCE
    else:
        is_correct = normalized_student == normalized_expected

    if is_correct:
        hint = ""
    else:
        hint = (
            "Double-check each step of your calculation, and make sure your "
            "answer is in the form the question asks for (e.g. a fraction or "
            "a whole number)."
        )

    return {
        "is_correct": is_correct,
        "normalized_student_answer": normalized_student,
        "normalized_expected_answer": normalized_expected,
        "hint": hint,
    }


@function_tool
def evaluate_answer(student_answer: str, expected_answer: str, problem_text: str = "") -> dict:
    """Determine if the student's answer matches the expected answer."""
    return evaluate_answer_impl(student_answer, expected_answer, problem_text)
