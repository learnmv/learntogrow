-- Migration 003: Add answered_questions table for tracking student answers
-- This prevents repeating questions for logged-in students

CREATE TABLE IF NOT EXISTS answered_questions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    standard_id INTEGER NOT NULL REFERENCES standards(id) ON DELETE CASCADE,
    selected_answer TEXT,
    is_correct BOOLEAN NOT NULL,
    answered_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, question_id)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_answered_student ON answered_questions(student_id);
CREATE INDEX IF NOT EXISTS idx_answered_question ON answered_questions(question_id);
CREATE INDEX IF NOT EXISTS idx_answered_student_standard ON answered_questions(student_id, standard_id);
CREATE INDEX IF NOT EXISTS idx_answered_student_answered ON answered_questions(student_id, answered_at DESC);