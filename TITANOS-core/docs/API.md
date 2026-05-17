# TITANOS API Documentation

## Hands Endpoints

### GET /hands/approvals
List all pending and historical command approvals.

### POST /hands/approvals/{id}/approve
Approve a pending command by its ID.

### POST /hands/approvals/{id}/reject
Reject a pending or approved command by its ID.

### POST /hands/approvals/{id}/run
Execute a previously approved command. Approved commands are single-use and cannot run again after an execution attempt.

### POST /hands/commands/classify
Classify a command for risk.
Request: `{ "command": "..." }`
Response: `{ "risk": "safe|review|blocked", "reason": "..." }`

### POST /hands/commands/preview
Dry-run preview of a command. Does not execute.

### POST /hands/files/write-preview
Preview a file write operation. Returns a unified diff.

### POST /hands/files/write
Perform a safe file write with backup.

### POST /hands/files/edit-preview
Preview a file edit operation. Returns a unified diff.

### POST /hands/files/edit
Perform a safe file edit with backup.

### GET /hands/backups
List all backup snapshots under `.titanos/backups/`.

### GET /hands/backups/{backup_id}
Read a specific backup snapshot.

### POST /hands/backups/{backup_id}/restore
Restore a backup snapshot to its original project path. A safety backup is created first when the current target exists.

## Runtime Endpoints

### GET /runtime/diagnostics
Return runtime mode, paths, database health, provider health, approval counts, run counts, and warnings.

### POST /runtime/diagnostics/export
Write a redacted diagnostics JSON bundle under runtime data.

## Provider Config Endpoints

### GET /providers/config
List saved provider config records. Raw API keys are never returned.

### POST /providers/config
Save or update a provider config using `{ "provider_id": "...", "label": "...", "base_url": "...", "model": "...", "api_key": "..." }`.

### DELETE /providers/config/{provider_id}
Delete a provider config and its local secret reference.

### POST /providers/config/{provider_id}/test
Update the provider config status from the backend provider health check.

## Brain Endpoints

### GET /runs
List all Brain run records, including goal, route, status, and artifacts.

### POST /route/explain
Explain the routing decision for a given goal.
Request: `{ "goal": "..." }`
Response: `{ "system": "...", "confidence": 0.0, "reason": "..." }`

### GET /body/health
Get the health report for all registered body systems.
