import json
import logging
import random
import re
import time
from typing import Any, Callable, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AnsweredQuestion, Question, Standard
from app.prompts import AppletType, format_prompt, get_applet_commands, load_prompt_template

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_TEMPERATURE = 0.7
TEMPERATURE_INCREMENT = 0.2
BACKOFF_BASE = 2
DIFFICULTY_TOLERANCE = 0.35

_OPTION_LABEL_PATTERN = re.compile(r"^[A-Da-d][\.)\s\-]+\s*")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_INCOMPLETE_MARKERS = ("___", "tbd", "todo", "placeholder", "insert ", "missing ")


def normalize_for_match(value: Any) -> str:
    """Normalize text for strict option/answer comparison."""
    return _WHITESPACE_PATTERN.sub(" ", str(value).strip()).lower()


def validate_question_data(data: dict, standard_code: str, target_difficulty: Optional[float] = None) -> dict:
    """Validate and clean question data from LLM."""
    errors = []

    if not data.get("question"):
        errors.append("Question text is missing")
    elif len(data["question"].strip()) < 10:
        errors.append(f"Question text too short: '{data['question']}'")
    elif "..." in data["question"] or data["question"].count("?") > 1:
        errors.append(f"Question appears incomplete: '{data['question']}'")

    question_lower = data.get("question", "").lower()
    if "when and" in question_lower and "=" not in question_lower:
        errors.append("Question has missing variable values (e.g., 'when and')")
    if any(marker in question_lower for marker in _INCOMPLETE_MARKERS):
        errors.append("Question contains incomplete placeholder text")

    if data.get("question_type") == "multiple_choice" or "options" in data:
        options = data.get("options", [])
        if not isinstance(options, list):
            errors.append("Options must be a list")
        elif len(options) != 4:
            errors.append(f"Expected 4 options, got {len(options)}")
        else:
            for i, opt in enumerate(options):
                if not opt or len(str(opt).strip()) < 1:
                    errors.append(f"Option {chr(65 + i)} is empty")
                elif str(opt).strip() in ["A", "B", "C", "D"]:
                    errors.append(f"Option {chr(65 + i)} is just a letter label")
            normalized_options = [normalize_for_match(opt) for opt in options]
            if len(set(normalized_options)) != len(normalized_options):
                errors.append("Options must be unique")

            answer = data.get("answer")
            if answer:
                normalized_answer = normalize_for_match(answer)
                matches = [opt for opt in normalized_options if opt == normalized_answer]
                if len(matches) != 1:
                    errors.append("Answer must match exactly one option")

    if data.get("requires_diagram"):
        commands = data.get("geogebra_commands")
        if not commands or not isinstance(commands, list) or len(commands) == 0:
            errors.append("GeoGebra commands are required for diagram questions but were missing or empty")
        elif not all(isinstance(cmd, str) and cmd.strip() for cmd in commands):
            errors.append("GeoGebra commands must be a list of non-empty strings")

    if not data.get("answer"):
        errors.append("Answer is missing")

    explanation = data.get("explanation")
    if not explanation or len(str(explanation).strip()) < 10:
        errors.append("Explanation is missing or too short")

    difficulty = data.get("difficulty")
    try:
        difficulty_value = float(difficulty)
    except (TypeError, ValueError):
        errors.append("Difficulty must be a number between 0 and 1")
    else:
        if difficulty_value < 0 or difficulty_value > 1:
            errors.append("Difficulty must be between 0 and 1")
        if target_difficulty is not None and abs(difficulty_value - target_difficulty) > DIFFICULTY_TOLERANCE:
            errors.append(
                f"Difficulty {difficulty_value:.2f} is too far from target {target_difficulty:.2f}"
            )
        data["difficulty"] = round(difficulty_value, 2)

    if errors:
        raise ValueError(f"Invalid question data: {'; '.join(errors)}")

    return data


def clean_option_text(option: str) -> str:
    """Clean option text by removing duplicate letter labels."""
    if not option:
        return option
    return _OPTION_LABEL_PATTERN.sub("", str(option).strip())


