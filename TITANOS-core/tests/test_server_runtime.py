from __future__ import annotations

import unittest
import time
from unittest.mock import patch
from pathlib import Path

from fastapi.testclient import TestClient

from titanos.server.app import app
from titanos.server.auth import create_access_token
from titanos.providers import ProviderHealth


class ServerRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        token = create_access_token({"sub": "test_operator"})
        self.headers = {"Authorization": f"Bearer {token}"}

    def test_provider_health_endpoint_uses_shared_provider_module(self) -> None:
        fake = ProviderHealth("ollama", "Ollama", "http://test", "offline", "mocked", 1)
        with patch("titanos.server.app.check_provider_health", return_value=[fake]):
            response = self.client.get("/health/providers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["providers"][0]["status"], "offline")

    def test_doctor_endpoint_includes_paths_and_providers(self) -> None:
        fake = ProviderHealth("ollama", "Ollama", "http://test", "online", "mocked", 1)
        with patch("titanos.server.app.check_provider_health", return_value=[fake]):
            response = self.client.get("/doctor")

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn("paths", data)
        self.assertIn("providers", data)

    def test_runtime_endpoint_reports_server_mode(self) -> None:
        response = self.client.get("/runtime")

        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()["mode"], {"server", "desktop"})
        self.assertIn("data_dir", response.json())
        self.assertIn("schema_version", response.json())

    def test_runtime_policy_endpoint_exposes_guardrails(self) -> None:
        response = self.client.get("/runtime/policy", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["writable_scope"], "project-root-only")
        self.assertIn(".git", data["protected_path_roots"])

    def test_protected_endpoint_requires_auth_outside_desktop_mode(self) -> None:
        response = self.client.get("/runs")

        self.assertEqual(response.status_code, 401)

    def test_role_guard_rejects_insufficient_role(self) -> None:
        token = create_access_token({"sub": "viewer", "roles": ["viewer"]})
        response = self.client.post(
            "/run",
            headers={"Authorization": f"Bearer {token}"},
            json={"goal": "list files"},
        )

        self.assertEqual(response.status_code, 403)

    def test_provider_config_endpoints_redact_raw_secret(self) -> None:
        response = self.client.post(
            "/providers/config",
            headers=self.headers,
            json={
                "provider_id": "openai",
                "label": "OpenAI",
                "model": "gpt-test",
                "api_key": "sk-test-secret-value",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["secret_ref"], "local-provider:openai")
        self.assertNotIn("sk-test-secret-value", str(data))

        listed = self.client.get("/providers/config", headers=self.headers)
        self.assertEqual(listed.status_code, 200)
        self.assertNotIn("sk-test-secret-value", str(listed.json()))

    def test_provider_presets_include_universal_options(self) -> None:
        response = self.client.get("/providers/presets", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        ids = {provider["provider_id"] for provider in response.json()["providers"]}
        self.assertIn("ollama-cloud", ids)
        self.assertIn("custom-openai", ids)
        self.assertIn("openrouter", ids)

    def test_chat_endpoint_uses_real_brain_and_session_context(self) -> None:
        hello = self.client.post("/chat", json={"goal": "hello"}, headers=self.headers)

        self.assertEqual(hello.status_code, 200)
        first = hello.json()
        self.assertEqual(first["system"], "voice")
        self.assertTrue(first["session_id"])

        marker = self.client.post(
            "/chat",
            json={"goal": "my session marker is titanium", "session_id": first["session_id"]},
            headers=self.headers,
        )
        self.assertEqual(marker.status_code, 200)

        recalled = self.client.post(
            "/chat",
            json={"goal": "what did I say before?", "session_id": first["session_id"]},
            headers=self.headers,
        )
        self.assertEqual(recalled.status_code, 200)
        self.assertIn("titanium", recalled.json()["response"])

    def test_runtime_diagnostics_and_export_redact_secrets(self) -> None:
        response = self.client.get("/runtime/diagnostics", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("pending_approvals", response.json())
        self.assertIn("schema_version", response.json())

        exported = self.client.post("/runtime/diagnostics/export", headers=self.headers)
        self.assertEqual(exported.status_code, 200)
        path = Path(exported.json()["path"])
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("super-secret-dev-key", text)

    def test_session_workspace_and_usage_endpoints(self) -> None:
        session = self.client.post(
            "/sessions",
            headers=self.headers,
            json={
                "actor": "ignored-in-favor-of-token",
                "mode": "desktop",
                "metadata": {"client": "test"},
            },
        )
        self.assertEqual(session.status_code, 200)
        self.assertEqual(session.json()["actor"], "test_operator")

        sessions = self.client.get("/sessions", headers=self.headers)
        self.assertEqual(sessions.status_code, 200)
        self.assertTrue(sessions.json()["sessions"])

        workspace = self.client.post(
            "/workspaces",
            headers=self.headers,
            json={"root_path": str(Path.cwd()), "label": "Test Workspace"},
        )
        self.assertEqual(workspace.status_code, 200)
        self.assertEqual(workspace.json()["label"], "Test Workspace")

        usage_event = self.client.post(
            "/usage/events",
            headers=self.headers,
            json={
                "provider_id": "openai",
                "model": "gpt-test",
                "input_tokens": 2,
                "output_tokens": 3,
                "estimated_cost": 0.01,
            },
        )
        self.assertEqual(usage_event.status_code, 200)

        usage = self.client.get("/usage", headers=self.headers)
        self.assertEqual(usage.status_code, 200)
        self.assertGreaterEqual(usage.json()["total_events"], 1)

    def test_background_job_lifecycle_and_cancel_endpoint(self) -> None:
        created = self.client.post(
            "/jobs",
            headers=self.headers,
            json={"goal": "dry run command: python --version"},
        )
        self.assertEqual(created.status_code, 200)
        job_id = created.json()["id"]
        self.assertIn(created.json()["status"], {"queued", "running", "completed"})

        final = created.json()
        for _ in range(30):
            final_response = self.client.get(f"/jobs/{job_id}", headers=self.headers)
            self.assertEqual(final_response.status_code, 200)
            final = final_response.json()
            if final["status"] in {"completed", "failed", "cancelled"}:
                break
            time.sleep(0.05)

        self.assertEqual(final["status"], "completed")
        self.assertEqual(final["result"]["status"], "needs_input")

        cancelled = self.client.post(f"/jobs/{job_id}/cancel", headers=self.headers)
        self.assertEqual(cancelled.status_code, 200)
        self.assertTrue(cancelled.json()["cancel_requested"])

    def test_reject_approval_endpoint(self) -> None:
        created = self.client.post(
            "/run",
            headers=self.headers,
            json={"goal": "run command: pip install pytest"},
        )
        self.assertEqual(created.status_code, 200)
        approval_id = created.json()["summary"].split("Approval id: ", 1)[1].strip()

        rejected = self.client.post(
            f"/hands/approvals/{approval_id}/reject",
            headers=self.headers,
        )

        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.json()["status"], "rejected")

    def test_backup_inspect_and_restore_flow(self) -> None:
        target = Path("restore_test_safe.txt")
        target.write_text("before", encoding="utf-8")
        try:
            edited = self.client.post(
                "/hands/files/edit",
                headers=self.headers,
                json={"path": str(target), "old_text": "before", "new_text": "after"},
            )
            self.assertEqual(edited.status_code, 200)
            backups = self.client.get("/hands/backups", headers=self.headers)
            self.assertEqual(backups.status_code, 200)
            backup = next(
                item for item in backups.json()["backups"]
                if item["original_path"].endswith(target.name)
            )

            inspected = self.client.get(f"/hands/backups/{backup['id']}", headers=self.headers)
            self.assertEqual(inspected.status_code, 200)

            restored = self.client.post(
                f"/hands/backups/{backup['id']}/restore",
                headers=self.headers,
            )
            self.assertEqual(restored.status_code, 200)
            self.assertEqual(target.read_text(encoding="utf-8"), "before")
        finally:
            if target.exists():
                target.unlink()

    def test_memory_crud_endpoints(self) -> None:
        created = self.client.post(
            "/memory",
            headers=self.headers,
            json={"content": "server memory api test"},
        )
        self.assertEqual(created.status_code, 200)
        memory_id = created.json()["id"]

        listed = self.client.get("/memory")
        self.assertEqual(listed.status_code, 200)
        self.assertTrue(
            any(item["id"] == memory_id for item in listed.json()["memories"])
        )

        searched = self.client.get("/memory/search", params={"q": "api test"})
        self.assertEqual(searched.status_code, 200)
        self.assertTrue(searched.json()["memories"])

        updated = self.client.patch(
            f"/memory/{memory_id}",
            headers=self.headers,
            json={"content": "server memory api updated"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["text"], "server memory api updated")

        deleted = self.client.delete(f"/memory/{memory_id}", headers=self.headers)
        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.json()["deleted"])


if __name__ == "__main__":
    unittest.main()
