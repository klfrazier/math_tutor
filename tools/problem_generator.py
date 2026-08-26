"""generate_problem tool.

Generates a novel, standards-aligned math problem for a given NC DPI
standard code using local, deterministic templates (no external calls).
Every problem is traceable to a standard_code present in NC_STANDARDS,
per the grounding rule in agents.md Section 4.3.
"""

import random
from fractions import Fraction

from _sdk import function_tool
from standards.nc_standards import NC_STANDARDS


def _difficulty_range(difficulty: int, base_lo: int, base_hi: int) -> tuple[int, int]:
    scale = max(1, min(3, difficulty))
    return base_lo * scale, base_hi * scale


def _gen_oa(difficulty: int) -> dict:
    a, b, c = random.randint(2, 5 * difficulty), random.randint(2, 5 * difficulty), random.randint(2, 9)
    problem_text = f"What is ({a} + {b}) x {c}?"
    expected = (a + b) * c
    return {"problem_text": problem_text, "expected_answer": str(expected)}


def _gen_nbt(difficulty: int) -> dict:
    lo, hi = _difficulty_range(difficulty, 10, 99)
    a = random.randint(lo, hi)
    b = random.randint(2, 9 * difficulty)
    problem_text = f"What is {a} x {b}?"
    expected = a * b
    return {"problem_text": problem_text, "expected_answer": str(expected)}


def _gen_nf(difficulty: int) -> dict:
    denom_choices = [2, 3, 4, 5, 6, 8, 10][: 3 + difficulty]
    d1, d2 = random.sample(denom_choices, 2)
    n1 = random.randint(1, d1 - 1)
    n2 = random.randint(1, d2 - 1)
    f1, f2 = Fraction(n1, d1), Fraction(n2, d2)
    result = f1 + f2
    problem_text = f"What is {n1}/{d1} + {n2}/{d2}? (Give your answer as a fraction.)"
    return {"problem_text": problem_text, "expected_answer": f"{result.numerator}/{result.denominator}"}


def _gen_md(difficulty: int) -> dict:
    length = random.randint(2, 4 * difficulty)
    width = random.randint(2, 4 * difficulty)
    height = random.randint(2, 3 * difficulty)
    problem_text = (
        f"A rectangular box is {length} cm long, {width} cm wide, and {height} cm tall. "
        "What is its volume in cubic centimeters?"
    )
    expected = length * width * height
    return {"problem_text": problem_text, "expected_answer": str(expected)}


def _gen_geometry(difficulty: int) -> dict:
    base = random.randint(3, 6 * difficulty)
    height = random.randint(3, 6 * difficulty)
    problem_text = (
        f"A triangle has a base of {base} units and a height of {height} units. "
        "What is its area in square units?"
    )
    expected = Fraction(base * height, 2)
    if expected.denominator == 1:
        expected_str = str(expected.numerator)
    else:
        expected_str = f"{expected.numerator}/{expected.denominator}"
    return {"problem_text": problem_text, "expected_answer": expected_str}


def _gen_rp(difficulty: int) -> dict:
    a = random.randint(2, 6)
    b = random.randint(2, 6)
    multiplier = random.randint(2, 4 * difficulty)
    problem_text = (
        f"A recipe uses a ratio of {a} cups of flour to {b} cups of sugar. "
        f"If you use {a * multiplier} cups of flour, how many cups of sugar do you need "
        "to keep the same ratio?"
    )
    expected = b * multiplier
    return {"problem_text": problem_text, "expected_answer": str(expected)}


def _gen_ns(difficulty: int) -> dict:
    d1 = random.choice([2, 3, 4, 5, 6])
    n1 = random.randint(1, d1 - 1)
    d2 = random.choice([2, 3, 4, 5])
    n2 = random.randint(1, d2 - 1)
    result = Fraction(n1, d1) / Fraction(n2, d2)
    problem_text = f"What is {n1}/{d1} divided by {n2}/{d2}? (Give your answer as a fraction.)"
    return {"problem_text": problem_text, "expected_answer": f"{result.numerator}/{result.denominator}"}


def _gen_ee(difficulty: int) -> dict:
    coeff = random.randint(2, 5 * difficulty)
    constant = random.randint(1, 10 * difficulty)
    total = random.randint(1, 10 * difficulty)
    x = random.randint(1, 9)
    total = coeff * x + constant
    problem_text = f"Solve for x: {coeff}x + {constant} = {total}"
    return {"problem_text": problem_text, "expected_answer": str(x)}


def _gen_sp(difficulty: int) -> dict:
    count = 4 + difficulty
    values = [random.randint(1, 10 * difficulty) for _ in range(count)]
    problem_text = f"What is the mean of this data set: {', '.join(str(v) for v in values)}?"
    mean = Fraction(sum(values), len(values))
    if mean.denominator == 1:
        expected_str = str(mean.numerator)
    else:
        expected_str = f"{round(float(mean), 2)}"
    return {"problem_text": problem_text, "expected_answer": expected_str}


_DOMAIN_GENERATORS = {
    "OA": _gen_oa,
    "NBT": _gen_nbt,
    "NF": _gen_nf,
    "MD": _gen_md,
    "G": _gen_geometry,
    "RP": _gen_rp,
    "NS": _gen_ns,
    "EE": _gen_ee,
    "SP": _gen_sp,
}


def _parse_domain(standard_code: str) -> str:
    parts = standard_code.split(".")
    return parts[2] if len(parts) >= 3 else ""


def generate_problem_impl(standard_code: str, difficulty: int = 1) -> dict:
    """Plain callable used by the tool wrapper below and directly in tests."""
    if standard_code not in NC_STANDARDS:
        return {
            "error": f"Unknown standard code '{standard_code}'. Please choose a different topic.",
        }

    difficulty = max(1, min(3, difficulty))
    domain = _parse_domain(standard_code)
    generator = _DOMAIN_GENERATORS.get(domain)
    if generator is None:
        return {
            "error": f"No problem generator available for standard '{standard_code}'.",
        }

    payload = generator(difficulty)
    payload["standard_code"] = standard_code
    payload["difficulty"] = difficulty
    return payload


@function_tool
def generate_problem(standard_code: str, difficulty: int = 1) -> dict:
    """Create a novel problem for the given NC DPI standard code."""
    return generate_problem_impl(standard_code, difficulty)
