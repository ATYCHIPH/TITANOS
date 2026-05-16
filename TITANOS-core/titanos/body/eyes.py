from ..contracts import BodySystem
from .base import StubAdapter, info


class EyesAdapter(StubAdapter):
    def __init__(self) -> None:
        super().__init__(
            info(
                BodySystem.EYES,
                "TITANOS Eyes",
                "CuaOS graft",
                "screenshots, visual state, GUI action and verification",
            ),
            ("screen", "screenshot", "gui", "desktop", "click", "vision"),
        )

