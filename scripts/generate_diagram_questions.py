#!/usr/bin/env python3
"""
Diagram Question Generation Script for LearnToGrow

Generates questions ONLY for standards that require diagrams (requires_diagram=True).
Uses a fixed timeout of 1000 seconds for Ollama calls to allow complex diagram generation.

Usage:
    DATABASE_URL="postgresql://..." python generate_diagram_questions.py --parallel 3 --count 50
    DATABASE_URL="postgresql://..." python generate_diagram_questions.py --parallel 3 --infinite

Environment Variables:
    DATABASE_URL: Required PostgreSQL connection string
    API_BASE_URL: Base URL for the dev API (default: http://localhost:8000)
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional, Set
from dataclasses import dataclass

import httpx
from sqlalchemy import create_engine, Column, Integer, String, Text, Numeric, TIMESTAMP, Boolean, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, Session, sessionmaker
from sqlalchemy.exc import IntegrityError

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_ENDPOINT = f"{API_BASE_URL}/api/v1/questions/generate"

# Fixed timeout for diagram questions (1000 seconds = ~16.7 minutes)
DIAGRAM_TIMEOUT = 1000

if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable is required", file=sys.stderr)
    print("Example: postgresql://user:pass@host:port/learntogrow_dev", file=sys.stderr)
    sys.exit(1)

# SQLAlchemy Setup - Engine created once at module level
Base = declarative_base()
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class Standard(Base):
    __tablename__ = "standards"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    requires_diagram = Column(Boolean, default=False)
    applet_type = Column(String(20))


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False, default="multiple_choice")
    options = Column(JSON)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text)
    difficulty = Column(Numeric(3, 2))
    requires_diagram = Column(Boolean, default=False)
    applet_type = Column(String(20))
    geogebra_commands = Column(JSON)
    applet_config = Column(JSON)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    generated_by = Column(String(100))
    is_active = Column(Boolean, default=True)


@dataclass
class GenerationTask:
    standard_id: int
    standard_code: str
    difficulty: Optional[float]
    applet_type: Optional[str]
    question_type: str = "multiple_choice"


def get_db_session() -> Session:
    return SessionLocal()


def get_diagram_standards(db: Session) -> List[Standard]:
    """Fetch only standards that require diagrams."""
    return db.query(Standard).filter(Standard.requires_diagram == True).all()


def store_question(db: Session, task: GenerationTask, question_data: dict) -> Optional[Question]:
    """Store a generated question. Returns None if duplicate or error."""
    question_text = question_data.get("question", "")
    if not question_text:
        logger.warning(f"Empty question text for standard {task.standard_id}")
        return None

    question = Question(
        standard_id=task.standard_id,
        question_text=question_text,
        question_type=question_data.get("question_type", task.question_type),
        options=question_data.get("options"),
        correct_answer=question_data.get("answer", ""),
        explanation=question_data.get("explanation"),
        difficulty=question_data.get("difficulty", task.difficulty),
        requires_diagram=question_data.get("requires_diagram", True),
        applet_type=question_data.get("applet_type", task.applet_type),
        geogebra_commands=question_data.get("geogebra_commands"),
        applet_config=question_data.get("applet_config"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        generated_by=question_data.get("model", "ollama"),
        is_active=True
    )

    try:
        db.add(question)
        db.commit()
        db.refresh(question)
        return question
    except IntegrityError:
        db.rollback()
        logger.debug(f"Duplicate question (IntegrityError) for standard {task.standard_code}")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error storing question: {e}")
        return None


async def call_generate_api(client: httpx.AsyncClient, task: GenerationTask) -> Optional[dict]:
    """Call the API to generate a diagram question with fixed timeout."""
    payload = {
        "standard_id": task.standard_id,
        "question_type": task.question_type,
        "timeout": DIAGRAM_TIMEOUT  # Fixed 1000 second timeout for diagrams
    }
    if task.difficulty is not None:
        payload["difficulty"] = task.difficulty

    try:
        response = await client.post(
            API_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API HTTP error {e.response.status_code} for standard {task.standard_code}")
        return None
    except httpx.RequestError as e:
        logger.error(f"API request error for standard {task.standard_code}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling API for standard {task.standard_code}: {e}")
        return None


def sync_generate_and_store(task: GenerationTask, question_data: dict) -> bool:
    """Synchronous function to store a question in the database."""
    db = get_db_session()
    try:
        stored = store_question(db, task, question_data)
        if stored:
            logger.info(f"Generated diagram question {stored.id} for standard {task.standard_code} (applet: {task.applet_type})")
            return True
        return False
    finally:
        db.close()


async def process_batch(
    client: httpx.AsyncClient,
    tasks: List[GenerationTask],
    seen_hashes: Set[str]
) -> int:
    """Process a batch of generation tasks."""
    success_count = 0

    for task in tasks:
        question_data = await call_generate_api(client, task)
        if not question_data:
            continue

        question_text = question_data.get("question", "")
        if not question_text:
            continue

        # In-memory duplicate check (fast)
        text_hash = hash(question_text)
        if text_hash in seen_hashes:
            logger.debug(f"Duplicate in batch for standard {task.standard_code}, skipping")
            continue
        seen_hashes.add(text_hash)

        # Store in database (runs in thread pool to not block async loop)
        result = await asyncio.to_thread(sync_generate_and_store, task, question_data)
        if result:
            success_count += 1

    return success_count


def create_tasks_for_standards(
    standards: List[Standard],
    count: int,
    difficulty: Optional[float]
) -> List[GenerationTask]:
    """Create generation tasks distributed across diagram standards."""
    tasks = []
    for i in range(count):
        standard = standards[i % len(standards)]
        tasks.append(GenerationTask(
            standard_id=standard.id,
            standard_code=standard.code,
            difficulty=difficulty,
            applet_type=standard.applet_type,
            question_type="multiple_choice"
        ))
    return tasks


def chunk_tasks(tasks: List[GenerationTask], chunk_size: int) -> List[List[GenerationTask]]:
    return [tasks[i:i + chunk_size] for i in range(0, len(tasks), chunk_size)]


async def run_generation(
    standards: List[Standard],
    total_count: int,
    parallel: int,
    difficulty: Optional[float] = None
) -> int:
    """Run the generation process for diagram questions."""
    logger.info(f"Starting diagram question generation: {total_count} questions, {parallel} parallel, {len(standards)} diagram standards")

    # Log the standards being used
    logger.info(f"Diagram standards: {[s.code for s in standards]}")

    tasks = create_tasks_for_standards(standards, total_count, difficulty)
    batches = chunk_tasks(tasks, parallel)

    total_success = 0
    seen_hashes: Set[str] = set()

    limits = httpx.Limits(max_connections=parallel + 5, max_keepalive_connections=parallel)
    async with httpx.AsyncClient(timeout=DIAGRAM_TIMEOUT + 10, limits=limits) as client:
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i+1}/{len(batches)} ({len(batch)} tasks)")
            success = await process_batch(client, batch, seen_hashes)
            total_success += success

            if (i + 1) % 5 == 0:
                logger.info(f"Progress: {total_success}/{total_count} diagram questions generated")

    return total_success


async def run_infinite_generation(
    standards: List[Standard],
    parallel: int,
    difficulty: Optional[float] = None
) -> None:
    """Run generation continuously for diagram questions."""
    logger.info(f"Starting infinite diagram generation: {parallel} parallel, {len(standards)} diagram standards")
    logger.info(f"Diagram standards: {[s.code for s in standards]}")

    batch_num = 0
    total_success = 0
    seen_hashes: Set[str] = set()

    # Cycle through difficulty levels
    difficulty_levels = [0.3, 0.45, 0.6, 0.75, 0.9]

    limits = httpx.Limits(max_connections=parallel + 5, max_keepalive_connections=parallel)
    async with httpx.AsyncClient(timeout=DIAGRAM_TIMEOUT + 10, limits=limits) as client:
        while True:
            try:
                # Create tasks for this batch
                batch_difficulty = difficulty or difficulty_levels[batch_num % len(difficulty_levels)]
                tasks = [
                    GenerationTask(
                        standard_id=std.id,
                        standard_code=std.code,
                        difficulty=batch_difficulty,
                        applet_type=std.applet_type
                    )
                    for std in standards[:parallel]  # One per standard, up to parallel
                ]

                success = await process_batch(client, tasks, seen_hashes)
                total_success += success
                batch_num += 1

                if batch_num % 10 == 0:
                    logger.info(f"Infinite mode: {total_success} total diagram questions across {batch_num} batches")

                # Clear hash set periodically to prevent unbounded growth
                if batch_num % 100 == 0:
                    seen_hashes.clear()
                    logger.debug("Cleared duplicate hash set")

                await asyncio.sleep(0.5)

            except KeyboardInterrupt:
                logger.info(f"Stopping infinite generation. Total generated: {total_success}")
                break
            except Exception as e:
                logger.error(f"Error in batch {batch_num}: {e}")
                await asyncio.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="Generate diagram questions via API and store in database")
    parser.add_argument("--parallel", type=int, default=3, help="Number of parallel API calls (default: 3)")
    parser.add_argument("--count", type=int, default=50, help="Total number of questions to generate (default: 50)")
    parser.add_argument("--infinite", action="store_true", help="Run continuously generating questions")
    parser.add_argument("--difficulty", type=float, help="Difficulty level (0-1, where 0=easy, 1=hard)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose/debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    db = get_db_session()
    try:
        standards = get_diagram_standards(db)
        if not standards:
            logger.error("No standards with requires_diagram=True found in database")
            sys.exit(1)

        logger.info(f"Found {len(standards)} standards requiring diagrams")

        if args.infinite:
            asyncio.run(run_infinite_generation(standards, args.parallel, args.difficulty))
        else:
            success = asyncio.run(run_generation(standards, args.count, args.parallel, args.difficulty))
            logger.info(f"Generation complete: {success}/{args.count} diagram questions generated")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        db.close()


if __name__ == "__main__":
    main()
