from __future__ import annotations

from dataclasses import dataclass

from ..config.settings import settings


@dataclass(frozen=True)
class MemoryDecision:
    accepted: bool
    text: str
    reason: str


class MemoryWritePolicy:
    """Small local policy for deciding which automatic memories are durable."""

    blocked_prefixes = (
        "command exited",
        "project root entries:",
        "no memories found",
        "hands can list files",
    )

    def evaluate(self, candidate: str) -> MemoryDecision:
        text = " ".join(candidate.strip().split())
        if not settings.AUTO_MEMORY_ENABLED:
            return MemoryDecision(False, text, "automatic memory is disabled")
        if len(text) < settings.MEMORY_MIN_CHARS:
            return MemoryDecision(False, text, "candidate is too short")
        if len(text) > settings.MEMORY_MAX_CHARS:
            return MemoryDecision(False, text, "candidate is too long")
        if text.lower().startswith(self.blocked_prefixes):
            return MemoryDecision(False, text, "candidate looks operational")
        return MemoryDecision(True, text, "accepted")
