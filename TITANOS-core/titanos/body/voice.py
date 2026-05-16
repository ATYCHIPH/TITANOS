from ..contracts import BodySystem
from .base import StubAdapter, info


class VoiceAdapter(StubAdapter):
    def __init__(self) -> None:
        super().__init__(
            info(
                BodySystem.VOICE,
                "TITANOS Voice",
                "hermes gateway graft",
                "CLI, messaging gateways, notifications, conversation delivery",
            ),
            ("message", "notify", "telegram", "discord", "slack", "chat"),
        )

