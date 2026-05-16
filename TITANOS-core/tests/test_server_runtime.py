from __future__ import annotations

import unittest
from unittest.mock import patch

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
