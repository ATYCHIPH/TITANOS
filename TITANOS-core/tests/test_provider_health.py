from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from titanos import providers


class ProviderHealthTests(unittest.TestCase):
    @patch("titanos.providers.urlopen")
    def test_provider_health_reports_online_provider(self, mock_urlopen) -> None:
        response = MagicMock()
        response.status = 200
        mock_urlopen.return_value.__enter__.return_value = response

        health = providers.provider_health(timeout=0.01)[0]

        self.assertEqual(health.status, "online")
        self.assertEqual(health.reason, "HTTP 200")

    @patch("titanos.providers.urlopen", side_effect=OSError("offline"))
    def test_provider_health_reports_offline_provider(self, mock_urlopen) -> None:
        health = providers.provider_health(timeout=0.01)[0]

        self.assertEqual(health.status, "offline")
        self.assertIn("OSError", health.reason)

    def test_configured_model_provider_uses_model_prefix(self) -> None:
        self.assertEqual(providers.configured_model_provider(), "ollama")


if __name__ == "__main__":
    unittest.main()
