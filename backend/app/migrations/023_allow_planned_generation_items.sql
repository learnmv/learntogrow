-- Allow cluster coverage jobs to schedule multiple work items for one standard.
-- Each planned row can target a different difficulty band, or multiple rows can
-- target the same band when an admin asks to top up question counts.

ALTER TABLE generation_job_standards
    DROP CONSTRAINT IF EXISTS generation_job_standards_job_id_standard_id_key;

CREATE INDEX IF NOT EXISTS idx_generation_job_standards_job_standard
    ON generation_job_standards(job_id, standard_id);
