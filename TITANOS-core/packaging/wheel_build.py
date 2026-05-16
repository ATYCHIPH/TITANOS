import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def build_wheel(no_deps: bool = False):
    """Build a Python wheel for TITANOS.

    Args:
        no_deps: If True, builds the wheel without installing declared dependencies.
    """
    print("Building TITANOS Python Wheel...")
    # Upgrade build tool
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "build"], check=True)
    # Build the wheel, optionally without dependencies
    build_cmd = [sys.executable, "-m", "build", "--outdir", str(PROJECT_ROOT / "dist")]
    if no_deps:
        build_cmd.append("--no-deps")
    subprocess.run(build_cmd, cwd=PROJECT_ROOT, check=True)
    print(f"Wheel built in {PROJECT_ROOT / 'dist'}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build TITANOS wheel")
    parser.add_argument("--no-deps", action="store_true", help="Build wheel without installing dependencies")
    args = parser.parse_args()
    build_wheel(no_deps=args.no_deps)
