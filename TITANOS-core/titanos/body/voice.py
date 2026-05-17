from __future__ import annotations

from ..contracts import BodyHealth, BodyResult, BodySystem, BodyTask
from .base import info


class VoiceAdapter:
    info = info(
        BodySystem.VOICE,
        "TITANOS Voice",
        "hermes gateway graft",
        "CLI, messaging gateways, notifications, conversation delivery",
    )

    _greetings = {"hi", "hello", "hey", "yo", "good morning", "good afternoon", "good evening"}
    _thanks = {"thanks", "thank you", "appreciate it", "nice", "perfect"}

    def initialize(self) -> None:
        return None

    def health(self) -> BodyHealth:
        return BodyHealth(
            system=BodySystem.VOICE,
            status="ready",
            summary="Conversation delivery is connected to session history.",
        )

    def shutdown(self) -> None:
        return None

    def can_handle(self, task: BodyTask) -> bool:
        text = task.goal.strip().lower()
        if not text:
            return True
        if text in self._greetings or text in self._thanks:
            return True
        if any(text.startswith(prefix) for prefix in ("chat ", "message ", "say ", "tell me ")):
            return True
        if text.endswith("?") and not self._looks_like_work_request(text):
            return True
        if "what did i" in text or "previous message" in text or "last thing" in text:
            return True
        if len(text.split()) <= 12 and not self._looks_like_work_request(text):
            return True
        return False

    def run(self, task: BodyTask) -> BodyResult:
        text = task.goal.strip()
        lowered = text.lower()
        previous_user_messages = [
            message.content
            for message in task.history
            if message.role == "user" and message.content.strip().lower() != lowered
        ]

        if not text:
            summary = "I'm here. Send me a goal, a question, or a direct command."
        elif lowered in self._greetings:
            summary = "Hello. I'm connected to the TITANOS body systems and ready to work with this conversation."
        elif lowered in self._thanks:
            summary = "You're welcome. I have the current conversation in context."
        elif "what did i" in lowered or "previous message" in lowered or "last thing" in lowered:
            substantive_messages = [
                message for message in previous_user_messages
                if message.strip().lower() not in self._greetings
            ]
            if substantive_messages:
                summary = f"Your previous message was: {substantive_messages[-1]}"
            elif previous_user_messages:
                summary = f"Your previous message was: {previous_user_messages[-1]}"
            else:
                summary = "I do not have an earlier user message in this conversation yet."
        elif lowered.startswith(("chat ", "message ", "say ")):
            summary = text.split(" ", 1)[1].strip() if " " in text else "I'm here."
        else:
            summary = self._answer_lightweight_question(text, previous_user_messages)

        return BodyResult(
            system=BodySystem.VOICE,
            status="success",
            summary=summary,
            memory_candidates=[],
        )

    def _answer_lightweight_question(self, text: str, previous_user_messages: list[str]) -> str:
        lowered = text.lower()
        normalized = lowered.replace(" ", "")
        if "whoareyou" in normalized or "whatareyou" in normalized:
            return "I'm TITANOS, a local desktop agent with linked body systems for memory, hands, craft, eyes, lab, voice, and cortex reasoning."
        if "connected" in lowered or "online" in lowered:
            return "The conversation layer is connected. I can route direct commands to body systems and keep this session's turns separate from other conversations."
        if "remember" in lowered and previous_user_messages:
            return f"I can use this conversation context. The last thing you said before this was: {previous_user_messages[-1]}"
        return "I understand. Tell me whether you want a conversation answer, a memory action, a file/system action, or a larger task and I'll route it to the right body system."

    def _looks_like_work_request(self, text: str) -> bool:
        work_words = (
            "build", "create", "fix", "run", "test", "package", "deploy", "install",
            "edit", "delete", "list files", "write", "review", "debug", "connect",
            "think", "production", "readiness", "analyze", "research", "compare",
        )
        return any(word in text for word in work_words)
