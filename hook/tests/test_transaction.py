import sqlite3

import pytest
from config import HookConfig
from prompt_hook import handle
from storage import PromptStorage


def test_counter_failure_rolls_back_entire_event(tmp_path, monkeypatch):
    config = HookConfig(
        True, False, tmp_path / "history.db", tmp_path / "optional.db", tmp_path / "hook.log"
    )

    def fail(*args, **kwargs):
        raise sqlite3.OperationalError("synthetic failure")

    monkeypatch.setattr(PromptStorage, "increment_session_counter", fail)
    with pytest.raises(sqlite3.OperationalError):
        handle(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "rollback",
                "cwd": str(tmp_path),
                "prompt": "synthetic",
            },
            config,
        )
    with sqlite3.connect(config.database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM prompt_records").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM codex_sessions").fetchone()[0] == 0
