from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from titanos import providers


class ProviderHealthTests(unittest.TestCase):
    def test_provider_health_reports_online_provider(self) -> None:
        response = MagicMock()
        response.status = 200
        mock_urlopen = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = response

        original = providers.urlopen
        providers.urlopen = mock_urlopen
        try:
            health = providers.provider_health(timeout=0.01)[0]
        finally:
            providers.urlopen = original

        self.assertEqual(health.status, "online")
        self.assertEqual(health.reason, "HTTP 200")

    def test_provider_health_reports_offline_provider(self) -> None:
        original = providers.urlopen
        providers.urlopen = MagicMock(side_effect=OSError("offline"))
        try:
            health = providers.provider_health(timeout=0.01)[0]
        finally:
            providers.urlopen = original

        self.assertEqual(health.status, "offline")
        self.assertIn("OSError", health.reason)

    def test_configured_model_provider_uses_model_prefix(self) -> None:
        self.assertEqual(providers.configured_model_provider(), "ollama")

    def test_provider_presets_include_ollama_cloud_and_custom(self) -> None:
        presets = {preset["provider_id"]: preset for preset in providers.provider_presets()}

        self.assertEqual(presets["ollama-cloud"]["base_url"], "https://ollama.com/api")
        self.assertEqual(presets["ollama-cloud"]["default_model"], "gpt-oss:120b")
        self.assertIn("custom-openai", presets)
        self.assertIn("custom-ollama", presets)

    def test_saved_provider_check_uses_authorization_header(self) -> None:
        response = MagicMock()
        response.status = 200
        mock_urlopen = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = response

        original = providers.urlopen
        providers.urlopen = mock_urlopen
        try:
            health = providers.check_saved_provider_config(
                {
                    "provider_id": "openai",
                    "label": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4.1-mini",
                },
                api_key="sk-test",
                timeout=0.01,
            )
        finally:
            providers.urlopen = original

        request = mock_urlopen.call_args.args[0]
        self.assertEqual(health.status, "healthy")
        self.assertEqual(request.headers["Authorization"], "Bearer sk-test")


if __name__ == "__main__":
    unittest.main()
