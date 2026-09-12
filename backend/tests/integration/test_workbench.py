import json
from datetime import UTC, datetime, timedelta

import pytest
from app.core.database import initialize_prompt_history_database, prompt_history_connection
from app.repositories.workbench import WorkbenchRepository
from app.schemas.workbench import LibraryInput, RecordingSettings
from app.services import workbench
from app.services.collector import Collector, messages, redact, within


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.setenv("PROMPT_HISTORY_DB", str(tmp_path / "history.db"))
    initialize_prompt_history_database()
    root = tmp_path / "codex"
    (root / "sessions").mkdir(parents=True)
    project = tmp_path / "sample-project"
    path = root / "sessions" / "test.jsonl"
    path.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": {"id": "task1", "cwd": str(project), "source": "vscode"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return Collector(root), project, path


def append(path, text="Please fix the regression", ident="m1", kind="user.text", timestamp=None):
    row = {
        "type": "response_item",
        "timestamp": timestamp or datetime.now(UTC).isoformat(),
        "payload": {
            "type": "message",
            "role": "user",
            "id": ident,
            "content": [{"type": "input_text", "text": text}],
            "internal_chat_message_metadata_passthrough": {
                "content_item_kinds": [kind],
                "turn_id": "turn1",
            },
        },
    }
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row) + "\n")


def records():
    return workbench.listing("records", page=1, page_size=100, hide_brief=False)["items"]


