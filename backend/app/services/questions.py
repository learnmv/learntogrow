import json
import logging
import random
import re
import time
from difflib import SequenceMatcher
from typing import Any, Callable, Dict, List, Optional

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AnsweredQuestion, Question, Standard
from app.prompts import AppletType, format_prompt, get_applet_commands, load_prompt_template
from app.services.ollama_client import (
    ollama_endpoint,
    ollama_headers,
    ollama_supports_structured_outputs,
    parse_ollama_json_response,
)
from app.services.question_genome import QuestionGenomePlanner

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_TEMPERATURE = 0.7
TEMPERATURE_INCREMENT = 0.2
BACKOFF_BASE = 2
DIFFICULTY_TOLERANCE = 0.35
DUPLICATE_TEXT_SIMILARITY_THRESHOLD = 0.90
DUPLICATE_SAME_NUMBERS_SIMILARITY_THRESHOLD = 0.70
DUPLICATE_SAME_NUMBERS_ANSWER_SIMILARITY_THRESHOLD = 0.70
DUPLICATE_NUMBER_OVERLAP_THRESHOLD = 0.75
DUPLICATE_OPTION_OVERLAP_THRESHOLD = 0.75
QUESTION_BANK_LOCK_NAMESPACE = 900_000_000
GENOME_MIN_ATTEMPTS = 4

_OPTION_LABEL_PATTERN = re.compile(r"^[A-Da-d][\.)\s\-]+\s*")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_LATEX_PATTERN = re.compile(r"\$([^$]+)\$")
_PUNCT_PATTERN = re.compile(r"[^a-z0-9./:\-\s]+")
_NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?|\\frac\{\d+\}\{\d+\}|\d+/\d+")
_UNSAFE_CONTROL_PATTERN = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_MARKDOWN_TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
_INCOMPLETE_MARKERS = ("___", "tbd", "todo", "placeholder", "insert ", "missing ")
_CONTROL_LATEX_REPAIRS = {
    "\x0crac": r"\frac",
    "\x0corall": r"\forall",
    "\x08ar": r"\bar",
    "\x08ecause": r"\because",
    "\x08oxed": r"\boxed",
    "\x08inom": r"\binom",
    "\x08eta": r"\beta",
    "\nabla": r"\nabla",
    "\neq": r"\neq",
    "\not": r"\not",
    "\range": r"\range",
    "\rightarrow": r"\rightarrow",
    "\right": r"\right",
    "\x07lpha": r"\alpha",
    "\x07ngle": r"\angle",
    "\x09an": r"\tan",
    "\x09ext": r"\text",
    "\x09frac": r"\tfrac",
    "\x09heta": r"\theta",
    "\x09herefore": r"\therefore",
    "\x09imes": r"\times",
}


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
    if has_unsafe_control_chars(data.get("question")):
        errors.append("Question contains unsafe control characters")
    if has_markdown_table(data.get("question")):
        errors.append("Question text contains a raw markdown table; use structured stimulus.table instead")
    if "when and" in question_lower and "=" not in question_lower:
        errors.append("Question has missing variable values (e.g., 'when and')")
    if any(marker in question_lower for marker in _INCOMPLETE_MARKERS):
        errors.append("Question contains incomplete placeholder text")

    errors.extend(validate_stimulus_data(data.get("stimulus")))

    if data.get("question_type") == "multiple_choice" or "options" in data:
        options = data.get("options", [])
        if not isinstance(options, list):
            errors.append("Options must be a list")
        elif len(options) != 4:
            errors.append(f"Expected 4 options, got {len(options)}")
        else:
            for i, opt in enumerate(options):
                if has_unsafe_control_chars(opt):
                    errors.append(f"Option {chr(65 + i)} contains unsafe control characters")
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
    elif has_unsafe_control_chars(data.get("answer")):
        errors.append("Answer contains unsafe control characters")

    explanation = data.get("explanation")
    if not explanation or len(str(explanation).strip()) < 10:
        errors.append("Explanation is missing or too short")
    elif has_unsafe_control_chars(explanation):
        errors.append("Explanation contains unsafe control characters")

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
    return _OPTION_LABEL_PATTERN.sub("", sanitize_generated_text(str(option)).strip())


def sanitize_generated_text(value: Any) -> str:
    """Repair common JSON escape/control-character damage in generated math text."""
    text = str(value or "")
    for broken, repaired in _CONTROL_LATEX_REPAIRS.items():
        text = text.replace(broken, repaired)
    return text


def has_unsafe_control_chars(value: Any) -> bool:
    return bool(_UNSAFE_CONTROL_PATTERN.search(str(value or "")))


def _markdown_table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def has_markdown_table(value: Any) -> bool:
    lines = str(value or "").splitlines()
    return any(_MARKDOWN_TABLE_SEPARATOR_PATTERN.match(line) for line in lines)


