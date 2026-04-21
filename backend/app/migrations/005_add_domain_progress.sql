-- Migration: Add domain_progress table for adaptive learning
-- Tracks student performance per domain to enable adaptive question selection

CREATE TABLE domain_progress (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    total_answered INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    accuracy DECIMAL(5,4) NOT NULL DEFAULT 0.0,
    current_difficulty DECIMAL(3,2) NOT NULL DEFAULT 0.5 CHECK (current_difficulty BETWEEN 0.00 AND 1.00),
    last_answered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, domain_id)
);

-- Indexes for performance
CREATE INDEX idx_domain_progress_student ON domain_progress(student_id);
CREATE INDEX idx_domain_progress_domain ON domain_progress(domain_id);
CREATE INDEX idx_domain_progress_accuracy ON domain_progress(accuracy);
