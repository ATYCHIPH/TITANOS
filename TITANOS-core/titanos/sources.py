from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import BodySystem


@dataclass(frozen=True)
class SourceProject:
    source_folder: str
    body_system: BodySystem
    titanos_name: str
    role: str
    status: str = "stubbed"

    def path_from_project_root(self, project_root: Path) -> Path:
        return project_root.parent / self.source_folder


SOURCE_PROJECTS: tuple[SourceProject, ...] = (
    SourceProject(
        "source-cortex",
        BodySystem.CORTEX,
        "TITANOS Cortex",
        "typed agent framework, graph workflows, tool schemas, evals",
    ),
    SourceProject(
        "source-hermes",
        BodySystem.CORTEX,
        "TITANOS Cortex / Voice / Memory",
        "agent loop, skills, gateway, cron, compression, model tools",
    ),
    SourceProject(
        "source-memory",
        BodySystem.MEMORY,
        "TITANOS Memory",
        "long-term memory, semantic recall, user and project facts",
        "thin-adapter",
    ),
    SourceProject(
        "source-hands",
        BodySystem.HANDS,
        "TITANOS Hands",
        "local code execution, shell, files, scripts, data operations",
        "thin-adapter",
    ),
    SourceProject(
        "source-eyes",
        BodySystem.EYES,
        "TITANOS Eyes",
        "GUI perception, screenshot verification, desktop actions",
    ),
    SourceProject(
        "source-craft",
        BodySystem.CRAFT,
        "TITANOS Craft",
        "coding workflows, repo operations, review and plugin patterns",
    ),
    SourceProject(
        "source-lab",
        BodySystem.LAB,
        "TITANOS Lab",
        "optional remote execution and disposable experiments",
    ),
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def inject_source_paths() -> None:
    """Inject source folders into sys.path for the developer preview."""
    import sys

    root = project_root()
    # Pydantic AI
    pydantic_ai_path = root.parent / "source-cortex" / "pydantic_ai_slim"
    if pydantic_ai_path.exists() and str(pydantic_ai_path) not in sys.path:
        sys.path.insert(0, str(pydantic_ai_path))

    pydantic_graph_path = root.parent / "source-cortex" / "pydantic_graph"
    if pydantic_graph_path.exists() and str(pydantic_graph_path) not in sys.path:
        sys.path.insert(0, str(pydantic_graph_path))

    # Open Interpreter
    hands_path = root.parent / "source-hands"
    if hands_path.exists() and str(hands_path) not in sys.path:
        sys.path.insert(0, str(hands_path))


def source_report() -> list[str]:
    root = project_root()
    lines: list[str] = []
    for source in SOURCE_PROJECTS:
        exists = source.path_from_project_root(root).exists()
        marker = "present" if exists else "missing"
        lines.append(
            f"{source.titanos_name} ({source.body_system.value}, "
            f"{source.status}, {marker}) [source: {source.source_folder}]"
        )
    return lines
