from __future__ import annotations

import unittest

from titanos.body.hands import HandsAdapter
from titanos.contracts import BodySystem, BodyTask
from titanos.defaults import create_titanos


class HandsAdapterTests(unittest.TestCase):
    def test_lists_project_files(self) -> None:
        result = HandsAdapter().run(BodyTask(goal="list files"))

        self.assertEqual(result.system, BodySystem.HANDS)
        self.assertEqual(result.status, "success")
        self.assertIn("README.md", result.summary)
        self.assertIn("titanos", result.summary)

    def test_reads_project_file(self) -> None:
        result = HandsAdapter().run(BodyTask(goal="read file README.md"))

        self.assertEqual(result.status, "success")
        self.assertIn("# TITANOS", result.summary)

    def test_blocks_path_escape(self) -> None:
        result = HandsAdapter().run(BodyTask(goal="read file ..\\README.md"))

        self.assertEqual(result.status, "failed")
        self.assertIn("escapes project root", result.summary)

    def test_runs_explicit_command(self) -> None:
        result = HandsAdapter().run(
            BodyTask(goal="run command: python -m titanos --sources")
        )

        self.assertEqual(result.status, "success")
        self.assertIn("TITANOS source bodies", result.summary)

    def test_brain_routes_to_hands(self) -> None:
        result = create_titanos().run("list files")

        self.assertEqual(result.system, BodySystem.HANDS)
        self.assertEqual(result.status, "success")


if __name__ == "__main__":
    unittest.main()
