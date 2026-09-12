from fastapi import APIRouter, HTTPException, Query

from app.schemas.workbench import (
    ActionResponse,
    LibraryInput,
    LibraryItemResponse,
    LibraryResponse,
    OverviewResponse,
    RecordingSettings,
    RecordsResponse,
    SettingsResponse,
    StatusResponse,
    TasksResponse,
)
from app.services import workbench
from app.services.collector import collector

router = APIRouter(prefix="/workbench", tags=["workbench"])


@router.get("/overview", response_model=OverviewResponse)
def overview():
    return {"data": workbench.overview()}


@router.get("/settings", response_model=SettingsResponse)
def settings():
    return {"data": workbench.settings()}


@router.put("/settings", response_model=SettingsResponse)
def save_settings(value: RecordingSettings):
    with collector.lock:
        result = workbench.settings(value)
    collector.sync()
    return {"data": result}


@router.get("/status", response_model=StatusResponse)
def status():
    return {"data": collector.status}


@router.get("/records", response_model=RecordsResponse)
def records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = "",
    session_id: str = "",
    project: str = "",
    hide_brief: bool = False,
):
    return {
        "data": workbench.listing(
            "records",
            page=page,
            page_size=page_size,
            keyword=keyword,
            session_id=session_id,
            project=project,
            hide_brief=hide_brief,
        )
    }


@router.get("/tasks", response_model=TasksResponse)
def tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = "",
    project: str = "",
):
    return {
        "data": workbench.listing(
            "tasks", page=page, page_size=page_size, keyword=keyword, project=project
        )
    }


@router.get("/library", response_model=LibraryResponse)
def library(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = "",
    kind: str = "",
    tag: str = "",
):
    return {
        "data": workbench.listing(
            "library", page=page, page_size=page_size, keyword=keyword, kind=kind, tag=tag
        )
    }


def change(action, item_id, value=None):
    try:
        return {"data": workbench.mutate(action, item_id, value)}
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/records/{item_id}/favorites", response_model=LibraryItemResponse)
def favorite(item_id: str):
    return change("favorite", item_id)


@router.delete("/records/{item_id}", response_model=ActionResponse)
def delete_record(item_id: str):
    return change("delete-record", item_id)


@router.post("/library/{item_id}/templates", response_model=LibraryItemResponse)
def template(item_id: str):
    return change("template", item_id)


@router.put("/library/{item_id}", response_model=LibraryItemResponse)
def update(item_id: str, value: LibraryInput):
    return change("update", item_id, value)


@router.delete("/library/{item_id}", response_model=ActionResponse)
def delete_library(item_id: str):
    return change("delete-library", item_id)
