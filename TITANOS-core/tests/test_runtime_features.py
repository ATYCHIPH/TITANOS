from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from titanos.body.base import info
from titanos.body.cortex import CortexAdapter
from titanos.body.hands import HandsAdapter
from titanos.body.memory import MemoryAdapter, MemoryStore
from titanos.brain import TitanosBrain
from titanos.config.settings import settings
from titanos.contracts import BodyResult, BodySystem, BodyTask


class CandidateAdapter:
    info = info(
        BodySystem.CRAFT,
        "TITANOS Test Craft",
        "test",
        "test memory candidate capture",
    )

    def can_handle(self, task: BodyTask) -> bool:
        return True

    def run(self, task: BodyTask) -> BodyResult:
        return BodyResult(
            system=BodySystem.CRAFT,
            status="success",
            summary="done",
            memory_candidates=["Project runtime candidate capture is active"],
        )


class RuntimeFeatureTests(unittest.TestCase):
    def test_brain_captures_accepted_memory_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory = MemoryAdapter(MemoryStore(Path(temp_dir) / "memory.sqlite"))
            brain = TitanosBrain(body=[memory, CandidateAdapter()])

            result = brain.run("do candidate work")
            recalled = memory.run(BodyTask(goal="recall candidate capture"))

        self.assertEqual(result.status, "success")
        self.assertIn("Project runtime candidate capture is active", recalled.summary)

    def test_memory_semantic_recall_uses_lightweight_aliases(self) -> None:
        adapter = self._memory_adapter()

        adapter.run(BodyTask(goal="remember operator prefers quiet logs"))
        result = adapter.run(BodyTask(goal="recall silent logging"))

        self.assertIn("operator prefers quiet logs", result.summary)

    def test_hands_dry_run_does_not_execute_command(self) -> None:
        result = HandsAdapter().run(BodyTask(goal="dry run command: python --version"))

        self.assertEqual(result.status, "needs_input")
        self.assertIn("was not executed", result.summary)

    def test_hands_blocks_destructive_command_policy(self) -> None:
        result = HandsAdapter().run(BodyTask(goal="run command: git reset --hard"))

        self.assertEqual(result.status, "needs_input")
        self.assertIn("destructive command", result.summary)

    def test_hands_does_not_match_read_inside_readiness(self) -> None:
        self.assertFalse(
            HandsAdapter().can_handle(BodyTask(goal="think about production readiness"))
        )

    def test_cortex_reports_offline_ollama_without_throwing(self) -> None:
        original_url = settings.OLLAMA_BASE_URL
        settings.OLLAMA_BASE_URL = "http://127.0.0.1:1"
        try:
            result = CortexAdapter(model_name="ollama:missing").run(
                BodyTask(goal="think about this")
            )
        finally:
            settings.OLLAMA_BASE_URL = original_url

        self.assertEqual(result.status, "needs_input")
        self.assertIn("provider is offline", result.summary)

    def _memory_adapter(self) -> MemoryAdapter:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return MemoryAdapter(MemoryStore(Path(temp_dir.name) / "memory.sqlite"))


if __name__ == "__main__":
    unittest.main()
