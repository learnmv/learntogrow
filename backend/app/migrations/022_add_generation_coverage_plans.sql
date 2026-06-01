-- Store optional per-work-item difficulty metadata for cluster coverage generation.

ALTER TABLE generation_job_standards
    ADD COLUMN IF NOT EXISTS target_difficulty NUMERIC(4,3),
    ADD COLUMN IF NOT EXISTS difficulty_band VARCHAR(20),
    ADD COLUMN IF NOT EXISTS generation_reason TEXT,
    ADD COLUMN IF NOT EXISTS cluster_id INTEGER REFERENCES clusters(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_generation_job_standards_cluster
    ON generation_job_standards(cluster_id);

CREATE INDEX IF NOT EXISTS idx_generation_job_standards_difficulty_band
    ON generation_job_standards(difficulty_band);
