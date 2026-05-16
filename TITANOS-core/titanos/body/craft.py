from ..contracts import BodySystem
from .base import StubAdapter, info


class CraftAdapter(StubAdapter):
    def __init__(self) -> None:
        super().__init__(
            info(
                BodySystem.CRAFT,
                "TITANOS Craft",
                "claude-code graft",
                "coding workflows, repo operations, review and plugin patterns",
            ),
            ("code", "bug", "review", "commit", "repo", "refactor"),
        )

