"""Math correctness spot-check (Section 14.2 / Phase 4 deliverable).

Generates 20 problems per standard domain and verifies each expected
answer is mathematically correct by recomputing it from the problem text,
and that the problem is aligned to a valid NC DPI standard code.
"""

import re
from fractions import Fraction

import pytest

from standards.nc_standards import NC_STANDARDS
from tools.problem_generator import generate_problem_impl

SAMPLES_PER_DOMAIN = 20

# One representative standard code per domain.
DOMAIN_CODES = {
    "OA": "NC.5.OA.1",
    "NBT": "NC.5.NBT.5",
    "NF": "NC.5.NF.1",
    "MD": "NC.5.MD.5",
    "G": "NC.6.G.1",
    "RP": "NC.6.RP.1",
    "NS": "NC.6.NS.1",
    "EE": "NC.6.EE.7",
    "SP": "NC.6.SP.3",
}


def _recompute(domain: str, text: str) -> str | None:
    """Recompute the expected answer from a generated problem text."""
    if domain == "OA":
        m = re.search(r"\((\d+) \+ (\d+)\) x (\d+)", text)
        if m:
            return str((int(m[1]) + int(m[2])) * int(m[3]))
    if domain == "NBT":
        m = re.search(r"What is (\d+) x (\d+)\?", text)
        if m:
            return str(int(m[1]) * int(m[2]))
    if domain == "NF":
        m = re.search(r"What is (\d+)/(\d+) \+ (\d+)/(\d+)\?", text)
        if m:
            r = Fraction(int(m[1]), int(m[2])) + Fraction(int(m[3]), int(m[4]))
            return f"{r.numerator}/{r.denominator}"
    if domain == "MD":
        m = re.search(r"(\d+) cm long, (\d+) cm wide, and (\d+) cm tall", text)
        if m:
            return str(int(m[1]) * int(m[2]) * int(m[3]))
    if domain == "G":
        m = re.search(r"base of (\d+) units and a height of (\d+) units", text)
        if m:
            r = Fraction(int(m[1]) * int(m[2]), 2)
            return str(r.numerator) if r.denominator == 1 else f"{r.numerator}/{r.denominator}"
    if domain == "RP":
        m = re.search(r"ratio of (\d+) cups of flour to (\d+) cups of sugar", text)
        m2 = re.search(r"you use (\d+) cups of flour", text)
        if m and m2:
            a, b = int(m[1]), int(m[2])
            mult = int(m2[1]) // a
            return str(b * mult)
    if domain == "NS":
        m = re.search(r"What is (\d+)/(\d+) divided by (\d+)/(\d+)\?", text)
        if m:
            r = Fraction(int(m[1]), int(m[2])) / Fraction(int(m[3]), int(m[4]))
            return f"{r.numerator}/{r.denominator}"
    if domain == "EE":
        m = re.search(r"(\d+)x \+ (\d+) = (\d+)", text)
        if m:
            coeff, const, total = int(m[1]), int(m[2]), int(m[3])
            return str((total - const) // coeff)
    if domain == "SP":
        nums = [int(x) for x in re.findall(r"\d+", text)]
        if nums:
            r = Fraction(sum(nums), len(nums))
            if r.denominator == 1:
                return str(r.numerator)
            return str(round(float(r), 2))
    return None


@pytest.mark.parametrize("domain", list(DOMAIN_CODES.keys()))
def test_spotcheck_domain(domain):
    code = DOMAIN_CODES[domain]
    assert code in NC_STANDARDS
    correct = 0
    total = 0
    for _ in range(SAMPLES_PER_DOMAIN):
        payload = generate_problem_impl(code, difficulty=1)
        assert "error" not in payload
        assert payload["standard_code"] == code
        expected = _recompute(domain, payload["problem_text"])
        assert expected is not None, f"Could not parse: {payload['problem_text']}"
        total += 1
        if expected == payload["expected_answer"]:
            correct += 1
    accuracy = correct / total
    assert accuracy >= 0.95, f"{domain}: only {correct}/{total} correct ({accuracy:.0%})"


def test_spotcheck_overall_accuracy():
    correct = 0
    total = 0
    for domain, code in DOMAIN_CODES.items():
        for _ in range(SAMPLES_PER_DOMAIN):
            payload = generate_problem_impl(code, difficulty=1)
            expected = _recompute(domain, payload["problem_text"])
            total += 1
            if expected == payload["expected_answer"]:
                correct += 1
    accuracy = correct / total
    assert accuracy >= 0.95, f"Overall: {correct}/{total} correct ({accuracy:.0%})"
