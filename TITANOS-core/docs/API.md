# TITANOS API Documentation

## Hands Endpoints

### GET /hands/approvals
List all pending and historical command approvals.

### POST /hands/approvals/{id}/approve
Approve a pending command by its ID.

### POST /hands/approvals/{id}/run
Execute a previously approved command.

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

## Brain Endpoints

### GET /runs
List all Brain run records, including goal, route, status, and artifacts.

### POST /route/explain
Explain the routing decision for a given goal.
Request: `{ "goal": "..." }`
Response: `{ "system": "...", "confidence": 0.0, "reason": "..." }`

### GET /body/health
Get the health report for all registered body systems.
