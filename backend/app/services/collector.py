"""Read-only adapter for local Codex JSONL transcripts; never executes transcript text."""

import hashlib
import json
import os
import re
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from app.core.database import prompt_history_connection
from app.repositories.workbench import WorkbenchRepository
from app.schemas.workbench import RecordingSettings
from app.services.workbench import now


def within(path, roots):
    resolved = Path(path).resolve()
    return any(
        resolved == Path(root).resolve() or Path(root).resolve() in resolved.parents
        for root in roots
    )


def session_kind(meta: dict) -> str:
    """Classify task provenance before reading either modern or legacy user messages."""
    source = meta.get("source")
    if (isinstance(source, dict) and "subagent" in source) or meta.get("parent_thread_id"):
        return "internal"
    if source in ("cli", "vscode"):
        return "human"
    return "unknown"


def redact(text):
    text = re.sub(
        r'(?i)(\b(?:api[_-]?key|password|token|secret)["\x27]?\s*[=:]\s*)'
        r'("[^"]*"|\x27[^\x27]*\x27|[^\s,;]+)',
        r"\1[已脱敏]",
        text,
    )
    return re.sub(r"(?i)\bBearer\s+[^\s]+", "Bearer [已脱敏]", text)


def messages(rows):
    modern = []
    unmarked = []
    legacy = []
    unrecognized = False
    for row in rows:
        payload = row.get("payload", {})
        if row.get("type") == "response_item" and payload.get("role") == "user":
            meta = payload.get("internal_chat_message_metadata_passthrough") or {}
            kinds = meta.get("content_item_kinds", [])
            if not kinds:
                parts = payload.get("content", [])
                text = "\n".join(
                    part.get("text", "") for part in parts if part.get("type") == "input_text"
                )
                # Older clients store ordinary user text without content_item_kinds.
                # Remove only complete client-generated context blocks, never prose keywords.
                for tag in ("environment_context", "recommended_plugins", "turn_aborted"):
                    text = re.sub(rf"<{tag}\b[^>]*>[\s\S]*?</{tag}>", "", text)
                if text.strip():
                    unmarked.append(
                        (payload.get("id"), meta.get("turn_id"), row.get("timestamp"), text.strip())
                    )
                elif not parts or any(
                    part.get("type") not in ("input_text", "input_image") for part in parts
                ):
                    unrecognized = True
                continue
            text = "\n".join(
                part.get("text", "")
                for kind, part in zip(kinds, payload.get("content", []), strict=False)
                if kind == "user.text"
            )
            if text.strip():
                modern.append((payload.get("id"), meta.get("turn_id"), row.get("timestamp"), text))
        elif row.get("type") == "event_msg" and payload.get("type") == "user_message":
            if isinstance(payload.get("message"), str) and payload["message"].strip():
                legacy.append(
                    (None, payload.get("turn_id"), row.get("timestamp"), payload["message"])
                )
    if unrecognized and not modern and not legacy and not unmarked:
        raise ValueError("Unrecognized user message format")
    if modern:
        return sorted(modern + unmarked, key=lambda message: message[2] or "")
    return legacy or unmarked


class Collector:
    def __init__(self, root=None):
        self.root = Path(root or os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        self.lock = threading.Lock()
        self.status = dict(
            state="waiting",
            source_path=str(self.root),
            available_projects=[],
            imported=0,
            ignored_lines=0,
            excluded_sessions=0,
            cleaned_records=0,
        )

    def sync(self):
        with self.lock:
            try:
                self._sync()
            except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
                self.status.update(
                    state="error", error="无法读取本地会话，请检查目录权限或会话格式。"
                )
            return dict(self.status)

    @contextmanager
    def tolerate_file_error(self):
        try:
            yield
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            self.status.update(
                state="error", error="部分会话无法读取或格式不受支持；其余文件继续同步。"
            )
            self.status["ignored_lines"] += 1

    def _sync(self):
        self.status.update(
            last_scan_at=now(),
            error=None,
            ignored_lines=0,
            source_path=str(self.root),
            excluded_sessions=0,
        )
        projects = {}
        with prompt_history_connection() as connection, connection:
            repo = WorkbenchRepository(connection)
            raw = repo.settings()
            config = RecordingSettings.model_validate(raw)
            if raw.get("parser_version") != 2:
                # Revisit unchanged transcripts once after adding older-format support.
                # Stable message keys and deletion tombstones prevent duplicate imports.
                repo.reset_file_signatures()
                raw["parser_version"] = 2
                repo.save_settings(raw)
            projects.update(
                {path: dict(path=path, name=Path(path).name) for path in config.projects}
            )
            self.status["state"] = (
                "recording" if config.all_projects or config.projects else "waiting"
            )
            if not config.enabled:
                self.status["state"] = "paused"
            if not (self.root / "sessions").is_dir():
                self.status.update(state="missing", error="没有找到本机 Codex sessions 目录。")
                return
            for folder in ("sessions", "archived_sessions"):
                for path in (self.root / folder).rglob("*.jsonl"):
                    with self.tolerate_file_error(), path.open(encoding="utf-8") as stream:
                        first = json.loads(stream.readline())
                        if first.get("type") != "session_meta":
                            continue
                        meta = first["payload"]
                        provenance = session_kind(meta)
                        if provenance == "internal":
                            self.status["excluded_sessions"] += 1
                            self.status["cleaned_records"] += repo.remove_internal_session(
                                meta.get("id")
                            )
                            continue
                        if provenance != "human":
                            self.status["ignored_lines"] += 1
                            continue
                        cwd = meta.get("cwd", "")
                        if not cwd:
                            continue
                        projects[cwd] = dict(path=cwd, name=Path(cwd).name)
                        if (
                            not config.enabled
                            or (not config.all_projects and not within(cwd, config.projects))
                            or within(cwd, config.excluded_projects)
                        ):
                            continue
                        stat = path.stat()
                        signature = (stat.st_size, stat.st_mtime_ns)
                        previous = repo.file_signature(path)
                        if previous == signature:
                            continue
                        rows = []
                        for line in stream:
                            if not line.endswith("\n"):
                                continue
                            try:
                                rows.append(json.loads(line))
                            except json.JSONDecodeError:
                                self.status["ignored_lines"] += 1
                        for message_id, turn_id, timestamp, text in messages(rows):
                            if not timestamp or any(
                                datetime.fromisoformat(start)
                                <= datetime.fromisoformat(timestamp)
                                <= datetime.fromisoformat(end)
                                for start, end in raw.get("skip_windows", [])
                            ):
                                continue
                            key = (
                                meta["id"]
                                + ":"
                                + (
                                    message_id
                                    or hashlib.sha256((timestamp + text).encode()).hexdigest()
                                )
                            )
                            content = redact(text) if config.redact else text
                            inserted = repo.insert_record(
                                dict(
                                    id=hashlib.sha256(key.encode()).hexdigest(),
                                    source_key=key,
                                    session_id=meta["id"],
                                    turn_id=turn_id,
                                    project_name=Path(cwd).name,
                                    working_directory=cwd,
                                    prompt=content,
                                    prompt_length=len(content),
                                    source="codex-local-session",
                                    created_at=timestamp,
                                )
                            )
                            self.status["imported"] += inserted
                            if inserted:
                                self.status["last_record_at"] = now()
                        repo.remember_file(path, signature)
        self.status["available_projects"] = sorted(projects.values(), key=lambda item: item["path"])


collector = Collector()
