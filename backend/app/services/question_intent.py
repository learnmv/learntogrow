"""Standard-specific intent contracts and deterministic rescue questions.

The LLM is good at natural wording, but nearby math standards often differ by
small intent boundaries. These contracts make those boundaries explicit before
generation, during review, and during repair.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.models import Standard


@dataclass(frozen=True)
class StandardIntentProfile:
    target: str
    allowed_tasks: tuple[str, ...]
    forbidden_tasks: tuple[str, ...]
    answer_focus: str
    reviewer_red_flags: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "allowed_tasks": list(self.allowed_tasks),
            "forbidden_tasks": list(self.forbidden_tasks),
            "answer_focus": self.answer_focus,
            "reviewer_red_flags": list(self.reviewer_red_flags),
        }


STANDARD_INTENT_PROFILES: dict[str, StandardIntentProfile] = {
    "6.RP.1": StandardIntentProfile(
        target="Understand ratio concepts and use ratio language to describe a relationship between two quantities.",
        allowed_tasks=(
            "identify a ratio from a context",
            "choose a correct 'for every A, there are B' statement",
            "interpret part-to-part or part-to-whole ratio language",
            "match a ratio to a verbal description",
        ),
        forbidden_tasks=(
            "find a unit rate",
            "calculate a price per one item",
            "calculate speed, pace, or work per one unit",
            "solve a multistep rate or percent problem",
        ),
        answer_focus="The answer should be a ratio statement or equivalent ratio representation, not a unit-rate value.",
        reviewer_red_flags=(
            "asks for 'per 1', unit price, speed, pace, or rate",
            "requires dividing by one quantity to compute a unit rate",
            "could be better aligned to 6.RP.2 or 6.RP.3",
        ),
    ),
    "6.RP.2": StandardIntentProfile(
        target="Understand and compute unit rates associated with ratios.",
        allowed_tasks=(
            "find a unit rate",
            "interpret a per-one quantity",
            "connect a ratio to a rate with units",
        ),
        forbidden_tasks=(
            "only identify ratio language without computing or interpreting a unit rate",
            "multistep percent or proportion solving",
        ),
        answer_focus="The answer should be a unit rate with correct units.",
        reviewer_red_flags=("does not ask for or interpret a unit rate",),
    ),
    "6.NS.4": StandardIntentProfile(
        target="Find GCF and LCM of whole numbers and use the distributive property to express sums.",
        allowed_tasks=(
            "find the greatest common factor of two whole numbers",
            "find the least common multiple of two whole numbers",
            "use the distributive property with a common factor",
        ),
        forbidden_tasks=(
            "signed rational number operations",
            "decimal or fraction arithmetic unrelated to GCF/LCM",
            "finding only a difference between two numbers",
        ),
        answer_focus="The answer should be a GCF, LCM, or equivalent distributive expression.",
        reviewer_red_flags=(
            "asks for addition, subtraction, multiplication, or division of rational numbers",
            "does not require GCF, LCM, or distributive property reasoning",
        ),
    ),
    "7.RP.1": StandardIntentProfile(
        target="Compute unit rates associated with ratios of fractions, including ratios of lengths, areas, and quantities.",
        allowed_tasks=(
            "divide a fractional quantity by another fractional quantity",
            "find a unit rate with compound units",
            "interpret the unit rate in context",
        ),
        forbidden_tasks=(
            "only write basic ratio language",
            "solve a generic percent problem",
        ),
        answer_focus="The answer should be a unit rate, often found by dividing fractions.",
        reviewer_red_flags=("does not involve a ratio of fractions or a unit-rate interpretation",),
    ),
    "7.RP.2": StandardIntentProfile(
        target="Recognize and represent proportional relationships between quantities.",
        allowed_tasks=(
            "identify whether a table is proportional",
            "find or interpret the constant of proportionality",
            "connect table, graph, equation, and verbal proportional relationships",
        ),
        forbidden_tasks=(
            "only compute one isolated unit rate with no proportional relationship",
            "nonlinear relationship reasoning",
        ),
        answer_focus="The answer should identify a proportional relationship, constant of proportionality, equation, or graph feature.",
        reviewer_red_flags=("relationship is not proportional but treated as proportional",),
    ),
    "7.NS.1": StandardIntentProfile(
        target="Apply and interpret addition and subtraction of rational numbers.",
        allowed_tasks=(
            "model addition or subtraction on a number line",
            "interpret signed changes in context",
            "find distance between rational numbers",
        ),
        forbidden_tasks=(
            "multiplication or division of rational numbers as the primary skill",
            "GCF or LCM tasks",
        ),
        answer_focus="The answer should reflect correct signed rational addition/subtraction.",
        reviewer_red_flags=("loses the sign meaning or uses the wrong operation",),
    ),
    "7.G.5": StandardIntentProfile(
        target="Use facts about supplementary, complementary, vertical, and adjacent angles to solve problems.",
        allowed_tasks=(
            "solve for an unknown angle from a relationship",
            "identify vertical or supplementary angle relationships",
            "write and solve a simple angle equation",
        ),
        forbidden_tasks=(
            "area, perimeter, volume, or scale drawing tasks",
            "angle measurement with no relationship reasoning",
        ),
        answer_focus="The answer should be an angle measure or equation justified by angle relationships.",
        reviewer_red_flags=("does not use angle relationships",),
    ),
}


def intent_profile_for_standard(standard: Standard) -> Optional[StandardIntentProfile]:
    return STANDARD_INTENT_PROFILES.get(str(standard.code or "").strip())


def intent_contract_text(standard: Standard) -> str:
    profile = intent_profile_for_standard(standard)
    if not profile:
        return ""

    allowed = "\n".join(f"- {item}" for item in profile.allowed_tasks)
    forbidden = "\n".join(f"- {item}" for item in profile.forbidden_tasks)
    red_flags = "\n".join(f"- {item}" for item in profile.reviewer_red_flags)
    return f"""STANDARD INTENT CONTRACT for {standard.code}
