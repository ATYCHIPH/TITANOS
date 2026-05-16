from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class BodySystem(str, Enum):
    CORTEX = "cortex"
    MEMORY = "memory"
    HANDS = "hands"
    EYES = "eyes"
    VOICE = "voice"
    CRAFT = "craft"
    LAB = "lab"


@dataclass(frozen=True)
class BodySystemInfo:
    name: BodySystem
    public_name: str
    source_project: str
    purpose: str
    always_on: bool = False


@dataclass(frozen=True)
class BodyHealth:
    system: BodySystem
    status: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteDecision:
    system: BodySystem
    confidence: float
    reason: str


@dataclass(frozen=True)
class RunRecord:
    goal: str
    route: RouteDecision
    status: str
    summary: str
    duration_ms: int
    artifacts: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class BodyTask:
    goal: str
    context: list[str] = field(default_factory=list)
    history: list[ChatMessage] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BodyResult:
    system: BodySystem
    status: str
    summary: str
    artifacts: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    memory_candidates: list[str] = field(default_factory=list)
    raw: Any | None = None


class BodyAdapter(Protocol):
    info: BodySystemInfo

    def initialize(self) -> None:
        """Prepare the body system for use."""

    def health(self) -> BodyHealth:
        """Return body-system readiness."""

    def shutdown(self) -> None:
        """Release body-system resources."""

    def can_handle(self, task: BodyTask) -> bool:
        """Return whether this body system is a reasonable handler."""

    def run(self, task: BodyTask) -> BodyResult:
        """Execute the task and return a structured result."""
