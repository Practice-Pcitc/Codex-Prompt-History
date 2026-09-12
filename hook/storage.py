from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from history_core.database import initialize_schema
from models import PromptRecord, SessionRecord, ToolEventRecord


class PromptStorage:
    def __init__(self, database_path: Path, *, timeout_seconds: float = 0.2) -> None:
        self.database_path = database_path
        self.timeout_seconds = timeout_seconds
        self._connection: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            self.database_path,
            timeout=self.timeout_seconds,
        )
        connection.execute(f"PRAGMA busy_timeout={int(self.timeout_seconds * 1000)}")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[None]:
        if self._connection is not None:
            raise RuntimeError("Nested Hook transactions are not supported")
        connection = self._connect()
        try:
            initialize_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            self._connection = connection
            yield
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            self._connection = None
            connection.close()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        if self._connection is None:
            raise RuntimeError("Hook writes require an explicit transaction")
        yield self._connection

    def insert(self, record: PromptRecord) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO prompt_records (
                    id, session_id, turn_id, project_id, project_name,
                    working_directory, repository_path, prompt, prompt_length,
                    source, model, permission_mode, git_branch, git_commit,
                    endpoint_ids, node_ids, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.session_id,
                    record.turn_id,
                    record.project_id,
                    record.project_name,
                    record.working_directory,
                    record.repository_path,
                    record.prompt,
                    record.prompt_length,
                    record.source,
                    record.model,
                    record.permission_mode,
                    record.git_branch,
                    record.git_commit,
                    record.endpoint_ids,
                    record.node_ids,
                    record.created_at,
                ),
            )

    def uses_local_collector(self) -> bool:
        """One database uses one capture source, so pause and project scope stay reliable."""
        with self.connection() as connection:
            row = connection.execute("SELECT value FROM collector_settings WHERE id=1").fetchone()
            return bool(row and json.loads(row[0]).get("source_mode") == "local_sessions")

    def start_session(self, record: SessionRecord) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO codex_sessions (
                    session_id, project_id, project_name, working_directory,
                    repository_path, model, permission_mode, git_branch,
                    git_commit, started_at, status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    project_id = COALESCE(excluded.project_id, codex_sessions.project_id),
                    project_name = excluded.project_name,
                    working_directory = excluded.working_directory,
                    repository_path = COALESCE(
                        excluded.repository_path, codex_sessions.repository_path
                    ),
                    model = COALESCE(excluded.model, codex_sessions.model),
                    permission_mode = COALESCE(
                        excluded.permission_mode, codex_sessions.permission_mode
                    ),
                    git_branch = COALESCE(excluded.git_branch, codex_sessions.git_branch),
                    git_commit = COALESCE(excluded.git_commit, codex_sessions.git_commit),
                    status = CASE
                        WHEN codex_sessions.status = 'ended' THEN codex_sessions.status
                        ELSE 'active'
                    END,
                    updated_at = excluded.updated_at
                """,
                (
                    record.session_id,
                    record.project_id,
                    record.project_name,
                    record.working_directory,
                    record.repository_path,
                    record.model,
                    record.permission_mode,
                    record.git_branch,
                    record.git_commit,
                    record.started_at,
                    record.started_at,
                ),
            )

    def increment_session_counter(
        self,
        session_id: str | None,
        *,
        counter: str,
        updated_at: str,
    ) -> None:
        if not session_id:
            return
        if counter not in {"prompt_count", "tool_call_count"}:
            raise ValueError("unsupported session counter")
        with self.connection() as connection:
            connection.execute(
                f"""
                UPDATE codex_sessions
                SET {counter} = {counter} + 1, updated_at = ?
                WHERE session_id = ?
                """,
                (updated_at, session_id),
            )

    def insert_tool_event(self, record: ToolEventRecord) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO codex_tool_events (
                    id, session_id, turn_id, project_id, project_name,
                    working_directory, tool_name, tool_use_id, status,
                    duration_ms, error_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.session_id,
                    record.turn_id,
                    record.project_id,
                    record.project_name,
                    record.working_directory,
                    record.tool_name,
                    record.tool_use_id,
                    record.status,
                    record.duration_ms,
                    record.error_type,
                    record.created_at,
                ),
            )

    def end_session(
        self,
        session_id: str,
        *,
        ended_at: str,
        reason: str | None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE codex_sessions
                SET ended_at = ?, end_reason = ?, status = 'ended', updated_at = ?
                WHERE session_id = ?
                """,
                (ended_at, reason, ended_at, session_id),
            )
