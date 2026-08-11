from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.database import initialize_prompt_history_database
from app.repository import PromptHistoryRepository
from app.schemas import (
    CodexSession,
    CodexSessionListData,
    CodexSessionListResponse,
    Pagination,
    PromptListData,
    PromptListResponse,
    PromptProject,
    PromptProjectListResponse,
    PromptRecord,
    PromptRecordResponse,
    PromptStats,
    PromptStatsResponse,
    ToolEvent,
    ToolEventListData,
    ToolEventListResponse,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_prompt_history_database()
    yield


app = FastAPI(
    title="Codex Prompt History API",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def repository() -> PromptHistoryRepository:
    return PromptHistoryRepository()


def safe_call(method: str, **filters: Any):
    try:
        return getattr(repository(), method)(**filters)
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(status_code=503, detail="Prompt History 数据库暂不可用") from exc


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/prompt-history/stats", response_model=PromptStatsResponse)
def prompt_stats() -> PromptStatsResponse:
    stats = safe_call("stats")
    return PromptStatsResponse(
        data=PromptStats(
            total_prompt_count=stats["total"],
            today_prompt_count=stats["today"],
            project_count=stats["projects"],
            recent_prompt_count=stats["recent"],
        )
    )


@app.get("/api/prompt-history/projects", response_model=PromptProjectListResponse)
def prompt_projects() -> PromptProjectListResponse:
    return PromptProjectListResponse(
        data=[PromptProject.model_validate(item) for item in safe_call("projects")]
    )


@app.get("/api/prompt-history/sessions", response_model=CodexSessionListResponse)
def sessions(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
    project_id: Annotated[str | None, Query(alias="projectId")] = None,
    project_name: Annotated[str | None, Query(alias="projectName", max_length=120)] = None,
    session_id: Annotated[str | None, Query(alias="sessionId", max_length=200)] = None,
    status: Annotated[str | None, Query(pattern="^(active|ended)$")] = None,
    start_time: Annotated[datetime | None, Query(alias="startTime")] = None,
    end_time: Annotated[datetime | None, Query(alias="endTime")] = None,
) -> CodexSessionListResponse:
    items, total = safe_call(
        "list_sessions",
        page=page,
        page_size=page_size,
        project_id=project_id,
        project_name=project_name,
        session_id=session_id,
        status=status,
        start_time=start_time,
        end_time=end_time,
    )
    return CodexSessionListResponse(
        data=CodexSessionListData(
            items=[CodexSession.model_validate(item) for item in items],
            pagination=Pagination(page=page, page_size=page_size, total=total),
        )
    )


@app.get("/api/prompt-history/tool-events", response_model=ToolEventListResponse)
def tool_events(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
    project_id: Annotated[str | None, Query(alias="projectId")] = None,
    project_name: Annotated[str | None, Query(alias="projectName", max_length=120)] = None,
    session_id: Annotated[str | None, Query(alias="sessionId", max_length=200)] = None,
    tool_name: Annotated[str | None, Query(alias="toolName", max_length=200)] = None,
    status: Annotated[str | None, Query(pattern="^(success|failed)$")] = None,
    start_time: Annotated[datetime | None, Query(alias="startTime")] = None,
    end_time: Annotated[datetime | None, Query(alias="endTime")] = None,
) -> ToolEventListResponse:
    items, total = safe_call(
        "list_tool_events",
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
    return ToolEventListResponse(
        data=ToolEventListData(
            items=[ToolEvent.model_validate(item) for item in items],
            pagination=Pagination(page=page, page_size=page_size, total=total),
        )
    )


@app.get("/api/prompt-history", response_model=PromptListResponse)
def prompts(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
    project_id: Annotated[str | None, Query(alias="projectId")] = None,
    project_name: Annotated[str | None, Query(alias="projectName", max_length=120)] = None,
    keyword: Annotated[str | None, Query(max_length=500)] = None,
    session_id: Annotated[str | None, Query(alias="sessionId", max_length=200)] = None,
    start_time: Annotated[datetime | None, Query(alias="startTime")] = None,
    end_time: Annotated[datetime | None, Query(alias="endTime")] = None,
) -> PromptListResponse:
    items, total = safe_call(
        "list",
        page=page,
        page_size=page_size,
        project_id=project_id,
        project_name=project_name,
        keyword=keyword,
        session_id=session_id,
        start_time=start_time,
        end_time=end_time,
    )
    return PromptListResponse(
        data=PromptListData(
            items=[PromptRecord.model_validate(item) for item in items],
            pagination=Pagination(page=page, page_size=page_size, total=total),
        )
    )


@app.get("/api/prompt-history/{record_id}", response_model=PromptRecordResponse)
def prompt_detail(record_id: str) -> PromptRecordResponse:
    record = safe_call("get", record_id=record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Prompt 记录不存在")
    return PromptRecordResponse(data=PromptRecord.model_validate(record))
