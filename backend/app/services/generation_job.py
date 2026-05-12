"""Service for async question generation jobs."""

import json
import logging
from sqlalchemy import func
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import (
    GenerationJob,
    GenerationJobStandard,
    JobStatus,
    JobStandardStatus,
    QuestionGenerationAudit,
    Question,
    Standard,
    User,
)
from app.services.questions import QuestionService

logger = logging.getLogger(__name__)

MAX_CONCURRENT_STANDARDS = 15


class QuestionGenerationJobService:
    """Manages creation and execution of async question generation jobs.

    Jobs track per-standard progress so admins can see which standards
    succeeded/failed and retry only failed ones.
    """

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Job lifecycle (synchronous, runs in request thread)
    # ------------------------------------------------------------------

    def create_job(
        self,
        standard_ids: List[int],
        questions_per_standard: int = 1,
        question_type: str = "multiple_choice",
        model: Optional[str] = None,
        timeout: int = 300,
        quality_mode: Optional[str] = None,
        candidate_count: Optional[int] = None,
        max_repair_attempts: Optional[int] = None,
        min_review_score: Optional[float] = None,
        subject_id: Optional[int] = None,
        grade_id: Optional[int] = None,
        created_by: Optional[int] = None,
    ) -> GenerationJob:
        """Create a new generation job and its per-standard records.

        Returns immediately; the caller is responsible for starting
        ``run_job`` in a background task or worker.
        """
        if not standard_ids:
            raise ValueError("At least one standard must be provided")

        settings = get_settings()
        resolved_quality_mode = quality_mode or settings.OLLAMA_QUALITY_MODE
        if resolved_quality_mode not in {"fast", "reviewed", "quality"}:
            resolved_quality_mode = "reviewed"
        resolved_candidate_count = candidate_count if candidate_count is not None else settings.OLLAMA_CANDIDATE_COUNT
        resolved_candidate_count = max(1, min(5, resolved_candidate_count))
        if resolved_quality_mode in {"fast", "reviewed"}:
            resolved_candidate_count = 1
        resolved_repairs = max_repair_attempts if max_repair_attempts is not None else settings.OLLAMA_MAX_REPAIR_ATTEMPTS
        resolved_repairs = max(0, min(3, resolved_repairs))
        resolved_min_score = min_review_score if min_review_score is not None else settings.OLLAMA_MIN_REVIEW_SCORE
        resolved_min_score = max(0.0, min(1.0, resolved_min_score))

        job = GenerationJob(
            status=JobStatus.PENDING.value,
            subject_id=subject_id,
            grade_id=grade_id,
            total_standards=len(standard_ids),
            created_by=created_by,
            question_type=question_type,
            model=model,
            timeout=timeout,
            quality_mode=resolved_quality_mode,
            candidate_count=resolved_candidate_count,
            max_repair_attempts=resolved_repairs,
            min_review_score=resolved_min_score,
        )
        self.db.add(job)
        self.db.flush()  # get job.id

        for sid in standard_ids:
            job_std = GenerationJobStandard(
                job_id=job.id,
                standard_id=sid,
                questions_requested=questions_per_standard,
                status=JobStandardStatus.PENDING.value,
            )
            self.db.add(job_std)

        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: int) -> Optional[GenerationJob]:
        """Fetch a job with its per-standard progress loaded."""
        return (
            self.db.query(GenerationJob)
            .filter(GenerationJob.id == job_id)
            .first()
        )

    def get_jobs(
        self,
        status: Optional[str] = None,
        created_by: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[GenerationJob]:
        """List generation jobs ordered by newest first."""
        query = self.db.query(GenerationJob).order_by(GenerationJob.created_at.desc())
        if status:
            query = query.filter(GenerationJob.status == status)
        if created_by:
            query = query.filter(GenerationJob.created_by == created_by)
        return query.offset(skip).limit(limit).all()

    def cancel_job(self, job_id: int) -> Optional[GenerationJob]:
        """Cancel a pending or running job."""
        job = self.get_job(job_id)
        if not job:
            return None

        if job.status not in (JobStatus.PENDING.value, JobStatus.RUNNING.value):
            raise ValueError(f"Cannot cancel job with status '{job.status}'")

        job.status = JobStatus.CANCELLED.value
        job.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def retry_failed_standards(self, job_id: int) -> GenerationJob:
        """Create a new job containing only the failed standards from a previous job.

        Raises ValueError if the original job is still running.
        """
        original = self.get_job(job_id)
        if not original:
            raise ValueError(f"Job {job_id} not found")
        if original.status == JobStatus.RUNNING.value:
            raise ValueError("Cannot retry while job is still running")

        failed = [
            js.standard_id
            for js in original.job_standards
            if js.status == JobStandardStatus.FAILED.value
        ]
        if not failed:
            raise ValueError("No failed standards to retry")

        return self.create_job(
            standard_ids=failed,
            questions_per_standard=max(
                js.questions_requested
                for js in original.job_standards
                if js.standard_id in failed
            ),
            question_type=original.question_type or "multiple_choice",
            model=original.model,
            timeout=original.timeout or 300,
            quality_mode=original.quality_mode or "reviewed",
            candidate_count=original.candidate_count or 1,
            max_repair_attempts=original.max_repair_attempts or 1,
            min_review_score=float(original.min_review_score or 0.75),
            subject_id=original.subject_id,
            grade_id=original.grade_id,
            created_by=original.created_by,
        )

    # ------------------------------------------------------------------
    # Execution (runs in a background thread / worker)
    # ------------------------------------------------------------------

    @staticmethod
    def run_job(
        job_id: int,
        question_type: str = "multiple_choice",
        model: Optional[str] = None,
        timeout: int = 300,
        quality_mode: Optional[str] = None,
        candidate_count: Optional[int] = None,
        max_repair_attempts: Optional[int] = None,
        min_review_score: Optional[float] = None,
    ) -> None:
        """Execute a generation job.  Must be called in a background task.

        Creates its own DB session so it can safely run outside the
        request thread.
        """
        db = SessionLocal()
        try:
            QuestionGenerationJobService._do_run(
                db,
                job_id,
                question_type,
                model,
                timeout,
                quality_mode,
                candidate_count,
                max_repair_attempts,
                min_review_score,
            )
        except Exception:
            logger.exception(f"Unhandled error running generation job {job_id}")
            # Mark job as failed if we can
            try:
                job = db.query(GenerationJob).get(job_id)
                if job and job.status not in (
                    JobStatus.COMPLETED.value,
                    JobStatus.CANCELLED.value,
                ):
                    job.status = JobStatus.FAILED.value
                    job.completed_at = datetime.utcnow()
                    db.commit()
            except Exception:
                logger.exception(f"Failed to mark job {job_id} as failed")
        finally:
            db.close()

    @staticmethod
    def _run_standard_worker(
        job_std_id: int,
        question_type: str,
        model: Optional[str],
        timeout: int,
        quality_mode: str,
        candidate_count: int,
        max_repair_attempts: int,
        min_review_score: float,
    ) -> Tuple[int, int, Optional[str]]:
        """Run generation for a single standard in its own thread + DB session.

        Returns (standard_id, questions_created, error_or_none).
        """
        db = SessionLocal()
        try:
            job_std = db.query(GenerationJobStandard).get(job_std_id)
            if not job_std:
                return (0, 0, "Job standard not found")

            job_std.status = JobStandardStatus.RUNNING.value
            job_std.started_at = datetime.utcnow()
            db.commit()

            service = QuestionGenerationJobService(db)
            question_service = QuestionService(db)

            created = service._generate_for_standard(
                question_service=question_service,
                job_std=job_std,
                question_type=question_type,
                model=model,
                timeout=timeout,
                quality_mode=quality_mode,
                candidate_count=candidate_count,
                max_repair_attempts=max_repair_attempts,
                min_review_score=min_review_score,
            )

            job_std.status = JobStandardStatus.DONE.value
            job_std.questions_created = created
            job_std.completed_at = datetime.utcnow()
            db.commit()
            return (job_std.standard_id, created, None)
        except Exception as exc:
            logger.error(f"Standard worker {job_std_id} failed: {exc}")
            try:
                db.rollback()
                job_std = db.query(GenerationJobStandard).get(job_std_id)
                if job_std:
                    job_std.status = JobStandardStatus.FAILED.value
                    job_std.error = str(exc)[:1000]
                    job_std.completed_at = datetime.utcnow()
                    db.commit()
            except Exception as inner_exc:
                logger.exception(f"Failed to mark standard {job_std_id} as failed: {inner_exc}")
            sid = job_std.standard_id if job_std else 0
            return (sid, 0, str(exc))
        finally:
            db.close()

    @staticmethod
    def _recompute_aggregates(db: Session, job_id: int) -> None:
        """Recalculate job counters directly from the DB.

        Uses aggregate queries so the update is correct even when called
        concurrently with worker threads in their own sessions.
        """
        job = db.query(GenerationJob).get(job_id)
        if not job:
            return

        completed = (
            db.query(func.count(GenerationJobStandard.id))
            .filter(
                GenerationJobStandard.job_id == job_id,
                GenerationJobStandard.status == JobStandardStatus.DONE.value,
            )
            .scalar()
            or 0
        )
        failed = (
            db.query(func.count(GenerationJobStandard.id))
            .filter(
                GenerationJobStandard.job_id == job_id,
                GenerationJobStandard.status == JobStandardStatus.FAILED.value,
            )
            .scalar()
            or 0
        )
        questions_created = (
            db.query(func.coalesce(func.sum(GenerationJobStandard.questions_created), 0))
            .filter(GenerationJobStandard.job_id == job_id)
            .scalar()
            or 0
        )

        job.completed_standards = completed
        job.failed_standards = failed
        job.questions_created = questions_created
        db.commit()

    @staticmethod
    def _do_run(
        db: Session,
        job_id: int,
        question_type: str,
        model: Optional[str],
        timeout: int,
        quality_mode: Optional[str],
        candidate_count: Optional[int],
        max_repair_attempts: Optional[int],
        min_review_score: Optional[float],
    ) -> None:
        """Core loop — must never raise unhandled exceptions."""
        service = QuestionGenerationJobService(db)
        job = service.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found, cannot run")
            return

        if job.status != JobStatus.PENDING.value:
            logger.warning(
                f"Job {job_id} has status '{job.status}', skipping execution"
            )
            return

        resolved_question_type = job.question_type or question_type
        resolved_model = job.model if job.model is not None else model
        resolved_timeout = job.timeout or timeout
        resolved_quality_mode = quality_mode or job.quality_mode or "reviewed"
        resolved_candidate_count = candidate_count or job.candidate_count or 1
        resolved_repairs = max_repair_attempts if max_repair_attempts is not None else (job.max_repair_attempts or 1)
        resolved_min_score = min_review_score if min_review_score is not None else float(job.min_review_score or 0.75)

        # Mark running
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        db.commit()

        # Load pending standards in deterministic order
        pending = (
            db.query(GenerationJobStandard)
            .filter(
                GenerationJobStandard.job_id == job_id,
                GenerationJobStandard.status == JobStandardStatus.PENDING.value,
            )
            .order_by(GenerationJobStandard.id)
            .all()
        )

        settings = get_settings()
        max_workers = max(1, min(MAX_CONCURRENT_STANDARDS, settings.OLLAMA_GENERATION_WORKERS))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(
                    QuestionGenerationJobService._run_standard_worker,
                    job_std.id,
                    resolved_question_type,
                    resolved_model,
                    resolved_timeout,
                    resolved_quality_mode,
                    resolved_candidate_count,
                    resolved_repairs,
                    resolved_min_score,
                ): job_std
                for job_std in pending
            }

            for future in as_completed(future_map):
                try:
                    standard_id, created, error = future.result()
                    if error:
                        logger.error(f"Standard {standard_id} failed: {error}")
                except Exception as exc:
                    logger.error(f"Unexpected worker error in job {job_id}: {exc}")

                # Update parent job counters incrementally after each standard
                QuestionGenerationJobService._recompute_aggregates(db, job_id)

                # Check for cancellation between completions
                db.refresh(job)
                if job.status == JobStatus.CANCELLED.value:
                    # Cancel futures that haven't started yet
                    for f in future_map:
                        if not f.done():
                            f.cancel()
                    logger.info(f"Job {job_id} cancelled, draining remaining workers")
                    break

            # Final counter sync before terminal state
            QuestionGenerationJobService._recompute_aggregates(db, job_id)

        # Finalise job
        db.refresh(job)
        if job.status == JobStatus.CANCELLED.value:
            return

        job = db.query(GenerationJob).get(job_id)
        if not job:
            return

        # Final aggregate sync before terminal state
        QuestionGenerationJobService._recompute_aggregates(db, job_id)

        # Build errors from per-standard DB records to avoid in-memory
        # accumulation and any concurrent-modification race on the JSON column.
        summary = (
            db.query(GenerationJobStandard)
            .filter(GenerationJobStandard.job_id == job_id)
            .all()
        )
        job.errors = [
            f"Standard {js.standard_id}: {js.error}"
            for js in summary
            if js.error
        ]
        job.status = (
            JobStatus.COMPLETED.value
            if job.failed_standards == 0
            else JobStatus.FAILED.value
        )
        if (
            job.status == JobStatus.COMPLETED.value
            and job.completed_standards < job.total_standards
        ):
            job.status = JobStatus.FAILED.value
        job.completed_at = datetime.utcnow()
        db.commit()
        logger.info(
            f"Job {job_id} finished: {job.completed_standards}/{job.total_standards} "
            f"completed, {job.failed_standards} failed, {job.questions_created} questions"
        )

    def _compute_difficulty_spread(self, base: float, count: int) -> list[float]:
        """Distribute N questions across difficulty tiers centered on the standard.

        Example: base=0.50, count=5 → [0.30, 0.40, 0.50, 0.60, 0.70]
        """
        if count == 1:
            return [base]
        min_d = max(base - 0.20, 0.05)
        max_d = min(base + 0.20, 0.95)
        if count == 2:
            return [min_d, max_d]
        step = (max_d - min_d) / (count - 1)
        return [round(min_d + step * i, 2) for i in range(count)]

    def _generate_for_standard(
        self,
        question_service: QuestionService,
        job_std: GenerationJobStandard,
        question_type: str,
        model: Optional[str],
        timeout: int,
        quality_mode: str,
        candidate_count: int,
        max_repair_attempts: int,
        min_review_score: float,
    ) -> int:
        """Generate questions for a single standard with difficulty spread.

        Returns the number of questions successfully created.
        """
        standard = self.db.query(Standard).get(job_std.standard_id)
        if not standard:
            raise ValueError(f"Standard {job_std.standard_id} not found")

        base_difficulty = float(standard.difficulty_base) if standard.difficulty_base is not None else 0.5
        difficulties = self._compute_difficulty_spread(base_difficulty, job_std.questions_requested)

        created = 0
        for target_difficulty in difficulties:
            audit_ids: list[int] = []

            def audit_callback(**kwargs) -> None:
                audit = QuestionGenerationAudit(
                    job_id=job_std.job_id,
                    job_standard_id=job_std.id,
                    standard_id=job_std.standard_id,
                    stage=kwargs.get("stage"),
                    candidate_index=kwargs.get("candidate_index"),
                    attempt=kwargs.get("attempt", 0),
                    status=kwargs.get("status", "completed"),
                    score=kwargs.get("score"),
                    prompt_name=kwargs.get("prompt_name"),
                    model=kwargs.get("model"),
                    request_payload=kwargs.get("request_payload", {}),
                    response_payload=kwargs.get("response_payload", {}),
                    notes=kwargs.get("notes"),
                )
                self.db.add(audit)
                self.db.commit()
                self.db.refresh(audit)
                audit_ids.append(audit.id)

            question_data = question_service.generate_question(
                standard_id=job_std.standard_id,
                difficulty=target_difficulty,
                question_type=question_type,
                model=model,
                timeout=timeout,
                quality_mode=quality_mode,
                candidate_count=candidate_count,
                max_repair_attempts=max_repair_attempts,
                min_review_score=min_review_score,
                audit_callback=audit_callback,
            )

            # Validate required fields before persisting so a malformed
            # or empty LLM response fails loudly instead of silently
            # storing empty strings.
            question_text = question_data.get("question")
            answer = question_data.get("answer")
            if not question_text or not answer:
                raise ValueError(
                    f"Generated question missing required fields: "
                    f"question={question_text!r}, answer={answer!r}"
                )

            # Use LLM's difficulty estimate if present, otherwise the target
            difficulty = question_data.get("difficulty", target_difficulty)

            question = Question(
                standard_id=job_std.standard_id,
                question_text=question_text,
                question_type=question_type,
                options=question_data.get("options"),
                correct_answer=answer,
                explanation=question_data.get("explanation"),
                difficulty=difficulty,
                requires_diagram=question_data.get("requires_diagram", False),
                applet_type=question_data.get("applet_type"),
                geogebra_commands=question_data.get("geogebra_commands"),
                generated_by="admin_job",
                is_active=True,
            )
            self.db.add(question)
            self.db.flush()
            if audit_ids:
                self.db.query(QuestionGenerationAudit).filter(
                    QuestionGenerationAudit.id.in_(audit_ids)
                ).update(
                    {QuestionGenerationAudit.question_id: question.id},
                    synchronize_session=False,
                )
            created += 1

        self.db.commit()
        return created
