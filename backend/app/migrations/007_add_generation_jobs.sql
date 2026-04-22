-- Migration: Add generation job tracking tables
-- Enables async question generation with per-standard progress and retry.

CREATE TABLE generation_jobs (
    id SERIAL PRIMARY KEY,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    grade_id INTEGER REFERENCES grades(id) ON DELETE SET NULL,
    total_standards INTEGER NOT NULL DEFAULT 0,
    completed_standards INTEGER NOT NULL DEFAULT 0,
    failed_standards INTEGER NOT NULL DEFAULT 0,
    questions_created INTEGER NOT NULL DEFAULT 0,
    errors JSONB DEFAULT '[]'::jsonb,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    question_type VARCHAR(50) DEFAULT 'multiple_choice',
    model VARCHAR(100),
    timeout INTEGER DEFAULT 300,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE generation_job_standards (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES generation_jobs(id) ON DELETE CASCADE,
    standard_id INTEGER REFERENCES standards(id) ON DELETE CASCADE,
    questions_requested INTEGER NOT NULL DEFAULT 1,
    questions_created INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'done', 'failed')),
    error TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(job_id, standard_id)
);

-- Performance indexes
CREATE INDEX idx_generation_jobs_status ON generation_jobs(status);
CREATE INDEX idx_generation_jobs_created_by ON generation_jobs(created_by);
CREATE INDEX idx_generation_job_standards_job_id ON generation_job_standards(job_id);
CREATE INDEX idx_generation_job_standards_status ON generation_job_standards(status);
