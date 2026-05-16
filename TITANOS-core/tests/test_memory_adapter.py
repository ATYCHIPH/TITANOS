from __future__ import annotations

import tempfile
import sqlite3
import unittest
from pathlib import Path

from titanos.body.memory import MemoryAdapter, MemoryStore
from titanos.brain import TitanosBrain
from titanos.contracts import BodySystem, BodyTask


class MemoryAdapterTests(unittest.TestCase):
    def test_remembers_and_recalls_fact(self) -> None:
        adapter = self._adapter()

        remembered = adapter.run(BodyTask(goal="remember operator likes quiet logs"))
        recalled = adapter.run(BodyTask(goal="recall quiet logs"))

        self.assertEqual(remembered.status, "success")
        self.assertIn("Remembered #", remembered.summary)
        self.assertEqual(recalled.status, "success")
        self.assertIn("operator likes quiet logs", recalled.summary)

    def test_stores_preference_kind(self) -> None:
        adapter = self._adapter()

        adapter.run(BodyTask(goal="preference use local models first"))
        result = adapter.run(BodyTask(goal="recall local models"))

        self.assertIn("[preference]", result.summary)
        self.assertIn("use local models first", result.summary)

    def test_recalls_recent_memories_without_query(self) -> None:
        adapter = self._adapter()

        adapter.run(BodyTask(goal="remember first project fact"))
        adapter.run(BodyTask(goal="remember second project fact"))
        result = adapter.run(BodyTask(goal="recall"))

        self.assertIn("second project fact", result.summary)
        self.assertIn("first project fact", result.summary)

    def test_updates_memory_by_id(self) -> None:
        adapter = self._adapter()

        remembered = adapter.run(BodyTask(goal="remember old project fact"))
        memory_id = remembered.raw.id
        result = adapter.run(BodyTask(goal=f"memory update {memory_id} new project fact"))
        recalled = adapter.run(BodyTask(goal="recall new project fact"))

        self.assertEqual(result.status, "success")
        self.assertIn("new project fact", recalled.summary)

    def test_deletes_memory_by_id(self) -> None:
        adapter = self._adapter()

        remembered = adapter.run(BodyTask(goal="remember disposable project fact"))
        memory_id = remembered.raw.id
        deleted = adapter.run(BodyTask(goal=f"memory delete {memory_id}"))
        recalled = adapter.run(BodyTask(goal="recall disposable project fact"))

        self.assertEqual(deleted.status, "success")
        self.assertIn("No memories found", recalled.summary)

    def test_migrates_legacy_memory_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "memory.sqlite"
            connection = sqlite3.connect(path)
            with connection:
                connection.execute(
                    """
                    create table memories (
                        id integer primary key autoincrement,
                        kind text not null,
                        text text not null,
                        created_at text not null
                    )
                    """
                )
            connection.close()

            adapter = MemoryAdapter(MemoryStore(path))
            result = adapter.run(BodyTask(goal="memory list"))

        self.assertEqual(result.status, "success")

    def test_brain_routes_to_memory(self) -> None:
        adapter = self._adapter()
        brain = TitanosBrain(body=[adapter])

        result = brain.run("remember TITANOS has Memory v0")

        self.assertEqual(result.system, BodySystem.MEMORY)
        self.assertEqual(result.status, "success")

    def _adapter(self) -> MemoryAdapter:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        store = MemoryStore(Path(temp_dir.name) / "memory.sqlite")
        return MemoryAdapter(store)


if __name__ == "__main__":
    unittest.main()
