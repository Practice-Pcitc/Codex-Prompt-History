ALTER TABLE prompt_records ADD COLUMN source_key TEXT;
CREATE UNIQUE INDEX ix_prompt_records_source_key ON prompt_records(source_key);
CREATE TABLE collector_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    value TEXT NOT NULL
);
CREATE TABLE collector_files (
    path TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    modified_ns INTEGER NOT NULL
);
CREATE TABLE deleted_prompts (
    source_key TEXT PRIMARY KEY
);
CREATE TABLE prompt_library (
    id TEXT PRIMARY KEY,
    source_record_id TEXT,
    kind TEXT NOT NULL CHECK (kind IN ('favorite', 'template')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX ix_prompt_library_updated_at ON prompt_library(updated_at DESC);
CREATE UNIQUE INDEX ix_prompt_library_favorite ON prompt_library(source_record_id)
    WHERE kind = 'favorite' AND source_record_id IS NOT NULL;
