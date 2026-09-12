import sqlite3
from importlib.resources import files


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Apply ordered migrations atomically; existing unversioned tables are preserved."""
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )""")
        applied = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
        scripts = sorted(files("history_core.migrations").iterdir(), key=lambda item: item.name)
        for script in scripts:
            if not script.name.endswith(".sql"):
                continue
            version = int(script.name.split("_", 1)[0])
            if version in applied:
                continue
            statement = ""
            for line in script.read_text(encoding="utf-8").splitlines(keepends=True):
                statement += line
                if sqlite3.complete_statement(statement):
                    connection.execute(statement)
                    statement = ""
            if statement.strip():
                raise ValueError(f"Incomplete migration: {script.name}")
            connection.execute(
                "INSERT INTO schema_migrations VALUES "
                "(?, strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now'))",
                (version,),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
