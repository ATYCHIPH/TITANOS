# TITANOS Merge Manifest

This file is the authoritative map for merging every downloaded project into
one TITANOS project.

## Merge Principle

We are not shipping many agents under their original names. We are building one
agent:

```text
TITANOS = brain
former projects = body systems
```

The original repositories remain as source material during the grafting phase.
Code is moved, wrapped, or selectively imported into TITANOS body systems. Any
runtime command, UI label, prompt, or user-facing output should say TITANOS.

## Source Projects

| Source folder | TITANOS name | Runtime role | Merge status |
| --- | --- | --- | --- |
| `source-cortex` | Cortex | typed agent framework, graph workflows, tool schemas, evals, verifier contracts | registered, tool-registration verified |
| `source-hermes` | Cortex / Voice / Memory | agent loop, skills, gateway, cron, context compression, model tools | registered, pending graft |
| `source-memory` | Memory | long-term memory, semantic recall, user/project facts | registered, verified thin-adapter |
| `source-hands` | Hands | local code execution, shell, file and data operations | registered, verified thin-adapter |
| `source-eyes` | Eyes | GUI perception, visual verification, desktop actions | registered, pending graft |
| `source-craft` | Craft | coding workflows, repo operations, review and plugin patterns | registered, pending graft |
| `source-lab` | Lab | optional remote execution backend | registered, pending graft |
| `TITANOS-core` | Platform | build, CI/CD, API, Console UI, packaging, security | verified core |

## Project Boundary

The unified project root is:

```text
TITANOS-core/
```

The sibling source folders are treated as raw material until each subsystem is
grafted into `TITANOS-core/titanos/body/`.

## Rebrand Rules

1. Public identity is always `TITANOS`.
2. Body systems may use anatomy names: `Cortex`, `Memory`, `Hands`, `Eyes`,
   `Voice`, `Craft`, and `Lab`.
3. Original project names are allowed in migration docs, source registry, and
   compatibility comments only.
4. Do not expose original project commands directly when a TITANOS wrapper
   exists.
5. Prefer small grafts over bulk imports. A body system should own the API
   surface even when the implementation still calls upstream code.

## Definition Of "Merged"

A source project counts as merged when:

1. It is registered in `titanos/sources.py`.
2. It has a TITANOS body-system adapter.
3. Its public role is documented here.
4. The adapter can be replaced incrementally with real implementation code.

By that definition, all seven source projects are now merged into the single
TITANOS project structure, with implementation grafting still to do.
