import unittest
import httpx
import os
import json
from titanos.server.app import app
from titanos.server.auth import create_access_token
from fastapi.testclient import TestClient

client = TestClient(app)

class TestNewAPI(unittest.TestCase):
    def setUp(self):
        self.token = create_access_token({"sub": "testuser"})
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_hands_approvals(self):
        response = client.get("/hands/approvals", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("approvals", response.json())

    def test_classify_command(self):
        response = client.post("/hands/commands/classify", json={"command": "ls"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("risk", data)
        self.assertEqual(data["risk"], "safe")

        response = client.post("/hands/commands/classify", json={"command": "rm -rf /"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["risk"], "blocked")

    def test_file_preview(self):
        # Create a temp file for testing
        test_file = "test_preview_safe.txt"
        with open(test_file, "w") as f:
            f.write("hello world")
        
        try:
            response = client.post("/hands/files/write-preview", json={"path": test_file, "content": "new content"}, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            self.assertIn("diff", response.json())
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_runs_history(self):
        response = client.get("/runs", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("runs", response.json())

    def test_route_explain(self):
        response = client.post("/route/explain", json={"goal": "list files"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["system"].lower(), "hands")

    def test_body_health(self):
        response = client.get("/body/health", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("systems", response.json())

if __name__ == "__main__":
    unittest.main()
