from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_prompt_history_service
from app.schemas.common import ErrorResponse, HealthResponse
from app.schemas.prompt import (
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
from app.schemas.requests import PromptFilters, SessionFilters, ToolEventFilters
from app.services.prompt_history import PromptHistoryService

router = APIRouter(responses={code: {"model": ErrorResponse} for code in (404, 422, 500, 503)})


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/prompt-history/stats", response_model=PromptStatsResponse)
def prompt_stats(
    service: Annotated[PromptHistoryService, Depends(get_prompt_history_service)],
) -> PromptStatsResponse:
    stats = service.stats()
    return PromptStatsResponse(
        data=PromptStats(
            total_prompt_count=stats["total"],
            today_prompt_count=stats["today"],
            project_count=stats["projects"],
            recent_prompt_count=stats["recent"],
        )
    )


@router.get("/prompt-history/projects", response_model=PromptProjectListResponse)
def prompt_projects(
    service: Annotated[PromptHistoryService, Depends(get_prompt_history_service)],
) -> PromptProjectListResponse:
    return PromptProjectListResponse(
        data=[PromptProject.model_validate(item) for item in service.projects()]
    )


@router.get("/prompt-history/sessions", response_model=CodexSessionListResponse)
def sessions(
    service: Annotated[PromptHistoryService, Depends(get_prompt_history_service)],
    filters: Annotated[SessionFilters, Query()],
) -> CodexSessionListResponse:
    items, total = service.list_sessions(**filters.model_dump())
    return CodexSessionListResponse(
        data=CodexSessionListData(
            items=[CodexSession.model_validate(item) for item in items],
            pagination=Pagination(page=filters.page, page_size=filters.page_size, total=total),
        )
    )


@router.get("/prompt-history/tool-events", response_model=ToolEventListResponse)
def tool_events(
    service: Annotated[PromptHistoryService, Depends(get_prompt_history_service)],
    filters: Annotated[ToolEventFilters, Query()],
) -> ToolEventListResponse:
    items, total = service.list_tool_events(**filters.model_dump())
    return ToolEventListResponse(
        data=ToolEventListData(
            items=[ToolEvent.model_validate(item) for item in items],
            pagination=Pagination(page=filters.page, page_size=filters.page_size, total=total),
        )
    )


@router.get("/prompt-history", response_model=PromptListResponse)
def prompts(
    service: Annotated[PromptHistoryService, Depends(get_prompt_history_service)],
    filters: Annotated[PromptFilters, Query()],
) -> PromptListResponse:
    items, total = service.list(**filters.model_dump())
    return PromptListResponse(
        data=PromptListData(
            items=[PromptRecord.model_validate(item) for item in items],
            pagination=Pagination(page=filters.page, page_size=filters.page_size, total=total),
        )
    )


@router.get("/prompt-history/{record_id}", response_model=PromptRecordResponse)
def prompt_detail(
    record_id: str, service: Annotated[PromptHistoryService, Depends(get_prompt_history_service)]
) -> PromptRecordResponse:
    record = service.get(record_id=record_id)
    return PromptRecordResponse(data=PromptRecord.model_validate(record))
