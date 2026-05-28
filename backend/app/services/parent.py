from datetime import datetime
import json
import re
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, Integer

from app.models import (
    User,
    UserRole,
    ParentStudentLink,
    LinkStatus,
    AnsweredQuestion,
    Standard,
    Subject,
    Grade,
    Domain,
    Cluster,
    StudentDomainAbility,
    Question,
    QuizAssignment,
    QuizAssignmentQuestion,
    ParentAssistantThread,
    ParentAssistantMessage,
    ParentAssistantToolCall,
)
from app.schemas.parent import (
    ParentAssistantChatRequest,
    ParentStudentLinkResponse,
    StudentProgressSummary,
    StudentDetailForParent,
)
from app.schemas.quiz_assignment import QuizAssignmentCreateRequest
from app.services.parent_assistant_llm import ParentAssistantLLMService
from app.services.parent_assistant_tools import ParentAssistantToolRegistry
from app.services.questions import QuestionService
from app.services.student import get_skill_level


class ParentService:
    """Service for parent-student relationship management."""

    def __init__(self, db: Session):
        self.db = db

    def get_linked_students(self, parent_id: int) -> List[ParentStudentLinkResponse]:
        """Get all students linked to a parent."""
        links = self.db.query(ParentStudentLink).options(
            joinedload(ParentStudentLink.student)
        ).filter(
            ParentStudentLink.parent_id == parent_id,
            ParentStudentLink.status == LinkStatus.APPROVED
        ).all()

        result = []
        for link in links:
            if link.student:
                result.append(ParentStudentLinkResponse(
                    id=link.id,
                    parent_id=link.parent_id,
                    student_id=link.student_id,
                    student_name=link.student.full_name or link.student.username,
                    student_email=link.student.email,
                    student_username=link.student.username,
                    status=link.status.value,
                    requested_at=link.requested_at,
                    approved_at=link.approved_at
                ))

        return result

    def request_student_link(self, parent_id: int, student_email_or_username: str) -> Optional[ParentStudentLink]:
        """Create a pending link request from parent to student."""
        # Find student
        student = self.db.query(User).filter(
            User.email == student_email_or_username,
            User.role == UserRole.STUDENT,
            User.is_active == True
        ).first()

        if not student:
            student = self.db.query(User).filter(
                User.username == student_email_or_username,
                User.role == UserRole.STUDENT,
                User.is_active == True
            ).first()

        if not student:
            raise ValueError(f"No active student found with email or username: {student_email_or_username}")

        # Check if link already exists
        existing = self.db.query(ParentStudentLink).filter(
            ParentStudentLink.parent_id == parent_id,
            ParentStudentLink.student_id == student.id
        ).first()

        if existing:
            if existing.status == LinkStatus.APPROVED:
                raise ValueError("You are already linked to this student")
            elif existing.status == LinkStatus.PENDING:
                raise ValueError("A link request is already pending for this student")
            else:
                # Rejected - allow re-request
                existing.status = LinkStatus.PENDING
                existing.requested_at = datetime.utcnow()
                self.db.commit()
                return existing

        # Create new pending link
        link = ParentStudentLink(
            parent_id=parent_id,
            student_id=student.id,
            status=LinkStatus.PENDING,
            requested_at=datetime.utcnow()
        )

        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)

        return link

    def get_pending_links(self) -> List[dict]:
        """Get all pending link requests (for admin review)."""
        links = self.db.query(ParentStudentLink).options(
            joinedload(ParentStudentLink.parent),
            joinedload(ParentStudentLink.student)
        ).filter(
            ParentStudentLink.status == LinkStatus.PENDING
        ).order_by(
            ParentStudentLink.requested_at
        ).all()

        result = []
        for link in links:
            if link.parent and link.student:
                result.append({
                    "id": link.id,
                    "parent_name": link.parent.full_name or link.parent.username,
                    "parent_email": link.parent.email,
                    "parent_username": link.parent.username,
                    "student_name": link.student.full_name or link.student.username,
                    "student_email": link.student.email,
                    "student_username": link.student.username,
                    "requested_at": link.requested_at
                })

        return result

    def approve_link(self, link_id: int, admin_id: int) -> bool:
        """Approve a parent-student link request."""
        link = self.db.query(ParentStudentLink).filter(
            ParentStudentLink.id == link_id,
            ParentStudentLink.status == LinkStatus.PENDING
        ).first()

        if not link:
            return False

        link.status = LinkStatus.APPROVED
        link.approved_at = datetime.utcnow()
        link.approved_by = admin_id

        self.db.commit()
        return True

    def reject_link(self, link_id: int, admin_id: int, reason: Optional[str] = None) -> bool:
        """Reject a parent-student link request."""
        link = self.db.query(ParentStudentLink).filter(
            ParentStudentLink.id == link_id,
            ParentStudentLink.status == LinkStatus.PENDING
        ).first()

        if not link:
            return False

        link.status = LinkStatus.REJECTED
        link.approved_at = datetime.utcnow()
        link.approved_by = admin_id
        link.rejected_reason = reason

        self.db.commit()
        return True

    def get_student_progress_summary(self, student_id: int) -> StudentProgressSummary:
        """Get progress summary for a student using answered_questions."""
        student = self.db.query(User).filter(
            User.id == student_id,
            User.role == UserRole.STUDENT
        ).first()

        if not student:
            raise ValueError("Student not found")

        # Get total answers and correct count
        total_result = self.db.query(
            func.count(AnsweredQuestion.id).label("total"),
            func.sum(func.cast(AnsweredQuestion.is_correct, Integer)).label("correct")
        ).filter(AnsweredQuestion.student_id == student_id).first()

        total_answered = total_result.total or 0
        correct_count = total_result.correct or 0 if total_result.total else 0
        accuracy = correct_count / total_answered if total_answered > 0 else None

        # Get last answer
        last_answer = self.db.query(AnsweredQuestion).filter(
            AnsweredQuestion.student_id == student_id
        ).order_by(
            AnsweredQuestion.answered_at.desc()
        ).first()

        # Get recent answers with standard info
        recent_answers = self.db.query(AnsweredQuestion).filter(
            AnsweredQuestion.student_id == student_id
        ).options(
            joinedload(AnsweredQuestion.standard)
        ).order_by(
            AnsweredQuestion.answered_at.desc()
        ).limit(10).all()

        recent_list = []
        for answer in recent_answers:
            recent_list.append({
                "answer_id": answer.id,
                "question_id": answer.question_id,
                "standard_code": answer.standard.code if answer.standard else None,
                "is_correct": answer.is_correct,
                "answered_at": answer.answered_at.isoformat() if answer.answered_at else None
            })

        # Get unique standards attempted
        standards_attempted = self.db.query(func.count(func.distinct(AnsweredQuestion.standard_id))).filter(
            AnsweredQuestion.student_id == student_id
        ).scalar()

        return StudentProgressSummary(
            student_id=student_id,
            student_name=student.full_name or student.username,
            student_username=student.username,
            total_attempts=total_answered,
            average_score=round(accuracy * 100, 2) if accuracy else None,
            last_attempt_at=last_answer.answered_at if last_answer else None,
            recent_attempts=recent_list
        )

    def get_student_detail_for_parent(self, parent_id: int, student_id: int) -> StudentDetailForParent:
        """Get detailed student info for a linked parent."""
        # Verify link exists
        link = self.db.query(ParentStudentLink).filter(
            ParentStudentLink.parent_id == parent_id,
            ParentStudentLink.student_id == student_id,
            ParentStudentLink.status == LinkStatus.APPROVED
        ).first()

        if not link:
            raise ValueError("You are not linked to this student or the link is pending approval")

        summary = self.get_student_progress_summary(student_id)

        # Get more detailed recent answers with standard info
        recent_answers = self.db.query(AnsweredQuestion).filter(
            AnsweredQuestion.student_id == student_id
        ).options(
            joinedload(AnsweredQuestion.standard)
        ).order_by(
            AnsweredQuestion.answered_at.desc()
        ).limit(20).all()

        detailed_attempts = []
        for answer in recent_answers:
            detailed_attempts.append({
                "answer_id": answer.id,
                "question_id": answer.question_id,
                "standard_code": answer.standard.code if answer.standard else None,
                "standard_description": answer.standard.description if answer.standard else None,
                "is_correct": answer.is_correct,
                "answered_at": answer.answered_at.isoformat() if answer.answered_at else None
            })

        student = self.db.query(User).filter(User.id == student_id).first()

        return StudentDetailForParent(
            student_id=student_id,
            student_name=student.full_name or student.username,
            student_username=student.username,
            email=student.email,
            total_attempts=summary.total_attempts,
            average_score=summary.average_score,
            standards_attempted=len(set(a.standard_id for a in recent_answers)),
            recent_attempts=detailed_attempts
        )

    def can_view_student(self, parent_id: int, student_id: int) -> bool:
        """Check if parent can view student's progress."""
        link = self.db.query(ParentStudentLink).filter(
            ParentStudentLink.parent_id == parent_id,
            ParentStudentLink.student_id == student_id,
            ParentStudentLink.status == LinkStatus.APPROVED
        ).first()

        return link is not None

    def create_quiz_assignment(
        self,
        parent_id: int,
        request: QuizAssignmentCreateRequest,
    ) -> dict:
        """Create a parent-assigned quiz from existing active questions."""
        if not self.can_view_student(parent_id, request.student_id):
            raise ValueError("You are not linked to this student or the link is pending approval")

        questions = self._select_assignment_questions(request)
        generated_count = 0
        if len(questions) < request.question_count and request.generate_missing:
            if request.subject_id is None and not request.domain_ids and not request.standard_ids:
                raise ValueError("Select a subject, domain, or standard before using AI-fill for missing questions.")
            missing_count = request.question_count - len(questions)
            try:
                generated_questions = self._generate_assignment_questions(request, missing_count)
                generated_count = len(generated_questions)
                questions.extend(generated_questions)
            except Exception:
                self.db.rollback()
                raise

        if len(questions) < request.question_count:
            raise ValueError(
                f"Only {len(questions)} matching unanswered questions are available. "
                "Try a lower question count, mixed difficulty, broader filters, or AI-fill missing questions."
            )

        assignment = QuizAssignment(
            parent_id=parent_id,
            student_id=request.student_id,
            subject_id=request.subject_id,
            grade_id=request.grade_id,
            title=request.title,
            description=request.description,
            difficulty=request.difficulty,
            status="assigned",
            question_count=len(questions),
            due_at=request.due_at,
        )
        self.db.add(assignment)
        self.db.flush()

        for index, question in enumerate(questions):
            self.db.add(QuizAssignmentQuestion(
                assignment_id=assignment.id,
                question_id=question.id,
                order_index=index,
            ))

        self.db.commit()
        self.db.refresh(assignment)
        result = self.get_quiz_assignment_for_parent(parent_id, assignment.id)
        result["generated_questions"] = generated_count
        return result

    def get_quiz_assignments_for_parent(self, parent_id: int) -> list[dict]:
        assignments = (
            self.db.query(QuizAssignment)
            .filter(QuizAssignment.parent_id == parent_id)
            .order_by(QuizAssignment.created_at.desc())
            .all()
        )
        return [self._serialize_assignment(assignment) for assignment in assignments]

    def get_quiz_assignment_for_parent(self, parent_id: int, assignment_id: int) -> dict:
        assignment = self.db.query(QuizAssignment).filter(
            QuizAssignment.id == assignment_id,
            QuizAssignment.parent_id == parent_id,
        ).first()
        if not assignment:
            raise ValueError("Quiz assignment not found")
        return self._serialize_assignment(assignment, include_questions=True)

    def _select_assignment_questions(self, request: QuizAssignmentCreateRequest) -> list[Question]:
        answered_subquery = (
            self.db.query(AnsweredQuestion.question_id)
            .filter(AnsweredQuestion.student_id == request.student_id)
            .subquery()
        )

        query = (
            self.db.query(Question)
            .join(Standard, Question.standard_id == Standard.id)
            .join(Domain, Standard.domain_id == Domain.id)
            .filter(
                Question.is_active == True,
                Question.question_type == "multiple_choice",
                ~Question.id.in_(answered_subquery),
            )
        )

        if request.subject_id is not None:
            query = query.filter(Domain.subject_id == request.subject_id)
        if request.grade_id is not None:
            query = query.filter(Standard.grade_id == request.grade_id)
        if request.domain_ids:
            query = query.filter(Standard.domain_id.in_(request.domain_ids))
        if request.standard_ids:
            query = query.filter(Standard.id.in_(request.standard_ids))

        if request.difficulty == "easy":
            query = query.filter(Question.difficulty <= 0.4)
        elif request.difficulty == "medium":
            query = query.filter(Question.difficulty >= 0.35, Question.difficulty <= 0.7)
        elif request.difficulty == "hard":
            query = query.filter(Question.difficulty >= 0.65)

        return query.order_by(func.random()).limit(request.question_count).all()

    def _select_assignment_standards(self, request: QuizAssignmentCreateRequest) -> list[Standard]:
        query = self.db.query(Standard).join(Domain, Standard.domain_id == Domain.id)

        if request.subject_id is not None:
            query = query.filter(Domain.subject_id == request.subject_id)
        if request.grade_id is not None:
            query = query.filter(Standard.grade_id == request.grade_id)
        if request.domain_ids:
            query = query.filter(Standard.domain_id.in_(request.domain_ids))
        if request.standard_ids:
            query = query.filter(Standard.id.in_(request.standard_ids))

        return query.order_by(func.random()).limit(25).all()

    def _generate_assignment_questions(
        self,
        request: QuizAssignmentCreateRequest,
        missing_count: int,
    ) -> list[Question]:
        standards = self._select_assignment_standards(request)
        if not standards:
            raise ValueError(
                "I could not find standards for those filters, so I could not generate missing questions."
            )

        question_service = QuestionService(self.db)
        generated_questions = []
        last_error = None

        for index in range(missing_count):
            standard = standards[index % len(standards)]
            target_difficulty = self._assignment_difficulty_target(request.difficulty, standard)
            try:
                question_data = question_service.generate_question(
                    standard_id=standard.id,
                    difficulty=target_difficulty,
                    question_type="multiple_choice",
                )
                generated_questions.append(
                    self._persist_generated_assignment_question(
                        standard_id=standard.id,
                        question_data=question_data,
                    )
                )
            except (ConnectionError, TimeoutError, RuntimeError):
                raise
            except Exception as exc:
                last_error = exc

        if len(generated_questions) < missing_count:
            raise RuntimeError(
                f"Generated {len(generated_questions)} of {missing_count} needed question"
                f"{'s' if missing_count != 1 else ''}. Last error: {last_error}"
            )

        return generated_questions

    def _assignment_difficulty_target(self, difficulty: str, standard: Standard) -> float:
        if difficulty == "easy":
            return 0.30
        if difficulty == "medium":
            return 0.55
        if difficulty == "hard":
            return 0.80
        return float(standard.difficulty_base) if standard.difficulty_base is not None else 0.50

    def _persist_generated_assignment_question(
        self,
        standard_id: int,
        question_data: dict,
    ) -> Question:
        question = Question(
            standard_id=standard_id,
            question_text=question_data["question"],
            question_type=question_data.get("question_type", "multiple_choice"),
            options=question_data.get("options"),
            correct_answer=question_data["answer"],
            explanation=question_data.get("explanation"),
            difficulty=question_data.get("difficulty"),
            requires_diagram=question_data.get("requires_diagram", False),
            applet_type=question_data.get("applet_type"),
            geogebra_commands=question_data.get("geogebra_commands"),
            generated_by="parent_assistant",
            is_active=True,
        )
        self.db.add(question)
        self.db.flush()
        return question

    def _serialize_assignment(self, assignment: QuizAssignment, include_questions: bool = False) -> dict:
        question_ids = [item.question_id for item in assignment.assignment_questions]
        answer_rows = []
        if question_ids:
            answer_rows = self.db.query(AnsweredQuestion).filter(
                AnsweredQuestion.student_id == assignment.student_id,
                AnsweredQuestion.question_id.in_(question_ids),
            ).all()

        answered_count = len(answer_rows)
        correct_count = sum(1 for answer in answer_rows if answer.is_correct)
        student_name = None
        if assignment.student:
            student_name = assignment.student.full_name or assignment.student.username

        data = {
            "id": assignment.id,
            "parent_id": assignment.parent_id,
            "student_id": assignment.student_id,
            "student_name": student_name,
            "title": assignment.title,
            "description": assignment.description,
            "difficulty": assignment.difficulty,
            "status": assignment.status,
            "question_count": assignment.question_count,
            "answered_count": answered_count,
            "correct_count": correct_count,
            "subject_id": assignment.subject_id,
            "subject_name": assignment.subject.name if assignment.subject else None,
            "grade_id": assignment.grade_id,
            "grade_name": assignment.grade.display_name if assignment.grade else None,
            "created_at": assignment.created_at,
            "started_at": assignment.started_at,
            "completed_at": assignment.completed_at,
            "due_at": assignment.due_at,
        }

        if include_questions:
            data["questions"] = [
                item.question
                for item in assignment.assignment_questions
                if item.question is not None
            ]
            data["answers"] = [
                {
                    "question_id": answer.question_id,
                    "selected_answer": answer.selected_answer,
                    "is_correct": answer.is_correct,
                    "answered_at": answer.answered_at,
                }
                for answer in answer_rows
            ]

        return data

    def handle_assistant_chat(self, parent_id: int, request: ParentAssistantChatRequest) -> dict:
        """Handle parent assistant requests with natural conversation plus controlled tools."""
        message = request.message.strip()
        thread = self._get_or_create_assistant_thread(parent_id, request)
        parent_message = self._add_assistant_message(
            thread_id=thread.id,
            role="parent",
            content=message,
        )

        memory = self._assistant_memory(thread.id)
        memory = self._apply_selected_context_to_memory(parent_id, request, memory)
        context = self._assistant_planner_context(parent_id, request, thread.id)
        context["memory"] = memory
        intent = self._detect_assistant_intent(message, memory)

        if intent in {"greeting", "thanks", "help", "unknown"}:
            answer = self._assistant_conversation_response(parent_id, intent)
            self._add_assistant_message(thread.id, "assistant", answer, intent="conversation")
            self._save_assistant_memory(thread.id, memory)
            return self._assistant_response_payload(
                thread_id=thread.id,
                intent="conversation",
                answer=answer,
                suggestions=self._assistant_default_suggestions(parent_id),
                data={"card_type": "help"},
            )

        if intent == "quiz_cancel":
            memory.pop("pending_quiz", None)
            answer = "No problem. I cancelled that quiz plan."
            self._add_assistant_message(thread.id, "assistant", answer, intent="quiz_assignment")
            self._save_assistant_memory(thread.id, memory)
            return self._assistant_response_payload(
                thread_id=thread.id,
                intent="quiz_assignment",
                answer=answer,
                suggestions=["Show weak topics", "Show syllabus", "Assign a different quiz"],
                data={"card_type": "quiz_cancelled"},
            )

        if intent == "quiz_confirm" and memory.get("pending_quiz"):
            result = self._execute_pending_quiz(parent_id, thread.id, parent_message.id, memory)
            self._add_assistant_message(thread.id, "assistant", result["answer"], intent="quiz_assignment")
            self._save_assistant_memory(thread.id, result["memory"])
            return self._assistant_response_payload(
                thread_id=thread.id,
                intent="quiz_assignment",
                answer=result["answer"],
                tool_name="create_quiz_assignment",
                suggestions=result["suggestions"],
                data=result["data"],
            )

        if intent == "quiz_assignment":
            result = self._prepare_pending_quiz(parent_id, request, thread.id, memory)
            self._add_assistant_message(thread.id, "assistant", result["answer"], intent="quiz_assignment")
            self._save_assistant_memory(thread.id, result["memory"])
            return self._assistant_response_payload(
                thread_id=thread.id,
                intent="quiz_assignment",
                answer=result["answer"],
                requires_student=result.get("requires_student", False),
                requires_subject=result.get("requires_subject", False),
                suggestions=result["suggestions"],
                data=result["data"],
            )

        tool_registry = ParentAssistantToolRegistry(self, parent_id)
        tool_call = self._assistant_tool_call_for_intent(intent, request, context)

        tool_arguments = self._merge_selected_context_into_tool_args(request, tool_call.get("arguments", {}))
        tool_call["arguments"] = tool_arguments

        audit = self._start_tool_call(
            thread_id=thread.id,
            message_id=parent_message.id,
            tool_name=tool_call["tool_name"],
            arguments=tool_arguments,
        )
        try:
            tool_result = tool_registry.execute(tool_call["tool_name"], tool_arguments)
            self._finish_tool_call(audit, "completed", result=tool_result)
        except Exception as exc:
            self.db.rollback()
            audit = self.db.query(ParentAssistantToolCall).filter(ParentAssistantToolCall.id == audit.id).first()
            tool_result = {
                "ok": False,
                "intent": "learning_summary",
                "fallback_answer": f"I could not complete that action: {exc}",
                "suggestions": ["Show weak topics", "Show syllabus"],
                "data": {},
            }
            if audit:
                self._finish_tool_call(audit, "failed", result=tool_result, error=str(exc))

        answer = ParentAssistantLLMService().write_response(
            message=message,
            context=context,
            tool_call=tool_call,
            tool_result=tool_result,
        ) or tool_result["fallback_answer"]
        intent = tool_result.get("intent", intent)
        memory = self._update_assistant_memory_from_tool_result(memory, intent, tool_result)

        self._add_assistant_message(
            thread_id=thread.id,
            role="assistant",
            content=answer,
            intent=intent,
        )
        self._save_assistant_memory(thread.id, memory)

        data = tool_result.get("data", {})
        data = dict(data)
        data.setdefault("card_type", self._assistant_card_type(intent))
        data["tool_call"] = {
            "id": audit.id if audit else None,
            "tool_name": tool_call["tool_name"],
            "status": tool_result.get("status", "completed" if tool_result.get("ok") else "failed"),
        }
        return self._assistant_response_payload(
            thread_id=thread.id,
            intent=intent,
            answer=answer,
            tool_name=tool_call["tool_name"],
            requires_student=tool_result.get("requires_student", False),
            requires_subject=tool_result.get("requires_subject", False),
            suggestions=tool_result.get("suggestions", []),
            data=data,
        )

    def _plan_assistant_request(self, parent_id: int, request: ParentAssistantChatRequest) -> dict:
        context = self._assistant_planner_context(parent_id, request)
        plan = ParentAssistantLLMService().plan(request.message, context)
        if not plan:
            return {}

        planned_student_id = plan.get("student_id")
        if planned_student_id is not None and not self.can_view_student(parent_id, planned_student_id):
            plan["student_id"] = None

        return plan

    def _assistant_response_payload(
        self,
        thread_id: int,
        intent: str,
        answer: str,
        tool_name: Optional[str] = None,
        requires_student: bool = False,
        requires_subject: bool = False,
        suggestions: Optional[list[str]] = None,
        data: Optional[dict] = None,
    ) -> dict:
        return {
            "intent": intent,
            "answer": answer,
            "thread_id": thread_id,
            "tool_name": tool_name,
            "requires_student": requires_student,
            "requires_subject": requires_subject,
            "suggestions": suggestions or [],
            "data": data or {},
        }

    def _assistant_memory(self, thread_id: int) -> dict:
        message = (
            self.db.query(ParentAssistantMessage)
            .filter(
                ParentAssistantMessage.thread_id == thread_id,
                ParentAssistantMessage.role == "system",
                ParentAssistantMessage.intent == "memory",
            )
            .order_by(ParentAssistantMessage.created_at.desc(), ParentAssistantMessage.id.desc())
            .first()
        )
        if not message:
            return {}
        try:
            parsed = json.loads(message.content)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError):
            return {}

    def _save_assistant_memory(self, thread_id: int, memory: dict) -> None:
        safe_memory = self._json_safe(memory)
        self._add_assistant_message(
            thread_id=thread_id,
            role="system",
            content=json.dumps(safe_memory),
            intent="memory",
        )

    def _apply_selected_context_to_memory(
        self,
        parent_id: int,
        request: ParentAssistantChatRequest,
        memory: dict,
    ) -> dict:
        next_memory = dict(memory or {})
        if request.student_id is not None and self.can_view_student(parent_id, request.student_id):
            student = self._get_student_by_id(request.student_id)
            if student:
                next_memory["student_id"] = student.id
                next_memory["student_name"] = student.full_name or student.username
        if request.subject_id is not None:
            subject = self.db.query(Subject).filter(Subject.id == request.subject_id).first()
            if subject:
                next_memory["subject_id"] = subject.id
                next_memory["subject_name"] = subject.name
        if request.grade_id is not None:
            grade = self.db.query(Grade).filter(Grade.id == request.grade_id).first()
            if grade:
                next_memory["grade_id"] = grade.id
                next_memory["grade_name"] = grade.display_name
                next_memory["grade_level"] = grade.level
        return next_memory

    def _assistant_default_suggestions(self, parent_id: int) -> list[str]:
        children = self.get_linked_students(parent_id)
        if children:
            return ["Show weak topics", "Show strong topics", "Show syllabus", "Assign a practice quiz"]
        return ["Request a student link", "What can you do?", "Show syllabus"]

    def _assistant_conversation_response(self, parent_id: int, intent: str) -> str:
        if intent == "greeting":
            return self._assistant_greeting_response(parent_id)
        if intent == "thanks":
            return "You are welcome. I can also help explain progress, find weak topics, show syllabus, or prepare a short practice quiz."
        if intent == "help":
            return (
                "I can help you understand your child's learning progress, find weak and strong topics, "
                "show syllabus coverage, and prepare short practice quizzes for the student's dashboard."
            )
        return (
            "I can help with progress, weak topics, strong topics, syllabus, and practice quizzes. "
            "Try asking, \"What are my child's weak topics?\" or \"Show Grade 7 Math syllabus.\""
        )

    def _assistant_tool_call_for_intent(
        self,
        intent: str,
        request: ParentAssistantChatRequest,
        context: dict,
    ) -> dict:
        arguments = self._assistant_base_tool_arguments(request, context)
        if intent == "syllabus":
            subject = self._resolve_assistant_subject(
                request.message,
                request.subject_id or arguments.get("subject_id"),
                context.get("memory") or {},
            )
            if subject:
                arguments["subject_id"] = subject.id
                grade = self._resolve_assistant_grade(
                    subject.id,
                    request.message,
                    request.grade_id or arguments.get("grade_id"),
                    context.get("memory") or {},
                )
                if grade:
                    arguments["grade_id"] = grade.id
            return {"tool_name": "get_syllabus", "arguments": arguments, "confidence": 1.0}
        if intent == "strong_topics":
            return {"tool_name": "get_strong_topics", "arguments": arguments, "confidence": 1.0}
        if intent == "weak_topics":
            return {"tool_name": "get_weak_topics", "arguments": arguments, "confidence": 1.0}
        if intent == "assignment_status":
            last_assignment = (context.get("memory") or {}).get("last_assignment") or {}
            if last_assignment.get("id"):
                arguments["assignment_id"] = last_assignment["id"]
            return {"tool_name": "get_assignment_status", "arguments": arguments, "confidence": 1.0}
        return {"tool_name": "get_learning_summary", "arguments": arguments, "confidence": 1.0}

    def _assistant_base_tool_arguments(
        self,
        request: ParentAssistantChatRequest,
        context: dict,
    ) -> dict:
        memory = context.get("memory") or {}
        arguments = {
            "student_id": request.student_id or memory.get("student_id"),
            "subject_id": request.subject_id or memory.get("subject_id"),
            "grade_id": request.grade_id or memory.get("grade_id"),
        }
        if arguments["student_id"] is None and len(context.get("children", [])) == 1:
            arguments["student_id"] = context["children"][0]["student_id"]
        return arguments

    def _assistant_card_type(self, intent: str) -> str:
        return {
            "weak_topics": "topics",
            "strong_topics": "topics",
            "learning_summary": "learning_summary",
            "syllabus": "syllabus",
            "quiz_assignment": "quiz_assignment",
            "assignment_status": "assignment_status",
        }.get(intent, "message")

    def _update_assistant_memory_from_tool_result(
        self,
        memory: dict,
        intent: str,
        tool_result: dict,
    ) -> dict:
        next_memory = dict(memory or {})
        data = tool_result.get("data") or {}

        if data.get("student_id"):
            next_memory["student_id"] = data["student_id"]
        if data.get("student_name"):
            next_memory["student_name"] = data["student_name"]
        if data.get("subject_id"):
            next_memory["subject_id"] = data["subject_id"]
        if data.get("subject_name"):
            next_memory["subject_name"] = data["subject_name"]
        if data.get("grade_id"):
            next_memory["grade_id"] = data["grade_id"]
        if data.get("grade_name"):
            next_memory["grade_name"] = data["grade_name"]

        if intent == "weak_topics":
            topics = data.get("weak_topics") or []
            next_memory["last_topic_focus"] = "weak_topics"
            next_memory["last_domains"] = self._topic_memory_payload(topics)
        elif intent == "strong_topics":
            topics = data.get("strong_topics") or []
            next_memory["last_topic_focus"] = "strong_topics"
            next_memory["last_domains"] = self._topic_memory_payload(topics)
        elif intent == "learning_summary":
            topics = data.get("weak_topics") or data.get("strong_topics") or []
            if topics:
                next_memory["last_topic_focus"] = "weak_topics"
                next_memory["last_domains"] = self._topic_memory_payload(topics[:2])
        elif intent == "syllabus":
            next_memory["last_syllabus_domains"] = [
                {
                    "domain_id": domain.get("domain_id"),
                    "domain_name": domain.get("domain_name"),
                    "domain_code": domain.get("domain_code"),
                }
                for domain in data.get("domains", [])
            ]

        assignment = data.get("assignment")
        if isinstance(assignment, dict):
            next_memory["last_assignment"] = assignment
            next_memory.pop("pending_quiz", None)

        return next_memory

    def _topic_memory_payload(self, topics: list[dict]) -> list[dict]:
        return [
            {
                "domain_id": topic.get("domain_id"),
                "domain_name": topic.get("domain_name"),
                "domain_code": topic.get("domain_code"),
            }
            for topic in topics
            if topic.get("domain_id")
        ]

    def _prepare_pending_quiz(
        self,
        parent_id: int,
        request: ParentAssistantChatRequest,
        thread_id: int,
        memory: dict,
    ) -> dict:
        message = request.message
        previous_quiz = memory.get("pending_quiz") if isinstance(memory.get("pending_quiz"), dict) else None
        student = self._resolve_quiz_student(parent_id, request, memory)
        if not student:
            children = [child.model_dump() for child in self.get_linked_students(parent_id)]
            answer = "Which child should I create the quiz for? Select a child, then ask again."
            return {
                "answer": answer,
                "memory": memory,
                "requires_student": True,
                "suggestions": [f"Assign a 5 question quiz to {child['student_name']}" for child in children[:3]],
                "data": {"card_type": "clarification", "children": children},
            }

        subject = self._resolve_quiz_subject(request, memory, previous_quiz)
        if not subject:
            subjects = self.db.query(Subject).order_by(Subject.name).all()
            answer = "Which subject should I use for the quiz? Select a subject, or include it in your message."
            return {
                "answer": answer,
                "memory": {**memory, "student_id": student.id, "student_name": student.full_name or student.username},
                "requires_subject": True,
                "suggestions": [f"Assign a 5 question {subject.name} quiz" for subject in subjects[:3]],
                "data": {
                    "card_type": "clarification",
                    "student_id": student.id,
                    "subjects": [{"id": item.id, "name": item.name, "code": item.code} for item in subjects],
                },
            }

        grade = self._resolve_quiz_grade(subject.id, request, memory, previous_quiz)
        if not grade:
            grades = self.db.query(Grade).filter(Grade.subject_id == subject.id).order_by(Grade.level).all()
            answer = f"Which grade should I use for the {subject.name} quiz?"
            return {
                "answer": answer,
                "memory": {
                    **memory,
                    "student_id": student.id,
                    "student_name": student.full_name or student.username,
                    "subject_id": subject.id,
                    "subject_name": subject.name,
                },
                "requires_subject": False,
                "suggestions": [
                    f"Assign a 5 question {subject.name} quiz for {item.display_name}"
                    for item in grades[:3]
                ],
                "data": {
                    "card_type": "clarification",
                    "student_id": student.id,
                    "subject_id": subject.id,
                    "grades": [{"id": item.id, "name": item.display_name, "level": item.level} for item in grades],
                },
            }

        difficulty = self._resolve_quiz_difficulty(message, previous_quiz)
        question_count = self._resolve_quiz_question_count(message, previous_quiz)
        domain_ids = self._resolve_quiz_domain_ids(message, student.id, subject.id, grade.id, memory, previous_quiz)
        domains = self.db.query(Domain).filter(Domain.id.in_(domain_ids)).order_by(Domain.display_order, Domain.name).all() if domain_ids else []
        student_name = student.full_name or student.username
        focus_label = self._quiz_focus_label(message, subject, domains, memory, previous_quiz)
        domain_payload = [
            {"domain_id": domain.id, "domain_name": domain.name, "domain_code": domain.code}
            for domain in domains
        ]
        title = f"{focus_label} Practice"[:150]
        pending_quiz = {
            "student_id": student.id,
            "student_name": student_name,
            "subject_id": subject.id,
            "subject_name": subject.name,
            "grade_id": grade.id,
            "grade_name": grade.display_name,
            "difficulty": difficulty,
            "question_count": question_count,
            "domain_ids": domain_ids,
            "domains": domain_payload,
            "title": title,
            "description": f"Created by the parent assistant from: {message[:220]}",
            "generate_missing": True,
            "created_from_thread_id": thread_id,
        }

        next_memory = {
            **memory,
            "student_id": student.id,
            "student_name": student_name,
            "subject_id": subject.id,
            "subject_name": subject.name,
            "grade_id": grade.id,
            "grade_name": grade.display_name,
            "pending_quiz": pending_quiz,
        }
        domain_text = f" focused on {', '.join(domain.name for domain in domains)}" if domains else ""
        answer = (
            f"I can assign {student_name} a {question_count}-question {difficulty} "
            f"{subject.name} quiz for {grade.display_name}{domain_text}. Should I assign it?"
        )
        return {
            "answer": answer,
            "memory": next_memory,
            "suggestions": ["Yes, assign it", "Make it easier", "Make it harder", "Change to 10 questions", "Cancel"],
            "data": {
                "card_type": "quiz_preview",
                "pending_quiz": pending_quiz,
            },
        }

    def _execute_pending_quiz(
        self,
        parent_id: int,
        thread_id: int,
        message_id: int,
        memory: dict,
    ) -> dict:
        pending_quiz = memory.get("pending_quiz") or {}
        audit = self._start_tool_call(
            thread_id=thread_id,
            message_id=message_id,
            tool_name="create_quiz_assignment",
            arguments=pending_quiz,
        )
        try:
            assignment = self.create_quiz_assignment(
                parent_id=parent_id,
                request=QuizAssignmentCreateRequest(
                    student_id=pending_quiz["student_id"],
                    title=pending_quiz.get("title") or "Assistant Practice Quiz",
                    description=pending_quiz.get("description"),
                    subject_id=pending_quiz.get("subject_id"),
                    grade_id=pending_quiz.get("grade_id"),
                    domain_ids=pending_quiz.get("domain_ids") or [],
                    difficulty=pending_quiz.get("difficulty") or "medium",
                    question_count=pending_quiz.get("question_count") or 5,
                    generate_missing=pending_quiz.get("generate_missing", True),
                ),
            )
            generated_count = int(assignment.get("generated_questions", 0))
            self._finish_tool_call(audit, "completed", result={"assignment": assignment})
            next_memory = dict(memory)
            next_memory.pop("pending_quiz", None)
            next_memory["last_assignment"] = self._assignment_chat_payload(assignment)
            answer = (
                f"Done. I assigned {assignment.get('student_name') or pending_quiz.get('student_name')} "
                f"a {assignment['question_count']}-question {assignment['difficulty']} quiz."
            )
            if generated_count > 0:
                answer += f" I generated {generated_count} new question{'s' if generated_count != 1 else ''} to fill it."
            else:
                answer += " I used existing unanswered questions."
            return {
                "answer": answer,
                "memory": next_memory,
                "suggestions": ["Show weak topics", "Check assignment status", "Assign another quiz"],
                "data": {
                    "card_type": "assignment_confirmation",
                    "assignment": self._assignment_chat_payload(assignment),
                    "generated_questions": generated_count,
                    "tool_call": {"id": audit.id, "tool_name": "create_quiz_assignment", "status": "completed"},
                },
            }
        except Exception as exc:
            self.db.rollback()
            audit = self.db.query(ParentAssistantToolCall).filter(ParentAssistantToolCall.id == audit.id).first()
            if audit:
                self._finish_tool_call(audit, "failed", result={"error": str(exc)}, error=str(exc))
            next_memory = dict(memory)
            answer = (
                f"I could not assign that quiz yet: {exc}\n\n"
                "Try fewer questions, mixed difficulty, broader filters, or use the Assign a Quiz form."
            )
            return {
                "answer": answer,
                "memory": next_memory,
                "suggestions": ["Make it easier", "Change to 3 questions", "Show weak topics"],
                "data": {
                    "card_type": "quiz_error",
                    "pending_quiz": pending_quiz,
                    "error": str(exc),
                    "tool_call": {"id": audit.id if audit else None, "tool_name": "create_quiz_assignment", "status": "failed"},
                },
            }

    def _resolve_quiz_student(
        self,
        parent_id: int,
        request: ParentAssistantChatRequest,
        memory: dict,
    ) -> Optional[User]:
        student_id = request.student_id or memory.get("student_id")
        student = self._resolve_assistant_student(parent_id, student_id)
        if student:
            return student
        return self._resolve_assistant_student(parent_id, None)

    def _resolve_quiz_subject(
        self,
        request: ParentAssistantChatRequest,
        memory: dict,
        previous_quiz: Optional[dict],
    ) -> Optional[Subject]:
        plan = {}
        if previous_quiz and self._message_is_quiz_adjustment(request.message):
            plan["subject_id"] = previous_quiz.get("subject_id")
        elif memory.get("subject_id"):
            plan["subject_id"] = memory["subject_id"]
        subject = self._resolve_assistant_subject(request.message, request.subject_id, plan)
        if subject:
            return subject
        subjects = self.db.query(Subject).order_by(Subject.name).all()
        return subjects[0] if len(subjects) == 1 else None

    def _resolve_quiz_grade(
        self,
        subject_id: int,
        request: ParentAssistantChatRequest,
        memory: dict,
        previous_quiz: Optional[dict],
    ) -> Optional[Grade]:
        plan = {}
        if previous_quiz and self._message_is_quiz_adjustment(request.message):
            plan["grade_id"] = previous_quiz.get("grade_id")
        elif memory.get("grade_id"):
            plan["grade_id"] = memory["grade_id"]
        grade = self._resolve_assistant_grade(subject_id, request.message, request.grade_id, plan)
        if grade:
            return grade
        grades = self.db.query(Grade).filter(Grade.subject_id == subject_id).order_by(Grade.level).all()
        return grades[0] if len(grades) == 1 else None

    def _resolve_quiz_difficulty(self, message: str, previous_quiz: Optional[dict]) -> str:
        if previous_quiz and self._message_is_quiz_adjustment(message):
            text = message.lower()
            if "easier" in text:
                return "easy"
            if "harder" in text:
                return "hard"
            if previous_quiz.get("difficulty") in {"easy", "medium", "hard", "mixed"}:
                return previous_quiz["difficulty"]
        return self._parse_assignment_difficulty(message)

    def _resolve_quiz_question_count(self, message: str, previous_quiz: Optional[dict]) -> int:
        parsed_count = self._parse_assignment_question_count(message)
        if previous_quiz and self._message_is_quiz_adjustment(message):
            count_match = re.search(r"\b(\d{1,2})\b", message.lower())
            if not count_match and isinstance(previous_quiz.get("question_count"), int):
                return previous_quiz["question_count"]
        return parsed_count

    def _resolve_quiz_domain_ids(
        self,
        message: str,
        student_id: int,
        subject_id: int,
        grade_id: int,
        memory: dict,
        previous_quiz: Optional[dict],
    ) -> list[int]:
        if previous_quiz and self._message_is_quiz_adjustment(message):
            return previous_quiz.get("domain_ids") or []

        text = message.lower()
        if any(term in text for term in ["that", "those", "same", "weak", "mistake"]):
            remembered_domains = memory.get("last_domains") or []
            remembered_ids = [
                item.get("domain_id")
                for item in remembered_domains
                if isinstance(item, dict) and item.get("domain_id")
            ]
            if remembered_ids:
                valid_domain_ids = {
                    row[0]
                    for row in self.db.query(Domain.id)
                    .join(Standard, Standard.domain_id == Domain.id)
                    .filter(Domain.subject_id == subject_id, Standard.grade_id == grade_id)
                    .distinct()
                    .all()
                }
                return [domain_id for domain_id in remembered_ids if domain_id in valid_domain_ids]

        return self._resolve_assignment_domain_ids(
            message=message,
            student_id=student_id,
            subject_id=subject_id,
            grade_id=grade_id,
            plan={"focus": "weak_topics"} if self._message_requests_weak_topics(message) else None,
        )

    def _quiz_focus_label(
        self,
        message: str,
        subject: Subject,
        domains: list[Domain],
        memory: dict,
        previous_quiz: Optional[dict],
    ) -> str:
        if domains:
            if self._message_requests_weak_topics(message) or (memory.get("last_topic_focus") == "weak_topics" and "that" in message.lower()):
                return "Weak Topics"
            if len(domains) == 1:
                return domains[0].name
            return "Selected Topics"
        if previous_quiz and previous_quiz.get("title") and self._message_is_quiz_adjustment(message):
            return str(previous_quiz["title"]).replace(" Practice", "")
        return subject.name

    def _message_is_quiz_adjustment(self, message: str) -> bool:
        text = message.lower()
        return any(term in text for term in ["easier", "harder", "change", "instead", "make it", "questions", "cancel"])

    def _assistant_planner_context(
        self,
        parent_id: int,
        request: ParentAssistantChatRequest,
        thread_id: Optional[int] = None,
    ) -> dict:
        children = self.get_linked_students(parent_id)
        subjects = self.db.query(Subject).order_by(Subject.name).all()
        grades_query = self.db.query(Grade)
        domains_query = self.db.query(Domain)

        subject_id = request.subject_id
        grade_id = request.grade_id
        if subject_id is not None:
            grades_query = grades_query.filter(Grade.subject_id == subject_id)
            domains_query = domains_query.filter(Domain.subject_id == subject_id)

        domains = domains_query.order_by(Domain.display_order, Domain.name).limit(50).all()
        grades = grades_query.order_by(Grade.subject_id, Grade.level).limit(50).all()

        if grade_id is not None:
            domain_ids = [
                row[0]
                for row in self.db.query(func.distinct(Standard.domain_id))
                .filter(Standard.grade_id == grade_id)
                .all()
            ]
            domains = [domain for domain in domains if domain.id in set(domain_ids)]

        return {
            "selected": {
                "student_id": request.student_id,
                "subject_id": request.subject_id,
                "grade_id": request.grade_id,
            },
            "children": [
                {
                    "student_id": child.student_id,
                    "student_name": child.student_name,
                    "student_username": child.student_username,
                }
                for child in children
            ],
            "subjects": [
                {"id": subject.id, "name": subject.name, "code": subject.code}
                for subject in subjects
            ],
            "grades": [
                {
                    "id": grade.id,
                    "subject_id": grade.subject_id,
                    "level": grade.level,
                    "display_name": grade.display_name,
                }
                for grade in grades
            ],
            "domains": [
                {
                    "id": domain.id,
                    "subject_id": domain.subject_id,
                    "code": domain.code,
                    "name": domain.name,
                }
                for domain in domains
            ],
            "recent_messages": self._recent_assistant_messages(thread_id) if thread_id else [],
        }

    def _get_or_create_assistant_thread(
        self,
        parent_id: int,
        request: ParentAssistantChatRequest,
    ) -> ParentAssistantThread:
        if request.thread_id is not None:
            thread = self.db.query(ParentAssistantThread).filter(
                ParentAssistantThread.id == request.thread_id,
                ParentAssistantThread.parent_id == parent_id,
            ).first()
            if thread:
                if request.student_id and self.can_view_student(parent_id, request.student_id):
                    thread.student_id = request.student_id
                    self._touch_assistant_thread(thread.id)
                    self.db.commit()
                return thread

        student_id = request.student_id if request.student_id and self.can_view_student(parent_id, request.student_id) else None
        thread = ParentAssistantThread(
            parent_id=parent_id,
            student_id=student_id,
            title=request.message.strip()[:120],
        )
        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)
        return thread

    def _add_assistant_message(
        self,
        thread_id: int,
        role: str,
        content: str,
        intent: Optional[str] = None,
    ) -> ParentAssistantMessage:
        message = ParentAssistantMessage(
            thread_id=thread_id,
            role=role,
            content=content,
            intent=intent,
        )
        self.db.add(message)
        self._touch_assistant_thread(thread_id)
        self.db.commit()
        self.db.refresh(message)
        return message

    def _recent_assistant_messages(self, thread_id: Optional[int], limit: int = 8) -> list[dict]:
        if thread_id is None:
            return []
        messages = (
            self.db.query(ParentAssistantMessage)
            .filter(ParentAssistantMessage.thread_id == thread_id)
            .order_by(ParentAssistantMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "role": message.role,
                "content": message.content,
                "intent": message.intent,
                "created_at": message.created_at,
            }
            for message in reversed(messages)
        ]

    def _start_tool_call(
        self,
        thread_id: int,
        message_id: int,
        tool_name: str,
        arguments: dict,
    ) -> ParentAssistantToolCall:
        tool_call = ParentAssistantToolCall(
            thread_id=thread_id,
            message_id=message_id,
            tool_name=tool_name,
            arguments=self._json_safe(arguments),
            status="running",
        )
        self.db.add(tool_call)
        self.db.commit()
        self.db.refresh(tool_call)
        return tool_call

    def _finish_tool_call(
        self,
        tool_call: ParentAssistantToolCall,
        status: str,
        result: dict,
        error: Optional[str] = None,
    ) -> None:
        tool_call.status = status
        tool_call.result = self._json_safe(result)
        tool_call.error = error
        tool_call.completed_at = datetime.utcnow()
        self._touch_assistant_thread(tool_call.thread_id)
        self.db.commit()
        self.db.refresh(tool_call)

    def _touch_assistant_thread(self, thread_id: int) -> None:
        thread = self.db.query(ParentAssistantThread).filter(ParentAssistantThread.id == thread_id).first()
        if thread:
            thread.updated_at = datetime.utcnow()

    def _json_safe(self, value):
        return json.loads(json.dumps(value, default=str))

    def _merge_selected_context_into_tool_args(
        self,
        request: ParentAssistantChatRequest,
        arguments: dict,
    ) -> dict:
        merged = dict(arguments or {})
        if request.student_id is not None:
            merged["student_id"] = request.student_id
        if request.subject_id is not None:
            merged["subject_id"] = request.subject_id
        if request.grade_id is not None:
            merged["grade_id"] = request.grade_id
        return merged

    def _fallback_tool_call(
        self,
        parent_id: int,
        request: ParentAssistantChatRequest,
        context: dict,
    ) -> dict:
        intent = self._detect_assistant_intent(request.message)
        arguments = {
            "student_id": request.student_id,
            "subject_id": request.subject_id,
            "grade_id": request.grade_id,
        }

        if request.student_id is None and len(context.get("children", [])) == 1:
            arguments["student_id"] = context["children"][0]["student_id"]

        if intent == "quiz_assignment":
            arguments.update({
                "difficulty": self._parse_assignment_difficulty(request.message),
                "question_count": self._parse_assignment_question_count(request.message),
                "focus": "weak_topics" if self._message_requests_weak_topics(request.message) else "subject",
            })
            return {"tool_name": "create_quiz_assignment", "arguments": arguments, "confidence": 0.5}
        if intent == "syllabus":
            return {"tool_name": "get_syllabus", "arguments": arguments, "confidence": 0.5}
        if intent == "strong_topics":
            return {"tool_name": "get_strong_topics", "arguments": arguments, "confidence": 0.5}
        if intent == "weak_topics":
            return {"tool_name": "get_weak_topics", "arguments": arguments, "confidence": 0.5}
        return {"tool_name": "get_learning_summary", "arguments": arguments, "confidence": 0.5}

    def _is_assistant_greeting(self, message: str) -> bool:
        text = message.strip().lower().strip("!.?, ")
        greetings = {
            "hi",
            "hello",
            "hey",
            "hey there",
            "good morning",
            "good afternoon",
            "good evening",
        }
        return text in greetings

    def _assistant_greeting_response(self, parent_id: int) -> str:
        children = self.get_linked_students(parent_id)
        if children:
            child_names = ", ".join(child.student_name for child in children[:2])
            if len(children) > 2:
                child_names = f"{child_names}, and {len(children) - 2} more"
            return (
                f"Hi! I can help you review {child_names}'s weak topics, strong topics, "
                "syllabus, or create a practice quiz."
            )
        return (
            "Hi! I can help with weak topics, strong topics, syllabus, and practice quizzes "
            "once a student is linked to your parent account."
        )

    def _detect_assistant_intent(self, message: str, memory: Optional[dict] = None) -> str:
        text = message.lower()
        normalized = text.strip().strip("!.?, ")
        memory = memory or {}

        if self._is_assistant_greeting(message):
            return "greeting"
        if normalized in {"thanks", "thank you", "thx", "ty", "ok thanks", "great thanks"}:
            return "thanks"
        if any(term in text for term in ["what can you do", "help me", "how can you help", "what do you do"]):
            return "help"

        has_pending_quiz = bool(memory.get("pending_quiz"))
        if has_pending_quiz and normalized in {"yes", "yes assign it", "assign it", "go ahead", "do it", "confirm", "sure"}:
            return "quiz_confirm"
        if has_pending_quiz and normalized in {"no", "cancel", "never mind", "nevermind", "stop", "do not assign it"}:
            return "quiz_cancel"

        assignment_actions = ["assign", "post", "create", "make", "give", "send"]
        assignment_targets = ["quiz", "questions", "question", "problems", "problem", "practice set", "practice"]
        if (
            any(action in text for action in assignment_actions)
            and any(target in text for target in assignment_targets)
        ):
            return "quiz_assignment"
        if has_pending_quiz and any(term in text for term in ["easier", "harder", "change", "instead", "question"]):
            return "quiz_assignment"
        if any(term in text for term in ["assign that", "practice on that", "quiz on that", "questions on that"]):
            return "quiz_assignment"
        if any(term in text for term in ["assignment status", "quiz status", "did they finish", "assigned quiz", "what quiz"]):
            return "assignment_status"
        if any(term in text for term in ["weak", "struggl", "improve", "mistake", "practice", "behind"]):
            return "weak_topics"
        if any(term in text for term in ["strong", "strength", "best", "good at", "doing well"]):
            return "strong_topics"
        if any(term in text for term in ["syllabus", "curriculum", "standards", "domains", "grade 6", "grade 7"]):
            return "syllabus"
        if any(term in text for term in ["progress", "how is", "how's", "doing", "score", "performance", "summary"]):
            return "learning_summary"
        if len(normalized.split()) <= 3:
            return "unknown"
        return "learning_summary"

    def _resolve_assistant_student(self, parent_id: int, student_id: Optional[int]) -> Optional[User]:
        if student_id is not None:
            if not self.can_view_student(parent_id, student_id):
                return None
            return self.db.query(User).filter(
                User.id == student_id,
                User.role == UserRole.STUDENT,
                User.is_active == True,
            ).first()

        linked_students = self.get_linked_students(parent_id)
        if len(linked_students) == 1:
            return self.db.query(User).filter(User.id == linked_students[0].student_id).first()
        return None

    def _get_student_by_id(self, student_id: int) -> Optional[User]:
        return self.db.query(User).filter(
            User.id == student_id,
            User.role == UserRole.STUDENT,
            User.is_active == True,
        ).first()

    def _assistant_quiz_assignment_response(
        self,
        parent_id: int,
        student: User,
        request: ParentAssistantChatRequest,
        plan: Optional[dict] = None,
    ) -> dict:
        subject = self._resolve_assistant_subject(request.message, request.subject_id, plan)
        if not subject:
            subjects = self.db.query(Subject).order_by(Subject.name).all()
            if len(subjects) == 1:
                subject = subjects[0]
            else:
                return {
                    "intent": "quiz_assignment",
                    "answer": "Which subject should I use for the quiz? Select a subject, then ask me to assign it again.",
                    "requires_subject": True,
                    "suggestions": [f"Assign a 5 question medium {item.name} quiz" for item in subjects[:3]],
                    "data": {
                        "student_id": student.id,
                        "subjects": [{"id": item.id, "name": item.name, "code": item.code} for item in subjects],
                    },
                }

        grade = self._resolve_assistant_grade(subject.id, request.message, request.grade_id, plan)
        if not grade:
            grades = self.db.query(Grade).filter(Grade.subject_id == subject.id).order_by(Grade.level).all()
            if len(grades) == 1:
                grade = grades[0]
            else:
                return {
                    "intent": "quiz_assignment",
                    "answer": "Which grade should I use for the quiz? Select a grade, then ask me to assign it again.",
                    "requires_subject": False,
                    "suggestions": [
                        f"Assign a 5 question medium {subject.name} quiz for {item.display_name}"
                        for item in grades[:3]
                    ],
                    "data": {
                        "student_id": student.id,
                        "subject_id": subject.id,
                        "grades": [{"id": item.id, "name": item.display_name, "level": item.level} for item in grades],
                    },
                }

        difficulty = self._parse_assignment_difficulty(request.message, plan)
        question_count = self._parse_assignment_question_count(request.message, plan)
        domain_ids = self._resolve_assignment_domain_ids(
            message=request.message,
            student_id=student.id,
            subject_id=subject.id,
            grade_id=grade.id if grade else None,
            plan=plan,
        )
        student_name = student.full_name or student.username
        grade_label = grade.display_name if grade else "Selected grade"
        focus_label = "weak topics" if self._message_requests_weak_topics(request.message) and domain_ids else subject.name
        title = f"{focus_label.title()} Practice"

        try:
            assignment = self.create_quiz_assignment(
                parent_id=parent_id,
                request=QuizAssignmentCreateRequest(
                    student_id=student.id,
                    title=title[:150],
                    description=f"Created by the parent assistant from: {request.message[:220]}",
                    subject_id=subject.id,
                    grade_id=grade.id if grade else None,
                    domain_ids=domain_ids,
                    difficulty=difficulty,
                    question_count=question_count,
                    generate_missing=True,
                ),
            )
        except ValueError as exc:
            return {
                "intent": "quiz_assignment",
                "answer": (
                    f"I could not assign that quiz yet: {exc}\n\n"
                    "Try a lower question count, mixed difficulty, or a broader subject/grade."
                ),
                "suggestions": [
                    f"Assign a 3 question mixed {subject.name} quiz",
                    "Show weak topics",
                    "Show syllabus",
                ],
                "data": {
                    "student_id": student.id,
                    "subject_id": subject.id,
                    "grade_id": grade.id if grade else None,
                },
            }
        except (ConnectionError, TimeoutError, RuntimeError) as exc:
            return {
                "intent": "quiz_assignment",
                "answer": (
                    "I found that this quiz needs new AI-generated questions, but generation is not available right now. "
                    f"Details: {exc}"
                ),
                "suggestions": [
                    "Assign a 3 question mixed quiz",
                    "Try existing questions only in Assign a Quiz",
                    "Show weak topics",
                ],
                "data": {
                    "student_id": student.id,
                    "subject_id": subject.id,
                    "grade_id": grade.id if grade else None,
                },
            }

        generated_count = int(assignment.get("generated_questions", 0))
        generation_text = (
            f" I generated {generated_count} new question{'s' if generated_count != 1 else ''} to fill the quiz."
            if generated_count > 0
            else " I used existing unanswered questions."
        )

        return {
            "intent": "quiz_assignment",
            "answer": (
                f"Done. I assigned {student_name} a {question_count}-question {difficulty} "
                f"{subject.name} quiz for {grade_label}.{generation_text}"
            ),
            "suggestions": [
                "Show weak topics",
                "Assign another 5 question quiz",
                "Show syllabus",
            ],
            "data": {
                "student_id": student.id,
                "assignment": self._assignment_chat_payload(assignment),
                "generated_questions": generated_count,
            },
        }

    def _parse_assignment_difficulty(self, message: str, plan: Optional[dict] = None) -> str:
        planned_difficulty = plan.get("difficulty") if plan else None
        if planned_difficulty in {"easy", "medium", "hard", "mixed"}:
            return planned_difficulty

        text = message.lower()
        if any(term in text for term in ["easy", "warm", "simple", "basic"]):
            return "easy"
        if any(term in text for term in ["hard", "challeng", "advanced", "difficult"]):
            return "hard"
        if any(term in text for term in ["mixed", "mix", "varied"]):
            return "mixed"
        return "medium"

    def _parse_assignment_question_count(self, message: str, plan: Optional[dict] = None) -> int:
        planned_count = plan.get("question_count") if plan else None
        if isinstance(planned_count, int):
            return max(1, min(25, planned_count))

        text = message.lower()
        count_match = re.search(r"\b(\d{1,2})\s*(?:question|questions|problem|problems)\b", text)
        if not count_match:
            count_match = re.search(r"\b(?:quiz|practice)\s+(?:with|of)?\s*(\d{1,2})\b", text)
        if not count_match:
            return 5

        return max(1, min(25, int(count_match.group(1))))

    def _message_requests_weak_topics(self, message: str) -> bool:
        text = message.lower()
        return any(term in text for term in ["weak", "struggl", "mistake", "improve", "behind"])

    def _resolve_assignment_domain_ids(
        self,
        message: str,
        student_id: int,
        subject_id: int,
        grade_id: Optional[int],
        plan: Optional[dict] = None,
    ) -> list[int]:
        text = message.lower()
        query = self.db.query(Domain).filter(Domain.subject_id == subject_id)
        if grade_id is not None:
            query = query.join(Standard, Standard.domain_id == Domain.id).filter(Standard.grade_id == grade_id)

        domains = query.distinct().all()
        domain_ids = [domain.id for domain in domains]

        planned_domain_ids = [
            domain_id
            for domain_id in (plan.get("domain_ids", []) if plan else [])
            if domain_id in domain_ids
        ]
        if planned_domain_ids:
            return planned_domain_ids

        explicit_domain_ids = []
        planned_domain_names = [name.lower() for name in (plan.get("domain_names", []) if plan else [])]
        for domain in domains:
            domain_name = domain.name.lower()
            domain_code = domain.code.lower()
            domain_words = [word for word in re.findall(r"[a-z]{4,}", domain_name)]
            if (
                domain_name in text
                or domain_name in planned_domain_names
                or re.search(rf"\b{re.escape(domain_code)}\b", text)
                or any(word in text for word in domain_words)
                or any(name in domain_name for name in planned_domain_names)
            ):
                explicit_domain_ids.append(domain.id)

        if explicit_domain_ids:
            return explicit_domain_ids

        if not self._message_requests_weak_topics(message):
            focus = (plan.get("focus") if plan else None) or ""
            if focus != "weak_topics":
                return []

        allowed_domain_ids = {domain.id for domain in domains}
        weak_topics = sorted(
            [
                topic
                for topic in self._get_student_domain_performance(student_id)
                if topic["domain_id"] in allowed_domain_ids
            ],
            key=lambda topic: (topic["accuracy"], -topic["questions_attempted"], topic["domain_name"]),
        )
        return [topic["domain_id"] for topic in weak_topics[:2]]

    def _assignment_chat_payload(self, assignment: dict) -> dict:
        keys = [
            "id",
            "student_id",
            "student_name",
            "title",
            "difficulty",
            "status",
            "question_count",
            "answered_count",
            "correct_count",
            "generated_questions",
            "subject_id",
            "subject_name",
            "grade_id",
            "grade_name",
        ]
        return {key: assignment.get(key) for key in keys}

    def _assistant_learning_response(self, student: User, focus: str) -> dict:
        topics = self._get_student_domain_performance(student.id)
        student_name = student.full_name or student.username

        if not topics:
            return {
                "intent": "learning_summary",
                "answer": f"I do not see any answered questions for {student_name} yet. Once they complete a quiz, I can identify strong and weak topics.",
                "suggestions": [
                    "Show syllabus",
                    "What should my child practice?",
                ],
                "data": {"student_id": student.id, "topics": []},
            }

        weak_topics = sorted(
            topics,
            key=lambda topic: (topic["accuracy"], -topic["questions_attempted"], topic["domain_name"]),
        )[:3]
        strong_topics = sorted(
            topics,
            key=lambda topic: (-topic["accuracy"], -topic["questions_attempted"], topic["domain_name"]),
        )[:3]

        if focus == "weak":
            answer = self._format_topic_answer(
                f"{student_name}'s weak topics",
                weak_topics,
                empty_text=f"I do not see clear weak topics for {student_name} yet.",
                include_recommendation=True,
            )
            intent = "weak_topics"
        elif focus == "strong":
            answer = self._format_topic_answer(
                f"{student_name}'s strong topics",
                strong_topics,
                empty_text=f"I do not see clear strong topics for {student_name} yet.",
                include_recommendation=False,
            )
            intent = "strong_topics"
        else:
            weak_text = self._format_topic_lines(weak_topics, include_recommendation=True)
            strong_text = self._format_topic_lines(strong_topics, include_recommendation=False)
            answer = (
                f"Here is what I see for {student_name}:\n\n"
                f"Strong topics:\n{strong_text}\n\n"
                f"Topics to practice:\n{weak_text}"
            )
            intent = "learning_summary"

        return {
            "intent": intent,
            "answer": answer,
            "suggestions": [
                "Show weak topics",
                "Show strong topics",
                "Show syllabus",
            ],
            "data": {
                "student_id": student.id,
                "student_name": student_name,
                "weak_topics": weak_topics,
                "strong_topics": strong_topics,
            },
        }

    def _get_student_domain_performance(self, student_id: int) -> list[dict]:
        rows = (
            self.db.query(
                Domain.id.label("domain_id"),
                Domain.name.label("domain_name"),
                Domain.code.label("domain_code"),
                func.count(AnsweredQuestion.id).label("questions_attempted"),
                func.sum(func.cast(AnsweredQuestion.is_correct, Integer)).label("correct_count"),
            )
            .join(Standard, Standard.domain_id == Domain.id)
            .join(AnsweredQuestion, AnsweredQuestion.standard_id == Standard.id)
            .filter(AnsweredQuestion.student_id == student_id)
            .group_by(Domain.id, Domain.name, Domain.code)
            .all()
        )

        ability_records = {
            ability.domain_id: ability
            for ability in self.db.query(StudentDomainAbility).filter(
                StudentDomainAbility.student_id == student_id,
            ).all()
        }

        topics = []
        for row in rows:
            attempted = row.questions_attempted or 0
            correct = row.correct_count or 0
            if attempted <= 0:
                continue

            ability = ability_records.get(row.domain_id)
            theta = float(ability.theta) if ability else correct / attempted
            level, description, progress = get_skill_level(theta, attempted)

            topics.append({
                "domain_id": row.domain_id,
                "domain_name": row.domain_name,
                "domain_code": row.domain_code,
                "questions_attempted": attempted,
                "correct_count": correct,
                "incorrect_count": attempted - correct,
                "accuracy": correct / attempted,
                "level": level,
                "level_description": description,
                "progress": progress,
            })

        return topics

    def _format_topic_answer(
        self,
        title: str,
        topics: list[dict],
        empty_text: str,
        include_recommendation: bool,
    ) -> str:
        if not topics:
            return empty_text
        return f"{title}:\n" + self._format_topic_lines(topics, include_recommendation)

    def _format_topic_lines(self, topics: list[dict], include_recommendation: bool) -> str:
        if not topics:
            return "- Not enough quiz data yet."

        lines = []
        for topic in topics:
            accuracy_pct = round(topic["accuracy"] * 100)
            line = (
                f"- {topic['domain_name']} ({topic['domain_code']}): "
                f"{accuracy_pct}% accuracy across {topic['questions_attempted']} question"
                f"{'s' if topic['questions_attempted'] != 1 else ''}; level: {topic['level']}."
            )
            if include_recommendation:
                line += " This is a good next practice area."
            lines.append(line)

        return "\n".join(lines)

    def _assistant_syllabus_response(self, request: ParentAssistantChatRequest, plan: Optional[dict] = None) -> dict:
        subject = self._resolve_assistant_subject(request.message, request.subject_id, plan)
        if not subject:
            subjects = self.db.query(Subject).order_by(Subject.name).all()
            return {
                "intent": "syllabus",
                "answer": "Which subject should I show? Select a subject, or ask with the subject name.",
                "requires_subject": True,
                "suggestions": [f"Show {subject.name} syllabus" for subject in subjects[:3]],
                "data": {
                    "subjects": [
                        {"id": subject.id, "name": subject.name, "code": subject.code}
                        for subject in subjects
                    ],
                },
            }

        grade = self._resolve_assistant_grade(subject.id, request.message, request.grade_id, plan)
        domains = self._get_syllabus_domains(subject.id, grade.id if grade else None)
        subject_label = subject.name
        grade_label = f" for {grade.display_name}" if grade else ""

        if not domains:
            return {
                "intent": "syllabus",
                "answer": f"I could not find syllabus domains for {subject_label}{grade_label}.",
                "requires_subject": False,
                "suggestions": ["Show another subject", "Show weak topics"],
                "data": {"subject_id": subject.id, "grade_id": grade.id if grade else None, "domains": []},
            }

        domain_lines = [
            f"- {domain['domain_name']} ({domain['domain_code']}): "
            f"{domain['standards_count']} standard{'s' if domain['standards_count'] != 1 else ''}"
            for domain in domains
        ]
        answer = (
            f"{subject_label}{grade_label} includes {len(domains)} domain"
            f"{'s' if len(domains) != 1 else ''}:\n"
            + "\n".join(domain_lines)
        )

        if grade:
            answer += "\n\nSelect a domain in the syllabus view later to drill into clusters and standards."
        else:
            grades = self.db.query(Grade).filter(Grade.subject_id == subject.id).order_by(Grade.level).all()
            if grades:
                grade_names = ", ".join(grade.display_name for grade in grades)
                answer += f"\n\nAvailable grades: {grade_names}."

        return {
            "intent": "syllabus",
            "answer": answer,
            "suggestions": [
                "Show weak topics",
                "Show strong topics",
                "What should my child practice?",
            ],
            "data": {
                "subject_id": subject.id,
                "subject_name": subject.name,
                "grade_id": grade.id if grade else None,
                "grade_name": grade.display_name if grade else None,
                "domains": domains,
            },
        }

    def _resolve_assistant_subject(
        self,
        message: str,
        subject_id: Optional[int],
        plan: Optional[dict] = None,
    ) -> Optional[Subject]:
        if subject_id is not None:
            return self.db.query(Subject).filter(Subject.id == subject_id).first()

        planned_subject_id = plan.get("subject_id") if plan else None
        if planned_subject_id is not None:
            subject = self.db.query(Subject).filter(Subject.id == planned_subject_id).first()
            if subject:
                return subject

        planned_subject_name = (plan.get("subject_name") or "").lower() if plan else ""
        text = message.lower()
        subjects = self.db.query(Subject).all()
        for subject in subjects:
            subject_name = subject.name.lower()
            subject_code = subject.code.lower()
            if (
                subject_name in text
                or subject_code in text
                or (planned_subject_name and planned_subject_name in subject_name)
                or (planned_subject_name and subject_name in planned_subject_name)
            ):
                return subject
        return None

    def _resolve_assistant_grade(
        self,
        subject_id: int,
        message: str,
        grade_id: Optional[int],
        plan: Optional[dict] = None,
    ) -> Optional[Grade]:
        if grade_id is not None:
            return self.db.query(Grade).filter(
                Grade.id == grade_id,
                Grade.subject_id == subject_id,
            ).first()

        planned_grade_id = plan.get("grade_id") if plan else None
        if planned_grade_id is not None:
            grade = self.db.query(Grade).filter(
                Grade.id == planned_grade_id,
                Grade.subject_id == subject_id,
            ).first()
            if grade:
                return grade

        planned_grade_level = plan.get("grade_level") if plan else None
        if planned_grade_level is not None:
            grade = self.db.query(Grade).filter(
                Grade.subject_id == subject_id,
                Grade.level == planned_grade_level,
            ).first()
            if grade:
                return grade

        grade_match = re.search(r"\bgrade\s*(\d+)\b|\b(\d+)(?:st|nd|rd|th)\s*grade\b", message.lower())
        if not grade_match:
            return None

        level = int(next(group for group in grade_match.groups() if group is not None))
        return self.db.query(Grade).filter(
            Grade.subject_id == subject_id,
            Grade.level == level,
        ).first()

    def _get_syllabus_domains(self, subject_id: int, grade_id: Optional[int]) -> list[dict]:
        query = self.db.query(Domain).filter(Domain.subject_id == subject_id)
        if grade_id is not None:
            query = query.join(Standard, Standard.domain_id == Domain.id).filter(Standard.grade_id == grade_id)

        domains = query.distinct().order_by(Domain.display_order, Domain.name).all()
        result = []

        for domain in domains:
            standards_query = self.db.query(Standard).filter(Standard.domain_id == domain.id)
            clusters_query = self.db.query(Cluster).filter(Cluster.domain_id == domain.id)
            if grade_id is not None:
                standards_query = standards_query.filter(Standard.grade_id == grade_id)
                clusters_query = clusters_query.filter(Cluster.grade_id == grade_id)

            standards = standards_query.order_by(Standard.code).all()
            clusters = clusters_query.order_by(Cluster.code).all()
            result.append({
                "domain_id": domain.id,
                "domain_name": domain.name,
                "domain_code": domain.code,
                "clusters_count": len(clusters),
                "standards_count": len(standards),
                "sample_standards": [
                    {
                        "id": standard.id,
                        "code": standard.code,
                        "description": standard.description,
                    }
                    for standard in standards[:5]
                ],
            })

        return result