def extract_markdown_table_stimulus(question_text: Any) -> tuple[str, Optional[dict]]:
    """Extract one markdown table from question text into structured stimulus data."""
    lines = sanitize_generated_text(question_text).splitlines()
    for index in range(len(lines) - 1):
        header = lines[index]
        separator = lines[index + 1]
        if "|" not in header or not _MARKDOWN_TABLE_SEPARATOR_PATTERN.match(separator):
            continue

        columns = _markdown_table_cells(header)
        if len(columns) < 2 or any(not column for column in columns):
            continue

        rows: list[list[str]] = []
        end = index + 2
        while end < len(lines) and "|" in lines[end].strip():
            row = _markdown_table_cells(lines[end])
            if len(row) != len(columns):
                break
            rows.append(row)
            end += 1

        if not rows:
            continue

        kept_lines = lines[:index] + lines[end:]
        cleaned_question = "\n".join(line for line in kept_lines).strip()
        cleaned_question = re.sub(r"\n{3,}", "\n\n", cleaned_question)
        stimulus = {
            "type": "table",
            "columns": columns,
            "rows": rows,
        }
        return cleaned_question, stimulus

    return sanitize_generated_text(question_text), None


def sanitize_stimulus(value: Any) -> Optional[dict]:
    if value in (None, "", []):
        return None
    if not isinstance(value, dict):
        return {"type": "text", "content": sanitize_generated_text(value)}

    stimulus = dict(value)
    stimulus_type = sanitize_generated_text(stimulus.get("type") or "").strip().lower()
    stimulus["type"] = stimulus_type

    if stimulus_type == "table":
        columns = stimulus.get("columns") or []
        rows = stimulus.get("rows") or []
        stimulus["columns"] = [sanitize_generated_text(column).strip() for column in columns]
        stimulus["rows"] = [
            [sanitize_generated_text(cell).strip() for cell in row]
            for row in rows
            if isinstance(row, list)
        ]
        if stimulus.get("title"):
            stimulus["title"] = sanitize_generated_text(stimulus["title"]).strip()
        return stimulus

    return {
        key: sanitize_generated_text(item).strip() if isinstance(item, str) else item
        for key, item in stimulus.items()
    }


def validate_stimulus_data(stimulus: Any) -> list[str]:
    if stimulus in (None, "", []):
        return []
    if not isinstance(stimulus, dict):
        return ["Stimulus must be an object"]

    stimulus_type = stimulus.get("type")
    if stimulus_type != "table":
        return [f"Unsupported stimulus type: {stimulus_type!r}"]

    columns = stimulus.get("columns")
    rows = stimulus.get("rows")
    errors: list[str] = []
    if not isinstance(columns, list) or not (2 <= len(columns) <= 5):
        errors.append("Table stimulus must have 2 to 5 columns")
    elif any(not isinstance(column, str) or not column.strip() for column in columns):
        errors.append("Table stimulus columns must be non-empty strings")

    if not isinstance(rows, list) or not (1 <= len(rows) <= 8):
        errors.append("Table stimulus must have 1 to 8 rows")
    elif isinstance(columns, list):
        for row_index, row in enumerate(rows):
            if not isinstance(row, list) or len(row) != len(columns):
                errors.append(f"Table row {row_index + 1} must match the column count")
                continue
            if any(not isinstance(cell, str) or not cell.strip() for cell in row):
                errors.append(f"Table row {row_index + 1} has an empty cell")

    text_parts = []
    if isinstance(columns, list):
        text_parts.extend(columns)
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, list):
                text_parts.extend(row)
    if any(has_unsafe_control_chars(part) for part in text_parts):
        errors.append("Table stimulus contains unsafe control characters")

    return errors


def stimulus_to_text(stimulus: Any) -> str:
    if not isinstance(stimulus, dict):
        return ""
    if stimulus.get("type") == "table":
        columns = stimulus.get("columns") or []
        rows = stimulus.get("rows") or []
        row_text = [
            " ".join(str(cell or "") for cell in row)
            for row in rows
            if isinstance(row, list)
        ]
        return " ".join([*(str(column or "") for column in columns), *row_text])
    return " ".join(str(value or "") for value in stimulus.values())


def normalize_question_for_similarity(value: Any) -> str:
    """Normalize question text while keeping numbers for duplicate detection."""
    text = str(value or "").lower()
    text = text.replace("\\dfrac", "\\frac")
    text = _LATEX_PATTERN.sub(r" \1 ", text)
    text = text.replace("\\times", " times ")
    text = text.replace("\\div", " divided by ")
    text = text.replace("\\left", " ").replace("\\right", " ")
    text = text.replace("{", "").replace("}", "")
    text = _PUNCT_PATTERN.sub(" ", text)
    return _WHITESPACE_PATTERN.sub(" ", text).strip()