def test_all_projects_backfill_new_projects_and_separate_conversations(source):
    collector, project, path = source
    append(path, "first", timestamp="2026-01-01T00:00:00Z")
    append(path, "继续", "m2", timestamp="2026-01-01T00:01:00Z")
    collector.sync()
    assert len(records()) == 2
    for ident, cwd in [("task2", project), ("task3", project.parent / "new-project")]:
        other = path.with_name(ident + ".jsonl")
        other.write_text(
            json.dumps(
                {
                    "type": "session_meta",
                    "payload": {"id": ident, "cwd": str(cwd), "source": "vscode"},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        append(other, "好的", ident)
    collector.sync()
    collector.sync()
    assert len(records()) == 4
    assert len(collector.status["available_projects"]) == 2
    tasks = workbench.listing("tasks", project=str(project), page=1, page_size=20)
    assert tasks["pagination"]["total"] == 2
    timeline = workbench.listing(
        "records", session_id="task1", project=str(project), page=1, page_size=20
    )
    assert [r["prompt"] for r in timeline["items"]] == ["first", "继续"]


def test_unmarked_older_user_messages_keep_short_replies_and_skip_context():
    def row(text, ident):
        return {
            "type": "response_item",
            "timestamp": "2026-01-01T00:00:00Z",
            "payload": {
                "role": "user",
                "id": ident,
                "content": [{"type": "input_text", "text": text}],
            },
        }

    rows = [
        row("<environment_context>system context</environment_context>", "env"),
        row("继续", "m1"),
        row("The following is the Codex agent history — explain this", "m2"),
    ]
    assert [item[3] for item in messages(rows)] == [
        "继续",
        "The following is the Codex agent history — explain this",
    ]


def test_selection_redaction_context_and_idempotency(source):
    collector, project, path = source
    workbench.settings(RecordingSettings(all_projects=False))
    append(path, 'password="test-only-secret"')
    append(path, "injected environment", "env", "environments.environment_context")
    append(path, "继续", "m2")
    collector.sync()
    assert records() == []
    assert collector.status["available_projects"][0]["path"] == str(project)
    workbench.settings(RecordingSettings(projects=[str(project)]))
    collector.sync()
    collector.sync()
    assert len(records()) == 2
    assert any("[已脱敏]" in row["prompt"] for row in records())
    assert workbench.listing("records", page=1, page_size=20)["pagination"]["total"] == 2
    tasks = workbench.listing("tasks", page=1, page_size=20)["items"]
    assert tasks[0]["count"] == 2
    assert tasks[0]["session_id"] == "task1"


def test_favorite_template_and_delete_preserve_original_and_tombstone(source):
    collector, project, path = source
    append(path, f"Fix {project} in sample-project")
    workbench.settings(RecordingSettings(projects=[str(project)]))
    collector.sync()
    original = records()[0]
    favorite = workbench.mutate("favorite", original["id"])
    assert workbench.mutate("favorite", original["id"])["id"] == favorite["id"]
    template = workbench.mutate("template", favorite["id"])
    assert "{{项目路径}}" in template["content"]
    assert "{{项目名称}}" in template["content"]
    workbench.mutate(
        "update",
        favorite["id"],
        LibraryInput(title="Useful", content="edited", tags=["fix"], note="solved"),
    )
    assert records()[0]["prompt"] == original["prompt"]
    workbench.mutate("delete-record", original["id"])
    append(path, "new message", "m2")
    collector.sync()
    assert len(records()) == 1
    with prompt_history_connection() as connection:
        assert WorkbenchRepository(connection).get_library(favorite["id"])["content"] == "edited"


def test_pause_skips_interval_and_exclusion_wins(source):
    collector, project, path = source
    workbench.settings(RecordingSettings(projects=[str(project)], enabled=False))
    append(path)
    collector.sync()
    workbench.settings(RecordingSettings(projects=[str(project)]))
    collector.sync()
    assert records() == []
    workbench.settings(RecordingSettings(projects=[str(project)], excluded_projects=[str(project)]))
    append(path, ident="excluded")
    collector.sync()
    assert records() == []


def test_project_boundary_and_legacy_adapter(tmp_path):
    assert within(tmp_path / "app" / "child", [tmp_path / "app"])
    assert not within(tmp_path / "app-other", [tmp_path / "app"])
    rows = [
        {
            "type": "event_msg",
            "timestamp": "2026-01-01T00:00:00Z",
            "payload": {"type": "user_message", "message": "hello"},
        }
    ]
    assert messages(rows)[0][3] == "hello"
    assert "test-only-secret" not in redact("Bearer test-only-secret")
    assert "test-only-secret" not in redact('{"password": "test-only-secret"}')


def test_old_hook_does_not_bypass_workbench_pause(source):
    from config import HookConfig
    from prompt_hook import handle

    _, project, _ = source
    workbench.settings(RecordingSettings(projects=[str(project)], enabled=False))
    assert (
        handle(
            {
                "hook_event_name": "UserPromptSubmit",
                "cwd": str(project),
                "prompt": "must not be recorded",
            },
            HookConfig.load(),
        )
        is None
    )
    assert records() == []


def test_partial_last_line_is_retried_when_completed(source):
    collector, project, path = source
    workbench.settings(RecordingSettings(projects=[str(project)]))
    with path.open("a", encoding="utf-8") as stream:
        stream.write('{"type":"event_msg","timestamp":"2026-01-01T00:00:00Z",')
    collector.sync()
    assert records() == []
    with path.open("a", encoding="utf-8") as stream:
        stream.write('"payload":{"type":"user_message","message":"completed prompt"}}\n')
    collector.sync()
    assert len(records()) == 1
    assert records()[0]["prompt"] == "completed prompt"


def test_corrupt_file_does_not_block_valid_files(source):
    collector, project, path = source
    workbench.settings(RecordingSettings(projects=[str(project)]))
    (path.parent / "broken.jsonl").write_text("not json\n", encoding="utf-8")
    append(path)
    collector.sync()
    assert len(records()) == 1
    assert collector.status["state"] == "error"
    with pytest.raises(ValueError, match="Unrecognized"):
        messages([{"type": "response_item", "payload": {"role": "user", "content": []}}])


def test_pause_uses_timezone_aware_comparison(source):
    collector, project, path = source
    workbench.settings(RecordingSettings(projects=[str(project)]))
    with prompt_history_connection() as connection, connection:
        repo = WorkbenchRepository(connection)
        settings = repo.settings()
        moment = datetime.now(UTC)
        settings["skip_windows"] = [
            [
                (moment - timedelta(seconds=1)).isoformat(),
                (moment + timedelta(seconds=1)).isoformat(),
            ]
        ]
        repo.save_settings(settings)
    append(path, timestamp=moment.astimezone().isoformat())
    collector.sync()
    assert records() == []


@pytest.mark.parametrize(
    "internal_source",
    [
        {"subagent": {"other": "guardian"}},
        {"subagent": {"thread_spawn": {"parent_thread_id": "parent", "depth": 1}}},
    ],
)
def test_internal_task_provenance_is_excluded_and_old_imports_removed(source, internal_source):
    collector, project, path = source
    workbench.settings(RecordingSettings(projects=[str(project)]))
    text = "The following is the Codex agent history whose request action you are assessing."
    # A human may legitimately quote this sentence. Do not use keyword deletion.
    append(path, text)
    internal = path.parent / "internal.jsonl"
    internal.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": {"id": "internal-task", "cwd": str(project), "source": internal_source},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    append(internal, text)
    with internal.open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps(
                {
                    "type": "event_msg",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "payload": {"type": "user_message", "message": text},
                }
            )
            + "\n"
        )
    with prompt_history_connection() as connection, connection:
        repo = WorkbenchRepository(connection)
        repo.insert_record(
            dict(
                id="bad-import",
                session_id="internal-task",
                turn_id=None,
                project_name=project.name,
                working_directory=str(project),
                prompt=text,
                prompt_length=len(text),
                source="codex-local-session",
                created_at=datetime.now(UTC).isoformat(),
                source_key="internal-task:old-import",
            )
        )
    collector.sync()
    collector.sync()
    assert [row["session_id"] for row in records()] == ["task1"]
    assert records()[0]["prompt"] == text
    assert collector.status["cleaned_records"] == 1
    assert collector.status["excluded_sessions"] == 1
    assert workbench.overview()["tasks"] == 1


def test_unknown_task_source_is_not_assumed_to_be_human(source):
    collector, project, path = source
    workbench.settings(RecordingSettings(projects=[str(project)]))
    header = {
        "type": "session_meta",
        "payload": {"id": "unknown", "cwd": str(project), "source": "unknown-worker"},
    }
    path.write_text(json.dumps(header) + "\n", encoding="utf-8")
    append(path)
    collector.sync()
    assert records() == []
    assert collector.status["ignored_lines"] == 1
