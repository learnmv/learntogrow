from typing import Any

from app.schemas.parent import ParentAssistantChatRequest
from app.schemas.quiz_assignment import QuizAssignmentCreateRequest


class ParentAssistantToolRegistry:
    """Controlled tools available to the parent assistant."""

    def __init__(self, parent_service: Any, parent_id: int):
        self.parent_service = parent_service
        self.parent_id = parent_id

    @staticmethod
    def list_tools() -> list[dict[str, Any]]:
        return [
            {
                "name": "get_children",
                "description": "List children linked to the current parent.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_learning_summary",
                "description": "Summarize a child's strong and weak learning areas.",
                "parameters": {
                    "type": "object",
                    "properties": {"student_id": {"type": "integer"}},
                    "required": ["student_id"],
                },
            },
            {
                "name": "get_weak_topics",
                "description": "Get the child's weakest curriculum domains.",
                "parameters": {
                    "type": "object",
                    "properties": {"student_id": {"type": "integer"}},
                    "required": ["student_id"],
                },
            },
            {
                "name": "get_strong_topics",
                "description": "Get the child's strongest curriculum domains.",
                "parameters": {
                    "type": "object",
                    "properties": {"student_id": {"type": "integer"}},
                    "required": ["student_id"],
                },
            },
            {
                "name": "get_syllabus",
                "description": "Show curriculum domains for a subject and optional grade.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject_id": {"type": "integer"},
                        "grade_id": {"type": "integer"},
                    },
                },
            },
            {
                "name": "create_quiz_assignment",
                "description": "Create and assign a quiz to a linked child.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "integer"},
                        "subject_id": {"type": "integer"},
                        "grade_id": {"type": "integer"},
                        "domain_ids": {"type": "array", "items": {"type": "integer"}},
                        "difficulty": {"type": "string", "enum": ["easy", "medium", "hard", "mixed"]},
                        "question_count": {"type": "integer", "minimum": 1, "maximum": 25},
                        "focus": {"type": "string", "enum": ["weak_topics", "subject", "domain"]},
                    },
                    "required": ["student_id", "subject_id", "grade_id"],
                },
            },
            {
                "name": "get_assignment_status",
                "description": "Get status for a parent-created quiz assignment.",
                "parameters": {
                    "type": "object",
                    "properties": {"assignment_id": {"type": "integer"}},
                    "required": ["assignment_id"],
                },
            },
        ]

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "get_children":
            return self._get_children()
        if tool_name == "get_learning_summary":
            return self._learning_response(arguments, focus="summary")
        if tool_name == "get_weak_topics":
            return self._learning_response(arguments, focus="weak")
        if tool_name == "get_strong_topics":
            return self._learning_response(arguments, focus="strong")
        if tool_name == "get_syllabus":
            return self._get_syllabus(arguments)
        if tool_name == "create_quiz_assignment":
            return self._create_quiz_assignment(arguments)
        if tool_name == "get_assignment_status":
            return self._get_assignment_status(arguments)

        return {
            "ok": False,
            "intent": "learning_summary",
            "fallback_answer": "I do not know how to use that assistant tool yet.",
            "suggestions": ["Show weak topics", "Show syllabus"],
            "data": {},
        }

    def _get_children(self) -> dict[str, Any]:
        children = [child.model_dump() for child in self.parent_service.get_linked_students(self.parent_id)]
        if not children:
            answer = "I do not see any approved student links yet."
        else:
            names = ", ".join(child["student_name"] for child in children)
            answer = f"Your linked children are: {names}."
        return {
            "ok": True,
            "intent": "learning_summary",
            "fallback_answer": answer,
            "suggestions": ["Show weak topics", "Show strong topics", "Show syllabus"],
            "data": {"children": children},
        }

    def _learning_response(self, arguments: dict[str, Any], focus: str) -> dict[str, Any]:
        student = self._get_student(arguments)
        if not student:
            return self._student_required_result()

        response = self.parent_service._assistant_learning_response(student, focus=focus)
        return {
            "ok": True,
            "intent": response["intent"],
            "fallback_answer": response["answer"],
            "suggestions": response.get("suggestions", []),
            "data": response.get("data", {}),
        }

    def _get_syllabus(self, arguments: dict[str, Any]) -> dict[str, Any]:
        request = ParentAssistantChatRequest(
            message="Show syllabus",
            subject_id=self._optional_int(arguments.get("subject_id")),
            grade_id=self._optional_int(arguments.get("grade_id")),
        )
        response = self.parent_service._assistant_syllabus_response(request)
        return {
            "ok": True,
            "intent": "syllabus",
            "fallback_answer": response["answer"],
            "suggestions": response.get("suggestions", []),
            "data": response.get("data", {}),
            "requires_subject": response.get("requires_subject", False),
        }

    def _create_quiz_assignment(self, arguments: dict[str, Any]) -> dict[str, Any]:
        student_id = self._optional_int(arguments.get("student_id"))
        subject_id = self._optional_int(arguments.get("subject_id"))
        grade_id = self._optional_int(arguments.get("grade_id"))
        if student_id is None:
            return self._student_required_result()
        if subject_id is None or grade_id is None:
            return {
                "ok": False,
                "intent": "quiz_assignment",
                "fallback_answer": "Which subject and grade should I use for the quiz?",
                "suggestions": ["Show syllabus", "Assign a 5 question math quiz"],
                "data": {"student_id": student_id},
                "requires_subject": subject_id is None,
            }
        if not self.parent_service.can_view_student(self.parent_id, student_id):
            return self._student_required_result()

        difficulty = arguments.get("difficulty")
        if difficulty not in {"easy", "medium", "hard", "mixed"}:
            difficulty = "medium"
        question_count = self._optional_int(arguments.get("question_count")) or 5
        question_count = max(1, min(25, question_count))
        domain_ids = self._int_list(arguments.get("domain_ids"))
        focus = arguments.get("focus")
        if focus == "weak_topics" and not domain_ids:
            domain_ids = self.parent_service._resolve_assignment_domain_ids(
                message="weak topics",
                student_id=student_id,
                subject_id=subject_id,
                grade_id=grade_id,
                plan={"focus": "weak_topics"},
            )

        assignment = self.parent_service.create_quiz_assignment(
            parent_id=self.parent_id,
            request=QuizAssignmentCreateRequest(
                student_id=student_id,
                title="Assistant Practice Quiz",
                description="Created by the parent assistant.",
                subject_id=subject_id,
                grade_id=grade_id,
                domain_ids=domain_ids,
                difficulty=difficulty,
                question_count=question_count,
                generate_missing=True,
            ),
        )
        generated_count = int(assignment.get("generated_questions", 0))
        generated_text = (
            f" Generated {generated_count} new question{'s' if generated_count != 1 else ''}."
            if generated_count > 0
            else " Used existing unanswered questions."
        )
        return {
            "ok": True,
            "intent": "quiz_assignment",
            "fallback_answer": (
                f"Done. I assigned a {question_count}-question {difficulty} quiz."
                f"{generated_text}"
            ),
            "suggestions": ["Show weak topics", "Assign another 5 question quiz", "Show syllabus"],
            "data": {
                "assignment": self.parent_service._assignment_chat_payload(assignment),
                "generated_questions": generated_count,
            },
        }

    def _get_assignment_status(self, arguments: dict[str, Any]) -> dict[str, Any]:
        assignment_id = self._optional_int(arguments.get("assignment_id"))
        if assignment_id is None:
            return {
                "ok": False,
                "intent": "quiz_assignment",
                "fallback_answer": "Which assignment should I check?",
                "suggestions": ["Show assigned quizzes"],
                "data": {},
            }
        assignment = self.parent_service.get_quiz_assignment_for_parent(self.parent_id, assignment_id)
        return {
            "ok": True,
            "intent": "quiz_assignment",
            "fallback_answer": (
                f"{assignment['title']} is {assignment['status'].replace('_', ' ')}: "
                f"{assignment['answered_count']}/{assignment['question_count']} answered."
            ),
            "suggestions": ["Show weak topics", "Assign another quiz"],
            "data": {"assignment": self.parent_service._assignment_chat_payload(assignment)},
        }

    def _get_student(self, arguments: dict[str, Any]):
        student_id = self._optional_int(arguments.get("student_id"))
        if student_id is None or not self.parent_service.can_view_student(self.parent_id, student_id):
            return None
        return self.parent_service._get_student_by_id(student_id)

    def _student_required_result(self) -> dict[str, Any]:
        children = [child.model_dump() for child in self.parent_service.get_linked_students(self.parent_id)]
        return {
            "ok": False,
            "intent": "learning_summary",
            "fallback_answer": "Which child should I look at? Select a child, then ask again.",
            "suggestions": ["Show weak topics", "Show strong topics", "Show syllabus"],
            "data": {"children": children},
            "requires_student": True,
        }

    def _optional_int(self, value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
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
