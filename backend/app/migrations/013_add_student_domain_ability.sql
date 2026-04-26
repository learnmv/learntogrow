-- Add student domain ability tracking for adaptive question serving
CREATE TABLE student_domain_ability (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    theta DECIMAL(4,3) NOT NULL DEFAULT 0.35,
    questions_attempted INTEGER DEFAULT 0,
    correct_streak INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, domain_id)
);

CREATE INDEX idx_ability_student ON student_domain_ability(student_id);
CREATE INDEX idx_ability_domain ON student_domain_ability(domain_id);

COMMENT ON TABLE student_domain_ability IS 'Tracks per-student ability per domain using an ELO-like theta score for adaptive question serving';
