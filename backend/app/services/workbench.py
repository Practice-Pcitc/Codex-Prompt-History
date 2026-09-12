"""Prompt library use cases and transaction boundaries."""

from datetime import UTC, datetime
from uuid import uuid4

from app.core.database import prompt_history_connection
from app.repositories.workbench import WorkbenchRepository
from app.schemas.workbench import LibraryInput, RecordingSettings


def now():
    return datetime.now(UTC).isoformat()


def settings(value: RecordingSettings | None = None):
    with prompt_history_connection() as connection, connection:
        repo = WorkbenchRepository(connection)
        old = repo.settings()
        if not old and value is None:
            old = RecordingSettings().model_dump()
            old["source_mode"] = "local_sessions"
            repo.save_settings(old)
        if value is not None:
            if old.get("enabled", True) and not value.enabled:
                old["paused_from"] = now()
            if not old.get("enabled", True) and value.enabled:
                old.setdefault("skip_windows", []).append([old.pop("paused_from", now()), now()])
            old.update(value.model_dump())
            old["source_mode"] = "local_sessions"
            repo.save_settings(old)
        return RecordingSettings.model_validate(old)


def listing(collection, **filters):
    with prompt_history_connection() as connection:
        items, total = getattr(WorkbenchRepository(connection), collection)(**filters)
        return {
            "items": items,
            "pagination": {
                "page": filters["page"],
                "page_size": filters["page_size"],
                "total": total,
            },
        }


def overview():
    with prompt_history_connection() as connection:
        return WorkbenchRepository(connection).overview()


def mutate(action, item_id, value: LibraryInput | None = None):
    with prompt_history_connection() as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        repo = WorkbenchRepository(connection)
        if action in ("favorite", "delete-record"):
            record = repo.get_record(item_id)
            if record is None:
                raise LookupError("记录不存在")
            if action == "delete-record":
                repo.delete_record(record)
                return True
            existing = repo.favorite_for(item_id)
            if existing:
                return existing
            item = dict(
                id=str(uuid4()),
                source_record_id=item_id,
                kind="favorite",
                title=record["prompt"][:80],
                content=record["prompt"],
                tags=[],
                note="",
                created_at=now(),
                updated_at=now(),
            )
        else:
            item = repo.get_library(item_id)
            if item is None:
                raise LookupError("收藏不存在")
            if action == "delete-library":
                repo.delete_library(item_id)
                return True
            if action == "template":
                record = repo.get_record(item["source_record_id"])
                if record:
                    item["content"] = item["content"].replace(
                        record["working_directory"], "{{项目路径}}"
                    )
                    if len(record["project_name"]) > 2:
                        item["content"] = item["content"].replace(
                            record["project_name"], "{{项目名称}}"
                        )
                item.update(
                    id=str(uuid4()),
                    kind="template",
                    title=item["title"][:150] + " · 模板",
                    created_at=now(),
                )
            elif value is not None:
                item.update(value.model_dump())
            item["updated_at"] = now()
        repo.save_library(item)
        return item
