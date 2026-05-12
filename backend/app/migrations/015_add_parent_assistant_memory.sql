-- Add persistent parent assistant conversation memory and tool audit trail.
CREATE TABLE IF NOT EXISTS parent_assistant_threads (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(150),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS parent_assistant_messages (
    id SERIAL PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES parent_assistant_threads(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('parent', 'assistant', 'system')),
    content TEXT NOT NULL,
    intent VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS parent_assistant_tool_calls (
    id SERIAL PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES parent_assistant_threads(id) ON DELETE CASCADE,
    message_id INTEGER REFERENCES parent_assistant_messages(id) ON DELETE SET NULL,
    tool_name VARCHAR(80) NOT NULL,
    arguments JSONB NOT NULL DEFAULT '{}'::jsonb,
    result JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed')),
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_parent_assistant_threads_parent
    ON parent_assistant_threads(parent_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_parent_assistant_messages_thread
    ON parent_assistant_messages(thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_parent_assistant_tool_calls_thread
    ON parent_assistant_tool_calls(thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_parent_assistant_tool_calls_tool
    ON parent_assistant_tool_calls(tool_name);
