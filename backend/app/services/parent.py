from datetime import datetime
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
)
from app.schemas.parent import (
    ParentAssistantChatRequest,
    ParentStudentLinkResponse,
    StudentProgressSummary,
    StudentDetailForParent,
)
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

    def handle_assistant_chat(self, parent_id: int, request: ParentAssistantChatRequest) -> dict:
        """Handle Phase 1 parent assistant requests using deterministic data tools."""
        message = request.message.strip()
        intent = self._detect_assistant_intent(message)

        if intent == "syllabus":
            return self._assistant_syllabus_response(request)

        student = self._resolve_assistant_student(parent_id, request.student_id)
        if not student:
            linked_students = self.get_linked_students(parent_id)
            if not linked_students:
                return {
                    "intent": intent,
                    "answer": "I do not see an approved student link yet. Once a link is approved, I can summarize strengths, weak topics, and practice needs.",
                    "requires_student": True,
                    "suggestions": ["Request a student link", "Show syllabus"],
                    "data": {"children": []},
                }

            return {
                "intent": intent,
                "answer": "Which child should I look at? Select a child, then ask about strengths, weak topics, or recent progress.",
                "requires_student": True,
                "suggestions": [
                    "What are my child's weak topics?",
                    "What are my child's strong topics?",
                    "Show recent progress",
                ],
                "data": {"children": [child.model_dump() for child in linked_students]},
            }

        if intent == "strong_topics":
            return self._assistant_learning_response(student, focus="strong")
        if intent == "weak_topics":
            return self._assistant_learning_response(student, focus="weak")

        return self._assistant_learning_response(student, focus="summary")

    def _detect_assistant_intent(self, message: str) -> str:
        text = message.lower()
        if any(term in text for term in ["syllabus", "curriculum", "topics", "standards", "domains"]):
            return "syllabus"
        if any(term in text for term in ["weak", "struggl", "improve", "mistake", "practice", "behind"]):
            return "weak_topics"
        if any(term in text for term in ["strong", "strength", "best", "good at", "doing well"]):
            return "strong_topics"
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

    def _assistant_syllabus_response(self, request: ParentAssistantChatRequest) -> dict:
        subject = self._resolve_assistant_subject(request.message, request.subject_id)
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

        grade = self._resolve_assistant_grade(subject.id, request.message, request.grade_id)
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

    def _resolve_assistant_subject(self, message: str, subject_id: Optional[int]) -> Optional[Subject]:
        if subject_id is not None:
            return self.db.query(Subject).filter(Subject.id == subject_id).first()

        text = message.lower()
        subjects = self.db.query(Subject).all()
        for subject in subjects:
            if subject.name.lower() in text or subject.code.lower() in text:
                return subject
        return None

    def _resolve_assistant_grade(self, subject_id: int, message: str, grade_id: Optional[int]) -> Optional[Grade]:
        if grade_id is not None:
            return self.db.query(Grade).filter(
                Grade.id == grade_id,
                Grade.subject_id == subject_id,
            ).first()

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
