from app.main import app
from app.services.collector import collector
from fastapi.testclient import TestClient


def test_settings_pagination_validation_and_origin(monkeypatch, tmp_path):
    monkeypatch.setenv("PROMPT_HISTORY_DB", str(tmp_path / "api.db"))
    monkeypatch.setattr(collector, "root", tmp_path / "codex")
    with TestClient(app) as client:
        base = "/api/v1/workbench"
        assert client.get(base + "/settings").json()["data"]["projects"] == []
        result = client.put(
            base + "/settings", json={"projects": [str(tmp_path)], "enabled": False}
        )
        assert result.status_code == 200
        assert result.json()["data"]["enabled"] is False
        for endpoint in ("records", "tasks", "library"):
            assert client.get(f"{base}/{endpoint}").json()["data"]["pagination"]["total"] == 0
            assert client.get(f"{base}/{endpoint}?page=0").status_code == 422
        assert client.post(base + "/records/missing/favorites").status_code == 404
        assert client.put(base + "/settings", json={"projects": ["relative"]}).status_code == 422
        assert (
            client.put(
                base + "/settings", json={}, headers={"Origin": "https://example.com"}
            ).status_code
            == 403
        )
