from typing import Literal

from pydantic import Field, field_validator

from app.schemas.prompt import ApiModel, Pagination


class RecordingSettings(ApiModel):
    enabled: bool = True
    all_projects: bool = True
    projects: list[str] = Field(default_factory=list, max_length=100)
    excluded_projects: list[str] = Field(default_factory=list, max_length=100)
    redact: bool = True

    @field_validator("projects", "excluded_projects")
    @classmethod
    def validate_paths(cls, paths: list[str]) -> list[str]:
        from pathlib import Path

        result = []
        for value in paths:
            if not Path(value).is_absolute():
                raise ValueError("Project paths must be absolute")
            path = str(Path(value).resolve())
            if path not in result:
                result.append(path)
        return result


class LibraryInput(ApiModel):
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=100_000)
    tags: list[str] = Field(default_factory=list, max_length=12)
    note: str = Field(default="", max_length=2000)

    @field_validator("title", "content")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be blank")
        return value.strip()

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, tags: list[str]) -> list[str]:
        return list(dict.fromkeys(tag.strip()[:30] for tag in tags if tag.strip()))


class LibraryItem(LibraryInput):
    id: str
    source_record_id: str | None
    kind: Literal["favorite", "template"]
    created_at: str
    updated_at: str


class RecordItem(ApiModel):
    id: str
    session_id: str | None
    project_name: str
    working_directory: str
    prompt: str
    created_at: str
    source: str
    favorite_id: str | None = None


class TaskItem(ApiModel):
    session_id: str
    title: str
    project_name: str
    working_directory: str
    count: int
    updated_at: str
    latest_prompt: str = ""


class PageData(ApiModel):
    items: list[RecordItem]
    pagination: Pagination


class RecordsResponse(ApiModel):
    data: PageData


class TaskPage(ApiModel):
    items: list[TaskItem]
    pagination: Pagination


class TasksResponse(ApiModel):
    data: TaskPage


class LibraryPage(ApiModel):
    items: list[LibraryItem]
    pagination: Pagination


class LibraryResponse(ApiModel):
    data: LibraryPage


class LibraryItemResponse(ApiModel):
    data: LibraryItem


class SettingsResponse(ApiModel):
    data: RecordingSettings


class ActionResponse(ApiModel):
    data: bool = True


class SourceProject(ApiModel):
    path: str
    name: str


class CollectorStatus(ApiModel):
    state: Literal["waiting", "recording", "paused", "missing", "error"]
    source_path: str
    last_scan_at: str | None = None
    last_record_at: str | None = None
    error: str | None = None
    imported: int = 0
    ignored_lines: int = 0
    excluded_sessions: int = 0
    cleaned_records: int = 0
    available_projects: list[SourceProject] = Field(default_factory=list)


class StatusResponse(ApiModel):
    data: CollectorStatus


class ProjectOverview(ApiModel):
    path: str
    name: str
    records: int
    tasks: int
    last_record_at: str


class Overview(ApiModel):
    records: int
    tasks: int
    library: int
    projects: list[ProjectOverview]


class OverviewResponse(ApiModel):
    data: Overview
