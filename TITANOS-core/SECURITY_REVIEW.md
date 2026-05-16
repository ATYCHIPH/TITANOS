# TITANOS Security Review

This document assesses the security posture of TITANOS and outlines controls for sensitive operations.

## 1. Secrets Management
- **Issue**: Provider API keys (OpenAI, Google, etc.) are sensitive credentials.
- **Control**: Keys are stored in a `.env` file, which is excluded from git via `.gitignore`.
- **Control**: The `Settings` system loads keys from environment variables as a primary source.
- **Risk**: Users might accidentally commit their `.env` file if not careful.

## 2. Command Execution (Hands)
- **Issue**: TITANOS can execute arbitrary shell commands and Python code.
- **Control**: Command risk classification (safe/review/blocked) is performed before execution.
- **Control**: Explicit operator approval is required for all "review" level commands.
- **Control**: "Blocked" commands (destructive or not allowed) cannot be executed.
- **Risk**: Advanced prompt injection bypassing classification logic.

## 3. Filesystem Access
- **Issue**: TITANOS can read and write files on the host system.
- **Control**: Access is restricted to the project root, excluding sensitive directories like `.git` and `.titanos`.
- **Control**: Path validation prevents traversal attacks.
- **Control**: All writes and edits create a timestamped backup in `.titanos/backups/`.
- **Control**: Unified diff previews are provided for operator review.

## 4. Local API & Web UI
- **Issue**: The FastAPI server listens on localhost, but could be exposed.
- **Control**: Default binding is `127.0.0.1` (localhost only).
- **Control**: CORS is restricted to relevant origins in production.
- **Risk**: Cross-Site Request Forgery (CSRF) if the operator visits a malicious site while TITANOS is running.

## 5. Plugin Security
- **Issue**: Third-party plugins could introduce malicious code.
- **Control**: Plugins must be explicitly registered in `titanos/sources.py`.
- **Control**: Plugin execution is subject to the same sandbox controls as core body systems.

## 6. Data Privacy
- **Issue**: Session history and memory contain user-specific information.
- **Control**: All data is stored locally in `.titanos/`. No telemetry or data is sent to TITANOS servers unless configured by the user.
- **Risk**: Local data theft if the host machine is compromised.

## Security Audit Status (Pass/Fail)
- [x] Path escape blocking (Hands): **PASS**
- [x] Environment variable key loading: **PASS**
- [x] Command risk classification & approvals: **PASS**
- [x] File write/edit safety & backups: **PASS**
- [x] Local-only API binding (default): **PASS**
- [ ] Sandbox execution for untrusted code: **PENDING**