def extract_numeric_tokens(value: Any) -> set[str]:
    normalized = normalize_question_for_similarity(value)
    return set(_NUMBER_PATTERN.findall(normalized))


def overlap_ratio(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left.intersection(right)) / max(1, min(len(left), len(right)))


def option_overlap_ratio(candidate_options: Any, existing_options: Any) -> float:
    if not isinstance(candidate_options, list) or not isinstance(existing_options, list):
        return 0.0
    candidate = {normalize_question_for_similarity(option) for option in candidate_options}
    existing = {normalize_question_for_similarity(option) for option in existing_options}
    candidate = {option for option in candidate if option}
    existing = {option for option in existing if option}
    return overlap_ratio(candidate, existing)


def question_similarity(left: Any, right: Any) -> float:
    return SequenceMatcher(
        None,
        normalize_question_for_similarity(left),
        normalize_question_for_similarity(right),
    ).ratio()


class QuestionService:
    """Service for generating and fetching questions."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.ollama_url = ollama_endpoint(self.settings, "generate")

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
            "options": {"temperature": temperature},
        }
        if ollama_supports_structured_outputs(self.settings):
            payload["format"] = "json"

        response = httpx.post(
            self.ollama_url,
            json=payload,
            headers=ollama_headers(self.settings),
            timeout=timeout,
        )
        response.raise_for_status()
        generated_text = response.json().get("response", "")
        return parse_ollama_json_response(generated_text)

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
        if "question" in question_data:
            cleaned_question, extracted_stimulus = extract_markdown_table_stimulus(question_data["question"])
            question_data["question"] = cleaned_question
            if extracted_stimulus and not question_data.get("stimulus"):
                question_data["stimulus"] = extracted_stimulus
        if "explanation" in question_data:
            question_data["explanation"] = sanitize_generated_text(question_data["explanation"])
        if "stimulus" in question_data:
            question_data["stimulus"] = sanitize_stimulus(question_data["stimulus"])
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

    def find_similar_existing_question(
        self,
        standard_id: int,
        question_data: dict,
        exclude_question_id: Optional[int] = None,
    ) -> Optional[dict]:
        """Return an existing active question that is too similar to generated data."""
        candidate_text = " ".join(
            part
            for part in [
                question_data.get("question") or question_data.get("question_text") or "",
                stimulus_to_text(question_data.get("stimulus")),
            ]
            if part
        )
        candidate_normalized = normalize_question_for_similarity(candidate_text)
        if not candidate_normalized:
            return None

        candidate_numbers = extract_numeric_tokens(candidate_text)
        candidate_options = question_data.get("options")
        candidate_answer = normalize_for_match(question_data.get("answer") or question_data.get("correct_answer") or "")
        candidate_semantic_hash = question_data.get("semantic_hash")

        query = self.db.query(Question).filter(
            Question.standard_id == standard_id,
            Question.is_active == True,
        )
        if exclude_question_id is not None:
            query = query.filter(Question.id != exclude_question_id)
        if candidate_semantic_hash:
            exact_hash_match = query.filter(Question.semantic_hash == candidate_semantic_hash).first()
            if exact_hash_match:
                return {
                    "question_id": exact_hash_match.id,
                    "reason": "semantic hash match",
                    "similarity": 1.0,
                }

        for existing in query.order_by(Question.id.desc()).limit(200).all():
            existing_text = " ".join(
                part
                for part in [
                    existing.question_text,
                    stimulus_to_text(existing.stimulus),
                ]
                if part
            )
            existing_normalized = normalize_question_for_similarity(existing_text)
            if not existing_normalized:
                continue
            if candidate_normalized == existing_normalized:
                return {
                    "question_id": existing.id,
                    "reason": "exact question text match",
                    "similarity": 1.0,
                }

            similarity = question_similarity(candidate_text, existing_text)
            number_overlap = overlap_ratio(candidate_numbers, extract_numeric_tokens(existing_text))
            option_overlap = option_overlap_ratio(candidate_options, existing.options)
            answer_matches = bool(candidate_answer) and candidate_answer == normalize_for_match(existing.correct_answer)

            if (
                similarity >= DUPLICATE_TEXT_SIMILARITY_THRESHOLD
                and (
                    number_overlap >= DUPLICATE_NUMBER_OVERLAP_THRESHOLD
                    or option_overlap >= DUPLICATE_OPTION_OVERLAP_THRESHOLD
                )
            ):
                return {
                    "question_id": existing.id,
                    "reason": (
                        f"similarity={similarity:.2f}, "
                        f"number_overlap={number_overlap:.2f}, "
                        f"option_overlap={option_overlap:.2f}"
                    ),
                    "similarity": round(similarity, 3),
                    "number_overlap": round(number_overlap, 3),
                    "option_overlap": round(option_overlap, 3),
                }
            if (
                answer_matches
                and number_overlap >= DUPLICATE_NUMBER_OVERLAP_THRESHOLD
                and similarity >= DUPLICATE_SAME_NUMBERS_ANSWER_SIMILARITY_THRESHOLD
            ):
                return {
                    "question_id": existing.id,
                    "reason": (
                        f"same answer and numbers with similarity={similarity:.2f}, "
                        f"number_overlap={number_overlap:.2f}"
                    ),
                    "similarity": round(similarity, 3),
                    "number_overlap": round(number_overlap, 3),
                    "option_overlap": round(option_overlap, 3),
                }
            if (
                len(candidate_numbers) >= 2
                and number_overlap >= 1.0
                and similarity >= DUPLICATE_SAME_NUMBERS_SIMILARITY_THRESHOLD
            ):
                return {
                    "question_id": existing.id,
                    "reason": (
                        f"same numeric setup with similarity={similarity:.2f}, "
                        f"number_overlap={number_overlap:.2f}"
                    ),
                    "similarity": round(similarity, 3),
                    "number_overlap": round(number_overlap, 3),
                    "option_overlap": round(option_overlap, 3),
                }

        return None

    def assert_not_duplicate_question(
        self,
        standard_id: int,
        question_data: dict,
        exclude_question_id: Optional[int] = None,
    ) -> None:
        similar = self.find_similar_existing_question(
            standard_id=standard_id,
            question_data=question_data,
            exclude_question_id=exclude_question_id,
        )
        if similar:
            raise ValueError(
                "Generated question is too similar to existing question "
                f"{similar['question_id']} ({similar['reason']})"
            )

    def lock_standard_question_bank(self, standard_id: int) -> None:
        """Serialize final duplicate-check-and-insert for one standard."""
        self.db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": QUESTION_BANK_LOCK_NAMESPACE + int(standard_id)},
        )

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
        active_prompt = prompt

        for attempt in range(MAX_RETRIES):
            started_at = time.perf_counter()
            try:
                temperature = BASE_TEMPERATURE + (attempt * TEMPERATURE_INCREMENT)
                raw = self._call_ollama_json(active_prompt, model, timeout, temperature=temperature)
                question_data = self._normalize_question_data(raw, standard, difficulty, question_type)
                self.assert_not_duplicate_question(standard.id, question_data)
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
                if "too similar" in str(exc).lower():
                    active_prompt = (
                        f"{prompt}\n\n"
                        "DIVERSITY RETRY FEEDBACK:\n"
                        f"The previous attempt was rejected because it was too similar: {exc}.\n"
                        "Keep the genome skill aligned, but change the surface scenario details, all reusable "
                        "numbers, and the answer value. Do not repeat the rejected setup."
                    )
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
        self.assert_not_duplicate_question(standard.id, repaired)

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
        genome_planner = QuestionGenomePlanner(self.db) if custom_prompt is None else None
        attempts_to_review = actual_candidate_count
        if actual_quality_mode in {"fast", "reviewed"}:
            attempts_to_review = max(1, actual_max_repairs + 1)
        if genome_planner:
            attempts_to_review = max(attempts_to_review, GENOME_MIN_ATTEMPTS)

        candidates = []
        last_error = None
        rejection_notes: list[str] = []
        started_at = time.perf_counter()
        for candidate_index in range(attempts_to_review):
            genome = None
            prompt = base_prompt
            if genome_planner:
                genome = genome_planner.build_genome(
                    standard=standard,
                    difficulty=actual_difficulty,
                    question_type=question_type,
                    attempt_index=candidate_index,
                    rejection_notes=rejection_notes[-5:],
                )
                prompt = genome_planner.compose_prompt(base_prompt, genome)
                self._audit(
                    audit_callback,
                    stage="genome",
                    status="completed",
                    prompt_name="question_genome",
                    model=ollama_model,
                    request_payload={
                        "standard_id": standard.id,
                        "difficulty": actual_difficulty,
                        "candidate_index": candidate_index,
                    },
                    response_payload=genome,
                    candidate_index=candidate_index,
                    notes=(
                        f"{genome['context_family']} | {genome['number_pattern']} | "
                        f"{genome['misconception_target']}"
                    ),
                )
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
                        "genome": genome,
                    }
                )
                if review.get("approved") and actual_quality_mode in {"fast", "reviewed"}:
                    break
            except Exception as exc:
                last_error = exc
                rejection_notes.append(str(exc))
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
        best_genome = best.get("genome") or {}
        if genome_planner and best_genome:
            question_data["generation_signature"] = best_genome
            question_data["math_spec"] = genome_planner.math_spec_from_question(question_data, best_genome)
            question_data["semantic_hash"] = genome_planner.semantic_hash(standard.id, question_data, best_genome)
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
