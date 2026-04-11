-- Migration: Add User System Tables
-- For: LearnToGrow
-- Creates: users, parent_student_links, quiz_attempts, password_reset_tokens

-- ============================================
-- Layer: Users and Authentication
-- ============================================

-- User roles enum
CREATE TYPE user_role AS ENUM ('student', 'parent', 'admin');

-- Link status enum
CREATE TYPE link_status AS ENUM ('pending', 'approved', 'rejected');

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Password reset tokens
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Layer: Parent-Student Relationships
-- ============================================

CREATE TABLE parent_student_links (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    status link_status DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    rejected_reason TEXT,
    UNIQUE(parent_id, student_id)
);

-- ============================================
-- Layer: Quiz Tracking (Replaces localStorage)
-- ============================================

CREATE TABLE quiz_attempts (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    standard_id INTEGER REFERENCES standards(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questions(id) ON DELETE SET NULL,
    answers JSONB,  -- {question_id: {selected: "A", correct: true}}
    score INTEGER,
    total_questions INTEGER,
    time_spent_seconds INTEGER,
    completed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Triggers for updated_at
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Indexes for Performance
-- ============================================

-- User lookups
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- Password reset
CREATE INDEX idx_reset_tokens_user ON password_reset_tokens(user_id);
CREATE INDEX idx_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX idx_reset_tokens_expires ON password_reset_tokens(expires_at);

-- Parent-student links
CREATE INDEX idx_links_parent ON parent_student_links(parent_id);
CREATE INDEX idx_links_student ON parent_student_links(student_id);
CREATE INDEX idx_links_status ON parent_student_links(status);
CREATE INDEX idx_links_pending ON parent_student_links(status) WHERE status = 'pending';

-- Quiz attempts
CREATE INDEX idx_attempts_student ON quiz_attempts(student_id);
CREATE INDEX idx_attempts_standard ON quiz_attempts(standard_id);
CREATE INDEX idx_attempts_completed ON quiz_attempts(completed_at);
CREATE INDEX idx_attempts_student_completed ON quiz_attempts(student_id, completed_at DESC);

-- ============================================
-- Seed: First Admin User
-- Run this separately after migration:
-- INSERT INTO users (username, email, hashed_password, role, full_name, is_active)
-- VALUES ('admin', 'admin@learntogrow.local', '<hashed_password>', 'admin', 'System Admin', TRUE);
-- ============================================
