import json
import logging
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

VALID_INTENTS = {
    "learning_summary",
    "weak_topics",
    "strong_topics",
    "syllabus",
    "quiz_assignment",
}

VALID_DIFFICULTIES = {"easy", "medium", "hard", "mixed"}


class ParentAssistantLLMService:
    """Small Ollama-backed planner for the parent assistant.

    The planner only interprets the parent request into a constrained JSON plan.
    Data access and actions still happen in ParentService.
    """

    def __init__(self):
        self.settings = get_settings()
        self.ollama_url = f"{self.settings.OLLAMA_URL}/api/generate"

    def plan(self, message: str, context: dict[str, Any]) -> Optional[dict[str, Any]]:
        prompt = self._build_prompt(message, context)
        try:
            response = httpx.post(
                self.ollama_url,
                json={
                    "model": self.settings.PARENT_ASSISTANT_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.1},
                },
                timeout=self.settings.PARENT_ASSISTANT_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
            raw_plan = payload.get("response", "{}")
            parsed = json.loads(raw_plan)
            return self._clean_plan(parsed)
        except Exception as exc:
            logger.warning("Parent assistant LLM planner unavailable: %s", exc)
            return None

    def _build_prompt(self, message: str, context: dict[str, Any]) -> str:
        context_json = json.dumps(context, default=str)
        return f"""
You are the planning brain for LearnToGrow's parent assistant.
Return only valid JSON. Do not answer the parent directly.

Your job:
- Classify the parent message into one intent.
- Extract IDs only when they are explicitly present in context or selected by the UI.
- Use null when unsure.
- Never invent children, subjects, grades, domains, or progress data.
- Quiz creation is allowed only as a plan; backend validation will execute it.

Valid intents:
- learning_summary
- weak_topics
- strong_topics
- syllabus
- quiz_assignment

Return this JSON shape:
{{
  "intent": "learning_summary|weak_topics|strong_topics|syllabus|quiz_assignment",
  "student_id": number|null,
  "subject_id": number|null,
  "grade_id": number|null,
  "subject_name": string|null,
  "grade_level": number|null,
  "difficulty": "easy|medium|hard|mixed|null",
  "question_count": number|null,
  "domain_ids": [number],
  "domain_names": [string],
  "focus": "weak_topics|strong_topics|subject|domain|null",
  "confidence": number
}}

Context:
{context_json}

Parent message:
{message}
""".strip()

    def _clean_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        intent = plan.get("intent")
        if intent not in VALID_INTENTS:
            intent = None

        difficulty = plan.get("difficulty")
        if difficulty not in VALID_DIFFICULTIES:
            difficulty = None

        question_count = self._optional_int(plan.get("question_count"))
        if question_count is not None:
            question_count = max(1, min(25, question_count))

        return {
            "intent": intent,
            "student_id": self._optional_int(plan.get("student_id")),
            "subject_id": self._optional_int(plan.get("subject_id")),
            "grade_id": self._optional_int(plan.get("grade_id")),
            "subject_name": self._optional_str(plan.get("subject_name")),
            "grade_level": self._optional_int(plan.get("grade_level")),
            "difficulty": difficulty,
            "question_count": question_count,
            "domain_ids": self._int_list(plan.get("domain_ids")),
            "domain_names": self._str_list(plan.get("domain_names")),
            "focus": self._optional_str(plan.get("focus")),
            "confidence": self._confidence(plan.get("confidence")),
        }

    def _optional_int(self, value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _optional_str(self, value: Any) -> Optional[str]:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    def _int_list(self, value: Any) -> list[int]:
        if not isinstance(value, list):
            return []
        result = []
        for item in value:
            parsed = self._optional_int(item)
            if parsed is not None:
                result.append(parsed)
        return result

    def _str_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]

    def _confidence(self, value: Any) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0
