-- Store spec-first generation metadata for question bank diversity.

ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS generation_signature JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS math_spec JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS semantic_hash VARCHAR(128),
    ADD COLUMN IF NOT EXISTS quality_score NUMERIC(4,3);

CREATE INDEX IF NOT EXISTS idx_questions_semantic_hash
    ON questions(semantic_hash);

CREATE INDEX IF NOT EXISTS idx_questions_generation_signature_gin
    ON questions USING GIN (generation_signature);
