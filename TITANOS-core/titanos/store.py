"""
titanos.store
=============
Lightweight durable store backed by SQLite.

Tables
------
- approvals   – persistent approval records (replaces in-memory dict)
- run_records – persistent run history (replaces in-memory list)
- audit_log   – structured audit event log (JSONL-style rows)

All writes are done through a threading.Lock so the module is safe to call
from both the sync test suite and an async FastAPI process.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Generator

from .config.settings import settings
from .utils.logging import get_logger

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover - fallback for tiny embedded builds
    Fernet = None
    InvalidToken = Exception

logger = get_logger(__name__)

_LOCK = threading.Lock()
SCHEMA_VERSION = 2


def _db_path() -> Path:
    """Canonical path to the runtime SQLite database."""
    return settings.RUNTIME_DB


@contextmanager
def _conn() -> Generator[sqlite3.Connection, None, None]:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not exist. Safe to call multiple times."""
    with _LOCK, _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS approvals (
                id                TEXT PRIMARY KEY,
                command           TEXT NOT NULL,
                risk              TEXT NOT NULL,
                reason            TEXT NOT NULL,
                status            TEXT NOT NULL DEFAULT 'pending',
                created_at        TEXT NOT NULL,
                approved_at       TEXT,
                rejected_at       TEXT,
                expires_at        TEXT,
                executed_at       TEXT,
                execution_count   INTEGER NOT NULL DEFAULT 0,
                result_summary    TEXT
            );

            CREATE TABLE IF NOT EXISTS run_records (
                id                TEXT PRIMARY KEY,
                goal              TEXT NOT NULL,
                system            TEXT NOT NULL,
                confidence        REAL NOT NULL,
                route_reason      TEXT NOT NULL,
                status            TEXT NOT NULL,
                duration_ms       INTEGER NOT NULL,
                created_at        TEXT NOT NULL,
                completed_at      TEXT,
                result_summary    TEXT,
                error_summary     TEXT,
                artifacts         TEXT NOT NULL DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id                TEXT PRIMARY KEY,
                ts                TEXT NOT NULL,
                event_type        TEXT NOT NULL,
                actor             TEXT,
                run_id            TEXT,
                approval_id       TEXT,
                meta              TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS provider_configs (
                provider_id       TEXT PRIMARY KEY,
                label             TEXT NOT NULL,
                base_url          TEXT,
                model             TEXT,
                masked_key        TEXT,
                secret_ref        TEXT,
                secret_material   TEXT,
                status            TEXT NOT NULL DEFAULT 'saved',
                created_at        TEXT NOT NULL,
                updated_at        TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS runtime_meta (
                key               TEXT PRIMARY KEY,
                value             TEXT NOT NULL,
                updated_at        TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS operator_sessions (
                id                TEXT PRIMARY KEY,
                actor             TEXT NOT NULL,
                mode              TEXT NOT NULL,
                status            TEXT NOT NULL DEFAULT 'active',
                created_at        TEXT NOT NULL,
                last_seen_at      TEXT NOT NULL,
                metadata          TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS workspaces (
                id                TEXT PRIMARY KEY,
                label             TEXT NOT NULL,
                root_path         TEXT NOT NULL UNIQUE,
                mode              TEXT NOT NULL DEFAULT 'local',
                status            TEXT NOT NULL DEFAULT 'active',
                created_at        TEXT NOT NULL,
                updated_at        TEXT NOT NULL,
                metadata          TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS usage_events (
                id                TEXT PRIMARY KEY,
                provider_id       TEXT NOT NULL,
                model             TEXT,
                input_tokens      INTEGER NOT NULL DEFAULT 0,
                output_tokens     INTEGER NOT NULL DEFAULT 0,
                estimated_cost    REAL NOT NULL DEFAULT 0,
                run_id            TEXT,
                created_at        TEXT NOT NULL,
                metadata          TEXT NOT NULL DEFAULT '{}'
            );
            """
        )
        _ensure_columns(
            conn,
            "approvals",
            {
                "rejected_at": "TEXT",
                "expires_at": "TEXT",
                "execution_count": "INTEGER NOT NULL DEFAULT 0",
            },
        )
        _ensure_columns(
            conn,
            "provider_configs",
            {
                "secret_material": "TEXT",
            },
        )
        conn.execute(
            """
            INSERT INTO runtime_meta (key, value, updated_at)
            VALUES ('schema_version', ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (str(SCHEMA_VERSION), _now()),
        )


# ---------------------------------------------------------------------------
# Runtime metadata, sessions, workspaces, and usage
# ---------------------------------------------------------------------------

def runtime_meta() -> dict[str, Any]:
    init_db()
    with _LOCK, _conn() as conn:
        rows = conn.execute("SELECT key, value FROM runtime_meta").fetchall()
    return {row["key"]: row["value"] for row in rows}


def session_touch(
    *,
    session_id: str | None = None,
    actor: str = "local-operator",
    mode: str = "desktop",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sid = session_id or uuid.uuid4().hex
    now = _now()
    encoded = json.dumps(metadata or {})
    with _LOCK, _conn() as conn:
        conn.execute(
            """
            INSERT INTO operator_sessions
                (id, actor, mode, status, created_at, last_seen_at, metadata)
            VALUES (?, ?, ?, 'active', ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                actor=excluded.actor,
                mode=excluded.mode,
                status='active',
                last_seen_at=excluded.last_seen_at,
                metadata=excluded.metadata
            """,
            (sid, actor, mode, now, now, encoded),
        )
    return session_get(sid)  # type: ignore[return-value]


def session_get(session_id: str) -> dict[str, Any] | None:
    with _LOCK, _conn() as conn:
        row = conn.execute(
            "SELECT * FROM operator_sessions WHERE id = ?", (session_id,)
        ).fetchone()
    return _decode_json_columns(dict(row), ("metadata",)) if row else None


def session_list(limit: int = 100) -> list[dict[str, Any]]:
    with _LOCK, _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM operator_sessions ORDER BY last_seen_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_decode_json_columns(dict(row), ("metadata",)) for row in rows]


def session_close(session_id: str) -> dict[str, Any] | None:
    now = _now()
    with _LOCK, _conn() as conn:
        conn.execute(
            "UPDATE operator_sessions SET status='closed', last_seen_at=? WHERE id=?",
            (now, session_id),
        )
    return session_get(session_id)


def workspace_register(
    *,
    root_path: str,
    label: str | None = None,
    mode: str = "local",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = str(Path(root_path).resolve())
    wid = hashlib.sha256(root.encode("utf-8")).hexdigest()[:16]
    now = _now()
    with _LOCK, _conn() as conn:
        conn.execute(
            """
            INSERT INTO workspaces
                (id, label, root_path, mode, status, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, 'active', ?, ?, ?)
            ON CONFLICT(root_path) DO UPDATE SET
                label=excluded.label,
                mode=excluded.mode,
                status='active',
                updated_at=excluded.updated_at,
                metadata=excluded.metadata
            """,
            (
                wid,
                label or Path(root).name or "Workspace",
                root,
                mode,
                now,
                now,
                json.dumps(metadata or {}),
            ),
        )
    return workspace_get(wid)  # type: ignore[return-value]


def workspace_get(workspace_id: str) -> dict[str, Any] | None:
    with _LOCK, _conn() as conn:
        row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    return _decode_json_columns(dict(row), ("metadata",)) if row else None


def workspace_list() -> list[dict[str, Any]]:
    with _LOCK, _conn() as conn:
        rows = conn.execute("SELECT * FROM workspaces ORDER BY updated_at DESC").fetchall()
    return [_decode_json_columns(dict(row), ("metadata",)) for row in rows]


def usage_event_record(
    *,
    provider_id: str,
    model: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    estimated_cost: float = 0.0,
    run_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    uid = uuid.uuid4().hex
    now = _now()
    with _LOCK, _conn() as conn:
        conn.execute(
            """
            INSERT INTO usage_events
                (id, provider_id, model, input_tokens, output_tokens,
                 estimated_cost, run_id, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uid,
                provider_id,
                model,
                max(0, int(input_tokens)),
                max(0, int(output_tokens)),
                max(0.0, float(estimated_cost)),
                run_id,
                now,
                json.dumps(metadata or {}),
            ),
        )
    return usage_event_get(uid)  # type: ignore[return-value]


def usage_event_get(event_id: str) -> dict[str, Any] | None:
    with _LOCK, _conn() as conn:
        row = conn.execute("SELECT * FROM usage_events WHERE id = ?", (event_id,)).fetchone()
    return _decode_json_columns(dict(row), ("metadata",)) if row else None


def usage_summary() -> dict[str, Any]:
    with _LOCK, _conn() as conn:
        rows = conn.execute(
            """
            SELECT provider_id, model,
                   COUNT(*) AS events,
                   SUM(input_tokens) AS input_tokens,
                   SUM(output_tokens) AS output_tokens,
                   SUM(estimated_cost) AS estimated_cost
            FROM usage_events
            GROUP BY provider_id, model
            ORDER BY provider_id, model
            """
        ).fetchall()
    providers = [dict(row) for row in rows]
    return {
        "providers": providers,
        "total_events": sum(row["events"] or 0 for row in providers),
        "total_input_tokens": sum(row["input_tokens"] or 0 for row in providers),
        "total_output_tokens": sum(row["output_tokens"] or 0 for row in providers),
        "total_estimated_cost": sum(row["estimated_cost"] or 0 for row in providers),
    }


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------

def approval_create(
    *,
    command: str,
    risk: str,
    reason: str,
    approval_id: str | None = None,
) -> dict[str, Any]:
    """Insert a new pending approval and return its record dict."""
    aid = approval_id or uuid.uuid4().hex[:12]
    now = _now()
    expires_at = _dt_now() + timedelta(hours=settings.APPROVAL_EXPIRY_HOURS)
    with _LOCK, _conn() as conn:
        conn.execute(
            """
            INSERT INTO approvals (id, command, risk, reason, status, created_at, expires_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """,
            (aid, command, risk, reason, now, expires_at.isoformat()),
        )
    logger.debug("approval_create", extra={"extra": {"id": aid}})
    return approval_get(aid)  # type: ignore[return-value]


def approval_get(approval_id: str) -> dict[str, Any] | None:
    with _LOCK, _conn() as conn:
        row = conn.execute(
            "SELECT * FROM approvals WHERE id = ?", (approval_id,)
        ).fetchone()
    if not row:
        return None
    record = dict(row)
    if _is_approval_expired(record):
        expired = approval_expire(approval_id)
        audit_log("approval_expired", approval_id=approval_id)
        return expired
    return record


def approval_list(status: str | None = None) -> list[dict[str, Any]]:
    approval_expire_stale()
    with _LOCK, _conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM approvals WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM approvals ORDER BY created_at DESC"
            ).fetchall()
    return [dict(r) for r in rows]


def approval_approve(approval_id: str) -> dict[str, Any] | None:
    now = _now()
    row = approval_get(approval_id)
    if row is None or row["status"] not in {"pending", "approved"}:
        return row
    with _LOCK, _conn() as conn:
        conn.execute(
            "UPDATE approvals SET status='approved', approved_at=? WHERE id=?",
            (now, approval_id),
        )
    return approval_get(approval_id)


def approval_reject(approval_id: str) -> dict[str, Any] | None:
    now = _now()
    with _LOCK, _conn() as conn:
        conn.execute(
            "UPDATE approvals SET status='rejected', rejected_at=? WHERE id=?",
            (now, approval_id),
        )
    return approval_get(approval_id)


def approval_expire(approval_id: str) -> dict[str, Any] | None:
    with _LOCK, _conn() as conn:
        conn.execute(
            """
            UPDATE approvals SET status='expired'
            WHERE id=? AND status IN ('pending', 'approved')
            """,
            (approval_id,),
        )
    return _approval_get_raw(approval_id)


def approval_expire_stale() -> int:
    now = _now()
    with _LOCK, _conn() as conn:
        cursor = conn.execute(
            """
            UPDATE approvals SET status='expired'
            WHERE expires_at IS NOT NULL
              AND expires_at < ?
              AND status IN ('pending', 'approved')
            """,
            (now,),
        )
        return cursor.rowcount


def approval_set_executed(
    approval_id: str, *, result_summary: str
) -> dict[str, Any] | None:
    now = _now()
    with _LOCK, _conn() as conn:
        conn.execute(
            """
            UPDATE approvals
            SET status='executed', executed_at=?, result_summary=?,
                execution_count=execution_count + 1
            WHERE id=?
            """,
            (now, result_summary, approval_id),
        )
    return approval_get(approval_id)


def approval_increment_execution_attempt(approval_id: str) -> dict[str, Any] | None:
    with _LOCK, _conn() as conn:
        conn.execute(
            "UPDATE approvals SET execution_count=execution_count + 1 WHERE id=?",
            (approval_id,),
        )
    return approval_get(approval_id)


# ---------------------------------------------------------------------------
# Run records
# ---------------------------------------------------------------------------

def run_record_create(
    *,
    goal: str,
    system: str,
    confidence: float,
    route_reason: str,
    status: str,
    duration_ms: int,
    result_summary: str,
    error_summary: str | None = None,
    artifacts: list[str] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    rid = run_id or uuid.uuid4().hex
    now = _now()
    with _LOCK, _conn() as conn:
        conn.execute(
            """
            INSERT INTO run_records
                (id, goal, system, confidence, route_reason, status,
                 duration_ms, created_at, completed_at, result_summary,
                 error_summary, artifacts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rid,
                goal,
                system,
                confidence,
                route_reason,
                status,
                duration_ms,
                now,
                now,
                result_summary,
                error_summary,
                json.dumps(artifacts or []),
            ),
        )
    return run_record_get(rid)  # type: ignore[return-value]


def run_record_get(run_id: str) -> dict[str, Any] | None:
    with _LOCK, _conn() as conn:
        row = conn.execute(
            "SELECT * FROM run_records WHERE id = ?", (run_id,)
        ).fetchone()
    if row is None:
        return None
    rec = dict(row)
    rec["artifacts"] = json.loads(rec["artifacts"])
    return rec


def run_record_list(limit: int = 200) -> list[dict[str, Any]]:
    with _LOCK, _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM run_records ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    results = []
    for row in rows:
        rec = dict(row)
        rec["artifacts"] = json.loads(rec["artifacts"])
        results.append(rec)
    return results


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def audit_log(
    event_type: str,
    *,
    actor: str | None = None,
    run_id: str | None = None,
    approval_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    """Append a structured audit event. Never raises – logs on failure."""
    try:
        now = _now()
        eid = uuid.uuid4().hex
        with _LOCK, _conn() as conn:
            conn.execute(
                """
                INSERT INTO audit_log (id, ts, event_type, actor, run_id, approval_id, meta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    eid,
                    now,
                    event_type,
                    actor,
                    run_id,
                    approval_id,
                    json.dumps(meta or {}),
                ),
            )
    except Exception as exc:
        logger.warning("audit_log write failed", extra={"extra": {"error": str(exc)}})


def audit_list(limit: int = 500) -> list[dict[str, Any]]:
    with _LOCK, _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
    results = []
    for row in rows:
        rec = dict(row)
        rec["meta"] = json.loads(rec["meta"])
        results.append(rec)
    return results


# ---------------------------------------------------------------------------
# Provider configs
# ---------------------------------------------------------------------------

def provider_config_save(
    *,
    provider_id: str,
    label: str,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    status: str = "saved",
) -> dict[str, Any]:
    now = _now()
    model = model or provider_default_model(provider_id)
    base_url = base_url or provider_default_endpoint(provider_id) or None
    current = provider_config_get(provider_id, include_secret=True)
    secret_ref = current.get("secret_ref") if current else None
    secret_material = current.get("secret_material") if current else None
    masked_key = current.get("masked_key") if current else None
    if api_key:
        secret_ref = f"local-provider:{provider_id}"
        secret_material = _protect_secret(api_key)
        masked_key = _mask_secret(api_key)
    elif not secret_ref:
        secret_ref = f"local-provider:{provider_id}:unset"
    with _LOCK, _conn() as conn:
        conn.execute(
            """
            INSERT INTO provider_configs
                (provider_id, label, base_url, model, masked_key, secret_ref,
                 secret_material, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider_id) DO UPDATE SET
                label=excluded.label,
                base_url=excluded.base_url,
                model=excluded.model,
                masked_key=excluded.masked_key,
                secret_ref=excluded.secret_ref,
                secret_material=excluded.secret_material,
                status=excluded.status,
                updated_at=excluded.updated_at
            """,
            (
                provider_id,
                label,
                base_url,
                model,
                masked_key,
                secret_ref,
                secret_material,
                status,
                current["created_at"] if current else now,
                now,
            ),
        )
    return provider_config_get(provider_id)  # type: ignore[return-value]


def provider_default_model(provider_id: str) -> str:
    from .providers import provider_default_model as default_model

    return default_model(provider_id)


def provider_default_endpoint(provider_id: str) -> str:
    from .providers import provider_default_endpoint as default_endpoint

    return default_endpoint(provider_id)


def provider_config_get(provider_id: str, *, include_secret: bool = False) -> dict[str, Any] | None:
    with _LOCK, _conn() as conn:
        row = conn.execute(
            "SELECT * FROM provider_configs WHERE provider_id = ?", (provider_id,)
        ).fetchone()
    if row is None:
        return None
    data = dict(row)
    if not include_secret:
        data.pop("secret_material", None)
    return data


def provider_config_list() -> list[dict[str, Any]]:
    with _LOCK, _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM provider_configs ORDER BY provider_id"
        ).fetchall()
    results = []
    for row in rows:
        data = dict(row)
        data.pop("secret_material", None)
        results.append(data)
    return results


def provider_config_delete(provider_id: str) -> bool:
    with _LOCK, _conn() as conn:
        cursor = conn.execute(
            "DELETE FROM provider_configs WHERE provider_id = ?", (provider_id,)
        )
        return cursor.rowcount > 0


def provider_secret_reveal(provider_id: str) -> str | None:
    row = provider_config_get(provider_id, include_secret=True)
    if not row or not row.get("secret_material"):
        return None
    return _unprotect_secret(row["secret_material"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return _dt_now().isoformat()


def _dt_now() -> datetime:
    return datetime.now(UTC)


def _approval_get_raw(approval_id: str) -> dict[str, Any] | None:
    with _LOCK, _conn() as conn:
        row = conn.execute(
            "SELECT * FROM approvals WHERE id = ?", (approval_id,)
        ).fetchone()
    return dict(row) if row else None


def _is_approval_expired(record: dict[str, Any]) -> bool:
    if record.get("status") not in {"pending", "approved"}:
        return False
    expires_at = record.get("expires_at")
    if not expires_at:
        return False
    try:
        return datetime.fromisoformat(expires_at) < _dt_now()
    except ValueError:
        return False


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def _decode_json_columns(row: dict[str, Any], columns: tuple[str, ...]) -> dict[str, Any]:
    for column in columns:
        value = row.get(column)
        if isinstance(value, str):
            try:
                row[column] = json.loads(value)
            except json.JSONDecodeError:
                row[column] = {}
    return row


def _mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "*" * 8
    return f"{value[:4]}...{value[-4:]}"


def _protect_secret(value: str) -> str:
    if Fernet is not None:
        token = _fernet().encrypt(value.encode("utf-8")).decode("ascii")
        return f"fernet:{token}"
    key = hashlib.sha256(settings.JWT_SECRET.encode("utf-8")).digest()
    data = value.encode("utf-8")
    protected = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(data))
    return f"xor:{base64.urlsafe_b64encode(protected).decode('ascii')}"


def _unprotect_secret(value: str) -> str:
    if value.startswith("fernet:"):
        if Fernet is None:
            raise RuntimeError("cryptography is required to decrypt this provider secret")
        try:
            return _fernet().decrypt(value.removeprefix("fernet:").encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise RuntimeError("provider secret could not be decrypted with current JWT secret") from exc
    payload = value.removeprefix("xor:")
    key = hashlib.sha256(settings.JWT_SECRET.encode("utf-8")).digest()
    data = base64.urlsafe_b64decode(payload.encode("ascii"))
    unprotected = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(data))
    return unprotected.decode("utf-8")


def _fernet() -> "Fernet":
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.JWT_SECRET.encode("utf-8")).digest())
    return Fernet(key)


# Initialise on import so tables exist before first use.
try:
    init_db()
except Exception as _exc:
    logger.warning(
        "store init failed (will retry on next write)",
        extra={"extra": {"error": str(_exc)}},
    )
