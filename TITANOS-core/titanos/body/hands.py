from __future__ import annotations

import difflib
import shlex
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ..config.settings import settings
from ..contracts import BodyHealth, BodyResult, BodySystem, BodyTask
from ..platform.shell import Shell
from ..sources import project_root
from ..utils.logging import get_logger
from .base import info
from .. import store as _store


logger = get_logger(__name__)


@dataclass
class ApprovalRecord:
    """Lightweight view object kept for API/test compatibility."""
    id: str
    command: str
    risk: str
    reason: str
    approved: bool = False
    status: str = "pending"
    expires_at: str | None = None
    execution_count: int = 0

    @classmethod
    def from_row(cls, row: dict) -> "ApprovalRecord":
        return cls(
            id=row["id"],
            command=row["command"],
            risk=row["risk"],
            reason=row["reason"],
            approved=row["status"] in {"approved", "executed"},
            status=row["status"],
            expires_at=row.get("expires_at"),
            execution_count=row.get("execution_count", 0),
        )


class HandsAdapter:
    """Local execution adapter for files, shell, scripts, and data tasks."""

    info = info(
        BodySystem.HANDS,
        "TITANOS Hands",
        "open-interpreter graft",
        "local code, shell, files, scripts, data operations",
    )

    def __init__(self) -> None:
        self.command_timeout_seconds = settings.COMMAND_TIMEOUT_SECONDS
        self.destructive_words = tuple(
            word.strip().lower()
            for word in settings.COMMAND_DENYLIST.split(",")
            if word.strip()
        )
        self.allowed_commands = tuple(
            word.strip().lower()
            for word in settings.COMMAND_ALLOWLIST.split(",")
            if word.strip()
        )
        # In-memory cache kept for same-process lookup speed.
        # The canonical store is the SQLite DB via titanos.store.
        self._approval_cache: dict[str, ApprovalRecord] = {}
        try:
            from interpreter import interpreter
            self.interpreter = interpreter
            self.interpreter.auto_run = True
            # For the vertical slice, we'll keep it simple
            self.interpreter.system_message = (
                "You are the Hands system of TITANOS. "
                "Execute code locally to fulfill the goal."
            )
        except ImportError:
            self.interpreter = None

    def initialize(self) -> None:
        return None

    def health(self) -> BodyHealth:
        return BodyHealth(
            system=BodySystem.HANDS,
            status="ready",
            summary="Hands can read files, write files, edit files, and run explicit commands.",
            details={
                "interpreter_available": self.interpreter is not None,
                "command_timeout_seconds": self.command_timeout_seconds,
                "pending_approvals": len(_store.approval_list(status="pending")),
            },
        )

    def shutdown(self) -> None:
        return None

    def can_handle(self, task: BodyTask) -> bool:
        goal = task.goal.lower()
        direct_prefixes = (
            "run command:",
            "execute command:",
            "dry run command:",
            "preview command:",
            "shell:",
            "command:",
            "list files",
            "list directory",
            "show files",
            "read file ",
            "show file ",
            "open file ",
            "write file ",
            "preview write file ",
            "edit file ",
            "preview edit file ",
            "approve command ",
            "run approved command ",
        )
        if goal.startswith(direct_prefixes):
            return True
        trigger_words = {
            "run",
            "execute",
            "shell",
            "command",
            "script",
            "file",
            "read",
            "list",
            "directory",
            "python",
            "node",
            "write",
            "edit",
            "approve",
        }
        tokens = set(re.findall(r"[a-z0-9]+", goal))
        return bool(tokens & trigger_words)

    def run(self, task: BodyTask) -> BodyResult:
        goal = task.goal.strip()
        lowered = goal.lower()

        if lowered.startswith(("list files", "list directory", "show files")):
            return self._list_files()

        if lowered.startswith(("read file ", "show file ", "open file ")):
            requested_path = goal.split(" ", 2)[2].strip()
            return self._read_file(requested_path)

        if lowered.startswith("approve command "):
            approval_id = goal.split(" ", 2)[2].strip()
            return self.approve_command(approval_id)

        if lowered.startswith("run approved command "):
            approval_id = goal.split(" ", 3)[3].strip()
            return self.run_approved_command(approval_id)

        write_result = self._maybe_file_write(goal, preview=lowered.startswith("preview write file "))
        if write_result is not None:
            return write_result

        edit_result = self._maybe_file_edit(goal, preview=lowered.startswith("preview edit file "))
        if edit_result is not None:
            return edit_result

        dry_run = lowered.startswith(("dry run command:", "preview command:"))
        command = self._extract_command(goal)
        if command:
            if dry_run:
                return BodyResult(
                    system=BodySystem.HANDS,
                    status="needs_input",
                    summary=f"Dry run only. Command was not executed: {command}",
                )
            return self._run_command(command)

        if self.interpreter is None:
            return BodyResult(
                system=BodySystem.HANDS,
                status="needs_input",
                summary=(
                    "Hands can list files, read files, and run explicit commands. "
                    "Open Interpreter is not available for free-form execution."
                ),
                next_steps=[
                    "Use 'list files', 'read file <path>', or 'run command: <command>'."
                ],
            )

        try:
            messages = self.interpreter.chat(goal)
            summary = messages[-1]["content"] if messages else "No output from Hands."

            return BodyResult(
                system=BodySystem.HANDS,
                status="success",
                summary=summary,
                raw=messages,
            )
        except Exception as e:
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Hands error: {str(e)}",
            )

    def _list_files(self) -> BodyResult:
        root = project_root()
        entries = sorted(path.name for path in root.iterdir())
        return BodyResult(
            system=BodySystem.HANDS,
            status="success",
            summary="Project root entries: " + ", ".join(entries),
            artifacts=[str(root)],
        )

    def _read_file(self, requested_path: str) -> BodyResult:
        root = project_root()
        try:
            path = self._project_path(root, requested_path)
        except ValueError as exc:
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=str(exc),
            )
        if not path.exists() or not path.is_file():
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"File not found inside project root: {requested_path}",
            )

        text = path.read_text(encoding="utf-8")
        if len(text) > 4000:
            text = text[:4000] + "\n... truncated ..."

        return BodyResult(
            system=BodySystem.HANDS,
            status="success",
            summary=text,
            artifacts=[str(path)],
        )

    def _run_command(self, command: str) -> BodyResult:
        risk, reason = self.classify_command(command)
        _store.audit_log(
            "command_classified",
            meta={"command": command, "risk": risk, "reason": reason},
        )
        if risk in {"review", "blocked"}:
            record = self._create_approval(command, risk, reason)
            return BodyResult(
                system=BodySystem.HANDS,
                status="needs_input",
                summary=(
                    f"Command requires approval [{risk}]: {reason}: {command}\n"
                    f"Approval id: {record.id}"
                ),
                next_steps=[
                    f"Run 'approve command {record.id}' to approve it.",
                    f"Run 'run approved command {record.id}' after approval.",
                ],
                raw=record,
            )

        return self._execute_command(command)

    def _execute_command(
        self, command: str, *, approval_id: str | None = None
    ) -> BodyResult:
        logger.info("Executing command", extra={"extra": {"command": command}})
        _store.audit_log(
            "approved_command_executed",
            approval_id=approval_id,
            meta={"command": command},
        )
        completed = Shell.execute(
            command,
            cwd=str(project_root()),
            shell=True,
            capture_output=True,
            text=True,
            timeout=self.command_timeout_seconds,
        )
        output = "\n".join(
            part for part in (completed.stdout.strip(), completed.stderr.strip()) if part
        )
        if not output:
            output = f"Command exited with code {completed.returncode}."

        status = "success" if completed.returncode == 0 else "failed"
        summary = self._summarize_output(output)
        if approval_id:
            _store.approval_set_executed(approval_id, result_summary=summary)
        return BodyResult(
            system=BodySystem.HANDS,
            status=status,
            summary=summary,
            raw={"returncode": completed.returncode, "command": command},
        )

    def classify_command(self, command: str) -> tuple[str, str]:
        first_token = self._first_token(command)
        if not first_token:
            return "blocked", "empty command"
        if self.allowed_commands and first_token not in self.allowed_commands:
            return "blocked", f"'{first_token}' is not in the command allowlist"
        if self._looks_destructive(command):
            return "blocked", "destructive command"
        review_markers = (
            " pip install ",
            " npm install ",
            " git commit ",
            " git push ",
            " curl ",
            " invoke-webrequest ",
        )
        padded = f" {command.lower()} "
        if any(marker in padded for marker in review_markers):
            return "review", "command changes environment, network, or repository state"
        return "safe", "safe command"

    def approve_command(self, approval_id: str) -> BodyResult:
        row = _store.approval_get(approval_id)
        if row is None:
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Approval id not found: {approval_id}",
            )
        if row["status"] not in {"pending", "approved"}:
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Approval cannot be approved from status {row['status']}: {approval_id}",
            )
        _store.approval_approve(approval_id)
        _store.audit_log("approval_approved", approval_id=approval_id)
        row = _store.approval_get(approval_id)
        record = ApprovalRecord.from_row(row)  # type: ignore[arg-type]
        self._approval_cache[approval_id] = record
        return BodyResult(
            system=BodySystem.HANDS,
            status="success",
            summary=f"Approved command {approval_id}: {record.command}",
            raw=record,
        )

    def reject_command(self, approval_id: str) -> BodyResult:
        row = _store.approval_get(approval_id)
        if row is None:
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Approval id not found: {approval_id}",
            )
        if row["status"] not in {"pending", "approved"}:
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Approval cannot be rejected from status {row['status']}: {approval_id}",
            )
        row = _store.approval_reject(approval_id)
        _store.audit_log("approval_rejected", approval_id=approval_id)
        record = ApprovalRecord.from_row(row)  # type: ignore[arg-type]
        return BodyResult(
            system=BodySystem.HANDS,
            status="success",
            summary=f"Rejected command {approval_id}: {record.command}",
            raw=record,
        )

    def run_approved_command(self, approval_id: str) -> BodyResult:
        row = _store.approval_get(approval_id)
        if row is None:
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Approval id not found: {approval_id}",
            )
        record = ApprovalRecord.from_row(row)
        if record.status == "pending":
            return BodyResult(
                system=BodySystem.HANDS,
                status="needs_input",
                summary=f"Command approval is still pending: {approval_id}",
                next_steps=[f"Run 'approve command {approval_id}' first."],
            )
        if record.status in {"rejected", "expired", "executed"}:
            _store.audit_log(
                "approval_execution_blocked",
                approval_id=approval_id,
                meta={"status": record.status},
            )
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Approval cannot be executed from status {record.status}: {approval_id}",
            )
        if record.execution_count > 0:
            _store.audit_log("duplicate_approval_execution_blocked", approval_id=approval_id)
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Approved command is single-use and was already attempted: {approval_id}",
            )
        return self._execute_command(record.command, approval_id=approval_id)

    def _create_approval(self, command: str, risk: str, reason: str) -> ApprovalRecord:
        row = _store.approval_create(command=command, risk=risk, reason=reason)
        record = ApprovalRecord.from_row(row)
        self._approval_cache[record.id] = record
        _store.audit_log(
            "approval_created",
            approval_id=record.id,
            meta={"command": command, "risk": risk, "reason": reason},
        )
        return record

    @property
    def approvals(self) -> dict[str, ApprovalRecord]:
        """Backward-compat view: returns all non-rejected DB approvals keyed by id."""
        rows = _store.approval_list()
        return {
            r["id"]: ApprovalRecord.from_row(r)
            for r in rows
            if r["status"] != "rejected"
        }

    def _extract_command(self, goal: str) -> str | None:
        lowered = goal.lower()
        for prefix in (
            "dry run command:",
            "preview command:",
            "run command:",
            "execute command:",
            "shell:",
            "command:",
        ):
            if lowered.startswith(prefix):
                return goal[len(prefix) :].strip()
        return None

    def _policy_error(self, command: str) -> str | None:
        risk, reason = self.classify_command(command)
        return None if risk == "safe" else reason

    def _looks_destructive(self, command: str) -> bool:
        padded = f" {command.lower()} "
        tokens = tuple(shlex.split(command, posix=False))
        token_text = " " + " ".join(token.lower() for token in tokens) + " "
        return any(
            f" {word} " in padded or f" {word} " in token_text
            for word in self.destructive_words
        )

    def _first_token(self, command: str) -> str:
        try:
            return shlex.split(command, posix=False)[0].lower()
        except (IndexError, ValueError):
            return ""

    def _summarize_output(self, output: str) -> str:
        if len(output) <= 4000:
            return output
        head = output[:1800]
        tail = output[-1800:]
        omitted = len(output) - len(head) - len(tail)
        return f"{head}\n... omitted {omitted} characters ...\n{tail}"

    def _project_path(self, root: Path, requested_path: str) -> Path:
        path = (root / requested_path).resolve()
        if path == root or root in path.parents:
            return path
        raise ValueError(f"Path escapes project root: {requested_path}")

    def _maybe_file_write(self, goal: str, *, preview: bool) -> BodyResult | None:
        prefixes = ("preview write file ",) if preview else ("write file ",)
        payload = self._strip_any_prefix(goal, prefixes)
        if payload is None:
            return None
        requested_path, separator, content = payload.partition(":")
        if not separator:
            return BodyResult(
                system=BodySystem.HANDS,
                status="needs_input",
                summary="File write needs '<path>: <content>'.",
            )
        return self.write_file(requested_path.strip(), content.lstrip(), preview=preview)

    def _maybe_file_edit(self, goal: str, *, preview: bool) -> BodyResult | None:
        prefixes = ("preview edit file ",) if preview else ("edit file ",)
        payload = self._strip_any_prefix(goal, prefixes)
        if payload is None:
            return None
        requested_path, separator, edit_payload = payload.partition(":")
        if not separator or "=>" not in edit_payload:
            return BodyResult(
                system=BodySystem.HANDS,
                status="needs_input",
                summary="File edit needs '<path>: <old text> => <new text>'.",
            )
        old_text, _, new_text = edit_payload.partition("=>")
        return self.edit_file(
            requested_path.strip(),
            old_text.strip(),
            new_text.strip(),
            preview=preview,
        )

    def write_file(self, requested_path: str, content: str, *, preview: bool = False) -> BodyResult:
        root = project_root()
        try:
            path = self._project_path(root, requested_path)
        except ValueError as exc:
            return BodyResult(system=BodySystem.HANDS, status="failed", summary=str(exc))
        if not self._is_writable_project_path(path):
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Refusing to write outside project file area: {requested_path}",
            )

        before = path.read_text(encoding="utf-8") if path.exists() else ""
        label = path.relative_to(root).as_posix()
        diff = self._diff_text(before, content, label)
        if preview:
            _store.audit_log(
                "file_write_previewed",
                meta={"path": str(path.relative_to(root))},
            )
            return BodyResult(
                system=BodySystem.HANDS,
                status="needs_input",
                summary=diff or "No changes.",
                artifacts=[str(path)],
            )

        backup = self._backup_file(path) if path.exists() else None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        artifacts = [str(path)]
        if backup:
            artifacts.append(str(backup))
        _store.audit_log(
            "file_written",
            meta={
                "path": str(path.relative_to(root)),
                "backup": str(backup.relative_to(root)) if backup else None,
            },
        )
        return BodyResult(
            system=BodySystem.HANDS,
            status="success",
            summary=f"Wrote file: {path.relative_to(root)}",
            artifacts=artifacts,
            raw={"diff": diff, "backup": str(backup) if backup else None},
        )

    def edit_file(
        self,
        requested_path: str,
        old_text: str,
        new_text: str,
        *,
        preview: bool = False,
    ) -> BodyResult:
        root = project_root()
        try:
            path = self._project_path(root, requested_path)
        except ValueError as exc:
            return BodyResult(system=BodySystem.HANDS, status="failed", summary=str(exc))
        if not path.exists() or not path.is_file():
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"File not found inside project root: {requested_path}",
            )
        if not self._is_writable_project_path(path):
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Refusing to edit outside project file area: {requested_path}",
            )

        before = path.read_text(encoding="utf-8")
        if old_text not in before:
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary="Edit target text was not found.",
            )
        after = before.replace(old_text, new_text, 1)
        label = path.relative_to(root).as_posix()
        diff = self._diff_text(before, after, label)
        if preview:
            return BodyResult(
                system=BodySystem.HANDS,
                status="needs_input",
                summary=diff or "No changes.",
                artifacts=[str(path)],
            )

        backup = self._backup_file(path)
        path.write_text(after, encoding="utf-8")
        _store.audit_log(
            "file_edited",
            meta={
                "path": str(path.relative_to(root)),
                "backup": str(backup.relative_to(root)),
            },
        )
        return BodyResult(
            system=BodySystem.HANDS,
            status="success",
            summary=f"Edited file: {path.relative_to(root)}",
            artifacts=[str(path), str(backup)],
            raw={"diff": diff, "backup": str(backup)},
        )

    def _is_writable_project_path(self, path: Path) -> bool:
        root = project_root()
        if path == root or root not in path.parents:
            return False
        relative_parts = path.relative_to(root).parts
        return relative_parts[0] not in {".git", ".titanos", "__pycache__"}

    def _backup_file(self, path: Path) -> Path:
        root = project_root()
        stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
        relative = path.relative_to(root)
        backup = root / ".titanos" / "backups" / f"{stamp}" / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        _store.audit_log(
            "backup_created",
            meta={"source": str(relative), "backup": str(backup.relative_to(root))},
        )
        return backup

    def restore_backup(self, backup_id: str) -> BodyResult:
        root = project_root()
        backup_root = root / ".titanos" / "backups"
        try:
            snapshot, relative = backup_id.split("::", 1)
        except ValueError:
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary="Backup id must use '<snapshot>::<relative path>'.",
            )
        try:
            backup_path = (backup_root / snapshot / relative).resolve()
            target_path = self._project_path(root, relative)
        except ValueError as exc:
            return BodyResult(system=BodySystem.HANDS, status="failed", summary=str(exc))
        if backup_root not in backup_path.parents or not backup_path.is_file():
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Backup not found: {backup_id}",
            )
        if not self._is_writable_project_path(target_path):
            return BodyResult(
                system=BodySystem.HANDS,
                status="failed",
                summary=f"Refusing to restore into protected path: {relative}",
            )
        safety_backup = self._backup_file(target_path) if target_path.exists() else None
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, target_path)
        _store.audit_log(
            "backup_restored",
            meta={
                "backup_id": backup_id,
                "target": str(target_path.relative_to(root)),
                "safety_backup": str(safety_backup.relative_to(root)) if safety_backup else None,
            },
        )
        return BodyResult(
            system=BodySystem.HANDS,
            status="success",
            summary=f"Restored backup to {target_path.relative_to(root)}",
            artifacts=[str(target_path), str(backup_path)],
            raw={
                "backup_id": backup_id,
                "restored_path": str(target_path),
                "safety_backup": str(safety_backup) if safety_backup else None,
            },
        )

    def _diff_text(self, before: str, after: str, label: str) -> str:
        return "".join(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"a/{label}",
                tofile=f"b/{label}",
            )
        )

    def _strip_any_prefix(self, text: str, prefixes: tuple[str, ...]) -> str | None:
        lowered = text.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                return text[len(prefix):].strip()
        return None
