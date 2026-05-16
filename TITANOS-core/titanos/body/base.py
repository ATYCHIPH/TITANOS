from __future__ import annotations

from dataclasses import dataclass

from ..contracts import BodyHealth, BodyResult, BodySystem, BodySystemInfo, BodyTask


@dataclass
class StubAdapter:
    info: BodySystemInfo
    trigger_words: tuple[str, ...]

    def initialize(self) -> None:
        return None

    def health(self) -> BodyHealth:
        return BodyHealth(
            system=self.info.name,
            status="stubbed",
            summary=f"{self.info.public_name} is registered but not fully grafted.",
        )

    def shutdown(self) -> None:
        return None

    def can_handle(self, task: BodyTask) -> bool:
        goal = task.goal.lower()
        return any(word in goal for word in self.trigger_words)

    def run(self, task: BodyTask) -> BodyResult:
        return BodyResult(
            system=self.info.name,
            status="needs_input",
            summary=(
                f"{self.info.public_name} is registered, but its implementation "
                "is currently being grafted from source material."
            ),
            next_steps=[
                f"Complete the TITANOS graft for: {self.info.purpose}",
                "Ensure the body system adapter conforms to the core contracts.",
            ],
        )


def info(
    name: BodySystem,
    public_name: str,
    source_project: str,
    purpose: str,
    *,
    always_on: bool = False,
) -> BodySystemInfo:
    return BodySystemInfo(
        name=name,
        public_name=public_name,
        source_project=source_project,
        purpose=purpose,
        always_on=always_on,
    )
