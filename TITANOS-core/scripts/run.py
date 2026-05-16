import os
import sys
import subprocess
import platform
import argparse
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

def test():
    print("Running unit tests...")
    run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests"])

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
            "dev",
            "serve",
            "install",
            "test",
            "api-test",
            "ui-test",
            "ci",
            "package",
            "doctor",
        ],
        help="Command to run",
    )
    
    args = parser.parse_args()
    
    if args.command == "build":
        build()
    elif args.command == "dev":
        dev()
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
