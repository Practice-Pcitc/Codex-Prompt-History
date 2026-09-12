import json
import sqlite3
from typing import Any

BRIEF = ("好", "好的", "继续", "继续干", "好，继续干", "谢谢", "ok", "yes", "继续执行")


def library_item(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["tags"] = json.loads(item["tags"])
    return item


class WorkbenchRepository:
    """Uses a connection whose transaction is controlled by the service."""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def settings(self) -> dict:
        row = self.connection.execute("SELECT value FROM collector_settings WHERE id=1").fetchone()
        return json.loads(row[0]) if row else {}

    def save_settings(self, settings: dict) -> None:
        self.connection.execute(
            "INSERT INTO collector_settings VALUES(1,?) "
            "ON CONFLICT(id) DO UPDATE SET value=excluded.value",
            (json.dumps(settings),),
        )

    def reset_file_signatures(self) -> None:
        self.connection.execute("DELETE FROM collector_files")

    def remove_internal_session(self, session_id: str | None) -> int:
        rows = self.connection.execute(
            "SELECT * FROM prompt_records WHERE session_id=? AND source='codex-local-session'",
            (session_id,),
        ).fetchall()
        for row in rows:
            self.delete_record(row)
        return len(rows)

    def overview(self):
        counts = self.connection.execute(
            "SELECT COUNT(*) AS records,COUNT(DISTINCT COALESCE(session_id,id)) AS tasks "
            "FROM prompt_records"
        ).fetchone()
        projects = self.connection.execute(
            "SELECT working_directory AS path,MAX(project_name) AS name,COUNT(*) AS records,"
            "COUNT(DISTINCT COALESCE(session_id,id)) AS tasks,MAX(created_at) AS last_record_at "
            "FROM prompt_records GROUP BY working_directory ORDER BY last_record_at DESC"
        ).fetchall()
        library = self.connection.execute("SELECT COUNT(*) FROM prompt_library").fetchone()[0]
        return {**dict(counts), "library": library, "projects": [dict(row) for row in projects]}

    def records(
        self, page=1, page_size=20, keyword="", session_id="", project="", hide_brief=False
    ):
        clauses, params = [], []
        if keyword:
            clauses.append("instr(lower(p.prompt), lower(?)) > 0")
            params.append(keyword)
        if session_id:
            clauses.append("COALESCE(p.session_id, p.id)=?")
            params.append(session_id)
        if project:
            clauses.append("p.working_directory=?")
            params.append(project)
        if hide_brief:
            clauses.append(f"lower(trim(p.prompt)) NOT IN ({','.join('?' for _ in BRIEF)})")
            params.extend(BRIEF)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        total = self.connection.execute(
            "SELECT count(*) FROM prompt_records p" + where, params
        ).fetchone()[0]
        order = "ASC" if session_id else "DESC"
        rows = self.connection.execute(
            "SELECT p.*, l.id AS favorite_id FROM prompt_records p LEFT JOIN prompt_library l "
            "ON l.source_record_id=p.id AND l.kind='favorite'"
            + where
            + f" ORDER BY p.created_at {order},p.id LIMIT ? OFFSET ?",
            [*params, page_size, (page - 1) * page_size],
        ).fetchall()
        return [dict(row) for row in rows], total

    def tasks(self, page=1, page_size=20, keyword="", project=""):
        conditions, params = [], []
        if project:
            conditions.append("working_directory=?")
            params.append(project)
        if keyword:
            conditions.append("instr(lower(prompt),lower(?))>0")
            params.append(keyword)
        matching = "SELECT DISTINCT COALESCE(session_id,id) FROM prompt_records"
        if conditions:
            matching += " WHERE " + " AND ".join(conditions)
        base = (
            "WITH ranked AS (SELECT *,COALESCE(session_id,id) AS task_id,"
            "ROW_NUMBER() OVER(PARTITION BY COALESCE(session_id,id) ORDER BY created_at,id) AS rn,"
            "ROW_NUMBER() OVER(PARTITION BY COALESCE(session_id,id) "
            "ORDER BY created_at DESC,id DESC) AS latest "
            "FROM prompt_records) SELECT task_id AS session_id,"
            "MAX(CASE WHEN rn=1 THEN prompt END) AS title,"
            "MAX(CASE WHEN latest=1 THEN prompt END) AS latest_prompt,"
            "MAX(CASE WHEN rn=1 THEN project_name END) AS project_name,"
            "MAX(CASE WHEN rn=1 THEN working_directory END) AS working_directory,"
            "COUNT(*) AS count,MAX(created_at) AS updated_at FROM ranked "
            f"WHERE task_id IN ({matching}) GROUP BY task_id"
        )
        total = self.connection.execute("SELECT COUNT(*) FROM (" + base + ")", params).fetchone()[0]
        rows = self.connection.execute(
            base + " ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            [*params, page_size, (page - 1) * page_size],
        ).fetchall()
        return [dict(row) for row in rows], total

    def library(self, page=1, page_size=20, keyword="", kind="", tag=""):
        clauses, params = [], []
        if keyword:
            clauses.append("instr(lower(title||' '||content||' '||note),lower(?))>0")
            params.append(keyword)
        if kind:
            clauses.append("kind=?")
            params.append(kind)
        if tag:
            clauses.append("EXISTS(SELECT 1 FROM json_each(tags) WHERE value=?)")
            params.append(tag)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        total = self.connection.execute(
            "SELECT COUNT(*) FROM prompt_library" + where, params
        ).fetchone()[0]
        rows = self.connection.execute(
            "SELECT * FROM prompt_library" + where + " ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            [*params, page_size, (page - 1) * page_size],
        ).fetchall()
        return [library_item(row) for row in rows], total

    def get_record(self, record_id: str):
        return self.connection.execute(
            "SELECT * FROM prompt_records WHERE id=?", (record_id,)
        ).fetchone()

    def favorite_for(self, record_id):
        row = self.connection.execute(
            "SELECT * FROM prompt_library WHERE source_record_id=? AND kind='favorite'",
            (record_id,),
        ).fetchone()
        return library_item(row) if row else None

    def delete_library(self, item_id):
        self.connection.execute("DELETE FROM prompt_library WHERE id=?", (item_id,))

    def file_signature(self, path):
        row = self.connection.execute(
            "SELECT size,modified_ns FROM collector_files WHERE path=?", (str(path),)
        ).fetchone()
        return tuple(row) if row else None

    def remember_file(self, path, signature):
        self.connection.execute(
            "INSERT INTO collector_files VALUES(?,?,?) ON CONFLICT(path) DO UPDATE "
            "SET size=excluded.size,modified_ns=excluded.modified_ns",
            (str(path), *signature),
        )

    def get_library(self, item_id: str):
        row = self.connection.execute(
            "SELECT * FROM prompt_library WHERE id=?", (item_id,)
        ).fetchone()
        return library_item(row) if row else None

    def save_library(self, item: dict) -> None:
        self.connection.execute(
            "INSERT INTO prompt_library VALUES(:id,:source_record_id,:kind,:title,:content,:tags,"
            ":note,:created_at,:updated_at) ON CONFLICT(id) DO UPDATE SET title=excluded.title,"
            "content=excluded.content,tags=excluded.tags,note=excluded.note,updated_at=excluded.updated_at",
            {**item, "tags": json.dumps(item["tags"], ensure_ascii=False)},
        )

    def delete_record(self, row: sqlite3.Row) -> None:
        if row["source_key"]:
            self.connection.execute(
                "INSERT OR IGNORE INTO deleted_prompts VALUES(?)", (row["source_key"],)
            )
        self.connection.execute(
            "UPDATE prompt_library SET source_record_id=NULL WHERE source_record_id=?", (row["id"],)
        )
        self.connection.execute("DELETE FROM prompt_records WHERE id=?", (row["id"],))

    def insert_record(self, record: dict) -> int:
        if self.connection.execute(
            "SELECT 1 FROM deleted_prompts WHERE source_key=?", (record["source_key"],)
        ).fetchone():
            return 0
        return self.connection.execute(
            "INSERT OR IGNORE INTO prompt_records(id,session_id,turn_id,project_name,"
            "working_directory,"
            "prompt,prompt_length,source,created_at,source_key) VALUES(:id,:session_id,:turn_id,"
            ":project_name,:working_directory,:prompt,:prompt_length,:source,:created_at,:source_key)",
            record,
        ).rowcount
