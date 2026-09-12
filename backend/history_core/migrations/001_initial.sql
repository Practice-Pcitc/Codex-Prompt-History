CREATE TABLE IF NOT EXISTS prompt_records (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    turn_id TEXT,
    project_id TEXT,
    project_name TEXT NOT NULL,
    working_directory TEXT NOT NULL,
    repository_path TEXT,
    prompt TEXT NOT NULL,
    prompt_length INTEGER NOT NULL,
    source TEXT NOT NULL,
    model TEXT,
    permission_mode TEXT,
    git_branch TEXT,
    git_commit TEXT,
    endpoint_ids TEXT NOT NULL DEFAULT '[]',
    node_ids TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_prompt_records_created_at
    ON prompt_records(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_prompt_records_project_name
    ON prompt_records(project_name);
CREATE INDEX IF NOT EXISTS ix_prompt_records_project_id
    ON prompt_records(project_id);
CREATE INDEX IF NOT EXISTS ix_prompt_records_session_id
    ON prompt_records(session_id);
CREATE TABLE IF NOT EXISTS codex_sessions (
    session_id TEXT PRIMARY KEY,
    project_id TEXT,
    project_name TEXT NOT NULL,
    working_directory TEXT NOT NULL,
    repository_path TEXT,
    model TEXT,
    permission_mode TEXT,
    git_branch TEXT,
    git_commit TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    end_reason TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    prompt_count INTEGER NOT NULL DEFAULT 0,
    tool_call_count INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_codex_sessions_started_at
    ON codex_sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS ix_codex_sessions_project_id
    ON codex_sessions(project_id);
CREATE TABLE IF NOT EXISTS codex_tool_events (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    turn_id TEXT,
    project_id TEXT,
    project_name TEXT NOT NULL,
    working_directory TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    tool_use_id TEXT,
    status TEXT NOT NULL,
    duration_ms REAL,
    error_type TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_codex_tool_events_created_at
    ON codex_tool_events(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_codex_tool_events_session_id
    ON codex_tool_events(session_id);
CREATE INDEX IF NOT EXISTS ix_codex_tool_events_tool_name
    ON codex_tool_events(tool_name);
