import unittest
import subprocess
import sys
import os
import time
import urllib.request
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

class TestCliServerUiIntegration(unittest.TestCase):
    def setUp(self):
        self.port = 18987
        self.host = "127.0.0.1"
        self.backend_process = None

    def tearDown(self):
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()

    def test_cli_doctor_command(self):
        """Verify the CLI doctor command runs successfully and reports health."""
        # run python -m titanos doctor
        cmd = [sys.executable, "-m", "titanos", "doctor"]
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # It should exit with 0
        self.assertEqual(result.returncode, 0)
        self.assertIn("TITANOS Doctor Report", result.stdout)

    def test_cli_server_ui_handshake(self):
        """Verify CLI can start the server and server responds correctly to simulated UI apiService requests."""
        env = {
            **os.environ,
            "TITANOS_DESKTOP_MODE": "1",
            "TITANOS_HOST": self.host,
            "TITANOS_PORT": str(self.port),
            "TITANOS_ENVIRONMENT": "production",
            "TITANOS_JWT_SECRET": "cli-server-ui-handshake-secret",
            "PYDANTIC_DISABLE_PLUGINS": "__all__"
        }
        
        # Start server via CLI
        cmd = [sys.executable, "-m", "titanos", "app", "--port", str(self.port)]
        self.backend_process = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Wait for server ready state
        ready = False
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://{self.host}:{self.port}/readyz", timeout=1) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    if data.get("status") == "ready":
                        ready = True
                        break
            except Exception:
                pass
            time.sleep(0.3)
            
        self.assertTrue(ready, "Server failed to reach ready state within timeout.")
        
        # Simulate UI apiService.getRuntimeStatus()
        with urllib.request.urlopen(f"http://{self.host}:{self.port}/runtime", timeout=2) as res:
            runtime = json.loads(res.read().decode("utf-8"))
        self.assertEqual(runtime.get("mode"), "desktop")
        
        # Simulate UI apiService.getBodyHealth()
        with urllib.request.urlopen(f"http://{self.host}:{self.port}/body/health", timeout=2) as res:
            health = json.loads(res.read().decode("utf-8"))
        self.assertIn("systems", health)
