from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from history_core.config import resolve_project_path


def _as_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


@dataclass(frozen=True, slots=True)
class HookConfig:
    enabled: bool
    redaction_enabled: bool
    database_path: Path
    project_database_path: Path
    log_path: Path
    sqlite_timeout_seconds: float = 0.2

    @classmethod
    def load(cls) -> HookConfig:
        return cls(
            enabled=_as_bool(os.getenv("PROMPT_HOOK_ENABLED"), default=True),
            redaction_enabled=_as_bool(os.getenv("PROMPT_REDACTION_ENABLED"), default=False),
            database_path=resolve_project_path("PROMPT_HISTORY_DB", "data/prompt_history.db"),
            project_database_path=resolve_project_path("CALLSCOPE_PROJECT_DB", "data/callscope.db"),
            log_path=resolve_project_path("PROMPT_HOOK_LOG", "logs/prompt-hook.log"),
        )
