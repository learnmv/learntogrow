"""Spec-first question genome planning.

The genome is a controlled blueprint for a generated question.  The LLM writes
the surface wording, but the backend chooses the lane: context, representation,
number pattern, misconception target, and difficulty shape.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from sqlalchemy.orm import Session

from app.models import Question, Standard


DOMAIN_PROFILES = {
    "RP": {
        "skills": [
            "compute and interpret a unit rate",
            "compare two rates after converting to unit rates",
            "solve a multistep proportional relationship",
            "connect a table, equation, or verbal rate",
        ],
        "contexts": [
            "grocery unit price",
            "paint or material coverage",
            "water flow",
            "sports pace",
            "map scale",
            "typing or work rate",
            "recipe scaling",
            "fuel or battery usage",
        ],
        "number_patterns": [
            "proper fraction divided by proper fraction",
            "mixed number divided by fraction",
            "decimal divided by fraction",
            "fraction divided by decimal",
            "compare two rational unit rates",
        ],
        "misconceptions": [
            "multiply instead of divide",
            "divide in the wrong order",
            "compare totals instead of unit rates",
            "ignore units while simplifying",
            "round too early",
        ],
    },
    "NS": {
        "skills": [
            "operate with rational numbers",
            "interpret signs in a real-world situation",
            "combine fractions, decimals, and integers",
            "choose the correct operation before computing",
        ],
        "contexts": [
            "bank account changes",
            "temperature changes",
            "elevation or depth",
            "game scores",
            "science measurement",
            "inventory gains and losses",
            "distance on a number line",
        ],
        "number_patterns": [
            "negative decimal plus positive fraction",
            "two-step signed rational operation",
            "fraction times negative decimal",
            "division with a negative rational number",
            "mixed fractions and decimals",
        ],
        "misconceptions": [
            "lose the negative sign",
            "add absolute values incorrectly",
            "apply integer rules to fractions incorrectly",
            "use the wrong operation from the context",
            "convert fractions and decimals incorrectly",
        ],
    },
    "EE": {
        "skills": [
            "write an equation or inequality from context",
            "solve a multistep equation",
            "rewrite equivalent expressions",
            "interpret variables and constraints",
        ],
        "contexts": [
            "school event planning",
            "mobile plan or subscription",
            "ticket or membership pricing",
            "savings goal",
            "craft or construction materials",
            "rental or delivery fee",
        ],
        "number_patterns": [
            "linear expression with rational coefficient",
            "two-step equation with decimal coefficient",
            "inequality with contextual constraint",
            "equivalent expression using distributive property",
            "compare two linear expressions",
        ],
        "misconceptions": [
            "combine unlike terms",
            "reverse inequality meaning",
            "forget to distribute",
            "solve only one side of the equation",
            "misread a fixed fee and variable rate",
        ],
    },
    "G": {
        "skills": [
            "apply a geometry formula in context",
            "combine area, surface area, or volume steps",
            "reason from angle relationships",
            "use scale or cross-section information",
        ],
        "contexts": [
            "garden or park design",
            "packaging and containers",
            "room renovation",
            "art or sign design",
            "blueprints and scale drawings",
            "sports court layout",
        ],
        "number_patterns": [
            "formula with fractional dimensions",
            "scale factor and actual measurement",
            "compose or decompose shapes",
            "angle equation from relationship facts",
            "volume or surface area with mixed units",
        ],
        "misconceptions": [
            "use diameter instead of radius",
            "confuse area and perimeter",
            "apply scale factor to area incorrectly",
            "miss one face in surface area",
            "treat supplementary and complementary angles the same",
        ],
    },
    "SP": {
        "skills": [
            "interpret a probability model",
            "compare samples or distributions",
            "use center and variability",
            "reason about compound events",
        ],
        "contexts": [
            "survey or poll",
            "classroom experiment",
            "sports data",
            "game spinner or dice",
            "quality control sample",
            "weather or environmental data",
        ],
        "number_patterns": [
            "sample proportion extrapolated to population",
            "two distributions with similar variability",
            "compound probability table",
            "relative frequency from repeated trials",
            "mean or median comparison with variability",
        ],
        "misconceptions": [
            "treat biased sample as representative",
            "compare centers without variability",
            "add probabilities for independent compound events",
            "confuse experimental and theoretical probability",
            "overgeneralize from a small sample",
        ],
    },
    "DEFAULT": {
        "skills": [
            "apply the standard in a real-world problem",
            "choose a correct representation",
            "complete a multistep calculation",
            "interpret the answer in context",
        ],
        "contexts": [
            "school planning",
            "shopping",
            "sports",
            "science measurement",
            "community project",
            "travel",
            "art or design",
        ],
        "number_patterns": [
            "whole numbers with one hidden step",
            "fractions and decimals",
            "two-step rational number calculation",
            "comparison of two quantities",
        ],
        "misconceptions": [
            "choose the wrong operation",
            "ignore units",
            "round too early",
            "confuse related quantities",
        ],
    },
}

REPRESENTATIONS = [
    "word problem",
    "table interpretation",
    "equation or expression selection",
    "compare two strategies",
    "error analysis",
    "short justification with computation",
]

ANSWER_FORMATS = [
    "decimal with units",
    "fraction with units",
    "mixed number with units",
    "expression and value",
    "comparison statement",
]

SURFACE_BANNED_CONTEXTS = {
    "snail": "travel/speed",
    "crawls": "travel/speed",
    "flour": "recipe scaling",
    "cookies": "recipe scaling",
}

NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?|\\frac\{\d+\}\{\d+\}|\d+/\d+")
WORD_PATTERN = re.compile(r"[a-z]{4,}")


@dataclass(frozen=True)
class ExistingQuestionSummary:
    question_id: int
    text: str
    context_hits: set[str]
    numeric_tokens: set[str]
    signature: dict[str, Any]


class QuestionGenomePlanner:
    """Builds underused question genomes for any math standard."""

    def __init__(self, db: Session):
        self.db = db

    def build_genome(
        self,
        standard: Standard,
        difficulty: float,
        question_type: str,
        attempt_index: int = 0,
        rejection_notes: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        existing = self._existing_questions(standard.id)
        profile = self._profile_for_standard(standard)
        domain_code = self._domain_code(standard)
        used = self._usage(existing)
        seed = self._seed(standard.id, difficulty, question_type, attempt_index, len(existing))

        skill = self._least_used(profile["skills"], used["skills"], seed)
        context = self._least_used(profile["contexts"], used["contexts"], seed + 3)
        number_pattern = self._least_used(profile["number_patterns"], used["number_patterns"], seed + 7)
        misconception = self._least_used(profile["misconceptions"], used["misconceptions"], seed + 11)
        representation = self._least_used(REPRESENTATIONS, used["representations"], seed + 13)
        answer_format = self._least_used(ANSWER_FORMATS, used["answer_formats"], seed + 17)

        if difficulty >= 0.85:
            reasoning_depth = "expert: combine concepts, require interpretation, include a non-obvious distractor"
            step_count = 4
        elif difficulty >= 0.70:
            reasoning_depth = "challenge: multistep, combine two related ideas, use rational numbers"
            step_count = 3
        elif difficulty >= 0.50:
            reasoning_depth = "hard: two steps, one inference, plausible misconception distractors"
            step_count = 2
        else:
            reasoning_depth = "foundational: one core step with clear quantities"
            step_count = 1

        avoid = self._avoidance(existing)
        genome = {
            "version": 1,
            "standard_id": standard.id,
            "standard_code": standard.code,
            "domain_code": domain_code,
            "skill_focus": skill,
            "context_family": context,
            "representation": representation,
            "number_pattern": number_pattern,
            "misconception_target": misconception,
            "answer_format": answer_format,
            "difficulty_target": round(float(difficulty), 2),
            "reasoning_depth": reasoning_depth,
            "step_count": step_count,
            "question_type": question_type,
            "attempt_index": attempt_index,
            "avoid_contexts": avoid["contexts"],
            "avoid_numbers": avoid["numbers"],
            "avoid_question_summaries": avoid["summaries"],
            "rejection_notes": rejection_notes or [],
        }
        genome["genome_hash"] = self.signature_hash(genome)
        return genome

    def compose_prompt(self, base_prompt: str, genome: dict[str, Any]) -> str:
        genome_json = json.dumps(genome, indent=2, default=str)
        return f"""{base_prompt}

