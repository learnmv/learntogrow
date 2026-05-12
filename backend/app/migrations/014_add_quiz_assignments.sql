-- Add parent-created quiz assignments for students.
CREATE TABLE IF NOT EXISTS quiz_assignments (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    grade_id INTEGER REFERENCES grades(id) ON DELETE SET NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    difficulty VARCHAR(20) NOT NULL DEFAULT 'medium'
        CHECK (difficulty IN ('easy', 'medium', 'hard', 'mixed')),
    status VARCHAR(20) NOT NULL DEFAULT 'assigned'
        CHECK (status IN ('assigned', 'in_progress', 'completed')),
    question_count INTEGER NOT NULL DEFAULT 0 CHECK (question_count >= 0),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    due_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quiz_assignment_questions (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES quiz_assignments(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    UNIQUE(assignment_id, question_id),
    UNIQUE(assignment_id, order_index)
);

CREATE INDEX IF NOT EXISTS idx_quiz_assignments_parent ON quiz_assignments(parent_id);
CREATE INDEX IF NOT EXISTS idx_quiz_assignments_student ON quiz_assignments(student_id);
CREATE INDEX IF NOT EXISTS idx_quiz_assignments_status ON quiz_assignments(status);
CREATE INDEX IF NOT EXISTS idx_quiz_assignment_questions_assignment ON quiz_assignment_questions(assignment_id);
