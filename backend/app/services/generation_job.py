"""Service for async question generation jobs."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    GenerationJob,
    GenerationJobStandard,
    JobStatus,
    JobStandardStatus,
    Question,
    Standard,
    User,
)
from app.services.questions import QuestionService

logger = logging.getLogger(__name__)

MAX_CONCURRENT_STANDARDS = 12


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

        job = GenerationJob(
            status=JobStatus.PENDING.value,
            subject_id=subject_id,
            grade_id=grade_id,
            total_standards=len(standard_ids),
            created_by=created_by,
            question_type=question_type,
            model=model,
            timeout=timeout,
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
    ) -> None:
        """Execute a generation job.  Must be called in a background task.

        Creates its own DB session so it can safely run outside the
        request thread.
        """
        db = SessionLocal()
        try:
            QuestionGenerationJobService._do_run(
                db, job_id, question_type, model, timeout
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

def _run_standard_worker(
    job_std_id: int,
    question_type: str,
    model: Optional[str],
    timeout: int,
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
    def _do_run(
        db: Session,
        job_id: int,
        question_type: str,
        model: Optional[str],
        timeout: int,
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

        # Mark running
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        db.commit()

        job_errors: List[str] = []

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

        for i in range(0, len(pending), MAX_CONCURRENT_STANDARDS):
            # Check cancellation before each batch
            db.refresh(job)
            if job.status == JobStatus.CANCELLED.value:
                logger.info(f"Job {job_id} cancelled, stopping")
                break

            batch = pending[i : i + MAX_CONCURRENT_STANDARDS]

            with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                futures = {
                    executor.submit(
                        _run_standard_worker,
                        job_std.id,
                        question_type,
                        model,
                        timeout,
                    ): job_std
                    for job_std in batch
                }

                for future in as_completed(futures):
                    try:
                        standard_id, created, error = future.result()
                        if error:
                            job_errors.append(f"Standard {standard_id}: {error}")
                    except Exception as exc:
                        logger.error(f"Unexpected worker error in job {job_id}: {exc}")
                        job_errors.append(str(exc))

            # Recompute aggregates from DB after each batch
            job = db.query(GenerationJob).get(job_id)
            if not job:
                break
            summary = (
                db.query(GenerationJobStandard)
                .filter(GenerationJobStandard.job_id == job_id)
                .all()
            )
            job.completed_standards = sum(
                1 for js in summary if js.status == JobStandardStatus.DONE.value
            )
            job.failed_standards = sum(
                1 for js in summary if js.status == JobStandardStatus.FAILED.value
            )
            job.questions_created = sum(
                (js.questions_created or 0) for js in summary
            )
            db.commit()

        # Finalise job
        db.refresh(job)
        if job.status == JobStatus.CANCELLED.value:
            return

        job = db.query(GenerationJob).get(job_id)
        if not job:
            return

        summary = (
            db.query(GenerationJobStandard)
            .filter(GenerationJobStandard.job_id == job_id)
            .all()
        )
        job.completed_standards = sum(
            1 for js in summary if js.status == JobStandardStatus.DONE.value
        )
        job.failed_standards = sum(
            1 for js in summary if js.status == JobStandardStatus.FAILED.value
        )
        job.questions_created = sum(
            (js.questions_created or 0) for js in summary
        )
        job.errors = job_errors
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

    def _generate_for_standard(
        self,
        question_service: QuestionService,
        job_std: GenerationJobStandard,
        question_type: str,
        model: Optional[str],
        timeout: int,
    ) -> int:
        """Generate questions for a single standard.

        Returns the number of questions successfully created.
        """
        created = 0
        for _ in range(job_std.questions_requested):
            question_data = question_service.generate_question(
                standard_id=job_std.standard_id,
                question_type=question_type,
                model=model,
                timeout=timeout,
            )

            question = Question(
                standard_id=job_std.standard_id,
                question_text=question_data.get("question", ""),
                question_type=question_type,
                options=question_data.get("options"),
                correct_answer=question_data.get("answer", ""),
                explanation=question_data.get("explanation", ""),
                difficulty=question_data.get("difficulty", 0.5),
                requires_diagram=question_data.get("requires_diagram", False),
                applet_type=question_data.get("applet_type"),
                geogebra_commands=question_data.get("geogebra_commands"),
                applet_config=question_data.get("applet_config"),
                generated_by="admin_job",
                is_active=True,
            )
            self.db.add(question)
            created += 1

        self.db.commit()
        return created
