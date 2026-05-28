-- Add admin question generation quality pipeline settings and audit trail.

ALTER TABLE generation_jobs
    ADD COLUMN IF NOT EXISTS quality_mode VARCHAR(20) NOT NULL DEFAULT 'reviewed'
        CHECK (quality_mode IN ('fast', 'reviewed', 'quality')),
    ADD COLUMN IF NOT EXISTS candidate_count INTEGER NOT NULL DEFAULT 1 CHECK (candidate_count BETWEEN 1 AND 5),
    ADD COLUMN IF NOT EXISTS max_repair_attempts INTEGER NOT NULL DEFAULT 1 CHECK (max_repair_attempts BETWEEN 0 AND 3),
    ADD COLUMN IF NOT EXISTS min_review_score NUMERIC(4,3) NOT NULL DEFAULT 0.750;

CREATE TABLE IF NOT EXISTS question_generation_audits (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES generation_jobs(id) ON DELETE CASCADE,
    job_standard_id INTEGER REFERENCES generation_job_standards(id) ON DELETE CASCADE,
    standard_id INTEGER REFERENCES standards(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questions(id) ON DELETE SET NULL,
    stage VARCHAR(40) NOT NULL,
    candidate_index INTEGER,
    attempt INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'completed',
    score NUMERIC(4,3),
    prompt_name VARCHAR(80),
    model VARCHAR(100),
    request_payload JSONB DEFAULT '{}'::jsonb,
    response_payload JSONB DEFAULT '{}'::jsonb,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_question_generation_audits_job
    ON question_generation_audits(job_id, created_at);
CREATE INDEX IF NOT EXISTS idx_question_generation_audits_job_standard
    ON question_generation_audits(job_standard_id, created_at);
CREATE INDEX IF NOT EXISTS idx_question_generation_audits_standard
    ON question_generation_audits(standard_id, created_at);
CREATE INDEX IF NOT EXISTS idx_question_generation_audits_stage
    ON question_generation_audits(stage);

INSERT INTO question_prompts (name, content, description)
VALUES
(
    'question_planner',
    'You are planning one curriculum-aligned assessment question.

Return only valid JSON with this shape:
{{
  "skill_focus": "the exact skill to test",
  "grade_language": "language level and vocabulary guidance",
  "misconceptions": ["common student mistake 1", "common student mistake 2", "common student mistake 3"],
  "difficulty_strategy": "how to make this question match the target difficulty",
  "diagram_guidance": "how to use a diagram, or null if no diagram is needed"
}}

Context:
- Grade: {grade_level}
- Standard: {standard_code}
- Standard description: {standard_description}
- Target difficulty: {difficulty}
- Keywords: {keywords}
- Question type: {question_type}
- Requires GeoGebra diagram: {requires_diagram}
- Applet type: {applet_type}

Keep the plan specific enough that a generator can produce a question without inventing unrelated skills.',
    'Plans the target skill, misconceptions, difficulty strategy, and diagram guidance before generation.'
),
(
    'question_reviewer',
    'You are reviewing a generated assessment question for quality.

Return only valid JSON with this shape:
{{
  "approved": true,
  "score": 0.0,
  "alignment_score": 0.0,
  "clarity_score": 0.0,
  "answer_score": 0.0,
  "distractor_score": 0.0,
  "explanation_score": 0.0,
  "difficulty_score": 0.0,
  "diagram_score": null,
  "difficulty_estimate": 0.0,
  "issues": [],
  "improvement_notes": "short notes for an editor"
}}

Review rules:
- The question must directly assess {standard_code}: {standard_description}
- The wording must fit grade {grade_level}.
- For multiple choice, exactly one option must be correct and distractors should reflect plausible misconceptions.
- The explanation must be mathematically/academically correct.
- Target difficulty is {difficulty}; reject if it is far too easy or far too hard.
- Requires GeoGebra diagram: {requires_diagram}; if true, verify the diagram commands support the question.
- Approve only if score is at least {min_review_score} and there are no serious issues.

Question JSON to review:
{question_json}',
    'Reviews generated questions for alignment, clarity, answer validity, distractor quality, explanation quality, and difficulty.'
),
(
    'question_repair',
    'You are repairing a generated assessment question that failed validation or review.

Return only the corrected question JSON. Keep the same JSON shape expected from generation.

Context:
- Grade: {grade_level}
- Standard: {standard_code}
- Standard description: {standard_description}
- Target difficulty: {difficulty}
- Keywords: {keywords}
- Question type: {question_type}
- Requires GeoGebra diagram: {requires_diagram}
- Applet type: {applet_type}
- GeoGebra command guidance: {applet_commands}

Original question JSON:
{question_json}

Problems to fix:
{issues}

Repair requirements:
- Stay aligned to the standard.
- Preserve grade-appropriate language.
- For multiple choice, provide exactly 4 options and exactly one correct answer.
- Make distractors plausible and based on misconceptions.
- Provide a correct explanation.
- If a diagram is required, include valid geogebra_commands that support the question.',
    'Repairs generated question JSON using validation/review issues.'
)
ON CONFLICT (name) DO NOTHING;
