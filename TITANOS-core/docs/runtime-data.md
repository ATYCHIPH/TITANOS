# TITANOS Runtime Data & Persistence

This document describes the runtime data layout, what is persisted across process restarts, how to clean generated files, and how to inspect the approval/run/audit history.

---

## Runtime data location

All runtime state is stored under a single directory:

```
.titanos/               ← default, relative to the project root
```

Override the location by setting the environment variable:

```bash
export TITANOS_DATA_DIR=/path/to/custom/dir
```

| Path | Contents |
|---|---|
| `.titanos/titanos.sqlite` | Approvals, run records, audit log |
| `.titanos/memory/` | SQLite long-term memory files |
| `.titanos/logs/` | Structured log files |
| `.titanos/sessions/` | Session JSON files |
| `.titanos/backups/` | File backups created before edits/restores |
| `.titanos/diagnostics/` | Redacted diagnostics exports |

All paths are resolved through `titanos.config.settings.Settings` (see `titanos/config/settings.py`). Nothing is hardcoded outside that module.

---

## What is persisted

### Approvals (`approvals` table)

Every command that requires a safety review or is blocked creates a durable approval record with:

| Field | Description |
|---|---|
| `id` | 12-character hex identifier |
| `command` | The full command string |
| `risk` | `pending` / `review` / `blocked` |
| `reason` | Why the command needs approval |
| `status` | `pending` → `approved` → `executed` (or `rejected` / `expired`) |
| `created_at` | ISO-8601 timestamp |
| `approved_at` | Set when approved |
| `rejected_at` | Set when rejected |
| `expires_at` | Default 24-hour expiry timestamp |
| `executed_at` | Set when the approved command runs |
| `execution_count` | Number of execution attempts |
| `result_summary` | Truncated stdout/stderr from execution |

Approved commands are single-use. Statuses `pending`, `rejected`, `expired`, and `executed` cannot be executed.

### Run records (`run_records` table)

Every call to `brain.run(goal)` writes a record:

| Field | Description |
|---|---|
| `id` | UUID hex |
| `goal` | User input |
| `system` | Body system that handled the goal (hands / memory / cortex …) |
| `confidence` | Routing confidence (0–1) |
| `route_reason` | Human-readable routing justification |
| `status` | `success` / `failed` / `needs_input` |
| `duration_ms` | Wall-clock time |
| `created_at` / `completed_at` | ISO-8601 timestamps |
| `result_summary` | What happened |
| `error_summary` | Populated when status is `failed` |
| `artifacts` | JSON array of file paths produced |

### Audit log (`audit_log` table)

Lightweight, append-only event log. Event types emitted automatically:

| Event type | When |
|---|---|
| `command_classified` | Before any command is run |
| `approval_created` | Risk/blocked command queued for review |
| `approval_approved` | Operator approves via API or goal |
| `approval_rejected` | Operator rejects an approval |
| `approval_expired` | Approval becomes stale |
| `approval_execution_blocked` | Attempted execution from a blocked status |
| `approved_command_executed` | Approved command actually runs |
| `file_write_previewed` | Diff shown, no write yet |
| `file_written` | File written to disk |
| `file_edited` | In-place edit applied |
| `backup_created` | File backed up before edit/write |
| `route_decision_made` | Brain selects a body system |

Each row has: `id`, `ts` (ISO-8601), `event_type`, `actor`, `run_id`, `approval_id`, `meta` (JSON).

---

## Inspecting history

### Via API

```
GET /runs                       → list all run records (newest first)
GET /runs/{run_id}              → single run record
GET /hands/approvals            → list all approval records
GET /hands/approvals/{id}       → single approval record
GET /audit/events               → list audit log events (newest first)
```

All endpoints require authentication (JWT Bearer token) if running in server/API mode. In plug-and-play desktop mode, backend authentication is bypassed, and the operator UI directly accesses the local desktop agent workspace.

Additional production-hardening endpoints:

```bash
POST /hands/approvals/{id}/reject
POST /hands/backups/{backup_id}/restore
GET /runtime/diagnostics
POST /runtime/diagnostics/export
GET /providers/config
POST /providers/config
DELETE /providers/config/{provider_id}
POST /providers/config/{provider_id}/test
```

### Directly from SQLite

```bash
sqlite3 .titanos/titanos.sqlite

.tables
SELECT * FROM approvals ORDER BY created_at DESC LIMIT 10;
SELECT * FROM run_records ORDER BY created_at DESC LIMIT 10;
SELECT * FROM audit_log ORDER BY ts DESC LIMIT 50;
```

---

## Cleaning generated files

```bash
python scripts/run.py clean
```

This removes:

- Python `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`
- `.pytest_cache/`, `.coverage`, `htmlcov/`
- `dist/`, `build/`, `*.egg-info/`, `release/`
- `*.log` files in the project root
- Frontend caches: `.cache/`, `.parcel-cache/`, `.next/`
- Cypress artifacts: `cypress/videos/`, `cypress/screenshots/`
- `desktop-runtime/`

**The clean command never removes:**

- Source code directories (`titanos/`, `tests/`, `scripts/`, `ui/`, …)
- Documentation (`docs/`)
- Config examples, committed assets
- `.titanos/` (runtime DB and memory are preserved)
- `node_modules/` (requires a deliberate `npm install` to recreate)
- `.venv/` (virtual environment)

> [!TIP]
> To also wipe runtime data (approvals, run history, audit log), delete `.titanos/` manually after confirming there is nothing you need to preserve.

---

## Provider configs

Provider configs are stored in `provider_configs`. The API returns provider metadata, model/base URL, masked key, and a local secret reference. Raw provider API keys are not returned from list/get endpoints. The current local protection is a milestone placeholder; OS keychain storage should replace it before broad external distribution.

---

## Database migration

The schema is created automatically on first import of `titanos.store`. The current store also adds missing columns for the production-hardening slice at startup. Future migration tooling should add numbered schema migrations and rollback-safe upgrade checks.