QUESTION GENOME CONTRACT
You must create the question from this backend-selected genome. The genome is mandatory, not inspiration.

{genome_json}

GENOME RULES:
- Use the exact context_family, skill_focus, number_pattern, misconception_target, representation, answer_format, and reasoning_depth.
- Do not reuse any avoid_contexts, avoid_numbers, or avoid_question_summaries.
- Choose fresh quantities that fit the number_pattern and produce a clean, verifiable answer.
- For challenge/expert difficulty, increase reasoning depth through meaningful steps, not confusing wording.
- For multiple choice, make distractors target the misconception_target and other common errors.
- Keep the question grade-appropriate and directly aligned to the standard.
- Return only the raw JSON object requested above.
""".strip()

    def math_spec_from_question(self, question_data: dict[str, Any], genome: dict[str, Any]) -> dict[str, Any]:
        text = " ".join(
            str(part or "")
            for part in [
                question_data.get("question"),
                json.dumps(question_data.get("stimulus") or {}, sort_keys=True),
                " ".join(question_data.get("options") or []),
                question_data.get("answer"),
            ]
        )
        return {
            "number_tokens": sorted(set(NUMBER_PATTERN.findall(text))),
            "number_pattern": genome.get("number_pattern"),
            "step_count": genome.get("step_count"),
            "answer_format": genome.get("answer_format"),
            "misconception_target": genome.get("misconception_target"),
        }

    def semantic_hash(self, standard_id: int, question_data: dict[str, Any], genome: dict[str, Any]) -> str:
        text = self._canonical_text(question_data.get("question", ""))
        payload = {
            "standard_id": standard_id,
            "skill_focus": genome.get("skill_focus"),
            "context_family": genome.get("context_family"),
            "number_tokens": self.math_spec_from_question(question_data, genome)["number_tokens"],
            "question": text,
        }
        return self._hash_payload(payload)

    def signature_hash(self, genome: dict[str, Any]) -> str:
        payload = {
            key: genome.get(key)
            for key in [
                "standard_id",
                "skill_focus",
                "context_family",
                "representation",
                "number_pattern",
                "misconception_target",
                "answer_format",
                "difficulty_target",
            ]
        }
        return self._hash_payload(payload)

    def _existing_questions(self, standard_id: int, limit: int = 200) -> list[ExistingQuestionSummary]:
        questions = (
            self.db.query(Question)
            .filter(Question.standard_id == standard_id, Question.is_active == True)
            .order_by(Question.id.desc())
            .limit(limit)
            .all()
        )
        result = []
        for question in questions:
            signature = question.generation_signature if isinstance(question.generation_signature, dict) else {}
            text = " ".join(
                part
                for part in [
                    question.question_text or "",
                    json.dumps(question.stimulus or {}, sort_keys=True),
                ]
                if part
            )
            result.append(
                ExistingQuestionSummary(
                    question_id=question.id,
                    text=text,
                    context_hits=self._context_hits(text, signature),
                    numeric_tokens=set(NUMBER_PATTERN.findall(text)),
                    signature=signature,
                )
            )
        return result

    def _profile_for_standard(self, standard: Standard) -> dict[str, list[str]]:
        return DOMAIN_PROFILES.get(self._domain_code(standard), DOMAIN_PROFILES["DEFAULT"])

    def _domain_code(self, standard: Standard) -> str:
        if standard.domain and standard.domain.code:
            parts = standard.domain.code.split(".")
            return parts[-1] if parts else "DEFAULT"
        if "." in standard.code:
            parts = standard.code.split(".")
            return parts[1] if len(parts) > 1 else "DEFAULT"
        return "DEFAULT"

    def _usage(self, existing: Iterable[ExistingQuestionSummary]) -> dict[str, dict[str, int]]:
        usage = {
            "skills": {},
            "contexts": {},
            "number_patterns": {},
            "misconceptions": {},
            "representations": {},
            "answer_formats": {},
        }
        for item in existing:
            signature = item.signature
            self._count(usage["skills"], signature.get("skill_focus"))
            self._count(usage["contexts"], signature.get("context_family"))
            self._count(usage["number_patterns"], signature.get("number_pattern"))
            self._count(usage["misconceptions"], signature.get("misconception_target"))
            self._count(usage["representations"], signature.get("representation"))
            self._count(usage["answer_formats"], signature.get("answer_format"))
            for context in item.context_hits:
                self._count(usage["contexts"], context)
        return usage

    def _avoidance(self, existing: list[ExistingQuestionSummary]) -> dict[str, list[str]]:
        contexts = set()
        numbers = set()
        summaries = []
        for item in existing[:12]:
            contexts.update(item.context_hits)
            numbers.update(item.numeric_tokens)
            summaries.append(self._summarize_text(item.text))
        return {
            "contexts": sorted(contexts)[:12],
            "numbers": sorted(numbers)[:24],
            "summaries": summaries[:8],
        }

    def _context_hits(self, text: str, signature: dict[str, Any]) -> set[str]:
        hits = set()
        context = signature.get("context_family")
        if isinstance(context, str) and context.strip():
            hits.add(context.strip())
        lowered = text.lower()
        for marker, label in SURFACE_BANNED_CONTEXTS.items():
            if marker in lowered:
                hits.add(label)
        return hits

    def _least_used(self, choices: list[str], usage: dict[str, int], seed: int) -> str:
        ranked = sorted(
            choices,
            key=lambda choice: (usage.get(choice, 0), (choices.index(choice) + seed) % len(choices), choice),
        )
        return ranked[0]

    def _summarize_text(self, text: str, max_words: int = 18) -> str:
        words = WORD_PATTERN.findall(text.lower())
        if not words:
            return self._canonical_text(text)[:120]
        return " ".join(words[:max_words])

    def _canonical_text(self, text: str) -> str:
        lowered = str(text or "").lower()
        lowered = re.sub(r"\$([^$]+)\$", r" \1 ", lowered)
        lowered = re.sub(r"[^a-z0-9./:\-\s]+", " ", lowered)
        return re.sub(r"\s+", " ", lowered).strip()

    def _seed(self, standard_id: int, difficulty: float, question_type: str, attempt_index: int, existing_count: int) -> int:
        raw = f"{standard_id}:{difficulty:.2f}:{question_type}:{attempt_index}:{existing_count}"
        return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8], 16)

    def _hash_payload(self, payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _count(self, bucket: dict[str, int], value: Any) -> None:
        if isinstance(value, str) and value.strip():
            bucket[value.strip()] = bucket.get(value.strip(), 0) + 1
