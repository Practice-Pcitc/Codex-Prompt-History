from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import prompt_history_database_path
from app.core.database import initialize_prompt_history_database
from app.main import app
from fastapi.testclient import TestClient


def test_prompt_history_api_is_standalone(monkeypatch, tmp_path) -> None:
    database = tmp_path / "prompt_history.db"
    monkeypatch.setenv("PROMPT_HISTORY_DB", str(database))
    initialize_prompt_history_database()
    now = datetime.now(UTC).isoformat()

    with sqlite3.connect(prompt_history_database_path()) as connection:
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
                str(uuid4()),
                "session-1",
                "turn-1",
                None,
                "standalone-project",
                str(tmp_path),
                str(tmp_path),
                "独立 Hook 测试",
                10,
                "codex_user_prompt_submit",
                "test-model",
                "default",
                "main",
                "abc123",
                "[]",
                "[]",
                now,
            ),
        )

    with TestClient(app) as client:
        health = client.get("/api/health")
        result = client.get(
            "/api/prompt-history",
            params={"projectName": "standalone-project"},
        )

    assert health.json() == {"status": "ok"}
    assert result.status_code == 200
    assert result.json()["data"]["pagination"]["total"] == 1
    assert result.json()["data"]["items"][0]["prompt"] == "独立 Hook 测试"
