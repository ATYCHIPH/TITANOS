from __future__ import annotations

import os
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ..contracts import BodyHealth, BodyResult, BodySystem, BodyTask
from ..config.settings import settings
from ..sources import project_root
from ..utils.logging import get_logger
from .base import info


logger = get_logger(__name__)

SEMANTIC_ALIASES = {
    "silent": "quiet",
    "silence": "quiet",
    "logging": "logs",
    "log": "logs",
    "preferences": "preference",
    "prefer": "preference",
    "prefers": "preference",
}


@dataclass(frozen=True)
class MemoryRecord:
    id: int
    kind: str
    text: str
    created_at: str


class MemoryStore:
    def __init__(self, path: Path | None = None) -> None:
        configured_path = os.getenv("TITANOS_MEMORY_PATH")
        if path is not None:
            self.path = path
        elif configured_path:
            self.path = Path(configured_path)
        else:
            self.path = settings.DATA_DIR / "memory.sqlite"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def remember(
        self, text: str, *, kind: str = "note", pinned: bool = False, meta: dict | None = None
    ) -> MemoryRecord:
        import json
        created_at = datetime.now(UTC).isoformat(timespec="seconds")
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    insert into memories (kind, text, created_at, pinned, metadata) 
                    values (?, ?, ?, ?, ?)
                    """,
                    (kind, text, created_at, 1 if pinned else 0, json.dumps(meta or {})),
                )
                memory_id = int(cursor.lastrowid)
        return MemoryRecord(memory_id, kind, text, created_at)

    def recall(self, query: str, *, limit: int = 10) -> list[MemoryRecord]:
        query = query.strip()
        with closing(sqlite3.connect(self.path)) as connection:
            # We prioritize pinned memories and then recent ones
            if query:
                rows = connection.execute(
                    """
                    select id, kind, text, created_at
                    from memories
                    where text like ? or kind like ?
                    order by pinned desc, id desc
                    limit ?
                    """,
                    (f"%{query}%", f"%{query}%", limit),
                ).fetchall()
                if not rows:
                    rows = self._semantic_recall(connection, query, limit)
            else:
                rows = connection.execute(
                    """
                    select id, kind, text, created_at
                    from memories
                    order by pinned desc, id desc
                    limit ?
                    """,
                    (limit,),
                ).fetchall()
        return [MemoryRecord(*row) for row in rows]

    def get(self, memory_id: int) -> MemoryRecord | None:
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute(
                "select id, kind, text, created_at from memories where id = ?",
                (memory_id,),
            ).fetchone()
        return MemoryRecord(*row) if row else None

    def _semantic_recall(
        self, connection: sqlite3.Connection, query: str, limit: int
    ) -> list[tuple[int, str, str, str]]:
        query_terms = self._terms(query)
        if not query_terms:
            return []
        rows = connection.execute(
            """
            select id, kind, text, created_at
            from memories
            order by pinned desc, id desc
            limit 200
            """
        ).fetchall()
        scored = []
        for row in rows:
            terms = self._terms(f"{row[1]} {row[2]}")
            score = len(query_terms & terms)
            if score:
                scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [row for _, row in scored[:limit]]

    def _terms(self, text: str) -> set[str]:
        raw_terms = re.findall(r"[a-z0-9]+", text.lower())
        return {SEMANTIC_ALIASES.get(term, term) for term in raw_terms}

    def update(self, memory_id: int, text: str) -> MemoryRecord | None:
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                cursor = connection.execute(
                    "update memories set text = ? where id = ?",
                    (text, memory_id),
                )
                if cursor.rowcount == 0:
                    return None
                row = connection.execute(
                    "select id, kind, text, created_at from memories where id = ?",
                    (memory_id,),
                ).fetchone()
        return MemoryRecord(*row) if row else None

    def delete(self, memory_id: int) -> bool:
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                cursor = connection.execute(
                    "delete from memories where id = ?",
                    (memory_id,),
                )
        return cursor.rowcount > 0

    def _initialize(self) -> None:
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                connection.execute(
                    """
                    create table if not exists memories (
                        id integer primary key autoincrement,
                        kind text not null,
                        text text not null,
                        created_at text not null,
                        pinned integer default 0,
                        metadata text
                    )
                    """
                )
                columns = {
                    row[1]
                    for row in connection.execute("pragma table_info(memories)").fetchall()
                }
                if "pinned" not in columns:
                    self._add_column_if_missing(
                        connection,
                        "alter table memories add column pinned integer default 0",
                    )
                if "metadata" not in columns:
                    self._add_column_if_missing(
                        connection,
                        "alter table memories add column metadata text",
                    )
                connection.execute(
                    "create index if not exists idx_memories_text on memories(text)"
                )
                connection.execute(
                    "create index if not exists idx_memories_kind on memories(kind)"
                )

    def _add_column_if_missing(
        self, connection: sqlite3.Connection, statement: str
    ) -> None:
        try:
            connection.execute(statement)
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise


class MemoryAdapter:
    info = info(
        BodySystem.MEMORY,
        "TITANOS Memory",
        "semantic storage graft",
        "long-term memory, recall, user and project models",
        always_on=True,
    )

    trigger_words = (
        "remember",
        "recall",
        "memory",
        "preference",
        "history",
        "index",
        "scan",
        "forget",
    )

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def initialize(self) -> None:
        return None

    def health(self) -> BodyHealth:
        return BodyHealth(
            system=BodySystem.MEMORY,
            status="ready",
            summary="Memory store is available.",
            details={"path": str(self.store.path)},
        )

    def shutdown(self) -> None:
        return None

    def can_handle(self, task: BodyTask) -> bool:
        goal = task.goal.lower()
        return any(word in goal for word in self.trigger_words)

    def list_records(self, *, limit: int = 50) -> list[MemoryRecord]:
        return self.store.recall("", limit=limit)

    def search_records(self, query: str, *, limit: int = 50) -> list[MemoryRecord]:
        return self.store.recall(query, limit=limit)

    def add_record(self, text: str, *, kind: str = "note") -> MemoryRecord:
        return self.store.remember(text, kind=kind)

    def update_record(self, memory_id: int, text: str) -> MemoryRecord | None:
        return self.store.update(memory_id, text)

    def delete_record(self, memory_id: int) -> bool:
        return self.store.delete(memory_id)

    def run(self, task: BodyTask) -> BodyResult:
        goal = task.goal.strip()
        lowered = goal.lower()

        if lowered.startswith(("index project", "scan project", "map project")):
            return self._index_project()

        if lowered.startswith(("remember ", "memory add ", "save memory ")):
            text = self._strip_prefix(
                goal, ("remember ", "memory add ", "save memory ")
            )
            return self._remember(text)

        if lowered.startswith(("preference ", "remember preference ")):
            text = self._strip_prefix(goal, ("preference ", "remember preference "))
            return self._remember(text, kind="preference")

        if lowered.startswith(("recall", "memory search", "show memory", "history")):
            query = self._strip_prefix(
                goal, ("recall", "memory search", "show memory", "history")
            )
            return self._recall(query)

        if lowered.startswith(("memory list", "list memories")):
            return self._recall("")

        if lowered.startswith(("forget ", "memory delete ", "delete memory ")):
            value = self._strip_prefix(
                goal, ("forget ", "memory delete ", "delete memory ")
            )
            return self._delete(value)

        if lowered.startswith(("memory update ", "update memory ")):
            value = self._strip_prefix(goal, ("memory update ", "update memory "))
            return self._update(value)

        return BodyResult(
            system=BodySystem.MEMORY,
            status="needs_input",
            summary=(
                "TITANOS Memory can persist notes and recall them. Try: "
                "remember project codename is TITANOS"
            ),
            next_steps=[
                "Use 'index project' to scan the workspace.",
                "Use 'remember <fact>' to store a note.",
                "Use 'recall <term>' to search stored notes.",
            ],
        )

    def _index_project(self) -> BodyResult:
        root = project_root()
        indexed_count = 0
        
        # Simple crawler: index top-level files and folders
        for path in root.rglob("*"):
            if ".git" in path.parts or "__pycache__" in path.parts or ".titanos" in path.parts:
                continue
            
            if path.is_file():
                kind = "project_file"
                text = f"File: {path.relative_to(root)}"
            else:
                kind = "project_dir"
                text = f"Directory: {path.relative_to(root)}"
            
            self.store.remember(text, kind=kind)
            indexed_count += 1
            
            if indexed_count > 500: # Safety cap
                break
        
        return BodyResult(
            system=BodySystem.MEMORY,
            status="success",
            summary=f"Indexed {indexed_count} project entries into memory.",
            artifacts=[str(root)],
        )

    def _remember(self, text: str, *, kind: str = "note") -> BodyResult:
        text = text.strip()
        if not text:
            return BodyResult(
                system=BodySystem.MEMORY,
                status="needs_input",
                summary="Memory needs text to store.",
                next_steps=["Use 'remember <fact>'."],
            )

        record = self.store.remember(text, kind=kind)
        logger.info("Memory stored", extra={"extra": {"memory_id": record.id, "kind": kind}})
        return BodyResult(
            system=BodySystem.MEMORY,
            status="success",
            summary=f"Remembered #{record.id}: {record.text}",
            artifacts=[str(self.store.path)],
            raw=record,
        )

    def _recall(self, query: str) -> BodyResult:
        records = self.store.recall(query)
        if not records:
            label = query.strip() or "recent memory"
            return BodyResult(
                system=BodySystem.MEMORY,
                status="success",
                summary=f"No memories found for: {label}",
                artifacts=[str(self.store.path)],
            )

        lines = [
            f"#{record.id} [{record.kind}] {record.text}"
            for record in records
        ]
        return BodyResult(
            system=BodySystem.MEMORY,
            status="success",
            summary="\n".join(lines),
            artifacts=[str(self.store.path)],
            raw=records,
        )

    def _delete(self, value: str) -> BodyResult:
        try:
            memory_id = int(value.strip().lstrip("#"))
        except ValueError:
            return BodyResult(
                system=BodySystem.MEMORY,
                status="needs_input",
                summary="Memory delete needs a numeric id.",
                next_steps=["Use 'memory delete <id>'."],
            )

        if not self.store.delete(memory_id):
            return BodyResult(
                system=BodySystem.MEMORY,
                status="failed",
                summary=f"Memory #{memory_id} was not found.",
                artifacts=[str(self.store.path)],
            )

        return BodyResult(
            system=BodySystem.MEMORY,
            status="success",
            summary=f"Deleted memory #{memory_id}.",
            artifacts=[str(self.store.path)],
        )

    def _update(self, value: str) -> BodyResult:
        if ":" in value and (value.find(":") < value.find(" ") or " " not in value):
            raw_id, separator, text = value.partition(":")
        else:
            raw_id, separator, text = value.partition(" ")
        try:
            memory_id = int(raw_id.strip().lstrip("#"))
        except ValueError:
            return BodyResult(
                system=BodySystem.MEMORY,
                status="needs_input",
                summary="Memory update needs a numeric id and replacement text.",
                next_steps=["Use 'memory update <id> <new text>'."],
            )

        text = text.strip(" :")
        if not text:
            return BodyResult(
                system=BodySystem.MEMORY,
                status="needs_input",
                summary="Memory update needs replacement text.",
                next_steps=["Use 'memory update <id> <new text>'."],
            )

        record = self.store.update(memory_id, text)
        if record is None:
            return BodyResult(
                system=BodySystem.MEMORY,
                status="failed",
                summary=f"Memory #{memory_id} was not found.",
                artifacts=[str(self.store.path)],
            )

        return BodyResult(
            system=BodySystem.MEMORY,
            status="success",
            summary=f"Updated #{record.id}: {record.text}",
            artifacts=[str(self.store.path)],
            raw=record,
        )

    def _strip_prefix(self, text: str, prefixes: tuple[str, ...]) -> str:
        lowered = text.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                return text[len(prefix) :].strip(" :")
        return text.strip()
