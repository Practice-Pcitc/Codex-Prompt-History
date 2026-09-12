from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

from app.core.errors import DatabaseUnavailableError, RecordNotFoundError
from app.repositories.prompt_history import PromptHistoryRepository

T = TypeVar("T")


class PromptHistoryService:
    def __init__(self, repository: PromptHistoryRepository) -> None:
        self.repository = repository

    def _call(self, operation: Callable[..., T], **filters: Any) -> T:
        try:
            return operation(**filters)
        except (OSError, sqlite3.Error) as exc:
            raise DatabaseUnavailableError() from exc

    def list(
        self,
        *,
        page: int,
        page_size: int,
        project_id: str | None = None,
        project_name: str | None = None,
        keyword: str | None = None,
        session_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        return self._call(
            self.repository.list,
            page=page,
            page_size=page_size,
            project_id=project_id,
            project_name=project_name,
            keyword=keyword,
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
        )

    def list_sessions(
        self,
        *,
        page: int,
        page_size: int,
        project_id: str | None = None,
        project_name: str | None = None,
        session_id: str | None = None,
        status: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        return self._call(
            self.repository.list_sessions,
            page=page,
            page_size=page_size,
            project_id=project_id,
            project_name=project_name,
            session_id=session_id,
            status=status,
            start_time=start_time,
            end_time=end_time,
        )

    def list_tool_events(
        self,
        *,
        page: int,
        page_size: int,
        project_id: str | None = None,
        project_name: str | None = None,
        session_id: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        return self._call(
            self.repository.list_tool_events,
            page=page,
            page_size=page_size,
            project_id=project_id,
            project_name=project_name,
            session_id=session_id,
            tool_name=tool_name,
            status=status,
            start_time=start_time,
            end_time=end_time,
        )

    def get(self, record_id: str) -> dict[str, Any]:
        record = self._call(self.repository.get, record_id=record_id)
        if record is None:
            raise RecordNotFoundError()
        return record

    def stats(self) -> dict[str, int]:
        return self._call(self.repository.stats)

    def projects(self) -> list[dict[str, Any]]:
        return self._call(self.repository.projects)
