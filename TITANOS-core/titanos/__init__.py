from .sources import inject_source_paths
inject_source_paths()

"""TITANOS core brain and body contracts."""

from .brain import TitanosBrain
from .contracts import BodyResult, BodyTask, BodySystem, BodySystemInfo

__all__ = [
    "BodyResult",
    "BodySystem",
    "BodySystemInfo",
    "BodyTask",
    "TitanosBrain",
]

