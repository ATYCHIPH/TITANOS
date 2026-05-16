import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def build_exe():
    print("Building TITANOS Standalone Executable...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        
        # Build command
        cmd = [
            "pyinstaller",
            "--noconfirm",
            "--onefile",
            "--console",
            "--name", "titanos",
            "--add-data", f"ui{os.pathsep}ui",
            "--hidden-import", "fastapi",
            "--hidden-import", "uvicorn",
            "titanos/__main__.py"
        ]
        
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
        print(f"Executable built in {PROJECT_ROOT / 'dist'}")
    except Exception as e:
        print(f"Build failed: {e}")

if __name__ == "__main__":
    build_exe()