Target: {profile.target}

Allowed task shapes:
{allowed}

Forbidden task shapes:
{forbidden}

Answer focus: {profile.answer_focus}

Reviewer red flags:
{red_flags}
""".strip()


def build_rescue_question(standard: Standard, difficulty: float, attempt_index: int = 0) -> Optional[dict[str, Any]]:
    code = str(standard.code or "").strip()
    builders = {
        "6.RP.1": _rescue_6_rp_1,
        "6.NS.4": _rescue_6_ns_4,
        "7.RP.1": _rescue_7_rp_1,
        "7.RP.2": _rescue_7_rp_2,
        "7.NS.1": _rescue_7_ns_1,
        "7.G.5": _rescue_7_g_5,
    }
    builder = builders.get(code)
    if not builder:
        return None
    return builder(float(difficulty), attempt_index)


def _clamped_difficulty(difficulty: float) -> float:
    return round(max(0.0, min(1.0, difficulty)), 2)


def _rescue_6_rp_1(difficulty: float, attempt_index: int) -> dict[str, Any]:
    pairs = [(12, 9, "art choices", "music choices"), (8, 5, "red tiles", "blue tiles")]
    a, b, left, right = pairs[attempt_index % len(pairs)]
    answer = f"For every {a} {left}, there are {b} {right}."
    return {
        "question": (
            f"A class survey counted {a} {left} and {b} {right}. "
            f"Which statement correctly describes the ratio of {left} to {right}?"
        ),
        "options": [
            answer,
            f"For every {b} {left}, there are {a} {right}.",
            f"For every {a + b} {left}, there are {a} {right}.",
            f"For every {a} {right}, there are {b} {left}.",
        ],
        "answer": answer,
        "explanation": (
            f"The ratio compares {left} first and {right} second, so the correct ratio language is "
            f"for every {a} {left}, there are {b} {right}."
        ),
        "difficulty": _clamped_difficulty(difficulty),
    }


def _rescue_6_ns_4(difficulty: float, attempt_index: int) -> dict[str, Any]:
    pairs = [(12, 18, 36, "minutes"), (8, 20, 40, "seconds")]
    a, b, lcm, unit = pairs[attempt_index % len(pairs)]
    return {
        "question": (
            f"Two lights flash at the same time. One flashes every {a} {unit}, and the other flashes "
            f"every {b} {unit}. After how many {unit} will they flash together again?"
        ),
        "options": [str(lcm), str(abs(b - a)), str(min(a, b)), str(a * b)],
        "answer": str(lcm),
        "explanation": (
            f"They will flash together at common multiples of {a} and {b}. "
            f"The least common multiple is {lcm}, so they flash together again after {lcm} {unit}."
        ),
        "difficulty": _clamped_difficulty(difficulty),
    }


def _rescue_7_rp_1(difficulty: float, attempt_index: int) -> dict[str, Any]:
    return {
        "question": (
            "A cyclist travels $\\frac{3}{4}$ mile in $\\frac{1}{2}$ hour. "
            "What is the cyclist's unit rate in miles per hour?"
        ),
        "options": ["$\\frac{3}{2}$ miles per hour", "$\\frac{3}{8}$ miles per hour", "$\\frac{2}{3}$ miles per hour", "$\\frac{5}{4}$ miles per hour"],
        "answer": "$\\frac{3}{2}$ miles per hour",
        "explanation": (
            "Divide distance by time: $\\frac{3}{4} \\div \\frac{1}{2} = "
            "\\frac{3}{4} \\times 2 = \\frac{3}{2}$ miles per hour."
        ),
        "difficulty": _clamped_difficulty(difficulty),
    }


def _rescue_7_rp_2(difficulty: float, attempt_index: int) -> dict[str, Any]:
    return {
        "question": "Which equation represents the proportional relationship shown in the table?",
        "stimulus": {
            "type": "table",
            "columns": ["x", "y"],
            "rows": [["2", "9"], ["4", "18"], ["6", "27"]],
        },
        "options": ["$y = 4.5x$", "$y = 2x + 5$", "$y = 9x$", "$y = x + 7$"],
        "answer": "$y = 4.5x$",
        "explanation": "Each y-value divided by its x-value is 4.5, so the constant of proportionality is 4.5.",
        "difficulty": _clamped_difficulty(difficulty),
    }


def _rescue_7_ns_1(difficulty: float, attempt_index: int) -> dict[str, Any]:
    return {
        "question": "A submarine is at -12.5 meters and rises 7.75 meters. What is its new elevation?",
        "options": ["-4.75 meters", "-20.25 meters", "4.75 meters", "-5.25 meters"],
        "answer": "-4.75 meters",
        "explanation": "Rising means adding: -12.5 + 7.75 = -4.75.",
        "difficulty": _clamped_difficulty(difficulty),
    }


def _rescue_7_g_5(difficulty: float, attempt_index: int) -> dict[str, Any]:
    return {
        "question": (
            "Two adjacent angles form a straight line. One angle measures 68 degrees. "
            "What is the measure of the other angle?"
        ),
        "options": ["112 degrees", "68 degrees", "22 degrees", "248 degrees"],
        "answer": "112 degrees",
        "explanation": "Adjacent angles on a straight line are supplementary, so they add to 180 degrees. 180 - 68 = 112.",
        "difficulty": _clamped_difficulty(difficulty),
    }
