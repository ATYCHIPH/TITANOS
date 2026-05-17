from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_node(source: str) -> dict:
    completed = subprocess.run(
        ["node", "-e", source],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return json.loads(completed.stdout)


class DesktopRuntimeTests(unittest.TestCase):
    def test_runtime_helpers_resolve_source_backend_and_paths(self) -> None:
        data = run_node(
            """
            const rt = require("./desktop/runtime.cjs");
            const command = rt.resolveBackendCommand({
              appIsPackaged: false,
              rootDir: "C:/repo",
              port: 18801,
              python: "python-test"
            });
            const paths = rt.desktopPaths("C:/Users/example/AppData/Roaming/TITANOS");
            console.log(JSON.stringify({
              url: rt.backendUrl(18801),
              command,
              hasRuntime: paths.runtimeDir.includes("runtime"),
              hasLogs: paths.backendOutLog.includes("backend.out.log")
            }));
            """
        )

        self.assertEqual(data["url"], "http://127.0.0.1:18801")
        self.assertEqual(data["command"]["command"], "python-test")
        self.assertEqual(data["command"]["args"], ["-m", "titanos", "app", "--port", "18801"])
        self.assertTrue(data["hasRuntime"])
        self.assertTrue(data["hasLogs"])

    def test_runtime_helpers_reject_missing_packaged_backend(self) -> None:
        data = run_node(
            """
            const rt = require("./desktop/runtime.cjs");
            try {
              rt.resolveBackendCommand({
                appIsPackaged: true,
                resourcesPath: "C:/missing-titanos-resources",
                port: 18802,
                platform: "win32"
              });
              console.log(JSON.stringify({ ok: true }));
            } catch (error) {
              console.log(JSON.stringify({ ok: false, message: error.message }));
            }
            """
        )

        self.assertFalse(data["ok"])
        self.assertIn("Bundled backend not found", data["message"])

    def test_runtime_helpers_find_fallback_port(self) -> None:
        data = run_node(
            """
            const rt = require("./desktop/runtime.cjs");
            rt.findBackendPort(18789, {
              attempts: 3,
              canConnect: async (port) => port === 18789
            }).then((port) => console.log(JSON.stringify({ port })));
            """
        )

        self.assertEqual(data["port"], 18790)

    def test_runtime_helpers_prefer_staged_react_ui(self) -> None:
        data = run_node(
            """
            const fs = require("node:fs");
            const os = require("node:os");
            const path = require("node:path");
            const rt = require("./desktop/runtime.cjs");
            const root = fs.mkdtempSync(path.join(os.tmpdir(), "titanos-ui-"));
            fs.mkdirSync(path.join(root, "ui"), { recursive: true });
            fs.writeFileSync(path.join(root, "ui", "index.html"), "legacy");
            const fallback = rt.resolveUiEntry(root);
            fs.mkdirSync(path.join(root, "desktop-ui"), { recursive: true });
            fs.writeFileSync(path.join(root, "desktop-ui", "index.html"), "react");
            const canonical = rt.resolveUiEntry(root);
            console.log(JSON.stringify({ fallback, canonical }));
            """
        )

        self.assertEqual(data["fallback"]["source"], "legacy")
        self.assertEqual(data["canonical"]["source"], "react")
        self.assertTrue(data["canonical"]["entry"].endswith("desktop-ui\\index.html") or data["canonical"]["entry"].endswith("desktop-ui/index.html"))


if __name__ == "__main__":
    unittest.main()
