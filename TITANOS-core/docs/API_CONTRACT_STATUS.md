# TITANOS API Contract Audit Report

Generated automatically.

This report validates that the React UI `apiService.js` client endpoints perfectly align with the backend FastAPI router definitions.

## Summary Metrics

- **FastAPI Defined Routes**: 42
- **React UI Queries**: 19
- **Fully Verified Mappings**: 19
- **Contract Violations / Warnings**: 0

## Verified Mappings Matrix

| UI Query Endpoint | Matching FastAPI Backend Route | Status |
|---|---|---|
| `/audit/events` | `/audit/events` | 🟢 Verified |
| `/body/health` | `/body/health` | 🟢 Verified |
| `/doctor` | `/doctor` | 🟢 Verified |
| `/hands/approvals` | `/hands/approvals` | 🟢 Verified |
| `/hands/approvals/*/approve` | `/hands/approvals/{approval_id}/approve` | 🟢 Verified |
| `/hands/approvals/*/reject` | `/hands/approvals/{approval_id}/reject` | 🟢 Verified |
| `/hands/backups` | `/hands/backups` | 🟢 Verified |
| `/hands/backups/*` | `/hands/backups/{backup_id:path}` | 🟢 Verified |
| `/hands/backups/*/restore` | `/hands/backups/{backup_id:path}/restore` | 🟢 Verified |
| `/health/providers` | `/health/providers` | 🟢 Verified |
| `/memory` | `/memory` | 🟢 Verified |
| `/providers/config` | `/providers/config` | 🟢 Verified |
| `/providers/config/*` | `/providers/config/{provider_id}` | 🟢 Verified |
| `/providers/config/*/test` | `/providers/config/{provider_id}/test` | 🟢 Verified |
| `/runs` | `/runs` | 🟢 Verified |
| `/runs/*` | `/runs/{run_id}` | 🟢 Verified |
| `/runtime` | `/runtime` | 🟢 Verified |
| `/runtime/diagnostics` | `/runtime/diagnostics` | 🟢 Verified |
| `/runtime/diagnostics/export` | `/runtime/diagnostics/export` | 🟢 Verified |


*Note: Verified mappings ensure loopback requests resolve with strict contract typing.*
