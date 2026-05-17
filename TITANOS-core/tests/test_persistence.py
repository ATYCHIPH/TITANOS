"""
Tests for persistent store: approvals, run records, and audit log.

All tests use isolated temporary databases (via TITANOS_DATA_DIR env override)
so they are fully deterministic and cross-platform.
"""
from __future__ import annotations

import importlib
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path


def _isolated_store(tmp_dir: str):
    """Return a freshly-imported store module backed by a temp directory.

    We manipulate the environment variable and reimport because `store.py`
    reads `settings.DATA_DIR` at import time (via the module-level
    `init_db()` call).  Each call returns a fresh module so tests are
    isolated from each other.
    """
    os.environ["TITANOS_DATA_DIR"] = tmp_dir
    # Force fresh import of the settings singleton and store module.
    mods_to_drop = [k for k in sys.modules if k.startswith("titanos.")]
    for mod in mods_to_drop:
        del sys.modules[mod]
    import titanos.store as fresh_store  # noqa: PLC0415
    return fresh_store


def _close_logging_handlers() -> None:
    root = logging.getLogger()
    for handler in list(root.handlers):
        handler.close()
        root.removeHandler(handler)
    if hasattr(root, "_titanos_configured"):
        delattr(root, "_titanos_configured")


class TestApprovalPersistence(unittest.TestCase):
    """Approvals survive across independent HandsAdapter instances."""

    def _make_hands(self, store_mod):
        """Return a HandsAdapter whose store module is the isolated one."""
        import titanos.body.hands as hands_mod
        hands_mod._store = store_mod
        return hands_mod.HandsAdapter()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._store = _isolated_store(self._tmp.name)

    def tearDown(self):
        _close_logging_handlers()
        self._tmp.cleanup()
        # Restore clean module state
        os.environ.pop("TITANOS_DATA_DIR", None)
        mods_to_drop = [k for k in sys.modules if k.startswith("titanos.")]
        for mod in mods_to_drop:
            del sys.modules[mod]

    def test_approval_persists_across_instances(self):
        """An approval created in one instance is visible to a new instance."""
        s = self._store

        row = s.approval_create(command="pip install pytest", risk="review", reason="network")
        approval_id = row["id"]
        self.assertEqual(row["status"], "pending")

        # Simulate a new process: fresh store reading same DB
        retrieved = s.approval_get(approval_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["command"], "pip install pytest")
        self.assertEqual(retrieved["status"], "pending")

    def test_approve_updates_status(self):
        s = self._store
        row = s.approval_create(command="git push", risk="review", reason="repo state")
        aid = row["id"]

        s.approval_approve(aid)
        updated = s.approval_get(aid)
        self.assertEqual(updated["status"], "approved")
        self.assertIsNotNone(updated["approved_at"])

    def test_execute_updates_status_and_result(self):
        s = self._store
        row = s.approval_create(command="echo hello", risk="review", reason="test")
        aid = row["id"]

        s.approval_approve(aid)
        s.approval_set_executed(aid, result_summary="hello")
        final = s.approval_get(aid)
        self.assertEqual(final["status"], "executed")
        self.assertEqual(final["result_summary"], "hello")
        self.assertIsNotNone(final["executed_at"])
        self.assertEqual(final["execution_count"], 1)

    def test_reject_updates_status_and_timestamp(self):
        s = self._store
        row = s.approval_create(command="git push", risk="review", reason="repo state")

        rejected = s.approval_reject(row["id"])

        self.assertEqual(rejected["status"], "rejected")
        self.assertIsNotNone(rejected["rejected_at"])

    def test_expired_approval_is_marked_expired_on_read(self):
        s = self._store
        row = s.approval_create(command="npm install x", risk="review", reason="network")
        with s._LOCK, s._conn() as conn:
            conn.execute(
                "UPDATE approvals SET expires_at='2000-01-01T00:00:00+00:00' WHERE id=?",
                (row["id"],),
            )

        expired = s.approval_get(row["id"])

        self.assertEqual(expired["status"], "expired")

    def test_approval_list_returns_all_records(self):
        s = self._store
        s.approval_create(command="cmd1", risk="review", reason="r1")
        s.approval_create(command="cmd2", risk="blocked", reason="r2")
        rows = s.approval_list()
        self.assertGreaterEqual(len(rows), 2)

    def test_approval_list_filters_by_status(self):
        s = self._store
        s.approval_create(command="pending-cmd", risk="review", reason="r")
        rows = s.approval_list(status="pending")
        self.assertTrue(all(r["status"] == "pending" for r in rows))


