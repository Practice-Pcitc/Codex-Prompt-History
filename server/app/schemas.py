from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


def _to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(word.capitalize() for word in tail)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)


class Pagination(ApiModel):
    page: int
    page_size: int
    total: int


class PromptRecord(ApiModel):
    id: str
    session_id: str | None
    turn_id: str | None
    project_id: str | None
    project_name: str
    working_directory: str
    repository_path: str | None
    prompt: str
    prompt_length: int
    source: str
    model: str | None
    permission_mode: str | None
    git_branch: str | None
    git_commit: str | None
    endpoint_ids: list[str]
    node_ids: list[str]
    created_at: datetime


class PromptListData(ApiModel):
    items: list[PromptRecord]
    pagination: Pagination


class PromptListResponse(ApiModel):
    data: PromptListData


class PromptRecordResponse(ApiModel):
    data: PromptRecord


class PromptStats(ApiModel):
    total_prompt_count: int
    today_prompt_count: int
    project_count: int
    recent_prompt_count: int
    recent_days: int = 7


class PromptStatsResponse(ApiModel):
    data: PromptStats


class PromptProject(ApiModel):
    project_id: str | None
    project_name: str
    prompt_count: int
    last_prompt_at: datetime


class PromptProjectListResponse(ApiModel):
    data: list[PromptProject]


class CodexSession(ApiModel):
    session_id: str
    project_id: str | None
    project_name: str
    working_directory: str
    repository_path: str | None
    model: str | None
    permission_mode: str | None
    git_branch: str | None
    git_commit: str | None
    started_at: datetime
    ended_at: datetime | None
    end_reason: str | None
    status: str
    prompt_count: int
    tool_call_count: int
    updated_at: datetime


class CodexSessionListData(ApiModel):
    items: list[CodexSession]
    pagination: Pagination


class CodexSessionListResponse(ApiModel):
    data: CodexSessionListData


class ToolEvent(ApiModel):
    id: str
    session_id: str | None
    turn_id: str | None
    project_id: str | None
    project_name: str
    working_directory: str
    tool_name: str
    tool_use_id: str | None
    status: str
    duration_ms: float | None
    error_type: str | None
    created_at: datetime


class ToolEventListData(ApiModel):
    items: list[ToolEvent]
    pagination: Pagination


class ToolEventListResponse(ApiModel):
    data: ToolEventListData
