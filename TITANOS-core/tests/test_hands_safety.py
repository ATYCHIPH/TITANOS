from __future__ import annotations

import unittest
from pathlib import Path

from titanos.body.hands import HandsAdapter
from titanos.contracts import BodyTask
from titanos.sources import project_root


class HandsSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = HandsAdapter()
        self.root = project_root()
        self.scratch = self.root / "scratch" / "hands_safety_test.txt"
        self.addCleanup(self._cleanup_scratch)

    def test_classifies_safe_review_and_blocked_commands(self) -> None:
        self.assertEqual(
            self.adapter.classify_command("python -m titanos --sources")[0],
            "safe",
        )
        self.assertEqual(
            self.adapter.classify_command("pip install example-package")[0],
            "review",
        )
        self.assertEqual(
            self.adapter.classify_command("git reset --hard")[0],
            "blocked",
        )

    def test_review_command_creates_approval_and_replays_after_approval(self) -> None:
        result = self.adapter.run(BodyTask(goal="run command: git commit --dry-run"))

        self.assertEqual(result.status, "needs_input")
        self.assertEqual(result.raw.risk, "review")
        approval_id = result.raw.id

        pending = self.adapter.run(BodyTask(goal=f"run approved command {approval_id}"))
        self.assertEqual(pending.status, "needs_input")

        approved = self.adapter.run(BodyTask(goal=f"approve command {approval_id}"))
        self.assertEqual(approved.status, "success")

    def test_approved_command_is_single_use(self) -> None:
        result = self.adapter.run(BodyTask(goal="run command: pip install example-package"))
        approval_id = result.raw.id
        self.adapter.run(BodyTask(goal=f"approve command {approval_id}"))

        first = self.adapter.run(BodyTask(goal=f"run approved command {approval_id}"))
        second = self.adapter.run(BodyTask(goal=f"run approved command {approval_id}"))

        self.assertIn(first.status, {"success", "failed"})
        self.assertEqual(second.status, "failed")
        self.assertIn("executed", second.summary)

    def test_preview_write_file_returns_diff_without_writing(self) -> None:
        result = self.adapter.run(
            BodyTask(goal="preview write file scratch/hands_safety_test.txt: hello")
        )

        self.assertEqual(result.status, "needs_input")
        self.assertIn("--- a/scratch/hands_safety_test.txt", result.summary)
        self.assertFalse(self.scratch.exists())

    def test_write_file_creates_project_file(self) -> None:
        result = self.adapter.run(
            BodyTask(goal="write file scratch/hands_safety_test.txt: hello")
        )

        self.assertEqual(result.status, "success")
        self.assertEqual(self.scratch.read_text(encoding="utf-8"), "hello")

    def test_edit_file_creates_backup_and_diff(self) -> None:
        self.scratch.parent.mkdir(parents=True, exist_ok=True)
        self.scratch.write_text("hello old world", encoding="utf-8")

        preview = self.adapter.run(
            BodyTask(goal="preview edit file scratch/hands_safety_test.txt: old => new")
        )
        result = self.adapter.run(
            BodyTask(goal="edit file scratch/hands_safety_test.txt: old => new")
        )

        self.assertEqual(preview.status, "needs_input")
        self.assertIn("-hello old world", preview.summary)
        self.assertEqual(result.status, "success")
        self.assertEqual(self.scratch.read_text(encoding="utf-8"), "hello new world")
        self.assertEqual(len(result.artifacts), 2)
        self.assertTrue(Path(result.artifacts[1]).exists())

    def test_blocks_write_path_escape(self) -> None:
        result = self.adapter.run(BodyTask(goal="write file ../escape.txt: nope"))

        self.assertEqual(result.status, "failed")
        self.assertIn("escapes project root", result.summary)

    def test_blocks_internal_runtime_write(self) -> None:
        result = self.adapter.run(BodyTask(goal="write file .titanos/secret.txt: nope"))

        self.assertEqual(result.status, "failed")
        self.assertIn("Refusing to write", result.summary)

    def _cleanup_scratch(self) -> None:
        if self.scratch.exists():
            self.scratch.unlink()


if __name__ == "__main__":
    unittest.main()
