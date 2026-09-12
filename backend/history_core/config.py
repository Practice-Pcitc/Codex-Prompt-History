import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_project_path(name: str, default: str) -> Path:
    path = Path(os.getenv(name) or default).expanduser()
    return (path if path.is_absolute() else PROJECT_ROOT / path).resolve()


def prompt_history_database_path() -> Path:
    return resolve_project_path("PROMPT_HISTORY_DB", "data/prompt_history.db")
