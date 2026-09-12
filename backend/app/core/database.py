from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from history_core.database import initialize_schema

from app.core.config import prompt_history_database_path


@contextmanager
def prompt_history_connection() -> Iterator[sqlite3.Connection]:
    path = prompt_history_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=1.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=1000")
    try:
        yield connection
    finally:
        connection.close()


def initialize_prompt_history_database() -> None:
    with prompt_history_connection() as connection:
        initialize_schema(connection)
