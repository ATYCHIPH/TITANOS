from ..contracts import BodySystem
from .base import StubAdapter, info


class LabAdapter(StubAdapter):
    def __init__(self) -> None:
        super().__init__(
            info(
                BodySystem.LAB,
                "TITANOS Lab",
                "E2B graft",
                "optional remote execution and disposable experiments",
            ),
            ("experiment", "remote", "isolate", "sandbox", "disposable"),
        )