class QuestionService:
    """Service for generating and fetching questions."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.ollama_url = f"{self.settings.OLLAMA_URL}/api/generate"

    def get_questions_by_standard(
        self,
        standard_id: int,
        limit: Optional[int] = None,
        student_id: Optional[int] = None,
    ) -> List[Question]:
        """Fetch active questions for a standard, optionally excluding answered ones."""
        query = self.db.query(Question).filter(
            Question.standard_id == standard_id,
            Question.is_active == True,
        )

        if student_id is not None:
            answered_ids = self.db.query(AnsweredQuestion.question_id).filter(
                AnsweredQuestion.student_id == student_id
            ).subquery()
            query = query.filter(Question.id.notin_(answered_ids))

        if limit:
            query = query.limit(limit)
        return query.all()

    def _build_prompt(
        self,
        standard: Standard,
        difficulty: float,
        question_type: str,
    ) -> str:
        """Build a prompt for question generation."""
        keywords = ", ".join(standard.keywords) if standard.keywords else "related concepts"
        grade_level = standard.grade.level if standard.grade else "appropriate"
        applet_type = self._applet_type_for_standard(standard)

        return format_prompt(
            db=self.db,
            question_type=question_type,
            grade_level=str(grade_level),
            standard_code=standard.code,
            standard_description=standard.description,
            difficulty=difficulty,
            keywords=keywords,
            requires_diagram=standard.requires_diagram,
            applet_type=applet_type,
        )

    def _applet_type_for_standard(self, standard: Standard) -> Optional[AppletType]:
        if not standard.applet_type:
            return None
        try:
            return AppletType(standard.applet_type)
        except ValueError:
            return None

    def _json_safe(self, value: Any) -> Any:
        return json.loads(json.dumps(value, default=str))

    def _call_ollama_json(
        self,
        prompt: str,
        model: str,
        timeout: int,
        temperature: float = BASE_TEMPERATURE,
    ) -> dict:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature},
        }
        response = httpx.post(self.ollama_url, json=payload, timeout=timeout)
        response.raise_for_status()
        generated_text = response.json().get("response", "")
        return json.loads(generated_text)

    def _audit(
        self,
        audit_callback: Optional[Callable[..., None]],
        stage: str,
        status: str,
        prompt_name: Optional[str] = None,
        model: Optional[str] = None,
        request_payload: Optional[dict] = None,
        response_payload: Optional[dict] = None,
        notes: Optional[str] = None,
        score: Optional[float] = None,
        candidate_index: Optional[int] = None,
        attempt: int = 0,
    ) -> None:
        if not audit_callback:
            return
        audit_callback(
            stage=stage,
            status=status,
            prompt_name=prompt_name,
            model=model,
            request_payload=self._json_safe(request_payload or {}),
            response_payload=self._json_safe(response_payload or {}),
            notes=notes,
            score=score,
            candidate_index=candidate_index,
            attempt=attempt,
        )

    def _quality_context(
        self,
        standard: Standard,
        difficulty: float,
        question_type: str,
        min_review_score: float = 0.75,
    ) -> dict:
        keywords = ", ".join(standard.keywords) if standard.keywords else "related concepts"
        grade_level = str(standard.grade.level) if standard.grade else "appropriate"
        applet_type = self._applet_type_for_standard(standard)
        applet_commands = ""
        if standard.requires_diagram and applet_type:
            try:
                applet_commands = get_applet_commands(self.db, applet_type)
            except ValueError:
                applet_commands = ""

        return {
            "grade_level": grade_level,
            "standard_code": standard.code,
            "standard_description": standard.description,
            "difficulty": difficulty,
            "keywords": keywords,
            "question_type": question_type.replace("_", " "),
            "requires_diagram": standard.requires_diagram,
            "applet_type": applet_type.value if applet_type else standard.applet_type,
            "applet_commands": applet_commands or "No diagram commands are required.",
            "min_review_score": min_review_score,
        }

    def _normalize_question_data(
        self,
        data: dict,
        standard: Standard,
        difficulty: float,
        question_type: str,
    ) -> dict:
        question_data = dict(data)
        question_data["standard_code"] = standard.code
        question_data["difficulty"] = question_data.get("difficulty", difficulty)
        question_data["question_type"] = question_type
        question_data["requires_diagram"] = standard.requires_diagram
        question_data["applet_type"] = standard.applet_type

        if "options" in question_data and isinstance(question_data["options"], list):
            question_data["options"] = [clean_option_text(opt) for opt in question_data["options"]]
        if "answer" in question_data:
            question_data["answer"] = clean_option_text(str(question_data["answer"]))

        validate_question_data(question_data, standard.code, target_difficulty=difficulty)

        if standard.requires_diagram and not question_data.get("geogebra_commands"):
            raise ValueError(f"Diagram question for {standard.code} is missing required geogebra_commands")

        return question_data

    def _generate_candidate(
        self,
        standard: Standard,
        difficulty: float,
        question_type: str,
        prompt: str,
        model: str,
        timeout: int,
        candidate_index: int = 0,
        audit_callback: Optional[Callable[..., None]] = None,
    ) -> dict:
        last_error = None

        for attempt in range(MAX_RETRIES):
            started_at = time.perf_counter()
            try:
                temperature = BASE_TEMPERATURE + (attempt * TEMPERATURE_INCREMENT)
                raw = self._call_ollama_json(prompt, model, timeout, temperature=temperature)
                question_data = self._normalize_question_data(raw, standard, difficulty, question_type)
                elapsed = time.perf_counter() - started_at
                self._audit(
                    audit_callback,
                    stage="candidate",
                    status="completed",
                    prompt_name=question_type,
                    model=model,
                    request_payload={"standard_id": standard.id, "difficulty": difficulty},
                    response_payload=question_data,
                    candidate_index=candidate_index,
                    attempt=attempt,
                    notes=f"Generated valid candidate on attempt {attempt + 1} in {elapsed:.2f}s",
                )
                logger.info(
                    "Generated candidate for %s in %.2fs (candidate=%s attempt=%s)",
                    standard.code,
                    elapsed,
                    candidate_index,
                    attempt,
                )
                return question_data
            except ValueError as exc:
                elapsed = time.perf_counter() - started_at
                logger.warning(f"Attempt {attempt + 1}: Validation failed: {exc}")
                last_error = exc
                self._audit(
                    audit_callback,
                    stage="candidate",
                    status="failed",
                    prompt_name=question_type,
                    model=model,
                    request_payload={"standard_id": standard.id, "difficulty": difficulty},
                    response_payload={},
                    candidate_index=candidate_index,
                    attempt=attempt,
                    notes=f"{exc} after {elapsed:.2f}s",
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_BASE ** attempt)
                continue
            except json.JSONDecodeError as exc:
                elapsed = time.perf_counter() - started_at
                logger.warning(f"Attempt {attempt + 1}: Failed to parse JSON: {exc}")
                last_error = exc
                self._audit(
                    audit_callback,
                    stage="candidate",
                    status="failed",
                    prompt_name=question_type,
                    model=model,
                    request_payload={"standard_id": standard.id, "difficulty": difficulty},
                    response_payload={},
                    candidate_index=candidate_index,
                    attempt=attempt,
                    notes=f"Invalid JSON after {elapsed:.2f}s: {exc}",
                )
                continue
            except httpx.ConnectError as exc:
                logger.error(f"Failed to connect to Ollama: {exc}")
                raise ConnectionError(f"Could not connect to Ollama at {self.settings.OLLAMA_URL}. Is Ollama running?")
            except httpx.TimeoutException:
                logger.error("Ollama request timed out")
                raise TimeoutError(f"Ollama request timed out after {timeout} seconds")
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in (429, 502, 503) and attempt < MAX_RETRIES - 1:
                    sleep_seconds = (BACKOFF_BASE ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Attempt {attempt + 1}: Ollama returned {status}, "
                        f"backing off {sleep_seconds:.1f}s before retry"
                    )
                    time.sleep(sleep_seconds)
                    last_error = exc
                    continue
                logger.error(f"Ollama HTTP error: {status} - {exc.response.text}")
                raise RuntimeError(f"Ollama error: {exc.response.text}")

        raise RuntimeError(f"Failed to generate valid question after {MAX_RETRIES} attempts. Last error: {last_error}")

    def _plan_question(
        self,
        standard: Standard,
        difficulty: float,
        question_type: str,
        model: str,
        timeout: int,
        audit_callback: Optional[Callable[..., None]],
    ) -> dict:
        context = self._quality_context(standard, difficulty, question_type)
        prompt = load_prompt_template(self.db, "question_planner").format(**context)
        try:
            plan = self._call_ollama_json(prompt, model, timeout, temperature=0.35)
            self._audit(
                audit_callback,
                stage="planner",
                status="completed",
                prompt_name="question_planner",
                model=model,
                request_payload=context,
                response_payload=plan,
                notes=plan.get("skill_focus") if isinstance(plan, dict) else None,
            )
            return plan if isinstance(plan, dict) else {}
        except Exception as exc:
            self._audit(
                audit_callback,
                stage="planner",
                status="failed",
                prompt_name="question_planner",
                model=model,
                request_payload=context,
                response_payload={},
                notes=str(exc),
            )
            raise

    def _review_question(
        self,
        question_data: dict,
        standard: Standard,
        difficulty: float,
        question_type: str,
        model: str,
        timeout: int,
        min_review_score: float,
        candidate_index: int,
        audit_callback: Optional[Callable[..., None]],
    ) -> dict:
        context = self._quality_context(standard, difficulty, question_type, min_review_score)
        context["question_json"] = json.dumps(question_data, default=str)
        prompt = load_prompt_template(self.db, "question_reviewer").format(**context)
        started_at = time.perf_counter()
        review = self._call_ollama_json(prompt, model, timeout, temperature=0.15)
        elapsed = time.perf_counter() - started_at
        score = float(review.get("score", 0) or 0)
        issues = review.get("issues") if isinstance(review.get("issues"), list) else []
        approved = bool(review.get("approved")) and score >= min_review_score and not issues
        review["approved"] = approved
        notes = review.get("improvement_notes")
        timed_notes = f"{notes} Review call {elapsed:.2f}s." if notes else f"Review call {elapsed:.2f}s."

        self._audit(
            audit_callback,
            stage="review",
            status="approved" if approved else "rejected",
            prompt_name="question_reviewer",
            model=model,
            request_payload={"standard_id": standard.id, "question": question_data},
            response_payload=review,
            notes=timed_notes,
            score=score,
            candidate_index=candidate_index,
        )
        logger.info(
            "Reviewed candidate for %s in %.2fs (candidate=%s approved=%s score=%.2f)",
            standard.code,
            elapsed,
            candidate_index,
            approved,
            score,
        )
        return review

    def _repair_question(
        self,
        question_data: dict,
        review_or_error: Any,
        standard: Standard,
        difficulty: float,
        question_type: str,
        model: str,
        timeout: int,
        candidate_index: int,
        attempt: int,
        audit_callback: Optional[Callable[..., None]],
    ) -> dict:
        context = self._quality_context(standard, difficulty, question_type)
        if isinstance(review_or_error, dict):
            issues = review_or_error.get("issues") or [review_or_error.get("improvement_notes")]
        else:
            issues = [str(review_or_error)]
        issues = [issue for issue in issues if issue]
        context["question_json"] = json.dumps(question_data, default=str)
        context["issues"] = json.dumps(issues, default=str)
        prompt = load_prompt_template(self.db, "question_repair").format(**context)
        raw = self._call_ollama_json(prompt, model, timeout, temperature=0.25)
        repaired = self._normalize_question_data(raw, standard, difficulty, question_type)

        self._audit(
            audit_callback,
            stage="repair",
            status="completed",
            prompt_name="question_repair",
            model=model,
            request_payload={"standard_id": standard.id, "issues": issues, "question": question_data},
            response_payload=repaired,
            candidate_index=candidate_index,
            attempt=attempt,
            notes="Repaired candidate",
        )
        return repaired

    def _build_planned_prompt(self, base_prompt: str, plan: dict) -> str:
        if not plan:
            return base_prompt
        return (
            f"{base_prompt}\n\n"
            "Use this planning guidance exactly when creating the question:\n"
            f"{json.dumps(plan, indent=2)}\n"
            "Distractors should reflect the listed misconceptions where possible."
        )

    def generate_question(
        self,
        standard_id: int,
        difficulty: Optional[float] = None,
        question_type: str = "multiple_choice",
        custom_prompt: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        quality_mode: Optional[str] = None,
        candidate_count: Optional[int] = None,
        max_repair_attempts: Optional[int] = None,
        min_review_score: Optional[float] = None,
        audit_callback: Optional[Callable[..., None]] = None,
    ) -> Dict[str, Any]:
        """Generate a question using Ollama and return only review-approved output."""
        standard = self.db.query(Standard).filter(Standard.id == standard_id).first()
        if not standard:
            raise ValueError(f"Standard with ID {standard_id} not found")

        actual_difficulty = difficulty if difficulty is not None else (
            float(standard.difficulty_base) if standard.difficulty_base else 0.5
        )
        ollama_model = model if model else self.settings.OLLAMA_MODEL
        actual_timeout = timeout if timeout is not None else self.settings.OLLAMA_TIMEOUT
        actual_quality_mode = (quality_mode or self.settings.OLLAMA_QUALITY_MODE).lower()
        if actual_quality_mode not in {"fast", "reviewed", "quality"}:
            actual_quality_mode = "reviewed"

        actual_candidate_count = candidate_count if candidate_count is not None else 1
        actual_candidate_count = max(1, min(5, actual_candidate_count))
        if actual_quality_mode in {"fast", "reviewed"}:
            actual_candidate_count = 1

        actual_max_repairs = max_repair_attempts if max_repair_attempts is not None else 1
        actual_max_repairs = max(0, min(3, actual_max_repairs))
        actual_min_score = min_review_score if min_review_score is not None else 0.75
        actual_min_score = max(0.0, min(1.0, actual_min_score))

        logger.info(
            f"Generating {question_type} question for standard {standard.code} "
            f"in {actual_quality_mode} mode"
        )

        base_prompt = custom_prompt if custom_prompt else self._build_prompt(
            standard,
            actual_difficulty,
            question_type,
        )

        plan: dict = {}
        prompt = base_prompt
        attempts_to_review = actual_candidate_count
        if actual_quality_mode in {"fast", "reviewed"}:
            attempts_to_review = max(1, actual_max_repairs + 1)

        candidates = []
        last_error = None
        started_at = time.perf_counter()
        for candidate_index in range(attempts_to_review):
            try:
                candidate = self._generate_candidate(
                    standard=standard,
                    difficulty=actual_difficulty,
                    question_type=question_type,
                    prompt=prompt,
                    model=ollama_model,
                    timeout=actual_timeout,
                    candidate_index=candidate_index,
                    audit_callback=audit_callback,
                )
                review = self._review_question(
                    question_data=candidate,
                    standard=standard,
                    difficulty=actual_difficulty,
                    question_type=question_type,
                    model=ollama_model,
                    timeout=actual_timeout,
                    min_review_score=actual_min_score,
                    candidate_index=candidate_index,
                    audit_callback=audit_callback,
                )

                candidates.append(
                    {
                        "question": candidate,
                        "review": review,
                        "score": float(review.get("score", 0) or 0),
                    }
                )
                if review.get("approved") and actual_quality_mode in {"fast", "reviewed"}:
                    break
            except Exception as exc:
                last_error = exc
                logger.warning(f"Candidate {candidate_index + 1} failed for {standard.code}: {exc}")

        if not candidates:
            raise RuntimeError(f"No valid candidates generated for {standard.code}. Last error: {last_error}")

        approved = [candidate for candidate in candidates if candidate["review"].get("approved")]
        if not approved:
            best_rejected = max(candidates, key=lambda candidate: candidate["score"])
            raise RuntimeError(
                f"No generated question passed review for {standard.code}. "
                f"Best score: {best_rejected['score']:.2f}. "
                f"Notes: {best_rejected['review'].get('improvement_notes')}"
            )

        best = max(approved, key=lambda candidate: candidate["score"])
        question_data = best["question"]
        question_data["review"] = best["review"]
        question_data["quality_score"] = best["score"]
        question_data["planner"] = plan
        elapsed = time.perf_counter() - started_at
        logger.info(
            "Generated reviewed question for %s with score %.2f in %.2fs (%s reviewed attempt%s)",
            standard.code,
            best["score"],
            elapsed,
            len(candidates),
            "" if len(candidates) == 1 else "s",
        )
        return question_data
