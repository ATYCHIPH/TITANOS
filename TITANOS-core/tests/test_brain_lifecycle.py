from __future__ import annotations

import unittest

from titanos.body.hands import HandsAdapter
from titanos.body.memory import MemoryAdapter
from titanos.brain import TitanosBrain
from titanos.contracts import BodySystem
from titanos.defaults import create_titanos


class BrainLifecycleTests(unittest.TestCase):
    def test_health_report_includes_all_attached_body_systems(self) -> None:
        brain = create_titanos()

        report = brain.health_report()

        self.assertEqual(len(report), len(brain.body))
        self.assertIn(BodySystem.HANDS, {entry.system for entry in report})
        self.assertIn(BodySystem.MEMORY, {entry.system for entry in report})

    def test_run_records_route_confidence_and_duration(self) -> None:
        brain = TitanosBrain(body=[MemoryAdapter(), HandsAdapter()])

        result = brain.run("list files")

        self.assertEqual(result.system, BodySystem.HANDS)
        self.assertEqual(len(brain.run_records), 1)
        record = brain.run_records[0]
        self.assertEqual(record.route.system, BodySystem.HANDS)
        self.assertGreaterEqual(record.route.confidence, 0.9)
        self.assertGreaterEqual(record.duration_ms, 0)

    def test_explain_route_uses_cortex_fallback_for_ambiguous_goal(self) -> None:
        brain = create_titanos()

        route = brain.explain_route("think about production readiness")

        self.assertEqual(route.system, BodySystem.CORTEX)
        self.assertIn("fallback", route.reason)

    def test_explain_route_prefers_direct_memory_intent(self) -> None:
        brain = create_titanos()

        route = brain.explain_route("remember runtime routes are recorded")

        self.assertEqual(route.system, BodySystem.MEMORY)
        self.assertGreater(route.confidence, 0.8)

    def test_conversation_routes_to_voice_not_cortex_fallback(self) -> None:
        brain = create_titanos()

        result = brain.run("hello")

        self.assertEqual(result.system, BodySystem.VOICE)
        self.assertEqual(result.status, "success")
        self.assertIn("connected", result.summary.lower())

    def test_session_history_keeps_conversations_distinct(self) -> None:
        brain = create_titanos()

        first = brain.run("hello")
        session_id = brain.session.session_id
        brain.run("this is my first conversation marker", session_id=session_id)
        brain.run("hello", session_id=session_id)
        recalled = brain.run("what did I say before?", session_id=session_id)

        self.assertEqual(first.system, BodySystem.VOICE)
        self.assertIn("first conversation marker", recalled.summary)

    def test_voice_handles_lightweight_identity_questions(self) -> None:
        brain = create_titanos()

        result = brain.run("who areyou")

        self.assertEqual(result.system, BodySystem.VOICE)
        self.assertIn("TITANOS", result.summary)


if __name__ == "__main__":
    unittest.main()
