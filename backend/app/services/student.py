import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from app.models import AnsweredQuestion, Standard, DomainProgress, Domain

logger = logging.getLogger(__name__)


class StudentService:
    """Service for student self-service operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_progress_summary(self, student_id: int) -> dict:
        """Get a student's progress summary from answered_questions."""
        # Total answered and correct count
        total_result = self.db.query(
            func.count(AnsweredQuestion.id).label("total"),
            func.sum(func.cast(AnsweredQuestion.is_correct, Integer)).label("correct")
        ).filter(AnsweredQuestion.student_id == student_id).first()

        total_answered = total_result.total or 0
        correct_count = total_result.correct or 0 if total_result.total else 0
        accuracy = correct_count / total_answered if total_answered > 0 else None

        # Unique standards attempted
        standards_result = self.db.query(
            func.count(func.distinct(AnsweredQuestion.standard_id)).label("count")
        ).filter(AnsweredQuestion.student_id == student_id).first()
        standards_attempted = standards_result.count or 0

        # Recent answers (last 20)
        recent = self.db.query(AnsweredQuestion).filter(
            AnsweredQuestion.student_id == student_id
        ).order_by(AnsweredQuestion.answered_at.desc()).limit(20).all()

        recent_answers = []
        for answer in recent:
            standard = self.db.query(Standard).filter(Standard.id == answer.standard_id).first()
            recent_answers.append({
                "question_id": answer.question_id,
                "standard_code": standard.code if standard else "Unknown",
                "is_correct": answer.is_correct,
                "answered_at": answer.answered_at,
            })

        return {
            "total_answered": total_answered,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "standards_attempted": standards_attempted,
            "recent_answers": recent_answers,
        }

    def get_answer_history(self, student_id: int) -> dict:
        """Get a student's full answer history."""
        return self.get_progress_summary(student_id)

    # ==================== Domain Progress (Adaptive Learning) ====================

    def update_domain_progress(self, student_id: int, domain_id: int, is_correct: bool) -> DomainProgress:
        """Update or create domain progress after a student answers a question."""
        progress = self.db.query(DomainProgress).filter(
            DomainProgress.student_id == student_id,
            DomainProgress.domain_id == domain_id
        ).first()

        if not progress:
            progress = DomainProgress(
                student_id=student_id,
                domain_id=domain_id,
                total_answered=0,
                correct_count=0,
                accuracy=0.0,
                current_difficulty=0.5,
            )
            self.db.add(progress)

        # Update counts
        progress.total_answered += 1
        if is_correct:
            progress.correct_count += 1

        # Recalculate accuracy
        progress.accuracy = float(progress.correct_count) / float(progress.total_answered)

        # Adjust difficulty based on accuracy
        # Increase difficulty if accuracy >= 80%, decrease if < 50%
        if progress.accuracy >= 0.80:
            progress.current_difficulty = min(1.0, float(progress.current_difficulty) + 0.1)
        elif progress.accuracy < 0.50:
            progress.current_difficulty = max(0.0, float(progress.current_difficulty) - 0.1)

        progress.last_answered_at = func.now()
        self.db.commit()
        self.db.refresh(progress)
        return progress

    def get_domain_progress(self, student_id: int) -> List[dict]:
        """Get progress for all domains a student has attempted."""
        results = self.db.query(DomainProgress, Domain).join(
            Domain, DomainProgress.domain_id == Domain.id
        ).filter(DomainProgress.student_id == student_id).all()

        progress_list = []
        for prog, domain in results:
            progress_list.append({
                "domain_id": domain.id,
                "domain_name": domain.name,
                "domain_code": domain.code,
                "total_answered": prog.total_answered,
                "correct_count": prog.correct_count,
                "accuracy": float(prog.accuracy),
                "current_difficulty": float(prog.current_difficulty),
                "last_answered_at": prog.last_answered_at.isoformat() if prog.last_answered_at else None,
            })
        return progress_list

    def get_strengths_weaknesses(self, student_id: int) -> dict:
        """Get student strengths (high accuracy) and weaknesses (low accuracy)."""
        results = self.db.query(DomainProgress, Domain).join(
            Domain, DomainProgress.domain_id == Domain.id
        ).filter(DomainProgress.student_id == student_id).all()

        strengths = []
        weaknesses = []
        recommendations = []

        for prog, domain in results:
            accuracy = float(prog.accuracy)
            item = {
                "domain_id": domain.id,
                "domain_name": domain.name,
                "domain_code": domain.code,
                "accuracy": accuracy,
                "total_answered": prog.total_answered,
                "recommendation": "",
            }

            if accuracy >= 0.80 and prog.total_answered >= 3:
                item["recommendation"] = f"Great job in {domain.name}! Try harder questions here."
                strengths.append(item)
            elif accuracy < 0.50 and prog.total_answered >= 3:
                item["recommendation"] = f"Focus on {domain.name} — review the concepts and try more practice questions."
                weaknesses.append(item)

        if not weaknesses:
            recommendations.append("You're doing well across all domains! Keep practicing to maintain your skills.")
        else:
            for w in weaknesses:
                recommendations.append(w["recommendation"])

        if strengths:
            recommendations.append(f"You excel in {len(strengths)} domain(s). Consider helping peers or exploring advanced topics.")

        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
        }
