# 🛡️ TITANOS — Production-Grade Local Agent Workspace

[![PyPI Version](https://img.shields.io/pypi/v/titanos-core.svg)](https://pypi.org/project/titanos-core/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/titanos/titanos-core/actions/workflows/ci.yml/badge.svg)](https://github.com/titanos/titanos-core/actions)

TITANOS is a state-of-the-art, **local-first operator desktop workspace** and agentic reasoning engine. It provides a secure, interactive interface for executing autonomous agent runs, shell integrations, and database operations under strict operator approvals and privacy controls.

---

## 🌟 Premium Features

### 🖥️ Local-First Desktop Environment
- Consolidates a secure Electron shell and a loopback-isolated Python runtime backend.
- **Zero-Telemetry Posture**: All configurations, databases, and history stay 100% local. No SaaS registration required.

### 🛡️ Safer Shell UX & Threat Classification
- Automatic real-time risk classification of proposed terminal commands (**Safe**, **Suspicious**, **Blocked**) across PowerShell, Bash, and zsh.
- High-fidelity visual diff approvals, interactive risk meters, and absolute protection against system-level exploits.

### 📊 System Diagnostics & Recovery
- Interactive **System Log Viewer** directly integrated into the operator interface with level selectors (`INFO`, `WARN`, `ERROR`), search filtering, and safe export.
- Instant, database-recovery reset buttons for reliable SQLite purge operations.

### 💾 Backup & Sync
- Secure workspace backups via single-click encrypted JSON import and export flows.

---

## 🚀 Quick Start & Installation

Install TITANOS directly via PyPI:

```bash
pip install titanos-core
```

Or clone the repository to run the native desktop shell in developer mode:

```bash
# Clone the repository
git clone https://github.com/titanos/titanos.git
cd titanos/TITANOS-core

# Install dependencies and start the app
python scripts/run.py dev
```

---

## 📖 Architectural Guides & Docs
For detailed playbooks, refer to our internal specifications:
- 🛡️ **[Safer Shell UX Specification](file:///C:/Users/WDAGUtilityAccount/.gemini/antigravity/brain/fc634c5d-fd3a-42c5-8880-3bc0d8f3cb9b/shell_ux.md)**
- 🔑 **[Desktop Code-Signing Playbook](file:///C:/Users/WDAGUtilityAccount/.gemini/antigravity/brain/fc634c5d-fd3a-42c5-8880-3bc0d8f3cb9b/code_signing.md)**
- 🔄 **[Auto-Update & Channel Strategy](file:///C:/Users/WDAGUtilityAccount/.gemini/antigravity/brain/fc634c5d-fd3a-42c5-8880-3bc0d8f3cb9b/auto_update.md)**
- 🔒 **[Privacy & Data Handling Policy](file:///C:/Users/WDAGUtilityAccount/.gemini/antigravity/brain/fc634c5d-fd3a-42c5-8880-3bc0d8f3cb9b/privacy.md)**
- 💻 **[Contributor & Local Setup Guide](file:///C:/Users/WDAGUtilityAccount/.gemini/antigravity/brain/fc634c5d-fd3a-42c5-8880-3bc0d8f3cb9b/contributing.md)**

---

## 🤝 Contributing
We welcome developers! Read our [Contributor Guide](file:///C:/Users/WDAGUtilityAccount/.gemini/antigravity/brain/fc634c5d-fd3a-42c5-8880-3bc0d8f3cb9b/contributing.md) to learn about our PEP 8 style standards, ESLint setups, and Cypress E2E test runs.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
