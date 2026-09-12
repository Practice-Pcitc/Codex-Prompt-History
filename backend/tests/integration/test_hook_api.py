import sqlite3

import pytest
from app.api.deps import get_prompt_history_service
from app.core.config import PROJECT_ROOT, prompt_history_database_path
from app.main import app
from app.repositories.prompt_history import PromptHistoryRepository
from app.services.prompt_history import PromptHistoryService
from config import HookConfig
from fastapi.testclient import TestClient
from prompt_hook import handle


@pytest.mark.parametrize("configured", [None, "data/custom.db"])
def test_hook_and_api_share_database_from_any_directory(monkeypatch, tmp_path, configured):
    monkeypatch.chdir(tmp_path)
    if configured is None:
        monkeypatch.delenv("PROMPT_HISTORY_DB", raising=False)
    else:
        monkeypatch.setenv("PROMPT_HISTORY_DB", configured)
    expected = PROJECT_ROOT / (configured or "data/prompt_history.db")
    assert prompt_history_database_path() == expected.resolve()
    assert HookConfig.load().database_path == expected.resolve()


def test_hook_record_visible_via_versioned_and_legacy_api(monkeypatch, tmp_path):
    monkeypatch.setenv("PROMPT_HISTORY_DB", str(tmp_path / "history.db"))
    monkeypatch.setenv("PROMPT_HOOK_LOG", str(tmp_path / "hook.log"))
    monkeypatch.setenv("CALLSCOPE_PROJECT_DB", str(tmp_path / "optional.db"))
    monkeypatch.setenv("PROMPT_HOOK_ENABLED", "true")
    record_id = handle(
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "test-session",
            "cwd": str(tmp_path),
            "prompt": "synthetic regression prompt",
        },
        HookConfig.load(),
    )
    assert record_id
    with TestClient(app) as client:
        for prefix in ["/api/v1", "/api"]:
            response = client.get(f"{prefix}/prompt-history/{record_id}")
            assert response.status_code == 200
            assert response.json()["data"]["prompt"] == "synthetic regression prompt"
            for suffix in ["", "/sessions", "/tool-events", "/stats", "/projects"]:
                assert client.get(f"{prefix}/prompt-history{suffix}").status_code == 200
        missing = client.get("/api/v1/prompt-history/missing")
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "PROMPT_NOT_FOUND"
        assert missing.json()["error"]["request_id"] == missing.headers["X-Request-ID"]
        for params in [
            {"page": 0},
            {"pageSize": 101},
            {"startTime": "2026-01-01T00:00:00"},
            {"startTime": "2026-02-01T00:00:00Z", "endTime": "2026-01-01T00:00:00Z"},
        ]:
            response = client.get("/api/v1/prompt-history", params=params)
            assert response.status_code == 422
            assert response.json()["error"]["code"] == "INVALID_REQUEST"
        assert (
            client.get(
                "/api/v1/prompt-history", params={"startTime": "2026-01-01T00:00:00+00:00"}
            ).status_code
            == 200
        )


def test_database_failure_is_sanitized(monkeypatch, tmp_path):
    monkeypatch.setenv("PROMPT_HISTORY_DB", str(tmp_path / "history.db"))

    class BrokenRepository(PromptHistoryRepository):
        def stats(self):
            raise sqlite3.OperationalError("private database path and query")

    app.dependency_overrides[get_prompt_history_service] = lambda: PromptHistoryService(
        BrokenRepository()
    )
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/prompt-history/stats")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert "private database" not in response.text
    finally:
        app.dependency_overrides.clear()
