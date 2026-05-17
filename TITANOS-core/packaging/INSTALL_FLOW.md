# TITANOS Installer Flow

This document outlines the planned installer flow for TITANOS users.

## 1. Recommended Install: Desktop App
1. Download the platform package from the release artifacts.
2. Launch TITANOS.
3. Complete local customization:
   - workspace mode
   - technical level
   - visible tools
   - optional provider configuration

No product login is required. The desktop app starts and supervises its bundled
backend internally.

## 2. Quick Install (Python Users)
```bash
pip install titanos-core
titanos init
titanos run
```

## 3. Standalone Executable (Windows/macOS/Linux)
1. Download the latest `titanos.exe` (or platform equivalent) from GitHub Releases.
2. Run the executable.
3. On first run, TITANOS will:
   - Create a runtime data directory in the OS app profile.
   - Prompt for AI provider keys (Ollama, OpenAI, etc.).
   - Open the TITANOS desktop workspace.

## 4. Developer/Source Install
```bash
git clone https://github.com/titanos/TITANOS.git
cd TITANOS/TITANOS-core
python scripts/run.py install
python scripts/run.py build
npm install
npm run desktop
```

## 5. Dependencies
- Python 3.11+ (if running from source/wheel)
- Ollama (optional, for local inference)
- Internet connection (for cloud providers)
