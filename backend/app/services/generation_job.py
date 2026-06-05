"""Service for async question generation jobs."""

import logging
import time
from sqlalchemy import func
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, List, Optional, Tuple

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
    Cluster,
    Standard,
)
from app.services.questions import QuestionService

logger = logging.getLogger(__name__)

MAX_CONCURRENT_QUESTION_WORKERS = 15

DIFFICULTY_BANDS = {
    "easy": (0.15, 0.35, 0.25),
    "medium": (0.35, 0.55, 0.45),
    "hard": (0.55, 0.70, 0.62),
    "challenge": (0.70, 0.85, 0.78),
    "expert": (0.85, 0.95, 0.92),
}

COVERAGE_GOAL_BANDS = {
    "fill_missing": ["easy", "medium", "hard", "challenge", "expert"],
    "full_ladder": ["easy", "medium", "hard", "challenge", "expert"],
    "top_up": ["easy", "medium", "hard", "challenge", "expert"],
    "challenge_heavy": ["hard", "challenge", "expert"],
}


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

    def create_planned_job(
        self,
        plan_items: list[dict[str, Any]],
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
        """Create a generation job from explicit standard+difficulty plan items."""
        if not plan_items:
            raise ValueError("Coverage plan has no generation items")

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
            total_standards=len(plan_items),
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
        self.db.flush()

        for item in plan_items:
            job_std = GenerationJobStandard(
                job_id=job.id,
                standard_id=int(item["standard_id"]),
                cluster_id=item.get("cluster_id"),
                questions_requested=1,
                status=JobStandardStatus.PENDING.value,
                target_difficulty=item.get("target_difficulty"),
                difficulty_band=item.get("difficulty_band"),
                generation_reason=item.get("reason"),
            )
            self.db.add(job_std)

        self.db.commit()
        self.db.refresh(job)
        return job

    def build_cluster_coverage_plan(
        self,
        grade_id: int,
        cluster_ids: list[int],
        coverage_goal: str = "fill_missing",
        target_per_band: int = 1,
    ) -> dict[str, Any]:
        """Plan cluster generation by standard and difficulty band."""
        if coverage_goal not in COVERAGE_GOAL_BANDS:
            coverage_goal = "fill_missing"
        target_per_band = max(1, min(5, target_per_band))
        clusters = (
            self.db.query(Cluster)
            .filter(Cluster.grade_id == grade_id, Cluster.id.in_(cluster_ids))
            .order_by(Cluster.code)
            .all()
        )
        if not clusters:
            raise ValueError("No clusters found for the selected grade")

        standards = (
            self.db.query(Standard)
            .filter(
                Standard.grade_id == grade_id,
                Standard.cluster_id.in_([cluster.id for cluster in clusters]),
            )
            .order_by(Standard.code)
            .all()
        )
        if not standards:
            raise ValueError("No standards found for the selected clusters")

        cluster_map = {cluster.id: cluster for cluster in clusters}
        items: list[dict[str, Any]] = []
        standards_report: list[dict[str, Any]] = []
        filled_cells = 0
        total_cells = 0
        bands = COVERAGE_GOAL_BANDS[coverage_goal]

        for standard in standards:
            band_counts = self._question_counts_by_band(standard.id)
            missing_bands = []
            for band in DIFFICULTY_BANDS:
                total_cells += 1
                if band_counts.get(band, 0) > 0:
                    filled_cells += 1
            for band in bands:
                existing = band_counts.get(band, 0)
                desired = target_per_band
                should_generate = False
                if coverage_goal == "full_ladder":
                    should_generate = True
                    desired = 1
                elif coverage_goal in {"fill_missing", "challenge_heavy"}:
                    should_generate = existing == 0
                    desired = 1
                elif coverage_goal == "top_up":
                    should_generate = existing < target_per_band

                if should_generate:
                    needed = max(1, desired - existing) if coverage_goal == "top_up" else 1
                    missing_bands.append(band)
                    for _ in range(needed):
                        target = self._target_for_band(standard, band)
                        cluster = cluster_map.get(standard.cluster_id)
                        items.append(
                            {
                                "standard_id": standard.id,
                                "standard_code": standard.code,
                                "standard_description": standard.description,
                                "cluster_id": standard.cluster_id,
                                "cluster_code": cluster.code if cluster else None,
                                "cluster_name": cluster.name if cluster else None,
                                "difficulty_band": band,
                                "target_difficulty": target,
                                "existing_count": existing,
                                "reason": self._coverage_reason(coverage_goal, band, existing, target_per_band),
                            }
                        )

            cluster = cluster_map.get(standard.cluster_id)
            standards_report.append(
                {
                    "standard_id": standard.id,
                    "standard_code": standard.code,
                    "standard_description": standard.description,
                    "cluster_id": standard.cluster_id,
                    "cluster_code": cluster.code if cluster else None,
                    "cluster_name": cluster.name if cluster else None,
                    "band_counts": band_counts,
                    "planned_bands": missing_bands,
                    "planned_count": sum(1 for item in items if item["standard_id"] == standard.id),
                }
            )

        cluster_reports = []
        for cluster in clusters:
            cluster_standards = [
                report for report in standards_report if report["cluster_id"] == cluster.id
            ]
            planned_count = sum(report["planned_count"] for report in cluster_standards)
            cluster_reports.append(
                {
                    "cluster_id": cluster.id,
                    "cluster_code": cluster.code,
                    "cluster_name": cluster.name,
                    "standard_count": len(cluster_standards),
                    "planned_count": planned_count,
                }
            )

        coverage_before = round((filled_cells / total_cells) * 100, 1) if total_cells else 0
        projected_filled = min(total_cells, filled_cells + len({
            (item["standard_id"], item["difficulty_band"]) for item in items
        }))
        coverage_after = round((projected_filled / total_cells) * 100, 1) if total_cells else 0
        return {
            "coverage_goal": coverage_goal,
            "grade_id": grade_id,
            "cluster_ids": [cluster.id for cluster in clusters],
            "difficulty_bands": [
                {
                    "band": band,
                    "min": DIFFICULTY_BANDS[band][0],
                    "max": DIFFICULTY_BANDS[band][1],
                    "target": DIFFICULTY_BANDS[band][2],
                }
                for band in DIFFICULTY_BANDS
            ],
            "coverage_before": coverage_before,
            "coverage_after": coverage_after,
            "total_planned": len(items),
            "estimated_generation_time": self._estimate_generation_time(len(items)),
            "clusters": cluster_reports,
            "standards": standards_report,
            "items": items,
        }

    def _question_counts_by_band(self, standard_id: int) -> dict[str, int]:
        rows = (
            self.db.query(Question.difficulty, func.count(Question.id))
            .filter(Question.standard_id == standard_id, Question.is_active == True)
            .group_by(Question.difficulty)
            .all()
        )
        counts = {band: 0 for band in DIFFICULTY_BANDS}
        for difficulty, count in rows:
            band = self._band_for_difficulty(float(difficulty or 0.5))
            counts[band] += int(count or 0)
        return counts

    def _band_for_difficulty(self, difficulty: float) -> str:
        for band, (low, high, _) in DIFFICULTY_BANDS.items():
            if low <= difficulty < high or (band == "expert" and difficulty <= high):
                return band
        if difficulty < 0.15:
            return "easy"
        return "expert"

    def _target_for_band(self, standard: Standard, band: str) -> float:
        target = DIFFICULTY_BANDS[band][2]
        base = float(standard.difficulty_base or target)
        if band == "easy":
            target = min(target, max(0.15, base - 0.25))
        elif band == "medium":
            target = min(max(target, base - 0.10), base + 0.05)
        elif band == "hard":
            target = max(target, base + 0.10)
        elif band == "challenge":
            target = max(target, base + 0.25)
        elif band == "expert":
            target = max(target, base + 0.35)
        return round(max(0.05, min(0.95, target)), 2)

    def _coverage_reason(self, goal: str, band: str, existing: int, target_per_band: int) -> str:
        if goal == "full_ladder":
            return f"Full ladder requested: add one {band} question"
        if goal == "top_up":
            return f"{band.title()} band has {existing}; target is {target_per_band}"
        if goal == "challenge_heavy":
            return f"Challenge-heavy coverage missing {band} band"
        return f"No active {band} questions exist for this standard"

    def _estimate_generation_time(self, item_count: int) -> str:
        if item_count <= 0:
            return "No generation needed"
        low_minutes = max(1, round(item_count * 0.4))
        high_minutes = max(low_minutes, round(item_count * 0.9))
        return f"{low_minutes}-{high_minutes} min"

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
            candidate_count=original.candidate_count if original.candidate_count is not None else 1,
            max_repair_attempts=(
                original.max_repair_attempts
                if original.max_repair_attempts is not None
                else 1
            ),
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
    def _run_question_worker(
        job_std_id: int,
        target_difficulty: float,
        question_index: int,
        question_type: str,
        model: Optional[str],
        timeout: int,
        quality_mode: str,
        candidate_count: int,
        max_repair_attempts: int,
        min_review_score: float,
    ) -> Tuple[int, int, int, int, Optional[str], float]:
        """Generate and persist one question in its own thread + DB session.

        Returns (job_standard_id, standard_id, question_index, created, error, elapsed_seconds).
        """
        started_at = time.perf_counter()
        db = SessionLocal()
        job_std: Optional[GenerationJobStandard] = None
        try:
            job_std = db.query(GenerationJobStandard).get(job_std_id)
            if not job_std:
                return (job_std_id, 0, question_index, 0, "Job standard not found", 0.0)
            question_service = QuestionService(db)

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
                db.add(audit)
                db.commit()
                db.refresh(audit)
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

            question_text = question_data.get("question")
            answer = question_data.get("answer")
            if not question_text or not answer:
                raise ValueError(
                    f"Generated question missing required fields: "
                    f"question={question_text!r}, answer={answer!r}"
                )
            question_service.lock_standard_question_bank(job_std.standard_id)
            question_service.assert_not_duplicate_question(job_std.standard_id, question_data)

            question = Question(
                standard_id=job_std.standard_id,
                question_text=question_text,
                question_type=question_type,
                options=question_data.get("options"),
                correct_answer=answer,
                explanation=question_data.get("explanation"),
                stimulus=question_data.get("stimulus"),
                difficulty=question_data.get("difficulty", target_difficulty),
                generation_signature=question_data.get("generation_signature"),
                math_spec=question_data.get("math_spec"),
                semantic_hash=question_data.get("semantic_hash"),
                quality_score=question_data.get("quality_score"),
                generated_by="admin_job",
                is_active=True,
            )
            db.add(question)
            db.flush()
            if audit_ids:
                db.query(QuestionGenerationAudit).filter(
                    QuestionGenerationAudit.id.in_(audit_ids)
                ).update(
                    {QuestionGenerationAudit.question_id: question.id},
                    synchronize_session=False,
                )

            db.commit()
            elapsed = time.perf_counter() - started_at
            logger.info(
                "Generated job standard %s question %s for standard %s in %.2fs",
                job_std.id,
                question_index + 1,
                job_std.standard_id,
                elapsed,
            )
            return (job_std.id, job_std.standard_id, question_index, 1, None, elapsed)
        except Exception as exc:
            elapsed = time.perf_counter() - started_at
            db.rollback()
            sid = job_std.standard_id if job_std else 0
            logger.error(
                "Question worker failed for job standard %s question %s after %.2fs: %s",
                job_std_id,
                question_index + 1,
                elapsed,
                exc,
            )
            return (job_std_id, sid, question_index, 0, str(exc), elapsed)
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
        job_started_at = time.perf_counter()

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

        for job_std in pending:
            job_std.status = JobStandardStatus.RUNNING.value
            job_std.started_at = datetime.utcnow()
            job_std.completed_at = None
            job_std.error = None
            job_std.questions_created = 0
        db.commit()

        question_work: list[tuple[int, int, float, int]] = []
        for job_std in pending:
            standard = job_std.standard
            base_difficulty = (
                float(standard.difficulty_base)
                if standard and standard.difficulty_base is not None
                else 0.5
            )
            if job_std.target_difficulty is not None:
                difficulties = [float(job_std.target_difficulty)] * job_std.questions_requested
            else:
                difficulties = service._compute_difficulty_spread(base_difficulty, job_std.questions_requested)
            for question_index, target_difficulty in enumerate(difficulties):
                question_work.append((job_std.id, job_std.standard_id, target_difficulty, question_index))

        work_totals = {job_std.id: job_std.questions_requested for job_std in pending}
        work_finished = {job_std.id: 0 for job_std in pending}
        worker_durations: list[float] = []
        logger.info(
            "Job %s starting %s question work items across %s standards",
            job_id,
            len(question_work),
            len(pending),
        )

        settings = get_settings()
        max_workers = max(1, min(MAX_CONCURRENT_QUESTION_WORKERS, settings.OLLAMA_GENERATION_WORKERS))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(
                    QuestionGenerationJobService._run_question_worker,
                    job_std_id,
                    target_difficulty,
                    question_index,
                    resolved_question_type,
                    resolved_model,
                    resolved_timeout,
                    resolved_quality_mode,
                    resolved_candidate_count,
                    resolved_repairs,
                    resolved_min_score,
                ): (job_std_id, standard_id, question_index)
                for job_std_id, standard_id, target_difficulty, question_index in question_work
            }

            for future in as_completed(future_map):
                job_std_id, standard_id, question_index = future_map[future]
                try:
                    result_job_std_id, standard_id, result_index, created, error, elapsed = future.result()
                    job_std_id = result_job_std_id or job_std_id
                    question_index = result_index
                    worker_durations.append(elapsed)
                    job_std = db.query(GenerationJobStandard).get(job_std_id)
                    if job_std:
                        work_finished[job_std_id] = work_finished.get(job_std_id, 0) + 1
                        if created:
                            job_std.questions_created = (job_std.questions_created or 0) + created
                        if error:
                            message = f"Question {question_index + 1}: {error}"
                            job_std.error = (
                                f"{job_std.error}\n{message}" if job_std.error else message
                            )[:1000]
                        if work_finished[job_std_id] >= work_totals.get(job_std_id, 0):
                            job_std.completed_at = datetime.utcnow()
                            if (job_std.questions_created or 0) >= job_std.questions_requested:
                                job_std.status = JobStandardStatus.DONE.value
                            else:
                                job_std.status = JobStandardStatus.FAILED.value
                                if not job_std.error:
                                    job_std.error = (
                                        f"Generated {job_std.questions_created or 0} of "
                                        f"{job_std.questions_requested} requested questions"
                                    )
                        db.commit()
                    if error:
                        logger.error(f"Standard {standard_id} question {question_index + 1} failed: {error}")
                except Exception as exc:
                    logger.error(f"Unexpected worker error in job {job_id}: {exc}")

                # Update parent job counters incrementally after each question.
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
        elapsed = time.perf_counter() - job_started_at
        avg_worker_seconds = (
            sum(worker_durations) / len(worker_durations)
            if worker_durations
            else 0
        )
        questions_per_minute = (
            (job.questions_created / elapsed) * 60
            if elapsed > 0
            else 0
        )
        logger.info(
            f"Job {job_id} finished: {job.completed_standards}/{job.total_standards} "
            f"completed, {job.failed_standards} failed, {job.questions_created} questions "
            f"in {elapsed:.2f}s ({questions_per_minute:.2f} questions/min, "
            f"avg worker {avg_worker_seconds:.2f}s)"
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