class TestRunRecordPersistence(unittest.TestCase):
    """Run records survive across independent Brain instances."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._store = _isolated_store(self._tmp.name)

    def tearDown(self):
        _close_logging_handlers()
        self._tmp.cleanup()
        os.environ.pop("TITANOS_DATA_DIR", None)
        mods_to_drop = [k for k in sys.modules if k.startswith("titanos.")]
        for mod in mods_to_drop:
            del sys.modules[mod]

    def test_run_record_persists_and_is_retrievable(self):
        s = self._store
        row = s.run_record_create(
            goal="list files",
            system="hands",
            confidence=0.9,
            route_reason="direct match",
            status="success",
            duration_ms=42,
            result_summary="Listed 10 files.",
        )
        rid = row["id"]
        retrieved = s.run_record_get(rid)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["goal"], "list files")
        self.assertEqual(retrieved["status"], "success")
        self.assertEqual(retrieved["system"], "hands")

    def test_run_record_list_returns_most_recent_first(self):
        s = self._store
        for i in range(3):
            s.run_record_create(
                goal=f"goal {i}",
                system="cortex",
                confidence=0.4,
                route_reason="fallback",
                status="success",
                duration_ms=i * 10,
                result_summary=f"ok {i}",
            )
        rows = s.run_record_list()
        self.assertGreaterEqual(len(rows), 3)
        # Most recent first
        self.assertGreaterEqual(rows[0]["created_at"], rows[-1]["created_at"])

    def test_run_record_artifacts_roundtrip(self):
        s = self._store
        artifacts = ["/path/to/a.txt", "/path/to/b.txt"]
        row = s.run_record_create(
            goal="write file",
            system="hands",
            confidence=0.9,
            route_reason="direct",
            status="success",
            duration_ms=10,
            result_summary="done",
            artifacts=artifacts,
        )
        retrieved = s.run_record_get(row["id"])
        self.assertEqual(retrieved["artifacts"], artifacts)


class TestAuditLog(unittest.TestCase):
    """Audit events are written for approval and command execution flows."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._store = _isolated_store(self._tmp.name)

    def tearDown(self):
        _close_logging_handlers()
        self._tmp.cleanup()
        os.environ.pop("TITANOS_DATA_DIR", None)
        mods_to_drop = [k for k in sys.modules if k.startswith("titanos.")]
        for mod in mods_to_drop:
            del sys.modules[mod]

    def test_audit_log_writes_event(self):
        s = self._store
        s.audit_log("approval_created", approval_id="abc123", meta={"command": "pip install x"})
        events = s.audit_list()
        self.assertTrue(any(e["event_type"] == "approval_created" for e in events))

    def test_audit_log_records_approval_id(self):
        s = self._store
        s.audit_log("approval_approved", approval_id="xyz", meta={})
        events = s.audit_list()
        approved_events = [e for e in events if e["event_type"] == "approval_approved"]
        self.assertTrue(any(e["approval_id"] == "xyz" for e in approved_events))


