import os
import sys
import subprocess
import platform
import argparse
import json
import tempfile
import time
import urllib.request
from pathlib import Path

# Add project root to path so we can import titanos
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from titanos.platform.shell import Shell
from typing import Union, List
from datetime import datetime

def log_build(status: str, details: list):
    log_path = PROJECT_ROOT / "BUILD_LOG.md"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S %z")
    
    with open(log_path, "a") as f:
        f.write(f"\n## {stamp} - {status}\n\n")
        f.write("Checks:\n")
        f.write("- python -m compileall titanos\n")
        f.write("- python -m titanos --sources\n")
        f.write("- python -m titanos --providers\n")
        f.write("- python -m unittest discover -s tests\n")
        f.write("- ui/index.html, ui/styles.css, ui/main.js, ui/api.js, ui/ui-components.js present\n\n")
        f.write("Output:\n")
        for line in details:
            f.write(f"- {line.strip()}\n")

def run_command(command: Union[str, list]) -> str:
    print(f"Running: {command if isinstance(command, str) else ' '.join(command)}")
    result = Shell.execute(command, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        raise RuntimeError(output or f"Command failed with exit code {result.returncode}")
    return result.stdout

def build():
    details = []
    status = "PASS"
    print("Starting TITANOS build...")
    try:
        # 1. Compileall
        print("Compiling...")
        out = run_command([sys.executable, "-m", "compileall", "titanos"])
        details.append(out)
        
        # 2. Sources
        print("Verifying sources...")
        out = run_command([sys.executable, "-m", "titanos", "--sources"])
        details.append(out)
        
        # 3. Providers
        print("Verifying providers...")
        out = run_command([sys.executable, "-m", "titanos", "--providers"])
        details.append(out)
        
        # 4. Tests
        print("Running unit tests...")
        out = run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests"])
        details.append(out)
        
        # 5. UI Check
        print("Checking UI files...")
        ui_files = [
            "ui/index.html",
            "ui/styles.css",
            "ui/main.js",
            "ui/api.js",
            "ui/ui-components.js",
        ]
        for f in ui_files:
            if not (PROJECT_ROOT / f).exists():
                raise FileNotFoundError(f"Missing UI file: {f}")
            details.append(f"UI present: {f}")
            
    except Exception as e:
        status = "FAIL"
        details.append(str(e))
        print(f"Build failed: {e}")
    
    log_build(status, details)
    if status == "FAIL":
        sys.exit(1)
    print("Build passed!")

def dev():
    print("Starting TITANOS in dev mode...")
    # This will eventually start the FastAPI server and UI watcher
    try:
        Shell.execute([sys.executable, "-m", "titanos.server.app"], cwd=str(PROJECT_ROOT), capture_output=False)
    except KeyboardInterrupt:
        print("\nStopping dev server...")

def desktop():
    print("Starting TITANOS desktop app...")
    run_command(["npm.cmd" if platform.system() == "Windows" else "npm", "run", "desktop"])

def install():
    print("Installing dependencies...")
    run_command([sys.executable, "-m", "pip", "install", "-e", "."])

def package():
    print("Packaging TITANOS...")
    # Run the wheel build script
    run_command([sys.executable, "packaging/wheel_build.py"])

def doctor():
    print("Running TITANOS doctor...")
    out = run_command([sys.executable, "-m", "titanos", "doctor"])
    print(out)

def desktop_smoke():
    """Start the source backend in desktop mode and verify its local API contract."""
    port = int(os.getenv("TITANOS_DESKTOP_SMOKE_PORT", "18878"))
    with tempfile.TemporaryDirectory(prefix="titanos-desktop-smoke-") as data_dir:
        env = {
            **os.environ,
            "TITANOS_DESKTOP_MODE": "1",
            "TITANOS_HOST": "127.0.0.1",
            "TITANOS_PORT": str(port),
            "TITANOS_DATA_DIR": data_dir,
            "TITANOS_ENVIRONMENT": "production",
            "TITANOS_JWT_SECRET": "desktop-smoke-test-secret",
            "PYDANTIC_DISABLE_PLUGINS": "__all__",
        }
        command = [sys.executable, "-m", "titanos", "app", "--port", str(port)]
        print(f"Running desktop backend smoke on 127.0.0.1:{port}...")
        process = subprocess.Popen(
            command,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        failed = False
        try:
            deadline = time.time() + int(os.getenv("TITANOS_DESKTOP_SMOKE_TIMEOUT_SECONDS", "45"))
            last_error = None
            while time.time() < deadline:
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/readyz", timeout=1) as response:
                        ready = json.loads(response.read().decode("utf-8"))
                    if ready.get("status") == "ready":
                        break
                except Exception as exc:  # noqa: BLE001 - smoke test reports the last connection error
                    last_error = exc
                time.sleep(0.4)
            else:
                raise RuntimeError(f"Desktop backend did not become ready: {last_error}")

            with urllib.request.urlopen(f"http://127.0.0.1:{port}/runtime", timeout=2) as response:
                runtime = json.loads(response.read().decode("utf-8"))
            if runtime.get("mode") != "desktop":
                raise RuntimeError(f"Expected desktop runtime mode, got: {runtime}")
            if runtime.get("data_dir") != data_dir:
                raise RuntimeError(f"Expected runtime data dir {data_dir}, got {runtime.get('data_dir')}")
            print("Desktop backend smoke passed.")
        except Exception:
            failed = True
            raise
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            if failed and process.returncode not in (0, None):
                output = process.stdout.read() if process.stdout else ""
                if output.strip():
                    print(output.strip())

def test():
    print("Running unit tests...")
    run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests"])


CLEAN_GLOBS = [
    # Python bytecode / caches
    "**/__pycache__",
    "**/*.pyc",
    "**/*.pyo",
    "**/*.pyd",
    "**/.pytest_cache",
    "**/.coverage",
    "**/htmlcov",
    # Build / dist / egg-info
    "dist",
    "build",
    "**/*.egg-info",
    "release",
    # Logs generated at runtime
    "*.log",
    # Frontend caches (not node_modules – that's a deliberate install)
    ".cache",
    ".parcel-cache",
    ".next",
    # Cypress test artifacts
    "cypress/videos",
    "cypress/screenshots",
    # Desktop runtime bundle
    "desktop-runtime",
]

# Source paths that the clean command must NEVER touch
_SAFE_ROOTS = {
    "titanos", "tests", "scripts", "docs", "ui", "assets",
    "charts", "docker", "benchmarks", "cypress",
    ".github", "packaging",
}

def clean():
    """Remove generated/cache artifacts without touching source files."""
    import glob as _glob
    import shutil as _shutil

    removed: list[str] = []
    skipped: list[str] = []

    for pattern in CLEAN_GLOBS:
        for hit in PROJECT_ROOT.glob(pattern):
            # Safety: refuse to delete anything inside a source root
            rel = hit.relative_to(PROJECT_ROOT)
            top = rel.parts[0] if rel.parts else ""
            if top in _SAFE_ROOTS or rel == PROJECT_ROOT:
                skipped.append(str(rel))
                continue
            # Extra guard: never delete .titanos (runtime DB lives there)
            if top == ".titanos":
                skipped.append(str(rel))
                continue
            try:
                if hit.is_dir():
                    _shutil.rmtree(hit)
                    removed.append(f"[dir]  {rel}")
                else:
                    hit.unlink()
                    removed.append(f"[file] {rel}")
            except OSError as exc:
                print(f"  Warning: could not remove {rel}: {exc}")

    if removed:
        print("Removed:")
        for item in removed:
            print(f"  {item}")
    else:
        print("Nothing to remove.")
    if skipped:
        print(f"Skipped (source-protected): {len(skipped)} path(s)")
    print("Clean done.")

def api_test():
    print("Running API tests...")
    # Check for pytest
    try:
        import pytest  # noqa: F401
        has_pytest = True
    except ImportError:
        has_pytest = False

    if has_pytest:
        return run_command([sys.executable, "-m", "pytest", "tests/test_api_new.py", "tests/test_api.py", "-v"])
    
    return run_command(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_api*.py"]
    )

def ui_test():
    print("Running UI tests (Cypress)...")
    if not (PROJECT_ROOT / "node_modules").exists():
        print("Warning: node_modules not found. UI tests require npm install.")
        return "Skipped: node_modules missing"
    
    # Check if cypress is installed in node_modules
    if not (PROJECT_ROOT / "node_modules" / ".bin" / "cypress").exists():
        print("Warning: Cypress not found in node_modules. Skipping.")
        return "Skipped: Cypress missing"
        
    return run_command(["npx", "cypress", "run"])

def ci():
    print("Starting CI pipeline...")
    try:
        # 1. Build & Unit Tests
        build()
        
        # 2. API Tests
        api_test()
        
        # 3. Server Smoke Test
        print("Running server import smoke test...")
        run_command([sys.executable, "-c", "import titanos.server.app; print('server import ok')"])
        
        # 4. UI Tests (optional locally, but we'll try)
        ui_test()
        
        print("\nCI Pipeline PASSED")
    except Exception as e:
        print(f"\nCI Pipeline FAILED: {e}")
        sys.exit(1)

def serve():
    print("Starting TITANOS in production mode (TLS)...")
    cert_dir = PROJECT_ROOT / "cert"
    key_path = cert_dir / "key.pem"
    cert_path = cert_dir / "cert.pem"
    
    if not (key_path.exists() and cert_path.exists()):
        print("Certificates not found. Generating dev certs...")
        run_command([sys.executable, "scripts/generate_cert.py"])
        
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "titanos.server.app:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--ssl-keyfile", str(key_path),
        "--ssl-certfile", str(cert_path)
    ]
    try:
        Shell.execute(cmd, cwd=str(PROJECT_ROOT), capture_output=False)
    except KeyboardInterrupt:
        print("\nStopping server...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TITANOS Build Runner")
    parser.add_argument(
        "command",
        choices=[
            "build",
            "clean",
            "dev",
            "desktop",
            "serve",
            "install",
            "test",
            "api-test",
            "ui-test",
            "ci",
            "package",
            "doctor",
            "desktop-smoke",
        ],
        help="Command to run",
    )
    
    args = parser.parse_args()
    
    if args.command == "build":
        build()
    elif args.command == "clean":
        clean()
    elif args.command == "dev":
        dev()
    elif args.command == "desktop":
        desktop()
    elif args.command == "serve":
        serve()
    elif args.command == "install":
        install()
    elif args.command == "test":
        test()
    elif args.command == "api-test":
        api_test()
    elif args.command == "ui-test":
        ui_test()
    elif args.command == "ci":
        ci()
    elif args.command == "package":
        package()
    elif args.command == "doctor":
        doctor()
    elif args.command == "desktop-smoke":
        desktop_smoke()
