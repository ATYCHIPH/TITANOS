# TITANOS Build Process

This document explains how TITANOS is being built and how each build must be
recorded.

## Current Strategy

TITANOS is built as one project with one public agent identity. The downloaded
projects are body sources. We do not preserve them as separate branded agents.

The work happens in three layers:

1. **Identity layer**: establish TITANOS as the only public agent.
2. **Contract layer**: define stable brain/body task and result contracts.
3. **Grafting layer**: replace stub body adapters with selected code from the
   source projects.

## Build Order

1. Core contracts: `BodyTask`, `BodyResult`, `BodyAdapter`, `TitanosBrain`.
2. Source registry: every original project mapped to a TITANOS body system.
3. Memory: local memory adapter from `mem0-main` and Hermes memory plugins.
4. Hands: local execution adapter from Open Interpreter.
5. Cortex: planner, verifier, compression, and model routing from Pydantic AI
   and Hermes.
6. Craft: coding and repo workflow patterns from Claude Code plugins.
7. Voice: CLI and messaging gateway from Hermes.
8. Eyes: GUI perception and action loop from CuaOS.
9. Lab: optional E2B remote execution backend.

## Required Build Command

Run:

```powershell
.\scripts\build.ps1
```

On Windows systems that block local PowerShell scripts, run:

```cmd
scripts\build.cmd
```

The script performs the lightweight checks and appends the result to
`BUILD_LOG.md`.

Current checks:

1. Python package compilation.
2. Source body registry report.
3. AI provider registry report.
4. Runtime unit and integration tests.
5. Static UI file presence check.

## What Must Be Updated After Every Build

After every build, update:

1. `BUILD_LOG.md`: what ran, whether it passed, and what changed.
2. `MERGE_MANIFEST.md`: if a body source changes status.
3. `MIGRATION.md`: if the next grafting step changes.
4. This file: if the build procedure itself changes.

The build script handles `BUILD_LOG.md` automatically. The other files should be
edited when the architecture or migration status changes.

## Build Status Terms

- `registered`: source project has a TITANOS body name and adapter contract.
- `stubbed`: adapter exists but still returns a placeholder result.
- `grafted`: real implementation code has been connected through the adapter.
- `verified`: adapter has tests or a working command path.

## Current State

All seven source projects are registered. Memory and Hands now have verified
thin adapters with local tests, Cortex has verified body-tool registration, and
the remaining body systems are still stubbed or pending graft.

The static UI has been added under `ui/` and is part of the build check.
Ollama, Google, and NVIDIA are registered as first-class AI providers.
