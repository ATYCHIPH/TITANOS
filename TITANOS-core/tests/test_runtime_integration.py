from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from titanos.body.cortex import CortexAdapter
from titanos.body.hands import HandsAdapter
from titanos.body.memory import MemoryAdapter, MemoryStore
from titanos.brain import TitanosBrain
from titanos.contracts import BodySystem


class RuntimeIntegrationTests(unittest.TestCase):
    def test_full_loop_routes_executes_and_remembers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory = MemoryAdapter(MemoryStore(Path(temp_dir) / "memory.sqlite"))
            brain = TitanosBrain(body=[memory, HandsAdapter()])

            remembered = brain.run("remember integration loop is active")
            listed = brain.run("list files")
            recalled = brain.run("recall integration loop")

        self.assertEqual(remembered.system, BodySystem.MEMORY)
        self.assertEqual(listed.system, BodySystem.HANDS)
        self.assertEqual(recalled.system, BodySystem.MEMORY)
        self.assertIn("integration loop is active", recalled.summary)

    def test_cortex_registers_body_tools_without_schema_error(self) -> None:
        cortex = CortexAdapter(tools=[MemoryAdapter(), HandsAdapter()])

        agent = cortex._get_agent()

        self.assertIsNotNone(agent)

    def test_cli_doctor_runs(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "titanos", "doctor"],
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "TITANOS_MEMORY_PATH": str(Path(tempfile.gettempdir()) / "titanos-test-memory.sqlite")},
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("TITANOS doctor", completed.stdout)
        self.assertIn("Body systems", completed.stdout)


if __name__ == "__main__":
    unittest.main()
