# TITANOS Operations Manual

## Command Approvals
TITANOS uses a risk-based approval model for shell commands.
- **Safe**: Commands that only read state or are on the allowlist run immediately.
- **Review**: Commands that modify the environment (e.g., `pip install`, `git push`) require explicit operator approval via the Approvals tab or API.
- **Blocked**: Destructive commands or those on the denylist are blocked by default.

## File Safety & Backups
All file write and edit operations are performed safely:
1. **Preview**: A unified diff is generated for operator review.
2. **Backup**: Before any change, the existing file is backed up to `.titanos/backups/YYYYMMDDHHMMSS/path/to/file`.
3. **Atomic Write**: Files are written with UTF-8 encoding and validated.

## Run Records & History
Every goal processed by the Brain is recorded in the `run_records` list.
Records include:
- Original goal
- Routed system (e.g., Hands, Cortex)
- Routing confidence and reasoning
- Execution status and duration
- Generated artifacts (paths, IDs)

## Health Checks
Body systems provide real-time health reports.
- **Ready**: System is initialized and functional.
- **Error**: System encountered a failure (e.g., missing dependencies).
- **Unknown**: System does not expose health.

## Provider Warnings
Operator UI shows warnings for:
- Development JWT secrets.
- Overly permissive CORS settings.
- Offline or unreachable AI providers (Ollama, Gemini).
