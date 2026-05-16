# TITANOS Rebrand And Grafting Plan

The goal is not to run many branded agents side by side. The goal is to absorb
their useful code into TITANOS body systems.

## Naming Rules

- The user only sees `TITANOS`.
- Former project names may appear in developer docs, logs, and source comments
  while migration is active.
- Runtime UI, CLI, prompts, commands, and generated messages should use TITANOS
  names only.
- Each graft keeps the smallest useful slice of code first. Avoid importing a
  whole upstream runtime when an adapter can call a smaller module.

## Body Systems

### TITANOS Cortex

Sources:
- `source-cortex`
- `source-hermes/run_agent.py`
- `source-hermes/trajectory_compressor.py`
- `source-hermes/model_tools.py`

Owns:
- task planning
- typed tool contracts
- verifier outputs
- context compression
- model/provider routing

First graft:
- replace `CortexAdapter` with a typed planner result object
- add verifier result schema
- add a small model router abstraction

### TITANOS Memory

Sources:
- `source-memory/mem0`
- `source-hermes/plugins/memory`
- `source-hermes/hermes_state.py`

Owns:
- long-term memory
- user facts and preferences
- project facts
- episodic task recall
- memory candidates from every body result

First graft:
- local memory CRUD
- semantic search adapter
- memory write policy

Current status:
- local SQLite remember, recall, update, delete, and project indexing are wired
- deterministic routing sends memory intents directly to Memory
- semantic search and memory write policy are still pending

### TITANOS Hands

Sources:
- `source-hands/interpreter/core`
- `source-hands/interpreter/computer_use`

Owns:
- local shell
- Python/Node execution
- file operations
- data transformations

First graft:
- command runner
- code runner
- approval hooks
- output summarizer

Current status:
- local file listing, safe file reading, explicit command execution, path escape
  blocking, command timeout, and destructive-command blocking are wired
- Open Interpreter remains an optional fallback for free-form execution
- richer code runner approvals and output summarization are still pending

### TITANOS Eyes

Sources:
- `source-eyes/src/vision.py`
- `source-eyes/src/actions.py`
- `source-eyes/src/verifier.py`
- `source-eyes/src/agent_loop.py`

Owns:
- visual observation
- GUI actions
- screenshot verification
- desktop task loop

First graft:
- screenshot observation interface
- action schema
- verifier schema

### TITANOS Voice

Sources:
- `source-hermes/gateway`
- `source-hermes/hermes_cli`
- `source-hermes/cli.py`

Owns:
- CLI
- chat gateways
- notifications
- sessions

First graft:
- local CLI wrapper
- session state
- delivery abstraction

### TITANOS Craft

Sources:
- `source-craft/plugins`
- `source-craft/examples`
- selected repo-workflow behavior from `source-hermes/mini_swe_runner.py`

Owns:
- coding workflow patterns
- review patterns
- commit and PR behaviors
- repo-aware task habits

First graft:
- code review command shape
- repo summary command
- patch verification checklist

### TITANOS Lab

Sources:
- `source-lab/packages/python-sdk`

Owns:
- optional remote execution
- disposable experiments

First graft:
- keep disabled by default
- expose as a remote execution backend only when configured

### TITANOS Platform

Owns:
- cross-platform build and run infrastructure
- API gateway and session management
- packaging and distribution
- developer/operator UI (The Console)
- security and release gates

Current status:
- cross-platform shell abstraction and Python build runner are active
- API expanded with Memory CRUD, provider health, and doctor endpoints
- UI (The Console) wired to real backend chat, sessions, and status
- CI workflow established for Windows, macOS, and Linux
- Security review and release checklist formalized

## Migration Order

1. Cortex contracts
2. Memory local adapter
3. Hands local execution adapter
4. Platform infrastructure and API
5. Craft coding workflows
6. Voice CLI
7. Eyes GUI loop
8. Lab optional backend

This order gives TITANOS a usable brain, memory, hands, and a product-ready delivery platform before heavier perception or remote execution features are introduced.
