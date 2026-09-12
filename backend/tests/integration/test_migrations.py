import sqlite3

import pytest
from history_core import database
from history_core.database import initialize_schema


def test_existing_database_is_preserved_and_migration_is_idempotent(tmp_path):
    with sqlite3.connect(tmp_path / "history.db") as connection:
        initialize_schema(connection)
        connection.execute(
            "INSERT INTO codex_sessions (session_id, project_name, working_directory, "
            "started_at, updated_at) VALUES ('preserved', 'sample', '.', 'now', 'now')"
        )
        connection.commit()
        initialize_schema(connection)
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 2
        assert (
            connection.execute("SELECT session_id FROM codex_sessions").fetchone()[0] == "preserved"
        )


def test_failed_migration_rolls_back_all_changes(tmp_path, monkeypatch):
    scripts = tmp_path / "migrations"
    scripts.mkdir()
    (scripts / "001_broken.sql").write_text("CREATE TABLE example (id INTEGER);\nINVALID SQL;\n")
    monkeypatch.setattr(database, "files", lambda _: scripts)
    with sqlite3.connect(tmp_path / "failed.db") as connection:
        with pytest.raises(sqlite3.Error):
            initialize_schema(connection)
        assert (
            connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []
        )
