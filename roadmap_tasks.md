# 50 Action Items – Assignment Table

| # | Task | Assigned Agent | Category |
|---|------|----------------|----------|
| 1 | Create many‑linux Docker container for wheel build | **You (Agent A)** | Packaging |
| 2 | Generate Linux x86_64 wheel and test locally | **You** | Packaging |
| 3 | Add `publish-to-pypi` job in GitHub Actions CI | **You** | CI/CD |
| 4 | Store PyPI token securely in GitHub Secrets | **You** | CI/CD |
| 5 | Write release‑notes‑generator script (auto‑extract from PR titles) | **You** | Documentation |
| 6 | Add OpenAPI spec generation (`fastapi.openapi`) and publish as `openapi.json` | **You** | API |
| 7 | Implement JWT‑based auth middleware for FastAPI | **You** | Security |
| 8 | Create self‑signed dev TLS cert and configure FastAPI to use HTTPS | **You** | Security |
| 9 | Add CORS configuration for UI‑to‑API calls | **You** | API |
|10| Write end‑to‑end integration test (CLI → server → UI) using Playwright | **You** | Testing |
|11| Benchmark latency & memory for typical request (10 ms target) | **You** | Performance |
|12| Refactor `titanos/platform/shell.py` to support PowerShell 7+ | **Agent B** | Shell |
|13| Add Bash‑compatible script hooks (init, shutdown) | **Agent B** | Shell |
|14| Write unit tests for new shell back‑ends (Windows, macOS, Linux) | **Agent B** | Testing |
|15| Update CI matrix to run shell tests on all three OSes (via `runs-on: windows‑latest`, `macos‑latest`, `ubuntu‑latest`) | **Agent B** | CI/CD |
|16| Create Dockerfile for FastAPI service with Uvicorn + gunicorn | **Agent C** | Deployment |
|17| Build multi‑arch Docker image (amd64 & arm64) and push to GitHub Container Registry | **Agent C** | Deployment |
|18| Write Helm chart for Helm‑based deployment on Kubernetes | **Agent C** | Deployment |
|19| Add health‑check endpoint (`/healthz`) and readiness probe | **Agent C** | Monitoring |
|20| Integrate Prometheus metrics exporter into FastAPI | **Agent C** | Monitoring |
|21| Design dark‑mode UI theme (colors, gradients, glass‑morphism) | **Agent D** | UI/UX |
|22| Implement CSS variables for theme switching (light/dark) | **Agent D** | UI/UX |
|23| Add micro‑animations to button hover, loading spinners, and panel transitions | **Agent D** | UI/UX |
|24| Replace default fonts with Google Font “Inter” throughout UI | **Agent D** | UI/UX |
|25| Refactor `ui/app.js` to use ES6 modules and async/await for API calls | **Agent D** | Code Quality |
|26| Write UI integration tests with Cypress (login flow, command execution) | **Agent D** | Testing |
|27| Create a public `README.md` with installation, quick‑start, and contribution sections | **You** | Documentation |
|28| Add `CHANGELOG.md` that is auto‑updated by release‑notes script | **You** | Documentation |
|29| Write end‑user CLI manual (`titanos‑cli --help` auto‑doc) | **You** | Documentation |
|30| Set up Dependabot security alerts for CI workflow and `requirements.txt` | **You** | Security |
|31| Add Sphinx documentation site for API reference | **You** | Documentation |
|32| Create a “Getting Started” video demo (screen‑capture of CLI → UI) | **You** | Marketing |
|33| Publish the demo video to the repository’s `assets/` folder | **You** | Marketing |
|34| Draft a licensing page (MIT + attribution) and add to repo | **You** | Legal |
|35| Implement graceful shutdown handling for FastAPI (signal handling) | **Agent C** | Reliability |
|36| Add retry logic to `titanos/platform/shell.py` for transient command failures | **Agent B** | Reliability |
|37| Set up GitHub Pages site to host documentation and demo | **Agent D** | Marketing |
|38| Write a “Contributing Guide” with coding standards and CI checks | **You** | Documentation |
|39| Create a `pyproject.toml` with build‑system and metadata (PEP 517) | **You** | Packaging |
|40| Add `setup.cfg`/`setup.py` fallback for legacy environments | **You** | Packaging |
|41| Ensure `wheel_build.py` supports `--no-deps` flag for lightweight builds | **You** | Packaging |
|42| Add conda‑forge recipe (meta‑yaml) for optional conda distribution | **Agent C** | Packaging |
|43| Create Homebrew formula for macOS users | **Agent C** | Packaging |
|44| Add automated release tagging (`vX.Y.Z`) via GitHub Actions on merge to `main` | **You** | CI/CD |
|45| Implement logging configuration (structured JSON logs) for server & CLI | **Agent B** | Observability |
|46| Provide a log‑viewer UI component within the operator console | **Agent D** | UI/UX |
|47| Write unit tests for logging formatter and error handling | **Agent B** | Testing |
|48| Conduct a security audit of dependencies (pip‑audit) in CI pipeline | **You** | Security |
|49| Set up a “bug‑bounty” issue template with severity levels | **You** | Community |
|50| Prepare a post‑release retrospective checklist (metrics, feedback) | **You** | Process |

---

**Prompts for the other agents**

*Agent B*: Please focus on the shell abstraction layer and related reliability features. Your tasks are #12‑#15, #36, #45‑#47. Ensure cross‑platform compatibility, add thorough unit & CI tests, and embed retry & structured logging logic.

*Agent C*: Your scope covers containerization, Helm, multi‑arch image builds, Docker‑based Linux wheel generation, and packaging for Conda/Homebrew. Work on #1‑#4, #16‑#21, #35, #42‑#44, and ensure CI/CD pipelines push artifacts securely.

*Agent D*: Concentrate on the user interface, visual polish, and public‑facing assets. Address #21‑#26, #32‑#34, #37, #46, and any UI‑related testing. Deliver a dark‑mode theme, micro‑animations, and a demo video for the project site.

---

*I (Agent A) will handle the overarching packaging, CI/CD, documentation, security, and overall coordination tasks listed under my name.*