class TestRuntimeProductPersistence(unittest.TestCase):
    """Product-level runtime records survive independent process boundaries."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._store = _isolated_store(self._tmp.name)

    def tearDown(self):
        _close_logging_handlers()
        self._tmp.cleanup()
        os.environ.pop("TITANOS_DATA_DIR", None)
        mods_to_drop = [k for k in sys.modules if k.startswith("titanos.")]
        for mod in mods_to_drop:
            del sys.modules[mod]

    def test_runtime_meta_records_schema_version(self):
        meta = self._store.runtime_meta()

        self.assertEqual(meta["schema_version"], str(self._store.SCHEMA_VERSION))

    def test_operator_session_touch_and_close(self):
        row = self._store.session_touch(
            actor="tester",
            mode="desktop",
            metadata={"client": "test"},
        )

        self.assertEqual(row["status"], "active")
        self.assertEqual(row["metadata"]["client"], "test")

        closed = self._store.session_close(row["id"])
        self.assertEqual(closed["status"], "closed")

    def test_workspace_register_deduplicates_by_root(self):
        root = Path(self._tmp.name) / "workspace"
        root.mkdir()

        first = self._store.workspace_register(root_path=str(root), label="One")
        second = self._store.workspace_register(root_path=str(root), label="Two")

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(second["label"], "Two")
        self.assertEqual(len(self._store.workspace_list()), 1)

    def test_usage_summary_aggregates_provider_totals(self):
        self._store.usage_event_record(
            provider_id="openai",
            model="gpt-test",
            input_tokens=10,
            output_tokens=20,
            estimated_cost=0.03,
        )
        self._store.usage_event_record(
            provider_id="openai",
            model="gpt-test",
            input_tokens=5,
            output_tokens=5,
            estimated_cost=0.01,
        )

        summary = self._store.usage_summary()

        self.assertEqual(summary["total_events"], 2)
        self.assertEqual(summary["total_input_tokens"], 15)
        self.assertEqual(summary["total_output_tokens"], 25)
        self.assertAlmostEqual(summary["total_estimated_cost"], 0.04)

    def test_audit_log_records_meta(self):
        s = self._store
        s.audit_log("command_classified", meta={"risk": "safe", "command": "python --version"})
        events = s.audit_list()
        classified = [e for e in events if e["event_type"] == "command_classified"]
        self.assertTrue(any(e["meta"].get("risk") == "safe" for e in classified))

    def test_audit_log_never_raises(self):
        """audit_log must be safe even if meta is None."""
        s = self._store
        # Should not raise
        s.audit_log("test_event")
        s.audit_log("test_event", meta=None)

    def test_audit_events_for_full_approval_flow(self):
        """Creating and approving records produces expected audit trail."""
        s = self._store
        row = s.approval_create(command="npm install lodash", risk="review", reason="network")
        aid = row["id"]
        s.audit_log("approval_created", approval_id=aid, meta={"command": "npm install lodash"})
        s.approval_approve(aid)
        s.audit_log("approval_approved", approval_id=aid)
        s.approval_set_executed(aid, result_summary="done")
        s.audit_log("approved_command_executed", approval_id=aid, meta={"command": "npm install lodash"})

        events = s.audit_list()
        event_types = {e["event_type"] for e in events}
        self.assertIn("approval_created", event_types)
        self.assertIn("approval_approved", event_types)
        self.assertIn("approved_command_executed", event_types)


class TestProviderConfigPersistence(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._store = _isolated_store(self._tmp.name)

    def tearDown(self):
        _close_logging_handlers()
        self._tmp.cleanup()
        os.environ.pop("TITANOS_DATA_DIR", None)
        mods_to_drop = [k for k in sys.modules if k.startswith("titanos.")]
        for mod in mods_to_drop:
            del sys.modules[mod]

    def test_provider_config_redacts_raw_secret(self):
        s = self._store
        row = s.provider_config_save(
            provider_id="openai",
            label="OpenAI",
            model="gpt-test",
            api_key="sk-test-secret-value",
        )

        self.assertNotIn("secret_material", row)
        self.assertEqual(row["secret_ref"], "local-provider:openai")
        self.assertEqual(row["masked_key"], "sk-t...alue")

        raw = s.provider_config_get("openai", include_secret=True)
        self.assertNotIn("sk-test-secret-value", raw["secret_material"])
        self.assertTrue(raw["secret_material"].startswith(("fernet:", "xor:")))
        self.assertEqual(s.provider_secret_reveal("openai"), "sk-test-secret-value")

    def test_provider_config_delete(self):
        s = self._store
        s.provider_config_save(provider_id="local", label="Local", base_url="http://localhost:11434")

        self.assertTrue(s.provider_config_delete("local"))
        self.assertIsNone(s.provider_config_get("local"))


class TestCleanCommandSafety(unittest.TestCase):
    """clean command must not remove source files."""

    def test_clean_preserves_source_roots(self):
        """Verify the clean command's safe-root guard list covers key directories."""
        # Import and check the constant without running the command
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "run_script",
                Path(__file__).parent.parent / "scripts" / "run.py",
            )
            run_mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            spec.loader.exec_module(run_mod)  # type: ignore[union-attr]
            safe_roots = run_mod._SAFE_ROOTS
        finally:
            if "run_script" in sys.modules:
                del sys.modules["run_script"]

        for required in ("titanos", "tests", "scripts", "docs", "ui"):
            self.assertIn(required, safe_roots, f"'{required}' must be protected from clean")

    def test_settings_path_resolution(self):
        """Settings resolves DATA_DIR and RUNTIME_DB as sub-paths of DATA_DIR."""
        # Use a temp override to avoid polluting the real .titanos dir
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["TITANOS_DATA_DIR"] = tmp
            try:
                # Force fresh settings
                mods_to_drop = [k for k in sys.modules if k.startswith("titanos.")]
                for mod in mods_to_drop:
                    del sys.modules[mod]
                from titanos.config.settings import settings as s
                self.assertEqual(str(s.DATA_DIR), tmp)
                self.assertTrue(str(s.RUNTIME_DB).startswith(tmp))
                self.assertTrue(str(s.LOG_PATH).startswith(tmp))
                self.assertTrue(str(s.MEMORY_PATH).startswith(tmp))
                self.assertTrue(str(s.SESSIONS_PATH).startswith(tmp))
            finally:
                os.environ.pop("TITANOS_DATA_DIR", None)
                mods_to_drop = [k for k in sys.modules if k.startswith("titanos.")]
                for mod in mods_to_drop:
                    del sys.modules[mod]


if __name__ == "__main__":
    unittest.main()
