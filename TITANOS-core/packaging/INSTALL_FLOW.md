# TITANOS Installer Flow

This document outlines the planned installer flow for TITANOS users.

## 1. Quick Install (Python Users)
```bash
pip install titanos-core
titanos init
titanos run
```

## 2. Standalone Executable (Windows/macOS/Linux)
1. Download the latest `titanos.exe` (or platform equivalent) from GitHub Releases.
2. Run the executable.
3. On first run, TITANOS will:
   - Create `.titanos/` data directory.
   - Prompt for AI provider keys (Ollama, OpenAI, etc.).
   - Launch the Operator Console in the default browser.

## 3. Developer/Source Install
```bash
git clone https://github.com/titanos/TITANOS.git
cd TITANOS/TITANOS-core
python scripts/run.py install
python scripts/run.py build
python scripts/run.py dev
```

## 4. Dependencies
- Python 3.11+ (if running from source/wheel)
- Ollama (optional, for local inference)
- Internet connection (for cloud providers)
